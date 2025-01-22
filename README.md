# Yamato Tracker with Map

ヤマト運輸の追跡番号を調査するWebアプリケーションです。

## このアプリの特徴

- 追跡番号を複数コピペして一括調査できます
- 最新の配送状況が経路毎に一覧表示できます
- 経路情報を地図表示できます
- ヤマトへの直リンクが追跡番号に含まれています
- 過去の追跡データを表示・管理できます
- データベースに最大20件まで記録を保持

## ディレクトリ構成

```
yamato-tracker-withmap/
├── src/
│   ├── database/           # データベース関連
│   │   └── database.py
│   ├── map/                # 地図表示関連
│   │   └── map.py
│   └── utils/              # ユーティリティ関数
│       └── utils.py
├── .gitignore              # Git除外設定
├── LICENSE                 # ライセンス
├── main.py                 # メインアプリケーション
├── README.md               # 本ファイル
├── requirements.txt        # 依存パッケージ
└── VERSION                 # バージョン情報
```

## インストール方法

1. リポジトリをクローン
```bash
git clone https://github.com/matzoka/yamato-tracker-withmap.git
cd yamato-tracker-withmap
```

2. 仮想環境を作成し、依存パッケージをインストール
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. アプリケーションを起動
```bash
streamlit run main.py
```

## 画面キャプチャ

![sample](https://private-user-images.githubusercontent.com/758331/404711684-6f0a6a47-b60f-4122-b3a6-296fbc166f4f.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzczMzYxNTksIm5iZiI6MTczNzMzNTg1OSwicGF0aCI6Ii83NTgzMzEvNDA0NzExNjg0LTZmMGE2YTQ3LWI2MGYtNDEyMi1iM2E2LTI5NmZiYzE2NmY0Zi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMTIwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDEyMFQwMTE3MzlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT04MDIzODVmY2I5ZmE3NmE2ZTU2YWVjOGI3YTNhNThkYjdkNzkwOGIxZTI0MmNlYmNiNWY4MjlmYWQ2NTE4M2YzJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.Zb4AeYW0BuO-zxon_jRSwvqRS54j3u4b6lABXH8vDPg)

![sample](https://private-user-images.githubusercontent.com/758331/404711888-c1c23845-ae16-4c6c-a6c1-836319c3884d.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzczMzYwNzAsIm5iZiI6MTczNzMzNTc3MCwicGF0aCI6Ii83NTgzMzEvNDA0NzExODg4LWMxYzIzODQ1LWFlMTYtNGM2Yy1hNmMxLTgzNjMxOWMzODg0ZC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMTIwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDEyMFQwMTE2MTBaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0xMGM4ZTRkMWM2Y2RiZGI1Zjk3NzA4NjhiNTllNTk5YTRkMDQyY2NhZjVkZGViYzdjZDczYjI2NjkzYzM2MjQ5JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.BA654RioF0QQbFL6hIWNVsOFX6dNsPZhDuiyJzJF7kI)

![Image](https://github.com/user-attachments/assets/30fcf2e8-c4b2-4416-bc83-06963a42ea8c)
