"""
ワークフロー可視化ユーティリティ

LangGraphワークフローを視覚的に表示するためのツール
"""

from typing import Dict, Any, Optional
import graphviz
from datetime import datetime

from src.workflows.comment_generation_workflow import create_comment_generation_workflow


def visualize_workflow(output_path: str = "workflow_diagram", format: str = "png") -> str:
    """
    ワークフローを可視化して画像ファイルとして保存
    
    Args:
        output_path: 出力ファイルパス（拡張子なし）
        format: 出力フォーマット（png, pdf, svg など）
        
    Returns:
        生成されたファイルのパス
    """
    # グラフの作成
    dot = graphviz.Digraph(comment='Comment Generation Workflow')
    dot.attr(rankdir='TB')  # Top to Bottom
    
    # グラフのスタイル設定
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
    dot.attr('edge', fontsize='10')
    
    # ノードの定義
    nodes = {
        'input': 'Input Node\n(入力検証)',
        'fetch_forecast': 'Fetch Weather\n(天気予報取得)',
        'retrieve_comments': 'Retrieve Comments\n(過去コメント取得)',
        'select_pair': 'Select Pair\n(コメントペア選択)',
        'evaluate': 'Evaluate\n(品質評価)',
        'generate': 'Generate Comment\n(コメント生成)',
        'output': 'Output Node\n(結果出力)'
    }
    
    # ノードの追加
    for node_id, label in nodes.items():
        if node_id == 'input':
            dot.node(node_id, label, fillcolor='lightgreen')
        elif node_id == 'output':
            dot.node(node_id, label, fillcolor='lightyellow')
        elif node_id == 'evaluate':
            dot.node(node_id, label, fillcolor='lightcoral')
        else:
            dot.node(node_id, label)
    
    # エッジの追加
    edges = [
        ('input', 'fetch_forecast', ''),
        ('fetch_forecast', 'retrieve_comments', ''),
        ('retrieve_comments', 'select_pair', ''),
        ('select_pair', 'evaluate', ''),
        ('evaluate', 'generate', 'continue'),
        ('evaluate', 'select_pair', 'retry'),
        ('generate', 'output', ''),
    ]
    
    for source, target, label in edges:
        if label == 'retry':
            dot.edge(source, target, label, color='red', style='dashed')
        elif label:
            dot.edge(source, target, label, color='green')
        else:
            dot.edge(source, target)
    
    # グラフの情報追加
    dot.attr(label=f'\\n\\nComment Generation Workflow\\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    dot.attr(fontsize='12')
    
    # ファイルとして保存
    output_file = dot.render(output_path, format=format, cleanup=True)
    print(f"Workflow diagram saved to: {output_file}")
    
    return output_file


def create_execution_trace_diagram(
    execution_history: Dict[str, Any],
    output_path: str = "execution_trace",
    format: str = "png"
) -> str:
    """
    実行履歴から実行トレースダイアグラムを作成
    
    Args:
        execution_history: ワークフロー実行の履歴データ
        output_path: 出力ファイルパス
        format: 出力フォーマット
        
    Returns:
        生成されたファイルのパス
    """
    dot = graphviz.Digraph(comment='Execution Trace')
    dot.attr(rankdir='TB')
    
    # 実行されたノードと時間を表示
    node_times = execution_history.get('node_execution_times', {})
    retry_count = execution_history.get('retry_count', 0)
    
    # ノードの追加（実行時間付き）
    for node_name, exec_time in node_times.items():
        label = f"{node_name}\\n{exec_time:.0f}ms"
        color = 'lightgreen' if exec_time < 1000 else 'yellow' if exec_time < 3000 else 'lightcoral'
        dot.node(node_name, label, fillcolor=color, style='filled')
    
    # 実行順序を示すエッジ
    node_order = list(node_times.keys())
    for i in range(len(node_order) - 1):
        dot.edge(node_order[i], node_order[i + 1])
    
    # リトライループの表示
    if retry_count > 0:
        dot.node('retry_info', f'Retry Count: {retry_count}', shape='note', fillcolor='lightyellow', style='filled')
    
    # 最終結果
    final_comment = execution_history.get('final_comment', 'N/A')
    total_time = execution_history.get('execution_time_ms', 0)
    
    result_label = f"Final Comment: {final_comment}\\nTotal Time: {total_time:.0f}ms"
    dot.node('result', result_label, shape='box', fillcolor='lightblue', style='filled,bold')
    
    if node_order:
        dot.edge(node_order[-1], 'result')
    
    # 保存
    output_file = dot.render(output_path, format=format, cleanup=True)
    return output_file


def generate_workflow_documentation():
    """ワークフローのドキュメントをMarkdown形式で生成"""
    doc = """# Comment Generation Workflow Documentation

## Overview
天気コメント生成ワークフローは、LangGraphを使用して実装された7つのノードから構成されています。

## Workflow Nodes

### 1. Input Node
- **責任**: ユーザー入力の検証と初期化
- **入力**: location_name, target_datetime, llm_provider
- **出力**: 検証済みの初期状態

### 2. Fetch Weather Forecast Node
- **責任**: 天気予報APIから最新の天気情報を取得
- **入力**: location情報
- **出力**: WeatherForecastオブジェクト

### 3. Retrieve Past Comments Node
- **責任**: S3から過去のコメントデータを取得
- **入力**: location, weather_data
- **出力**: 類似条件の過去コメントリスト

### 4. Select Comment Pair Node
- **責任**: 最適なコメントペアを選択
- **入力**: past_comments, weather_data
- **出力**: 選択されたコメントペア

### 5. Evaluate Candidate Node
- **責任**: 生成予定のコメントを評価
- **入力**: selected_pair, generated_comment (if any)
- **出力**: validation_result

### 6. Generate Comment Node
- **責任**: LLMを使用してコメントを生成
- **入力**: selected_pair, weather_data
- **出力**: generated_comment

### 7. Output Node
- **責任**: 最終結果の整形と出力
- **入力**: 全ての処理結果
- **出力**: JSON形式の最終結果

## Retry Logic
- 最大リトライ回数: 5回
- リトライ条件: 評価結果がNGの場合
- リトライ時の動作: Select Pair Nodeから再実行

## Error Handling
- 各ノードでエラーをキャッチし、stateに記録
- エラー発生時もワークフローは継続実行
- 最終的にfallbackコメントを使用

## Performance Considerations
- 各ノードの実行時間を計測
- 並行処理は現在未実装
- キャッシュ機能は将来的に実装予定
"""
    
    with open("workflow_documentation.md", "w", encoding="utf-8") as f:
        f.write(doc)
    
    print("Workflow documentation generated: workflow_documentation.md")
    return doc


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ワークフロー可視化ツール")
    parser.add_argument("--action", choices=["visualize", "trace", "document"], 
                        default="visualize", help="実行するアクション")
    parser.add_argument("--format", default="png", help="出力フォーマット")
    parser.add_argument("--output", default="workflow", help="出力ファイル名")
    
    args = parser.parse_args()
    
    if args.action == "visualize":
        visualize_workflow(args.output, args.format)
    elif args.action == "document":
        generate_workflow_documentation()
    elif args.action == "trace":
        # サンプル実行履歴
        sample_history = {
            "node_execution_times": {
                "input_node": 50,
                "fetch_weather_forecast_node": 1200,
                "retrieve_past_comments_node": 800,
                "select_comment_pair_node": 300,
                "evaluate_candidate_node": 150,
                "generate_comment_node": 2500,
                "output_node": 100
            },
            "retry_count": 1,
            "final_comment": "爽やかな一日です",
            "execution_time_ms": 5100
        }
        create_execution_trace_diagram(sample_history, args.output, args.format)
