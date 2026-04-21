"""
步骤 1：向量召回（Retrieval）
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import time

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    DASHSCOPE_API_KEY,
)

from qdrant_client import QdrantClient
import dashscope

# 设置 dashscope API Key
dashscope.api_key = DASHSCOPE_API_KEY


def get_embedding(text: str, text_type: str = "query") -> List[float]:
    """
    生成文本向量
    """
    resp = dashscope.TextEmbedding.call(
        model=EMBEDDING_MODEL,
        input=text,
        text_type=text_type,
        dimensions=EMBEDDING_DIMENSION,
    )
    if resp.status_code != 200:
        raise Exception(f"Embedding failed: {resp}")
    return resp.output["embeddings"][0]["embedding"]


def vector_recall(
    query: str,
    top_n: int = 20,
    filter_conditions: Dict[str, Any] = None,
) -> List[Dict]:
    """
    向量召回
    """
    import requests
    import json
    
    query_embedding = get_embedding(query, text_type="query")
    
    # 使用 Qdrant HTTP API
    url = f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search"
    payload = {
        "vector": query_embedding,
        "limit": top_n,
        "with_payload": True,
        "with_score": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        search_result = response.json()
        
        results = []
        for hit in search_result.get("result", []):
            results.append({
                "content": hit["payload"]["content"],
                "score": hit["score"],
                "source": hit["payload"].get("source", ""),
                "breadcrumbs": hit["payload"].get("breadcrumbs", []),
                "metadata": {k: v for k, v in hit["payload"].items() if k != "content"},
                "recall_method": "vector",
            })
        
        return results
    except Exception as e:
        print(f"Qdrant HTTP API 错误: {e}")
        return []


def main():
    """测试向量召回"""
    if not DASHSCOPE_API_KEY:
        print("❌ 请配置 DASHSCOPE_API_KEY")
        return
    
    query = "什么是统一力位控制？"
    
    print("="*50)
    print("测试向量召回")
    print("="*50)
    print(f"查询: {query}")
    print()
    
    try:
        results = vector_recall(query, top_n=5)
        
        print(f"召回结果 ({len(results)} 条):")
        print("-"*50)
        
        for i, res in enumerate(results):
            print(f"\n{i+1}. [分数: {res['score']:.4f}]")
            print(f"   来源: {res['source']}")
            print(f"   标题: {' > '.join(res['breadcrumbs']) if res['breadcrumbs'] else '无'}")
            print(f"   内容: {res['content'][:150]}...")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
