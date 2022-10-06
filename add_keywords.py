import utils
import sqlite3

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

with open('add_keywords.txt', 'r') as f:
    keywords = f.readlines()

keywords = [(k.strip(),) for k in keywords]
print(keywords)

utils.add_keywords(keywords, con)