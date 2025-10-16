"""
LangGraph エージェントシステムの定数定義

複数のモジュールで共有される定数を集約しています。
"""

from typing import Dict, List


# ===== 複数エージェント連携（Sequential Chain）の定義 =====
CHAIN_INTENTS: Dict[str, List[str]] = {
    # 資料検索 → コンテンツ生成 → 品質チェック
    "research_and_write": [
        "search_chromadb",      # 1. ChromaDBで資料検索
        "generate_content",     # 2. コンテンツ生成
        "quality_assessment",   # 3. 品質チェック
    ],

    # 構造分析 → 批判的分析 → 品質評価
    "deep_analysis": [
        "structure_analysis",   # 1. 構造分析
        "critical_analysis",    # 2. 批判的分析
        "quality_assessment",   # 3. 品質評価
    ],

    # セクション作成 → ドラフト生成 → 品質チェック
    "section_workflow": [
        "create_section",       # 1. セクション作成
        "generate_draft",       # 2. ドラフト生成
        "quality_assessment",   # 3. 品質チェック
    ],

    # ギャップ分析 → 戦略立案 → コンテンツ生成
    "strategic_writing": [
        "gap_analysis",              # 1. ギャップ分析
        "research_strategy_planning", # 2. 研究戦略立案
        "generate_content",          # 3. コンテンツ生成
    ],

    # 参考文献検索 → 類似コンテンツ探索 → コンテンツ生成
    "reference_based_writing": [
        "search_references",        # 1. 参考文献検索
        "find_similar_content",     # 2. 類似コンテンツ探索
        "generate_content",         # 3. コンテンツ生成
    ],
}
