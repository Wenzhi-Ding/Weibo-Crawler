import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

import pandas as pd

from util.util import connect_db, MIDS, log_print

con = connect_db()

if os.path.isfile(MIDS):
    with open(MIDS, 'r') as f:
        mids = f.read().splitlines()
    valid_mids = [mid for mid in mids if len(mid) == 16 and mid.isdigit()]
    log_print(f"mids.txt 中共 {len(valid_mids)} 个有效微博 ID")
    mids = ",".join(valid_mids)

script = f"""
    SELECT
        mid, 
        json_extract(data,"$.user.id"),
        json_extract(data,"$.user.screen_name"),
        json_extract(data,"$.created_at"),
        json_extract(data,"$.reposts_count"),
        json_extract(data,"$.comments_count"),
        json_extract(data,"$.attitudes_count"),
        json_extract(data,"$.text_raw"),
        json_extract(data,"$.geo")
    FROM posts
    WHERE 
        data not null
        AND mid IN ({mids})
    """

df = pd.read_sql(script, con)
df.columns = ["mid", "user_id", "screen_name", "created_at", "reposts_count", "comments_count", "attitudes_count", "text_raw", "geo"]
df["created_at"] = pd.to_datetime(df["created_at"])

df.to_csv("output/json_by_mids.csv", index=False)
log_print("导出完成，数据位于 output/json_by_mids.csv")