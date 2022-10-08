import os
import utils
import sqlite3
import os

con = sqlite3.connect(os.path.dirname(__file__) + '/../weibo.db')

cur = con.cursor()
cur.execute(f'SELECT mid FROM posts WHERE data IS NULL')
r = cur.fetchall()

print(r)

for mid in r:
    mid = str(mid[0])
    print(mid)
    json = utils.get_post_json(mid)
    utils.dump_post_content_non_parallel((json, mid), con)