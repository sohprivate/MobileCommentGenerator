# 天気予報コメント生成プロジェクト

## プロジェクト概要

本プロジェクトは、Python と Streamlit を使用したバックエンドと、React／Vue + TypeScript を使用したフロントエンドから構成される天気予報コメント生成システムです。指定した各地点の天気予報データと過去のコメントデータをもとに、LLM（大規模言語モデル）を活用して短い天気コメント（約 15 文字）を自動生成します。

* **バックエンド**: Python、Streamlit、LangGraph
* **フロントエンド**: TypeScript + React (または Vue)
* **LLM**: OpenAI API（デフォルト）／Gemini API／Anthropic Claude API に切り替え可能
* **データソース**:

  * Weathernews WxTech API（12 時間後・24 時間後の詳細予報）
  * 過去コメント JSONL（S3 バケット: `it-literacy-457604437098-ap-northeast-1` 以下 `downloaded_jsonl_files_archive/YYYYMM/YYYYMM.jsonl`）
  * 地点リスト CSV（`Chiten.csv`）
* **特徴**: 過去コメント例を参考に LLM へプロンプトを組み立て、表現ルール（NG ワード等）を満たすかを LangGraph 上で自動チェック。フロントエンドではワンクリックでコメントをコピー可能。

---

## システムの主な処理フロー

1. **地点読み込み**: `Chiten.csv` を読み取り、地点名と緯度経度を取得。
2. **天気予報取得**: WxTech API から 12h／24h 先の予報を取得。
3. **過去コメント取得**: S3 から対象年月の JSONL を読み込み、地点名でフィルタ。
4. **コメント候補選定**: 予報条件に近い `weather_comment` / `advice` ペアを抽出。
5. **LLM 生成**: 選定したペアをプロンプトに組み込み、LLM に新規コメント生成を依頼。
6. **ルールチェック**: 表現ルールを自動検証し、問題があれば再生成または別ペアを選択。
7. **結果表示**: フロントエンドにコメントを返却し、ユーザーはコピー可能。

---

## LangGraph ワークフロー

このフローを **LangGraph** で実装することで、状態遷移と再試行ロジックを簡潔に記述できます。以下は主要ノードと遷移の概要です。

```
┌────────────┐      ┌─────────────────┐      ┌──────────────────────┐
│ InputNode   │──▶──│ FetchForecastNode │──▶──│ RetrievePastCommentsNode │
└────────────┘      └─────────────────┘      └──────────────────────┘
                                                       │
                              ┌────────────────────────┘
                              ▼
                     ┌──────────────────┐
                     │ SelectCommentPair │
                     └──────────────────┘
                              │
                              ▼
                     ┌──────────────────┐  Failure (rule NG)  ┌──────────────────┐
                     │ EvaluateCandidate│ ───────────────▶── │ SelectCommentPair │ (retry)
                     └──────────────────┘                     └──────────────────┘
                              │ Success
                              ▼
                     ┌──────────────────┐
                     │ GenerateComment  │  (LLM 呼び出し)
                     └──────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ OutputNode       │ (Streamlit API)
                     └──────────────────┘
```

| ノード                          | 役割                                                  |
| ---------------------------- | --------------------------------------------------- |
| **InputNode**                | API 呼び出しまたはフロント入力を受け付け、地点・ターゲット時間を渡す                |
| **FetchForecastNode**        | WxTech API から該当地点の 12h／24h 予報を取得                    |
| **RetrievePastCommentsNode** | S3 から対象年月の JSONL を読み込み、地点でフィルタ                      |
| **SelectCommentPair**        | コサイン類似度・ルールベースで *weather\_comment* と *advice* を候補選定 |
| **EvaluateCandidate**        | 15 文字以内か・NG 表現がないか等、表現ルールを検証                        |
| **GenerateComment**          | LLM にプロンプトを投げ、最終コメントを生成                             |
| **OutputNode**               | 生成結果を JSON で返却し、フロントが受け取る                           |

LangGraph により、`EvaluateCandidate` で NG が出た場合に **自動で SelectCommentPair へループ** し、条件を満たすまで再試行できる点が最大のメリットです。

### LangGraph 実装例（抜粋）

```python
from langgraph import StateMachine, node

@node
def select_comment_pair(ctx):
    # 過去コメント候補の選択ロジック
    return ctx  # ctx に candidate を追加

@node
def evaluate_candidate(ctx):
    candidate = ctx["candidate"]
    if not is_valid(candidate):
        ctx["retry"] = True
    else:
        ctx["retry"] = False
    return ctx

@node
def generate_comment(ctx):
    # OpenAI / Gemini / Anthropic いずれかで生成
    return ctx

sm = StateMachine()
sm.add_node("select", select_comment_pair)
sm.add_node("eval", evaluate_candidate)
sm.add_node("gen", generate_comment)
sm.add_edge("select", "eval")
sm.add_edge("eval", "select", condition=lambda ctx: ctx["retry"])
sm.add_edge("eval", "gen", condition=lambda ctx: not ctx["retry"])
```

---

## 環境構築

### 前提条件

* Python 3.10 以上
* Node.js 18 以上 (npm または yarn)
* AWS CLI (S3 連携確認用)
* OpenAI, Anthropic, Gemini, WxTech の API キー

### バックエンドセットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 例をコピーしてキーを設定
streamlit run app.py
```

### フロントエンドセットアップ

```bash
cd frontend
npm install   # または yarn install
npm run dev
```

続きは前述と同様にローカル確認 → AWS デプロイ手順をご利用ください。

---

## Issue 分解

* **LangGraph パイプライン実装**
* **過去コメント取得ロジック**
* **地点データ読み込み**
* **天気予報取得機能**
* **LLM プロンプト生成**
* **コメント生成ルール適用**
* **LLM プロバイダ選択対応**
* **Streamlit バックエンド**
* **フロントエンド UI & コピー機能**
* **開発環境ドキュメント化**
* **AWS デプロイ準備**

