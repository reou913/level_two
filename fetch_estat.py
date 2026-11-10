"""e-Stat API から薩摩川内市の人口データを取り直して、data/satsumasendai.json を更新するスクリプト。

使い方
  1. e-Stat でユーザー登録し、アプリケーションID（appId）を発行する
  2. ターミナルで appId を設定する
       export ESTAT_APP_ID="ここに自分のappId"
  3. このスクリプトを実行する
       python3 scripts/fetch_estat.py

更新されるのは「総人口と世帯数」と「年齢3区分別人口」です。
産業・観光・島の人口などは市の統計書から手で入れた値なので、そのまま残ります。

使っている統計表
  社会・人口統計体系 市区町村データ 基礎データ「A 人口・世帯」（statsDataId: 0000020201）
"""

import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
STATS_DATA_ID = "0000020201"   # 市区町村データ 基礎データ「A 人口・世帯」
AREA_CODE = "46215"            # 薩摩川内市
FIRST_YEAR = 2000              # ここから後の国勢調査の年を使う

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "satsumasendai.json"

ERA = [(2019, "令和", 2018), (1989, "平成", 1988), (1926, "昭和", 1925)]


def era_label(year):
    """西暦を和暦の表記にする（例：2020 → 令和2年）"""
    for start, name, base in ERA:
        if year >= start:
            n = year - base
            return f"{name}{'元' if n == 1 else n}年"
    return f"{year}年"


def normalize(text):
    """全角・半角や波ダッシュの違いをそろえる"""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("〜", "~").replace("～", "~").replace("-", "~")


# 統計表の指標名にふくまれる言葉で、どの数字かを見分ける
INDICATORS = {
    "total": ["総人口"],
    "child": ["15歳未満人口"],
    "working": ["15~64歳人口"],
    "elderly": ["65歳以上人口"],
    "households": ["世帯数"],   # 一般世帯数ではなく、すべての世帯の数（市の統計書と同じ）
}
EXCLUDE_WORDS = ["男", "女", "割合", "日本人", "外国人", "比率", "%"]


def fetch(app_id):
    params = {
        "appId": app_id,
        "statsDataId": STATS_DATA_ID,
        "cdArea": AREA_CODE,
        "metaGetFlg": "Y",
        "cntGetFlg": "N",
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as res:
        return json.load(res)


def as_list(x):
    return x if isinstance(x, list) else [x]


def pick_indicators(class_objs):
    """指標コード → 名前 の対応表から、必要な指標のコードを探す"""
    names = {}
    for obj in as_list(class_objs):
        if obj.get("@id") == "cat01":
            for c in as_list(obj.get("CLASS", [])):
                names[c["@code"]] = c["@name"]

    def plain(name):
        # 「A7101_世帯数」のような名前から、先頭のコード部分をとる
        n = normalize(name)
        return n.split("_", 1)[1] if "_" in n else n

    found = {}
    for key, words in INDICATORS.items():
        for word in words:  # 先に書いた言葉を優先する
            w = normalize(word)
            # 1回目：名前がぴったり同じものを探す（「世帯数」と「一般世帯数」を取りちがえないため）
            for code, name in names.items():
                if plain(name) == w:
                    found[key] = code
                    break
            # 2回目：見つからなければ、言葉をふくむものを探す
            if key not in found:
                for code, name in names.items():
                    n = normalize(name)
                    if w in n and not any(x in n for x in EXCLUDE_WORDS) and "一般" not in n and "施設" not in n:
                        found[key] = code
                        break
            if key in found:
                break
    return found, names


def main():
    app_id = os.environ.get("ESTAT_APP_ID", "").strip()
    if not app_id:
        sys.exit("ESTAT_APP_ID が設定されていません。README の手順で appId を設定してください。")

    data = fetch(app_id)
    root = data.get("GET_STATS_DATA", {})
    status = root.get("RESULT", {})
    if str(status.get("STATUS")) != "0":
        sys.exit(f"e-Stat からエラーが返りました：{status.get('ERROR_MSG')}")

    stat = root["STATISTICAL_DATA"]
    found, names = pick_indicators(stat["CLASS_INF"]["CLASS_OBJ"])

    missing = [k for k in INDICATORS if k not in found]
    if missing:
        print("見つからなかった指標：", ", ".join(missing))
        print("この統計表にある指標の名前（一部）：")
        for code, name in list(names.items())[:60]:
            print(f"  {code}  {name}")
        sys.exit("INDICATORS の言葉を、上の名前に合わせて直してください。")

    # 年ごとに数字を集める
    by_year = {}
    code_to_key = {v: k for k, v in found.items()}
    for v in as_list(stat["DATA_INF"]["VALUE"]):
        key = code_to_key.get(v.get("@cat01"))
        if not key:
            continue
        year = int(str(v["@time"])[:4])
        try:
            value = int(float(v["$"]))
        except (ValueError, TypeError):
            continue  # 「-」や「***」など、数字でないものは飛ばす
        by_year.setdefault(year, {})[key] = value

    census_years = sorted(
        y for y, vals in by_year.items()
        if y >= FIRST_YEAR and y % 5 == 0 and "total" in vals
    )
    if not census_years:
        sys.exit("国勢調査の年のデータが見つかりませんでした。")

    population, age = [], []
    for y in census_years:
        vals = by_year[y]
        population.append({
            "year": y,
            "label": era_label(y),
            "total": vals["total"],
            "households": vals.get("households"),
        })
        if all(k in vals for k in ("child", "working", "elderly")):
            known = vals["child"] + vals["working"] + vals["elderly"]
            age.append({
                "year": y,
                "label": era_label(y),
                "child": vals["child"],
                "working": vals["working"],
                "elderly": vals["elderly"],
                "unknown": max(0, vals["total"] - known),  # 年齢不詳
            })

    out = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    source = "e-Stat 社会・人口統計体系 市区町村データ「A 人口・世帯」"
    out["population"]["years"] = population
    out["population"]["source"] = source
    if age:
        out["age"]["years"] = age
        out["age"]["source"] = source
    out["updated"] = date.today().isoformat()

    DATA_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"更新しました：{DATA_FILE}")
    for p in population:
        print(f"  {p['label']}  総人口 {p['total']:,}人  世帯 {p['households'] or '-'}")


if __name__ == "__main__":
    main()
