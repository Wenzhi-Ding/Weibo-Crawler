import sqlite3
import time
from typing import List
import requests
import re
from datetime import datetime, timedelta
import random

from py_reminder import send_email

import numpy as np
import base62

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'
}


def get_expired_cookies():
    with open('expired_cookies.txt', 'r') as f:
        cookies = f.readlines()
    cookies = [x.strip() for x in cookies]
    return cookies


def add_expired_cookie(sub):
    with open('expired_cookies.txt', 'a') as f:
        f.write(f'{sub}\n')


def get_random_cookie():
    with open('cookies.txt', 'r') as f:
        cookies = f.readlines()
    cookies = [x.strip().split() for x in cookies]
    cookies = [(sub, name) for sub, name in cookies if sub not in get_expired_cookies()]
    if not cookies:
        send_email(task="没有可用COOKIE")
        raise Exception("没有可用COOKIE")
    return random.choice(cookies)


def get_api(api: str, wait=1, check_cookie=False, retries=3):
    sub, name = get_random_cookie()
    r = requests.get(api, headers=HEADERS, cookies={'SUB': sub})

    for _ in range(retries):
        time.sleep(random.randint(wait, wait + 2))
        if r.status_code in [200, 304]:
            r = r.content.decode()
            if check_cookie and "$CONFIG[\'watermark\']" not in r:
                # send_email(task=f"{name}的COOKIE可能过期")  # 等所有COOKIE都不能用了再提示
                print(f"{name}的COOKIE可能过期")
                add_expired_cookie(sub)
            return r
    # raise ValueError('API未能成功访问。')
    print('API未能成功访问。')


def get_search_page(keyword: str, start: str, end: str, page: int):
    api = f'https://s.weibo.com/weibo?q={keyword}&typeall=1&suball=1&timescope=custom:{start}:{end}&page={page}'
    r = get_api(api, check_cookie=True)
    res = re.findall('(?<=<a href=").+?(?=".*wb_time">)', r)
    data = []
    for u in res:
        u = u.split('/')
        data.append((decode_mid(u[4][:9]), u[3]))  # (mid, uid)
    return data


def get_post_json(mid: str):
    emid = encode_mid(mid)
    api = f'https://weibo.com/ajax/statuses/show?id={emid}'
    # print(api)
    r = get_api(api)
    return r


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
    cur.execute(f"UPDATE posts SET data='{json}' WHERE mid={mid}")
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


def update_keyword_progress(keyword: str, end_time: str, con: sqlite3.Connection, mids=[], start_time=""):
    if mids:
        cur = con.cursor()
        cur.execute(f'SELECT json_extract(data,"$.created_at") FROM posts WHERE mid in ({",".join(mids)}) AND data NOT NULL')
        created_at = cur.fetchall()
        if not created_at: return 0  # 当前页面没爬到数据，就不更新进度
        ts = [datetime.strptime(t[0], '%a %b %d %H:%M:%S %z %Y') for t in created_at]
    min_timestamp = datetime.strptime(start_time, '%Y-%m-%d-%H').strftime('%Y-%m-%d %H:%M:%S') if start_time else min(ts).strftime('%Y-%m-%d %H:%M:%S')
    # max_timestamp = max(ts).strftime('%Y-%m-%d %H:%M:%S')
    max_timestamp = datetime.strptime(end_time, '%Y-%m-%d-%H').strftime('%Y-%m-%d %H:%M:%S')  # Use query end time as max timestamp

    cur.execute(f'SELECT * FROM keywords WHERE keyword="{keyword}"')
    r = cur.fetchall()

    if r:
        _, st, et, _ = r[0]
        st = min(st, min_timestamp)
        et = max(et, max_timestamp)
        cur.execute(f'UPDATE keywords SET start_time="{st}", end_time="{et}" WHERE keyword="{keyword}"')
        con.commit()
    else:
        cur.execute(f'INSERT INTO keywords(keyword, start_time, end_time) VALUES ("{keyword}", "{min_timestamp}", "{max_timestamp}")')
        con.commit()


def get_query_periods(keyword: str, start: str, end: str, con: sqlite3.Connection) -> List[tuple]:
    cur = con.cursor()
    cur.execute(f'SELECT * FROM keywords WHERE keyword="{keyword}"')
    r = cur.fetchall()
    kw, st, et, ut = r[0]
    start = datetime.strptime(start, '%Y-%m-%d-%H').strftime('%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(end, '%Y-%m-%d-%H').strftime('%Y-%m-%d %H:%M:%S')

    periods = []
    if st > start:
        _end = (datetime.strptime(st, '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)).strftime('%Y-%m-%d-%-H')
        _start = (datetime.strptime(start, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d-%-H')
        periods.append((_start, _end))

    if et < end:
        _end = (datetime.strptime(end, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d-%-H')
        _start = (datetime.strptime(et, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d-%-H')
        periods.append((_start, _end))

    return periods


def search_period(keyword: str, start: str, end: str, con: sqlite3.Connection) -> bool:
    new_posts = 0
    for page in range(1, 51):
        print(f'keyword={keyword} start={start} end={end} page={page}')

        # 获取搜索页
        data = get_search_page(keyword=keyword, start=start, end=end, page=page)
        if not data: continue  # 获取失败则跳过该条
        dump_posts(data, con)

        # 记录搜索结果
        sr_data = [(keyword, mid) for mid, uid in data]
        dump_search_results(sr_data, con)

        # 获取搜索结果的详细数据
        mids = [mid for mid, uid in data]
        mids = con.execute(f'SELECT mid FROM posts WHERE data IS NULL and mid IN ({",".join(mids)})').fetchall()
        if not mids:
            print("所有搜索结果已经获取过详细数据")
            continue
        mids = [str(x[0]) for x in mids]
        new_posts += len(mids)
        for mid in mids:
            print(mid)
            json = get_post_json(mid)
            if json: dump_post_content((mid, json), con)

        # 更新搜索进度
        update_keyword_progress(keyword=keyword, mids=mids, end_time=end, con=con)

    if new_posts == 0:
        print("此区间无新数据")
        update_keyword_progress(keyword=keyword, end_time=end, start_time=start, con=con)
        return False
    else:
        return True


def add_keywords(keywords: List[str], con: sqlite3.Connection):
    cur = con.cursor()
    cur.executemany(f'INSERT OR IGNORE INTO keywords(keyword) VALUES (?)', keywords)
    con.commit()