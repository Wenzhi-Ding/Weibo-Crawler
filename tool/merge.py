import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from util.util import MERGE, connect_db

con = connect_db()
print('数据库读取连接创建成功')

cur = con.cursor()

for ndb in os.listdir(MERGE):
    cur.execute(f"ATTACH '{MERGE}/{ndb}' as ndb")
    # 正常更新各个表
    for table in ['posts', 'keyword_queries', 'search_results']:
        main_table = set([x[1] for x in cur.execute(f'PRAGMA table_info({table})').fetchall()])
        new_table = set([x[1] for x in cur.execute(f'PRAGMA ndb.table_info({table})').fetchall()])
        cols = ','.join(main_table & new_table)
        if cols:
            cur.execute(f'INSERT OR IGNORE INTO {table}({cols}) SELECT {cols} FROM ndb.{table}')
            con.commit()

    cur.execute('UPDATE posts SET (data, data_at) = (np.data, np.data_at) FROM ndb.posts AS np WHERE posts.mid=np.mid AND posts.data IS NULL AND np.data IS NOT NULL;')
    con.commit()
    
    cur.execute(f"DETACH ndb")
    con.commit()

print('数据库合并及更新完成')