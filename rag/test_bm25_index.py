import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.rag import rag_system
from scripts.bm25_index import bm25_index

def test_bm25_index():
    """
    测试 BM25 索引功能
    """
    print("=" * 60)
    print("测试动态 BM25 索引")
    print("=" * 60)
    
    # 1. 构建知识库（包括 BM25 索引）
    print("\n1. 构建知识库...")
    build_result = rag_system.build_knowledge_base()
    print(f"   构建结果: {build_result}")
    
    # 2. 测试 BM25 搜索
    print("\n2. 测试 BM25 搜索...")
    test_queries = [
        "AlphaOPT 是什么？",
        "AlphaOPT 的核心功能是什么？",
        "AlphaOPT 如何从有限的演示中学习？",
        "什么是统一力位控制？",
        "机器人如何进行擦黑板任务？"
    ]
    
    for query in test_queries:
        print(f"\n   查询: {query}")
        results = bm25_index.search(query, top_n=3)
        print(f"   结果数: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. 得分: {result['score']:.4f}")
            print(f"      来源: {result['source']}")
            print(f"      内容: {result['content'][:100]}...")
    
    # 3. 测试 RAG 流程
    print("\n3. 测试 RAG 流程...")
    test_query = "AlphaOPT 是什么？"
    rag_result = rag_system.rag_pipeline(test_query)
    print(f"   查询: {test_query}")
    print(f"   回答: {rag_result['answer'][:200]}...")
    print(f"   检索到的文档数: {len(rag_result['retrieved_docs'])}")
    
    # 4. 打印索引统计信息
    print("\n4. 索引统计信息...")
    stats = bm25_index.get_stats()
    print(f"   文档数: {stats.get('doc_count', 0)}")
    print(f"   切分块数: {stats.get('chunk_count', 0)}")
    print(f"   关键词数: {stats.get('keyword_count', 0)}")
    print(f"   索引条目数: {stats.get('index_count', 0)}")
    
    print("\n" + "=" * 60)
    print("BM25 索引测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_bm25_index()
