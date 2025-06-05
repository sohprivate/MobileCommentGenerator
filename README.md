# 天気コメント生成システム

LangGraphとLLMを活用した天気コメント自動生成システムです。

## 現在の実装状況

### ✅ Phase 1-1: 地点データ管理システム (Issue #2) - **完了**

地点データの読み込み、検索、正規化機能が実装されています。

#### 主な機能
- `Chiten.csv`からの地点データ読み込み（141件の地点）
- 地点名の正規化処理（全角半角統一、空白除去、ひらがなカタカナ統一）
- 地点検索機能（完全一致・部分一致・類似度検索）
- 緯度経度データ対応（3列形式CSVサポート）
- 型安全性とエラーハンドリング

#### 改善された機能
- ✅ **CSVデータ読み込みロジックの簡素化**
- ✅ **緯度経度データ対応**（3列以上のCSVファイル対応）
- ✅ **オプショナル依存関係の警告機能**
- ✅ **スコア付き検索機能**（`search_location_with_scores()`）
- ✅ **依存関係状態確認**（`get_dependency_status()`）

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

# スコア付き検索
results_with_scores = manager.search_location_with_scores("大阪")
for location, score in results_with_scores:
    print(f"地点: {location.name}, スコア: {score:.2f}")

# 依存関係状態確認
status = manager.get_dependency_status()
print(f"jaconv利用可能: {status['jaconv_available']}")
print(f"Levenshtein利用可能: {status['levenshtein_available']}")

# 関数インターフェース
results = search_location("大阪", "Chiten.csv")
```

#### CSV形式サポート

**基本形式（地点名のみ）:**
```csv
稚内
札幌
東京
大阪
```

**拡張形式（緯度経度付き）:**
```csv
稚内,45.4167,141.6833
札幌,43.0642,141.3469
東京,35.6762,139.6503
大阪,34.6937,135.5023
```

## 開発環境のセットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

**必須ライブラリ**: `pandas`, `numpy`  
**推奨ライブラリ**: `jaconv`（ひらがなカタカナ正規化）, `python-Levenshtein`（高度な類似度検索）

### 2. テストの実行

```bash
# 全テスト実行
pytest

# カバレッジ付きテスト実行
pytest --cov=src --cov-report=html

# 特定のテストファイル実行
pytest tests/test_location_manager.py

# 詳細出力
pytest -v
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
│   │   └── location_manager.py    # 地点データ管理 ✅
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_location_manager.py   # 地点管理のテスト ✅
├── Chiten.csv                     # 地点データファイル ✅
├── requirements.txt               # 依存関係
├── pytest.ini                    # pytest設定
├── mypy.ini                       # 型チェック設定
├── pyproject.toml                 # プロジェクト設定
├── .gitignore
└── README.md
```

## 次の開発予定

- **Issue #3**: 天気予報取得機能の統合とLangGraphノード化
- **Issue #4**: S3過去コメント取得機能の実装

## テスト結果

### 受け入れ条件達成状況
- [x] `Chiten.csv`からの地点データ読み込みが正常動作
- [x] 地点名検索（完全一致・部分一致）が動作  
- [x] データ正規化処理が適切に動作
- [x] ユニットテストのカバレッジ80%以上
- [x] 型ヒントとdocstringの完備

### テストカバレッジ
- **Locationクラス**: データクラス作成・文字列表現
- **LocationManagerクラス**: CSV読み込み・検索・正規化・エラーハンドリング
- **緯度経度データ**: 3列形式CSV、無効データ処理
- **検索機能**: 完全一致・部分一致・スコア付き・類似度検索
- **関数インターフェース**: `load_locations_from_csv()`, `search_location()`
- **エッジケース**: 空ファイル・空白・不正データ・依存関係なし等

## 貢献方法

1. 各Issueの受け入れ条件を確認
2. 実装前にテストを書く（TDD推奨）
3. 型ヒントとdocstringを必ず記述
4. テストカバレッジ80%以上を維持

## ライセンス

MIT License

---

**Current Status**: Phase 1-1 ✅ **COMPLETED**  
**Next Milestone**: Issue #3 (天気予報取得機能の統合とLangGraphノード化)
