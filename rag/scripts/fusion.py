"""
步骤 2：多路召回融合（Fusion）
使用 RRF（Reciprocal Rank Fusion）算法
"""

import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from retrieve import vector_recall
from config import MARKDOWN_DIR


def rrf_fusion(results_list: List[List[Dict]], k: int = 60) -> List[Dict]:
    """
    RRF 融合算法
    score = 1 / (k + rank)
    """
    scores = defaultdict(float)
    all_items = {}
    
    for results in results_list:
        for rank, item in enumerate(results):
            content = item["content"]
            all_items[content] = item
            scores[content] += 1.0 / (k + rank + 1)
    
    sorted_items = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    fused_results = []
    for content, score in sorted_items:
        item = all_items[content].copy()
        item["fusion_score"] = score
        item["recall_method"] = "fused"
        fused_results.append(item)
    
    return fused_results


def bm25_recall(query: str, top_n: int = 20) -> List[Dict]:
    """
    BM25 关键词召回
    """
    print("  执行 BM25 关键词召回...")
    
    try:
        from bm25_index import bm25_index
        
        # 使用动态 BM25 索引进行搜索
        results = bm25_index.search(query, top_n=top_n)
        
        # 确保返回格式与原函数一致
        for result in results:
            if "breadcrumbs" not in result:
                result["breadcrumbs"] = []
            if "source" not in result:
                result["source"] = "unknown"
            if "recall_method" not in result:
                result["recall_method"] = "bm25"
            if "metadata" not in result:
                result["metadata"] = {"source": result["source"]}
        
        print(f"  BM25 召回结果数: {len(results)}")
        return results
    except Exception as e:
        print(f"⚠️  BM25 召回失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def multi_channel_recall(query: str, top_n: int = 20) -> List[Dict]:
    """
    多路召回：向量召回 + BM25 关键词召回
    """
    # 向量召回
    print("  执行向量召回...")
    vector_results = vector_recall(query, top_n=top_n)
    
    # BM25 关键词召回
    bm25_results = bm25_recall(query, top_n=top_n)
    
    # 构建结果列表
    results_list = [vector_results]
    if bm25_results:
        results_list.append(bm25_results)
    
    # 融合多路召回结果
    print(f"  融合 {len(results_list)} 路召回结果...")
    fused_results = rrf_fusion(results_list)
    
    return fused_results[:top_n]


def main():
    """测试融合"""
    query = "什么是统一力位控制？"
    
    print("="*50)
    print("测试多路召回融合")
    print("="*50)
    print(f"查询: {query}")
    print()
    
    try:
        results = multi_channel_recall(query, top_n=5)
        
        print(f"\n融合结果 ({len(results)} 条):")
        print("-"*50)
        
        for i, res in enumerate(results):
            print(f"\n{i+1}. [融合分数: {res['fusion_score']:.4f}]")
            print(f"   来源: {res['source']}")
            print(f"   内容: {res['content'][:150]}...")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
