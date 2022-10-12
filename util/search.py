import sqlite3
import time
from typing import List
import re
from datetime import datetime, timedelta
from multiprocessing import Queue

from util.util import log_print, get_api, decode_mid, timestamp_to_query_time, query_time_to_timestamp, KEYWORDS, monitor


def get_search_page(keyword: str, start: str, end: str, page: int):
    start = timestamp_to_query_time(start)
    end = timestamp_to_query_time(end, {'hours': 1})  # 实际查询时结束时间向上取整一小时
    api = f'https://s.weibo.com/weibo?q={keyword}&nodup=1&typeall=1&suball=1&timescope=custom:{start}:{end}&page={page}'
    log_print(f"查询API：{api}")
    r = get_api(api, check_cookie=True)
    posts = re.findall('"feed_list_item"[.\s\S]*?(?=<div class="m-footer">)', r)
    if posts: 
        posts = posts[0].split('"feed_list_item"')
        posts = [x for x in posts if x]
        data = [parse_post(post) for post in posts]
        return data
    
    return []


def parse_post(post):
    url = re.findall('(?<=<a href="//weibo.com/).+?(?=".*wb_time">)', post)
    uid, mid, *k = re.split('[/\?]', url[0]) if url else (None, None, [])
    mid = decode_mid(mid) if mid else None

    nn = re.findall('(?<=nick-name=").+?(?=")', post)
    nn = nn[0] if nn else None

    create_at = re.findall('(?<=click:wb_time">)[.\s\S]+?(?=</a>)', post)
    create_at = parse_date(create_at[0]) if create_at else None

    if "feed_list_content_full" in post:
        p = re.findall('(?<="feed_list_content_full")[.\s\S]+?(?=</p>)', post)
    else:
        p = re.findall('(?<="feed_list_content")[.\s\S]+?(?=</p>)', post)

    if p:
        p = re.sub('<br.*?/>', '\n', p[0])
        p = p.split('>\n', maxsplit=1)[1]
        p = p.replace('<i class="wbicon">O</i>网页链接', '').replace('收起<i class="wbicon">d</i>', '').replace('<i class="wbicon">\ue627</i>', '##')
        p = re.sub('<[a|/a|i|/i|img].*?>', '', p).replace('\u200b', '').replace('\u3000', '').strip()
        p = p.replace('&#xe627;', '##')  # 用两个#号代替超话符号
    else:
        p = None

    repost, comment = re.findall('(?<=</i></span>)[.\s\S]+?(?=</a></li>)', post)
    repost = None if not repost else 0 if not repost.strip().isdigit() else int(repost)
    comment = None if not comment else 0 if not comment.strip().isdigit() else int(comment)

    attitude = re.findall('(?<=class="woo-like-count">)[.\s\S]+?(?=</span>)', post)
    attitude = None if not attitude else 0 if not attitude[0].strip().isdigit() else int(attitude[0])

    return mid, uid, nn, create_at, p, repost, comment, attitude


def dump_posts(data: List[tuple], write_queue: Queue):
    write_queue.put((f'INSERT OR IGNORE INTO posts(mid, uid, nick_name, created_at, content, repost_count, comment_count, attitude_count) VALUES (?,?,?,?,?,?,?,?)', data))


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


def parse_date(s):
    s = s.strip()
    if '秒前' in s:
        return datetime.now() - timedelta(seconds=int(s[:-2]))
    elif '分钟前' in s:
        d = datetime.now() - timedelta(minutes=int(s[:-3]))
    else:
        if '今天' in s:
            s = s.replace('今天', datetime.now().strftime('%Y年%m月%d日 '))
        elif '年' not in s:
            s = f'{datetime.now().year}年{s}'

        s = datetime.strptime(s, '%Y年%m月%d日 %H:%M')

    return s.strftime('%Y-%m-%d %H:%M:%S')


@monitor('微博关键词搜索', mute_success=False)
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
            data = get_search_page(keyword=keyword, start=start, end=end, page=page)
            log_print(f"本页面共{len(data)}条数据")
            if not data: continue  # 无内容或获取失败则跳过该条
            dump_posts(data, write_queue)

            # 记录搜索结果
            sr_data = [(keyword, mid) for mid, *_ in data]
            dump_search_results(sr_data, write_queue)

            # 记录搜索结果的时间戳
            timestamps = set([create_at for _, _, _, create_at, *_ in data if create_at])
            all_timestamps |= timestamps

        min_time = min(all_timestamps) if all_timestamps else end  # 完全没有新内容时则视为停止
        update_keyword_progress(keyword=keyword, start_time=start, min_time=min_time, end_time=end, write_queue=write_queue)
        time.sleep(3)  # 留足够时间等writer更新完数据库

        if task_queue.empty(): get_query_periods(START, END, con, task_queue, keywords)  # 如果队列已空，则更新队列
