# 数字で見る薩摩川内市

国勢調査と市の統計書の数字を JSON にまとめ、グラフで表示する授業用のWebページです（AI教室 レベル2）。

## ファイルの構成

```
index.html                  表示するページ（グラフ・クイズ・考えてみよう）
data/satsumasendai.json     表示する数字（ここを書きかえるとページも変わる）
scripts/fetch_estat.py      e-Stat から人口の数字を取り直すスクリプト
README.md                   この説明
```

## 公開のしかた（GitHub Pages）

1. リポジトリの「Add file」→「Upload files」に、`index.html`、`data` フォルダ、`scripts` フォルダ、`README.md` をまとめてドラッグする
2. 「Commit changes」を押す
3. 「Settings」→「Pages」で、Branch を `main`、フォルダを `/(root)` にして「Save」
4. 数分待って、表示されたURLを開く

`index.html` をパソコンでダブルクリックして開くと、データを読み込めません（ブラウザの安全のしくみのため）。
GitHub Pages のURLか、Codespaces のプレビューで開いてください。

## e-Stat から最新の数字を取り直す

「総人口と世帯数」と「年齢3区分別人口」は、e-Stat の API から取り直せます。

1. e-Stat でユーザー登録し、マイページでアプリケーションID（appId）を発行する
2. Codespaces のターミナルで次を実行する

```bash
export ESTAT_APP_ID="自分のappId"
python3 scripts/fetch_estat.py
```

3. `data/satsumasendai.json` が更新されるので、GitHub にアップロード（またはコミット）する

使っている統計表：社会・人口統計体系 市区町村データ 基礎データ「A 人口・世帯」（statsDataId `0000020201`、薩摩川内市の地域コード `46215`）

指標の名前が見つからないときは、スクリプトが統計表の指標名の一覧を表示します。
`fetch_estat.py` の `INDICATORS` の言葉を、表示された名前に合わせて直してください。

appId は自分専用の鍵です。ファイルに書きこんだり、GitHub にアップロードしたりしないでください。

## 手で入れている数字

次の数字は e-Stat ではなく、市の統計書「統計さつませんだい」から手で入れています。
新しい版が出たら、`data/satsumasendai.json` の該当する数字を書きかえてください。

- 産業別の15歳以上就業者（令和2年国勢調査）
- 1年間の人の動き（出生・死亡・転入・転出）
- 面積、ブロイラーの生産、観光客数、甑島の地域別人口、市の花と木

## 出典

- 統計さつませんだい 令和7年版：https://www.city.satsumasendai.lg.jp/material/files/group/5/R7toukeisatsumasendai.pdf
- 統計さつませんだい 令和6年版：https://www.city.satsumasendai.lg.jp/material/files/group/9/R6_toukeisatsumasendai.pdf
- 統計さつませんだい 令和5年版：https://www.city.satsumasendai.lg.jp/material/files/group/9/R5_tokeisatsumasendai.pdf
- e-Stat（政府統計の総合窓口）：https://www.e-stat.go.jp/
