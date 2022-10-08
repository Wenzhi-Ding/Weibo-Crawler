# Weibo User Crawler

本爬虫用于爬取特定用户的所有微博。使用方法

```bash
python run.py [-n|--nickname nickname] [-u|--uid uid] [-s|--start start_time] [-e|--end end_time]
```

其中：

- `-n`或`--nickname`：（可选）指定需要查询的昵称，将返回一个列表的用户供选择。
- `-u`或`--uid`：（可选）指定需要查询的用户ID。
- `-s`或`--start`：（可选）指定查询开始的日期。如未指定，默认从最早日期开始。
- `-e`或`--end`：（可选）指定查询结束的日期。如未指定，默认到最近日期结束。