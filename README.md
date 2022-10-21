# Weibo Crawler

微博爬虫。以 SQLite 形式存储数据，支持多进程、随机 Cookie、随机代理等功能。爬虫包含以下模块：
- User：用户页面的完整爬取（已完成，未整合）
- Search：基于关键词及时间区间的爬取（已完成）
- Content：爬取某条微博的JSON数据（已完成）
- Repost：爬取某条微博的所有转发
- Comment：爬取某条微博的所有评论
- Topic：爬取话题或超话内的微博
- Trending：记录热搜榜

该项目是业余练手用，其他模块作者本人未必有时间完成。非常欢迎发起 Pull Request！

如果使用过程中遇到问题，请在 GitHub 仓库的 Issues 板块提出。

## 依赖

本爬虫完全以 Python 标准库完成，额外依赖仅 SQLite 3 一项。一般而言，Python 已经自带了对 SQLite 3 的支持。若提示找不到 SQLite 3，可以参考 [该网页](https://www.runoob.com/sqlite/sqlite-installation.html) 安装。

请使用 Python 3.6 以上的版本。

## 下载

### 不安装 Git

若不使用 Git，可以直接下载代码的 [压缩包](https://github.com/Wenzhi-Ding/Weibo-Crawler/archive/refs/heads/master.zip) 并解压。

### 安装 Git

若使用 Windows 系统，请先安装 [Git](https://www.liaoxuefeng.com/wiki/896043488029600)。

在命令行中（Windows 的 PowerShell、CMD；Linux 的 Bash；MacOS 的 Terminal）先切换至你希望存放项目的路径：
```bash
cd C:\Users\xxx\Desktop
```

然后运行此命令下载项目：

```bash
git clone https://github.com/Wenzhi-Ding/Weibo-Crawler.git
```

## 使用

1. 切换目录

每次使用首先要确保在命令行中已切换到项目文件夹，否则将无法正常使用以下任何脚本。比如项目位置是 `C:\Users\xxx\Desktop\Weibo-Crawler`，应首先：
```bash
cd C:\Users\xxx\Desktop\Weibo-Crawler
```

2. 初始化项目

若首次运行该爬虫或希望重置项目（清空数据库、日志、过期 Cookies 等），请先运行：
```bash
python tool/init_project.py
```

3. Cookies

对于 `cookies.txt` 文件，请先登录微博后，按 `F12` 打开检查工具，在“网络 (Network)”页面下，选择任意一条含 Cookies 的请求，右键“复制值”，粘贴进 `cookies.txt` 文件即可。该文件每行保存一个 Cookies，在运行时将自动随机调用。可以只放一个 Cookies。

4. 搜索关键词

如果使用关键词搜索爬虫，需要将关键词放入 `keywords.txt` 中。

5. 运行爬虫

此后每次使用，用户只需运行（请先确保 `settings.ini` 已经妥善设置）：
```bash
python run.py
```

6. 中止爬虫

若需要中止程序，请在终端键入 `Ctrl+C` 使程序退出。

## 报告

在任何时候，如果需要监控爬虫进展，可以使用以下脚本：
```bash
python tool/summary.py
```

在 `settings.ini` 中，如果将 `monitor` 选项设置为1，程序将在以下情况发送邮件：
- 每隔一段时间发送一次爬取进度报告（由 `settings.ini` 中的 `interval` 参数决定间隔）
- 运行出错（如 Cookies 过期失效）
- 爬取任务完成

使用该选项需要首先配置 [py_reminder](https://github.com/Wenzhi-Ding/py_reminder)。推荐使用 163 邮箱作为报告的发送邮箱（已经稳定使用 3 年）。


## 取用数据

对于不熟悉 Python 的用户，可以直接运行以下脚本将 `posts` 表格导出为 CSV 文件：
```bash
python tool/export_post.py
```

需注意的是，该 CSV 文件用 Excel 或 WPS 打开可能会乱码，建议在其他数据处理工具（如 Pandas、R、Stata 等）中直接打开。

Python 用户可以修改上面的脚本导出 Parquet、Feather、Pickle 或 HDF5 等性能更好的格式。

## 更新代码

本项目在持续开发中，如果需要同步 GitHub 上更新的代码，请使用以下脚本：
```bash
python tool/update_code.py
```

注意，更新代码需要首先安装 [Git](https://www.liaoxuefeng.com/wiki/896043488029600)。

## 进阶使用

由于微博JSON数据（Content）爬取绝大多数不需要使用 Cookie，因此建议单独运行用户（User）和搜索（Search）等爬虫，得到微博 ID 后，批量将微博 ID 分配至多台设备并行爬取JSON数据，以此实现尽可能少 Cookie、尽可能高效率的爬取。

使用JSON数据而非微博摘要数据的好处在于，摘要数据需要自行清洗，比如提取@、话题、超话、链接等，而JSON数据则是结构化的存储这些信息，可以直接以字典的形式调用相关字段。由于不需要解析，数据质量是外部用户可能达到的最高水平。

拆分尚未完成JSON数据下载的微博：
```bash
python tool/break.py
```

拆分后的数据会输出到 `break` 文件夹下。拷贝至各台计算机（服务器）后，重命名为 `weibo.db` 放在本项目的根目录。随后运行以下脚本即可自动下载：
```bash
python tool/get_content.py
```

分布于各服务器的抓取任务完成后，可以将 `weibo.db` 全部拷贝至某台服务器的 `merge` 文件夹下，运行以下脚本即可自动合并更新数据库：
```bash
python tool/merge.py
```

此外，还可以通过在根目录下增加 `mids.txt` 文件，并在其中放入 16 位的微博数字 ID 的方式，指定爬取这些微博的 JSON 数据。命令同样为：
```bash
python tool/get_content.py
```

若需要取用 JSON 格式存储的博文细节数据，可以使用以下查询
```python
import sqlite3
import pandas as pd

con = sqlite3.connect('weibo.db')
keyword = "完全二叉树"
script = f"""
    SELECT
        posts.mid, posts.uid,
        json_extract(posts.data,"$.created_at"),
        json_extract(posts.data,"$.text_raw"),
        json_extract(posts.data,"$.user.screen_name"),
        json_extract(posts.data,"$.reposts_count"),
        json_extract(posts.data,"$.comments_count"),
        json_extract(posts.data,"$.attitudes_count")
    FROM posts
    INNER JOIN search_results ON posts.mid = search_results.mid
    WHERE 
        posts.data not null
        AND search_results.keyword LIKE "%{keyword}%"
    """
df = pd.read_sql(script, con)
```

SQLite 的 `json_extract` 允许查询复杂结构的 JSON 数据。
