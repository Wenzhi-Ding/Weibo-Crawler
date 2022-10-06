import utils
import sqlite3
from multiprocessing import Process, Queue, JoinableQueue


START = "2010-01-01-0"
END = "2020-01-01-0"

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

if __name__ == "__main__":

    task_queue = JoinableQueue()
    write_queue = Queue()

    utils.get_query_periods(START, END, con, task_queue)
    writer = Process(target=utils.write_sqlite, args=(write_queue,))
    worker1 = Process(target=utils.search_period, args=(task_queue, write_queue, con, START, END, "worker1.log"))
    worker2 = Process(target=utils.search_period, args=(task_queue, write_queue, con, START, END, "worker2.log"))


    writer.start()
    worker1.start()
    worker2.start()

    writer.join()
    worker1.join()
    worker2.join()

    writer.terminate()