from datetime import datetime
import sqlite3
from multiprocessing import Queue
from typing import List

from util.util import get_api, log_print, encode_mid, monitor


def get_post_json(mid: str, con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute(f'SELECT mid FROM posts WHERE data IS NULL and mid=?', (mid,))
    if not cur.fetchall():
        log_print(f"已爬取微博{mid}，跳过")
        return ''
    log_print(f"正在爬取微博{mid}")
    emid = encode_mid(mid)
    api = f'https://weibo.com/ajax/statuses/show?id={emid}'
    r = get_api(api)
    return r


def dump_post_content(data: tuple, write_queue: Queue):
    write_queue.put(("UPDATE posts SET data=?, data_at=? WHERE mid=?", [data]))


def dump_post_content_non_parallel(data: tuple, con: sqlite3.Connection):
    cur = con.cursor()
    cur.executemany("UPDATE posts SET data=? WHERE mid=?", [data])
    con.commit()


@monitor('微博JSON数据下载')
def get_post_contents(con: sqlite3.Connection, write_queue: Queue, keywords: List[str]):
    cur = con.cursor()
    if not keywords:  # 对所有未完成的微博进行内容爬取
        cur.execute('SELECT mid FROM posts WHERE data IS NULL')
    else:
        s = ",".join([f"'{x}'" for x in keywords])
        cur.execute(f"SELECT posts.mid FROM search_results INNER JOIN posts ON search_results.mid = posts.mid WHERE search_results.keyword IN ({s}) AND posts.data IS NULL") 
    r = cur.fetchall()

    log_print(f'获取到{len(r)}条无数据的微博')

    for mid in r:
        mid = str(mid[0])
        json = get_post_json(mid, con)
        if json: dump_post_content((json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mid), write_queue)
