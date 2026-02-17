# TCBF Map App

イベント会場のマップデータを作成・編集するためのPythonアプリケーション

## クイックスタート

```bash
# 1. セットアップ
python setup.py

# 2. 起動
python main.py
```

## 機能

- **マップ表示モード**: 作成したマップの表示・確認
- **カテゴリ編集モード**: 施設・カテゴリの設定
- **オブジェクト管理**: 四角形・テキスト・ポリゴン図形の編集
- **データ保存**: JSON形式での保存・読み込み
- **画像出力**: PNG形式でのエクスポート
- **CSV エクスポート**: 電力データなどのエクスポート

## システム要件

- Python 3.10 以上
- 4GB以上のメモリ推奨

## 依存パッケージ

- pygame 2.5.0以上

## インストール

自動セットアップ:
```bash
python setup.py
```

または手動セットアップ:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# または
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

## 使用方法

```bash
python main.py
```

