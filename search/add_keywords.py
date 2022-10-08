import utils
import sqlite3
import os

con = sqlite3.connect(os.path.dirname(__file__) + '/../weibo.db')

with open('add_keywords.txt', 'r') as f:
    keywords = f.readlines()

keywords = [(k.strip(),) for k in keywords]
print(keywords)

utils.add_keywords(keywords, con)