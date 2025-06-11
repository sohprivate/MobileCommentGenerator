import json
import os
from collections import Counter, defaultdict

import boto3
import pandas as pd

# 🔑 SSOログイン済みのプロファイルを指定（例: "dit-training"）
session = boto3.Session(profile_name="dit-training")
s3 = session.client("s3")

# 📂 S3バケット情報
BUCKET = "it-literacy-457604437098-ap-northeast-1"
PREFIX = "downloaded_jsonl_files_archive/"

# 🗃 出力フォルダを作成
os.makedirs("output", exist_ok=True)


# 🗓 カテゴリ分類関数
def classify_category(yyyymm: str) -> str:
    month = int(yyyymm[4:])
    if month in [3, 4, 5]:
        return "春"
    if month == 6:
        return "梅雨"
    if month in [7, 8]:
        return "夏"
    if month == 9:
        return "台風"
    if month in [10, 11]:
        return "秋"
    if month in [12, 1, 2]:
        return "冬"
    return "不明"


# 📥 S3の.jsonlファイル一覧を取得
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
jsonl_keys = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".jsonl")]

# 🧺 カテゴリごとのコメント集計用
weather_by_category = defaultdict(list)
advice_by_category = defaultdict(list)

# 🔄 各ファイルを処理
for key in sorted(jsonl_keys):
    yyyymm = key.split("/")[-1].replace(".jsonl", "")
    category = classify_category(yyyymm)
    print(f"📂 処理中: {key} → カテゴリ: {category}")

    obj = s3.get_object(Bucket=BUCKET, Key=key)
    lines = obj["Body"].read().decode("utf-8").splitlines()
    for line in lines:
        try:
            data = json.loads(line)
            wc = data.get("weather_comment")
            adv = data.get("advice")
            if wc:
                weather_by_category[category].append(wc)
            if adv:
                advice_by_category[category].append(adv)
        except json.JSONDecodeError:
            continue

# 💾 weather_comment のCSV出力
for cat, comments in weather_by_category.items():
    counter = Counter(comments).most_common(30)
    df = pd.DataFrame(counter, columns=["weather_comment", "count"])
    output_path = f"output/{cat}_weather_comment_top30.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ 出力: {output_path}")

# 💾 advice のCSV出力
for cat, advs in advice_by_category.items():
    counter = Counter(advs).most_common(30)
    df = pd.DataFrame(counter, columns=["advice", "count"])
    output_path = f"output/{cat}_advice_top30.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ 出力: {output_path}")
