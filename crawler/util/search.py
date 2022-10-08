import sqlite3
import time
from typing import List
import re
from datetime import datetime
from multiprocessing import Queue

from util.util import log_print, get_api, decode_mid, timestamp_to_query_time, query_time_to_timestamp, KEYWORDS


def get_search_page(keyword: str, start: str, end: str, page: int):
    start = timestamp_to_query_time(start)
    end = timestamp_to_query_time(end, {'hours': 1})  # 实际查询时结束时间向上取整一小时
    api = f'https://s.weibo.com/weibo?q={keyword}&typeall=1&suball=1&timescope=custom:{start}:{end}&page={page}'
    log_print(f"查询API：{api}")
    r = get_api(api, check_cookie=True)
    res = re.findall('(?<=<a href=").+?(?=".*wb_time">)', r)
    data = []
    for u in res:
        u = u.split('/')
        data.append((decode_mid(u[4][:9]), u[3]))  # (mid, uid)

    timestamps = [x.strip() for x in re.findall('(?<=wb_time">)[.\S\s]+?(?=</a>)', r) if '前' not in x]
    timestamps = [f'{datetime.now().year}年{x}' if '年' not in x else x  for x in timestamps]
    timestamps = set([datetime.strptime(x, '%Y年%m月%d日 %H:%M') for x in timestamps])

    return data, timestamps


def dump_posts(data: List[tuple], write_queue: Queue):
    write_queue.put(("INSERT OR IGNORE INTO posts(mid, uid) VALUES (?, ?)", data))


def dump_search_results(data: List[tuple], write_queue: Queue):
    write_queue.put(("INSERT OR IGNORE INTO search_results(keyword, mid) VALUES (?, ?)", data))


def update_keyword_progress(keyword: str, start_time: str, min_time: str, end_time: str, write_queue: Queue):
    write_queue.put(('INSERT INTO keyword_queries(keyword, start_time, min_time, end_time) VALUES (?, ?, ?, ?)', [(keyword, start_time, min_time, end_time)]))


def get_query_periods(start: str, end: str, con: sqlite3.Connection, task_queue: Queue, keywords: List[str]) -> List[tuple]:
    cur = con.cursor()
    start = query_time_to_timestamp(start)
    end = query_time_to_timestamp(end)
    if not keywords:
        log_print("查询待查关键词")
        cur.execute(f'SELECT keyword FROM keyword_queries')
        r = cur.fetchall()
        keywords = set([x[0] for x in r])
    else:
        log_print("使用指定关键词")

    # 更新待搜索队列
    log_print(f"共{len(keywords)}个关键词: {','.join(keywords)}")
    for keyword in keywords:
        periods = [x for x in break_query_period(keyword, start, end, con) if x]
        for period in periods:
            cur.execute(f'SELECT keyword FROM keyword_queries WHERE keyword=? AND start_time=? AND end_time=?', (keyword, period[1], period[2]))
            if cur.fetchall():
                log_print(f"关键词{keyword}在{period[1]}~{period[2]}已经查询过，不加入队列")
                continue
            log_print(f"关键词{keyword}在{period[1]}~{period[2]}未查询过，加入队列")
            task_queue.put(period)


def break_query_period(keyword: str, start: str, end: str, con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute("SELECT min_time, end_time FROM keyword_queries WHERE keyword=?", (keyword,))
    r = cur.fetchall()

    if not r: return [(keyword, start, end)]

    _left = set([start] + [_r for _l, _r in r])
    _right = set([end] + [_l for _l, _r in r])
    left = list(_left - _right)
    right = list(_right - _left)
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


def search_periods(task_queue: Queue, write_queue: Queue, con: sqlite3.Connection, START, END, keywords) -> bool:
    while True:
        time.sleep(3)  # 留足够时间等队列更新
        if task_queue.empty():  # 更新完后仍然无任务则退出
            return True
        else:
            keyword, start, end = task_queue.get()
        all_timestamps = set()
        for page in range(1, 51):
            # 获取搜索页
            data, timestamps = get_search_page(keyword=keyword, start=start, end=end, page=page)
            log_print(f"本页面共{len(data)}条数据")
            if not data: continue  # 无内容或获取失败则跳过该条
            dump_posts(data, write_queue)

            # 记录搜索结果
            sr_data = [(keyword, mid) for mid, uid in data]
            dump_search_results(sr_data, write_queue)

            # 记录搜索结果的时间戳
            all_timestamps |= timestamps

        min_time = min(all_timestamps) if all_timestamps else end  # 完全没有新内容时则视为停止
        update_keyword_progress(keyword=keyword, start_time=start, min_time=min_time, end_time=end, write_queue=write_queue)
        time.sleep(3)  # 留足够时间等writer更新完数据库

        if task_queue.empty(): get_query_periods(START, END, con, task_queue, keywords)  # 如果队列已空，则更新队列


def add_keywords(keywords: List[str], write_queue: Queue):
    write_queue.put((f'INSERT OR IGNORE INTO keyword_queries(keyword) VALUES (?)', keywords))


def get_keywords():
    with open(KEYWORDS, 'r') as f:
        keywords = f.readlines()
    keywords = [x.strip() for x in keywords]
    keywords = [x for x in keywords if x]
    if not keywords:
        raise Exception("关键词文件为空，请检查keywords.txt或crawler.ini中的keywords变量。")
    return keywords

# def refresh_search_progress(con: sqlite3.Connection):
#    算法整合清理search_progress表
