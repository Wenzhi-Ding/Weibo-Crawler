from ast import keyword
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from util.util import connect_db, write_csv

HEADER = [
    'posts.mid', 'posts.uid', 'posts.nick_name', 'posts.created_at', 
    'posts.content', 'posts.repost_count', 'posts.comment_count', 
    'posts.attitude_count', 'posts.abstract_at']

con = connect_db()

# 使用标准库
cur = con.cursor()
keywords = cur.execute("SELECT keyword FROM search_results GROUP BY keyword").fetchall()
keywords = {x[0] for x in keywords}
print(keywords)

for keyword in keywords:
    script = f"SELECT {','.join(HEADER)} FROM posts INNER JOIN search_results ON posts.mid = search_results.mid WHERE keyword = '{keyword}'"
    write_csv(table='posts', cur=cur.execute(script), header=HEADER, keyword=keyword)

print('已导出posts至output目录')