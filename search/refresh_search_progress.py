import utils
import sqlite3
import os

con = sqlite3.connect(os.path.dirname(__file__) + '/../weibo.db')

utils.refresh_search_progress(con)