# 天気コメント生成システム

LangGraphとLLMを活用した天気コメント自動生成システムです。

## 現在の実装状況

### ✅ Phase 1-1: 地点データ管理システム (Issue #2)

地点データの読み込み、検索、正規化機能が実装されています。

#### 主な機能
- `Chiten.csv`からの地点データ読み込み
- 地点名の正規化処理（全角半角統一、空白除去、ひらがなカタカナ統一）
- 地点検索機能（完全一致・部分一致・類似度検索）
- 型安全性とエラーハンドリング

#### 使用方法

```python
from src.data.location_manager import LocationManager, search_location

# LocationManagerを使用
manager = LocationManager("Chiten.csv")

# 全地点取得
all_locations = manager.get_all_locations()
print(f"読み込まれた地点数: {len(all_locations)}")

# 地点検索
results = manager.search_location("札幌")
for location in results:
    print(f"地点: {location.name} (正規化名: {location.normalized_name})")

# 完全一致検索
exact_match = manager.find_exact_match("東京")
if exact_match:
    print(f"発見: {exact_match.name}")

# 関数インターフェース
results = search_location("大阪", "Chiten.csv")
```

## 開発環境のセットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. テストの実行

```bash
# 全テスト実行
pytest

# カバレッジ付きテスト実行
pytest --cov=src --cov-report=html

# 特定のテストファイル実行
pytest tests/test_location_manager.py
```

### 3. 型チェック

```bash
mypy src/
```

### 4. コード品質チェック

```bash
# フォーマット
black src/ tests/

# リント
flake8 src/ tests/
```

## プロジェクト構造

```
.
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   └── location_manager.py    # 地点データ管理
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_location_manager.py   # 地点管理のテスト
├── requirements.txt               # 依存関係
├── pytest.ini                   # pytest設定
├── mypy.ini                      # 型チェック設定
├── .gitignore
Chiten.csv                        # 地点データファイル (要配置)
└── README.md
```

## 次の開発予定

- **Issue #3**: 天気予報取得機能の統合とLangGraphノード化
- **Issue #4**: S3過去コメント取得機能の実装

## 貢献方法

1. 各Issueの受け入れ条件を確認
2. 実装前にテストを書く（TDD推奨）
3. 型ヒントとdocstringを必ず記述
4. テストカバレッジ80%以上を維持
