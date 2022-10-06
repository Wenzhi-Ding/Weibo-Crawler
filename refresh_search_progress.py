import utils
import sqlite3

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

utils.refresh_search_progress(con)