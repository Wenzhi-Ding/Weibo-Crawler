import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from multiprocessing import Process, Queue

from util.util import write_sqlite, log_print, parse_config, connect_db, MIDS
from util.content import get_post_contents

cfg = parse_config()

con = connect_db()
print('数据库读取连接创建成功')

if __name__ == "__main__":

    task_queue = Queue()
    write_queue = Queue()
    print("队列初始化成功")

    write = Process(target=write_sqlite, args=(write_queue,))
    write.start()

    try:
        if os.path.isfile(MIDS):
            with open(MIDS, 'r') as f:
                mids = f.read().splitlines()
            valid_mids = [(int(mid),) for mid in mids if len(mid) == 16 and mid.isdigit()]
            log_print(f"mids.txt 中共 {len(valid_mids)} 个有效微博 ID")
            cur = con.cursor()
            cur.executemany("INSERT OR IGNORE INTO posts(mid) VALUES (?)", valid_mids)
            con.commit()

        if cfg['multi_process']:
            content = Process(target=get_post_contents, args=(con, write_queue, []))
            content.start()
            content.join()
        else:
            get_post_contents(con, write_queue, [])
    except KeyboardInterrupt:
        write.terminate()
        log_print("任务被中止，退出程序")
    else:
        write.terminate()
        log_print("任务执行完毕，退出程序")