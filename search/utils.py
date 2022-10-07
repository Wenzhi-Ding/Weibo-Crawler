import sqlite3
import time
from typing import List
import requests
import re
from datetime import datetime, timedelta
import random
from multiprocessing import Queue
import logging
import os

# from py_reminder import send_email
import base62

logging.basicConfig(filename=os.path.dirname(__file__) + '/../log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
        # send_email(task="没有可用COOKIE")
        raise Exception("没有可用COOKIE")
    return random.choice(cookies)


def get_api(api: str, wait=2, check_cookie=False, retries=3):
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
    logger = logging.getLogger("get_search_page")
    start = timestamp_to_query_time(start)
    end = timestamp_to_query_time(end)
    api = f'https://s.weibo.com/weibo?q={keyword}&typeall=1&suball=1&timescope=custom:{start}:{end}&page={page}'
    logger.info(f"查询API：{api}")
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


def dump_posts(data: List[tuple], write_queue: Queue):
    write_queue.put(("INSERT OR IGNORE INTO posts(mid, uid) VALUES (?, ?)", data))


def dump_search_results(data: List[tuple], write_queue: Queue):
    write_queue.put(("INSERT OR IGNORE INTO search_results(keyword, mid) VALUES (?, ?)", data))


def dump_post_content(data: tuple, write_queue: Queue):
    write_queue.put(("UPDATE posts SET data=? WHERE mid=?", [data]))


def dump_post_content_non_parallel(data: tuple, con: sqlite3.Connection):
    cur = con.cursor()
    cur.executemany("UPDATE posts SET data=? WHERE mid=?", [data])
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


def update_keyword_progress(keyword: str, start_time: str, end_time: str, mids: List[str], con: sqlite3.Connection, write_queue: Queue):
    logger = logging.getLogger('update_keyword_progress')
    cur = con.cursor()
    cur.execute(f'SELECT json_extract(data,"$.created_at") FROM posts WHERE mid in ({",".join(mids)}) AND data NOT NULL')
    created_at = cur.fetchall()
    if not created_at: return 0  # 当前页面没爬到数据，就不更新进度
    ts = [datetime.strptime(t[0], '%a %b %d %H:%M:%S %z %Y') for t in created_at]
    logger.info(ts)
    min_time = query_time_to_timestamp(min(ts))
    logger.info(min_time)

    write_queue.put(('INSERT INTO keyword_queries(keyword, start_time, min_time, end_time) VALUES (?, ?, ?, ?)', [(keyword, start_time, min_time, end_time)]))


def query_time_to_timestamp(query_time, shift={}):
    if not isinstance(query_time, datetime):
        query_time = datetime.strptime(query_time, '%Y-%m-%d-%H')
    if shift:
        timestamp += timedelta(**shift)
    return query_time.strftime('%Y-%m-%d %H:%M:%S')


def timestamp_to_query_time(timestamp, shift={}):
    if not isinstance(timestamp, datetime):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    if shift:
        timestamp += timedelta(**shift)
    return timestamp.strftime('%Y-%m-%d-%H')


def get_query_periods(start: str, end: str, con: sqlite3.Connection, task_queue: Queue) -> List[tuple]:
    print("查询待查关键词")
    start = query_time_to_timestamp(start)
    end = query_time_to_timestamp(end)

    cur = con.cursor()
    cur.execute(f'SELECT keyword FROM keyword_queries')  #  WHERE "{start}" < start_time OR end_time < "{end}" OR start_time IS NULL OR end_time IS NULL
    r = cur.fetchall()
    keywords = [x[0] for x in r]

    # 更新待搜索队列
    print(f"共{len(keywords)}个关键词")
    for keyword in keywords:
        periods = break_query_period(keyword, start, end, con)
        for period in periods:
            task_queue.put(period)


def break_query_period(keyword: str, start: str, end: str, con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute("SELECT min_time, end_time FROM keyword_queries WHERE keyword=?", (keyword,))
    r = cur.fetchall()

    if not r: return [(keyword, start, end)]

    left = [start] + [_r for _l, _r in r]
    right = [end] + [_l for _l, _r in r]
    left.sort(reverse=True)
    right.sort(reverse=True)

    periods = []
    while left and right:
        _l = left.pop()
        _r = right.pop()
        while _l == _r and right:
            _r = right.pop()
        if _l < _r:
            periods.append((keyword, _l, _r))
            
    return periods


def search_period(task_queue: Queue, write_queue: Queue, con: sqlite3.Connection, START, END) -> bool:
    logger = logging.getLogger('search_period')
    while True:
        keyword, start, end = task_queue.get()
        if start >= end:
            _s = f"{keyword}查询开始时间不小于结束时间：{start} >= {end}"
        all_mids = set()
        for page in range(1, 51):
            _s = f'keyword={keyword} start={start} end={end} page={page}'
            logging.info(_s)
            print(_s)

            # 获取搜索页
            data = get_search_page(keyword=keyword, start=start, end=end, page=page)
            if not data: continue  # 获取失败则跳过该条
            dump_posts(data, write_queue)

            # 记录搜索结果
            sr_data = [(keyword, mid) for mid, uid in data]
            dump_search_results(sr_data, write_queue)

            # 获取搜索结果的详细数据
            mids = set([mid for mid, uid in data])
            all_mids |= mids
            logging.info((keyword, "本页微博", mids))
            print(keyword, mids)
            cur = con.cursor()
            cur.execute(f'SELECT mid FROM posts WHERE data IS NULL and mid IN ({",".join(mids)})')
            mids = cur.fetchall()
            if not mids:
                _s = "所有搜索结果已经获取过详细数据"
                logging.info((keyword, mids))
                print(keyword, _s)
                continue
            mids = [str(x[0]) for x in mids]
            for mid in mids:
                logging.info((keyword, "查询微博", mid))
                print(keyword, mid)
                json = get_post_json(mid)
                if json: dump_post_content((json, mid), write_queue)

        get_no_data_posts(con=con, write_queue=write_queue)  # 尝试补齐漏的数据

        update_keyword_progress(keyword=keyword, end_time=end, start_time=start, mids=all_mids, con=con, write_queue=write_queue)

        if task_queue.empty(): get_query_periods(START, END, con, task_queue)  # 更新队列


def add_keywords(keywords: List[str], write_queue: Queue):
    write_queue.put((f'INSERT OR IGNORE INTO keywords(keyword) VALUES (?)', keywords))


def write_sqlite(write_queue: Queue):
    logger = logging.getLogger('write')
    write_con = sqlite3.connect('weibo.db')
    print('数据库写入连接创建成功')
    cur = write_con.cursor()
    while True:
        try:
            script, data = write_queue.get()
            cur.executemany(script, data)
            write_con.commit()
        except:
            logger.exception('写入数据库出错')


def refresh_search_progress(con: sqlite3.Connection):
    cur = con.cursor()

    cur.execute("UPDATE keyword_queries SET start_time=NULL, end_time=NULL, min_time=NULL")
    con.commit()

    cur.execute("SELECT DISTINCT(keyword) FROM search_results")
    r = cur.fetchall()
    keywords = [x[0] for x in r]
    for keyword in keywords:
        cur.execute(f"""
            SELECT
                json_extract(posts.data,"$.created_at")
            FROM posts
            INNER JOIN search_results ON posts.mid = search_results.mid
            WHERE 
                posts.data not null
                AND search_results.keyword=?
            """, [keyword])
        r = cur.fetchall()
        r = [datetime.strptime(x[0], "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d %H:%M:%S") for x in r if x[0] is not None]
        if not r: continue
        st = min(r)
        et = max(r)
        cur.execute("UPDATE keyword_queries SET start_time=?, end_time=? WHERE keyword=?", (st, et, keyword))
        con.commit()


def get_no_data_posts(con: sqlite3.Connection, write_queue: Queue):
    cur = con.cursor()
    cur.execute(f'SELECT mid FROM posts WHERE data IS NULL')
    r = cur.fetchall()

    print("尝试补缺：", r)

    for mid in r:
        mid = str(mid[0])
        print(mid)
        json = get_post_json(mid)
        dump_post_content((json, mid), write_queue)