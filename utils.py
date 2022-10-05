import sqlite3
import time
from typing import List
import requests
import re
from datetime import datetime

import numpy as np
import base62

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'
}

COOKIES = {'SUB': '_2A25OOQJIDeRhGeFI41MY9ivFyz6IHXVtT3SArDV8PUNbmtAKLXj8kW9NfMwjonOeAz-iUncOg-Uw1Bx8474j71Ch'}


def get_api(api: str, wait=3):
    r = requests.get(api, headers=HEADERS, cookies=COOKIES)
    time.sleep(np.random.randint(wait, wait + 5))
    if r.status_code in [200, 304]:
        return r
    else:
        raise ValueError('API未能成功访问。')


def get_search_page(keyword: str, start: str, end: str, page: int):
    api = f'https://s.weibo.com/weibo?q={keyword}&typeall=1&suball=1&timescope=custom:{start}:{end}&page={page}'
    r = get_api(api)
    # print(r.content.decode())
    res = re.findall('(?<=<a href=").+?(?=".*wb_time">)', r.content.decode())
    data = []
    for u in res:
        u = u.split('/')
        data.append((decode_mid(u[4][:9]), u[3]))  # (mid, uid)
    return data


def get_post_json(mid: str):
    emid = encode_mid(mid)
    api = f'https://weibo.com/ajax/statuses/show?id={emid}'
    r = get_api(api)
    return r.content.decode()


def dump_posts(data: List[tuple], con: sqlite3.Connection):
    cur = con.cursor()
    cur.executemany("INSERT OR IGNORE INTO posts(mid, uid) VALUES (?, ?)", data)
    con.commit()


def dump_search_results(data: List[tuple], con: sqlite3.Connection):
    cur = con.cursor()
    cur.executemany("INSERT OR IGNORE INTO search_results(keyword, mid) VALUES (?, ?)", data)
    con.commit()


def dump_post_content(data: tuple, con: sqlite3.Connection):
    mid, json = data
    cur = con.cursor()
    cur.execute(f"UPDATE posts SET data='{json}', status=1 WHERE mid={mid}")
    # cur.execute(f"INSERT OR REPLACE INTO posts(mid, uid, data, status) VALUES ({mid}, (SELECT uid from posts where mid={mid}), '{json}', 1)")
    con.commit()


def decode_mid(mid: str):
    '''4021924038830731 <- E9cllB3h9'''
    mid = mid.swapcase()
    a, b, c = mid[0], mid[1:5], mid[5:]
    return str(base62.decode(a)) + str(base62.decode(b)).zfill(7) + str(base62.decode(c)).zfill(7)


def encode_mid(mid: str):
    '''4021924038830731 -> E9cllB3h9'''
    a, b, c = mid[:2], mid[2:9], mid[9:]
    return (base62.encode(int(a)) + base62.encode(int(b)).zfill(4) + base62.encode(int(c)).zfill(4)).swapcase()


def update_keyword_progress(keyword: str, mids: List[str], con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute(f'SELECT json_extract(data,"$.created_at") FROM posts WHERE mid in ({",".join(mids)})')
    created_at = cur.fetchall()
    ts = [datetime.strptime(t[0], '%a %b %d %H:%M:%S %z %Y') for t in created_at]
    min_timestamp = min(ts).strftime('%Y-%m-%d %H:%M:%S')
    max_timestamp = max(ts).strftime('%Y-%m-%d %H:%M:%S')

    cur.execute(f'SELECT * FROM keywords WHERE keyword="{keyword}"')
    r = cur.fetchall()

    if r:
        _, st, et, _ = r[0]
        st = min(st, min_timestamp)
        et = max(et, max_timestamp)
        cur.execute(f'UPDATE keywords SET start_time="{st}", end_time="{et}" WHERE keyword="{keyword}"')
    else:
        cur.execute(f'INSERT INTO keywords(keyword, start_time, end_time) VALUES ("{keyword}", "{min_timestamp}", "{max_timestamp}")')