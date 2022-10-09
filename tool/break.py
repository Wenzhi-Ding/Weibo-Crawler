import sys
import os
import sqlite3
sys.path.append(os.path.dirname(__file__) + '/..')

from util.util import parse_config, BREAK, connect_db

cfg = parse_config()
n_worker = cfg['n_worker']

con = connect_db()
print('数据库读取连接创建成功')

cur = con.cursor()
cur.execute('SELECT mid FROM posts WHERE data IS NULL')
r = cur.fetchall()

r = [(i[0], None) for i in r]

size = len(r) // n_worker
rs = [r[i::n_worker] for i in range(n_worker)]

if not os.path.exists(BREAK): os.mkdir(BREAK)

for db in os.listdir(BREAK):
    os.remove(f'{BREAK}/{db}')

for i in range(n_worker):
    new_con = sqlite3.connect(f'{BREAK}/weibo.db.{i}')

    cur = new_con.cursor()
    cur.execute('CREATE TABLE posts (mid INTEGER PRIMARY KEY, data TEXT, data_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    new_con.commit()
    cur.executemany('INSERT INTO posts (mid, data_at) VALUES (?, ?)', rs[i])
    new_con.commit()

print('未完成数据已分配至break文件夹')