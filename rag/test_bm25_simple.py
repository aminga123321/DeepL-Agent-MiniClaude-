import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.bm25_index import bm25_index

def test_bm25_simple():
    """
    简单测试 BM25 索引功能
    """
    print("=" * 60)
    print("简单测试动态 BM25 索引")
    print("=" * 60)
    
    # 1. 测试清空索引
    print("\n1. 测试清空索引...")
    bm25_index.clear_index()
    
    # 2. 测试添加文档
    print("\n2. 测试添加文档...")
    test_chunks = [
        {
            "content": "AlphaOPT 是一个优化系统，用于制定优化程序。",
            "metadata": {"source": "test.md"},
            "breadcrumbs": ["介绍", "AlphaOPT 系统"]
        },
        {
            "content": "AlphaOPT 的核心功能包括库学习和库进化。",
            "metadata": {"source": "test.md"},
            "breadcrumbs": ["功能", "核心功能"]
        },
        {
            "content": "统一力位控制是一种用于机器人的控制策略。",
            "metadata": {"source": "test.md"},
            "breadcrumbs": ["控制", "统一力位控制"]
        }
    ]
    
    bm25_index.add_document("test.md", "path/to/test.md", test_chunks)
    
    # 3. 测试搜索
    print("\n3. 测试搜索...")
    test_queries = [
        "AlphaOPT 是什么？",
        "AlphaOPT 的核心功能是什么？",
        "什么是统一力位控制？"
    ]
    
    for query in test_queries:
        print(f"\n   查询: {query}")
        results = bm25_index.search(query, top_n=2)
        print(f"   结果数: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. 得分: {result['score']:.4f}")
            print(f"      来源: {result['source']}")
            print(f"      内容: {result['content']}")
    
    # 4. 测试统计信息
    print("\n4. 测试统计信息...")
    stats = bm25_index.get_stats()
    print(f"   文档数: {stats.get('doc_count', 0)}")
    print(f"   切分块数: {stats.get('chunk_count', 0)}")
    print(f"   关键词数: {stats.get('keyword_count', 0)}")
    print(f"   索引条目数: {stats.get('index_count', 0)}")
    
    print("\n" + "=" * 60)
    print("BM25 索引简单测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_bm25_simple()
