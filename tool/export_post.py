import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from util.util import connect_db, write_csv

HEADER = ['mid', 'uid', 'nick_name', 'created_at', 'content', 'repost_count', 'comment_count', 'attitude_count', 'abstract_at']

con = connect_db()
script = f"SELECT {','.join(HEADER)} FROM posts"

# 使用标准库
cur = con.cursor()
write_csv(table='posts', cur=cur.execute(script), header=HEADER)

# 如果你有Pandas，可以使用Pandas的DataFrame来导出数据
# import pandas as pd
# from util.util import OUTPUT
# df = pd.read_sql(script, con, columns=HEADER)
# df.to_csv(f'{OUTPUT}/posts.csv', index=False, encoding='utf-8')
# df.to_parquet(f'{OUTPUT}/posts.pq', encoding='utf-8')
# df.to_excel(f'{OUTPUT}/posts.xlsx', index=False, encoding='utf-8')

print('已导出posts至output目录')