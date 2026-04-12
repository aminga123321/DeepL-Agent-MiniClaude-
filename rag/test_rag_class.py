import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.rag import rag_system

def test_rag_class():
    """
    测试 RAG 类的功能
    """
    print("🚀 开始测试 RAG 类...")
    
    # 1. 测试 RAG 流程
    print("\n1. 测试 RAG 流程:")
    queries = [
        "AlphaOPT 是什么？",
        "AlphaOPT 的核心功能是什么？",
        "AlphaOPT 如何从有限的演示中学习？"
    ]
    
    for query in queries:
        print(f"\n测试查询: {query}")
        result = rag_system.rag_pipeline(query)
        print(f"回答长度: {len(result['answer'])} 字符")
        print(f"检索到的文档数: {len(result['retrieved_docs'])}")
    
    # 2. 测试构建知识库
    print("\n2. 测试构建知识库:")
    try:
        build_result = rag_system.build_knowledge_base()
        print(f"知识库构建结果: {build_result}")
    except Exception as e:
        print(f"知识库构建失败: {e}")
    
    # 3. 测试检索功能
    print("\n3. 测试检索功能:")
    test_query = "AlphaOPT 是什么？"
    retrieved_docs = rag_system.retrieve(test_query, top_k=3)
    print(f"检索到的文档数: {len(retrieved_docs)}")
    for i, doc in enumerate(retrieved_docs):
        print(f"文档 {i+1}: {doc['content'][:100]}...")
    
    print("\n✅ RAG 类测试完成！")

if __name__ == "__main__":
    test_rag_class()
