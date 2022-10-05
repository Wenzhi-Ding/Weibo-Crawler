import sqlite3
import time
from typing import List
import requests
import re

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
    mid = mid.swapcase()
    a, b, c = mid[0], mid[1:5], mid[5:]
    return str(base62.decode(a)) + str(base62.decode(b)).zfill(7) + str(base62.decode(c)).zfill(7)


def encode_mid(mid: str):
    '''4021924038830731 -> E9cllB3h9'''
    a, b, c = mid[:2], mid[2:9], mid[9:]
    return (base62.encode(int(a)) + base62.encode(int(b)) + base62.encode(int(c))).swapcase()