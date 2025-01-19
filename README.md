# Yamato Tracker with Map

ヤマト運輸の追跡番号を調査するWebアプリケーションです。

## 特徴

- 追跡番号を複数コピペして一括調査できます
- 最新の配送状況が経路毎に一覧表示できます
- 経路情報を地図表示できます
- ヤマトへの直リンクが追跡番号に含まれています
- 過去の追跡データを表示・管理できます
- データベースに最大20件まで記録を保持

## ディレクトリ構成

```
yamato-tracker-withmap/
├── .github/
│   └── workflows/          # GitHub Actions設定
├── src/
│   ├── database/           # データベース関連
│   ├── email/              # メール関連
│   ├── map/                # 地図表示関連
│   └── utils/              # ユーティリティ関数
├── .env                    # 環境変数設定
├── .gitignore              # Git除外設定
├── main.py                 # メインアプリケーション
├── README.md               # 本ファイル
├── requirements.txt        # 依存パッケージ
└── SessionState.py         # セッション状態管理
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
