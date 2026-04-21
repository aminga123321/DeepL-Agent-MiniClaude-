import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rerank import rag_pipeline
from test_config import TEST_CASES, TEST_PARAMS

def evaluate_llm_answer(query, answer, retrieved_docs):
    """
    评估 LLM 回答的准确性
    """
    answer_lower = answer.lower()
    query_lower = query.lower()
    
    # 关键词映射
    keyword_mappings = {
        "alphaopt": ["alphaopt", "self-improving", "experience library"],
        "核心功能": ["library learning", "library evolution", "insight"],
        "库学习": ["library learning", "insight extraction", "self-exploration"],
        "库进化": ["library evolution", "condition refinement", "diagnosis"],
        "有限演示": ["limited demonstration", "answer-only", "self-exploration"],
        "基准测试": ["benchmark", "logior", "optibench", "accuracy"],
        "经验库": ["experience library", "insight", "taxonomy"],
        "优势": ["advantage", "benefit", "improvement", "generalization"]
    }
    
    score = 0.0
    
    # 检查回答中是否包含相关关键词
    for chinese_keyword, english_keywords in keyword_mappings.items():
        if chinese_keyword in query_lower:
            for english_keyword in english_keywords:
                if english_keyword in answer_lower:
                    score += 1.0 / len(english_keywords)
    
    # 检查回答是否基于检索的文档
    for doc in retrieved_docs:
        doc_content = doc["content"].lower()
        # 检查回答是否包含文档中的关键信息
        if any(keyword in answer_lower for keyword in doc_content.split()[:100]):
            score += 0.2
    
    # 归一化分数
    return min(1.0, score)

def test_llm_accuracy():
    """
    测试 LLM 回答准确性
    """
    results = []
    
    for test_case in TEST_CASES:
        query = test_case["query"]
        print(f"\n测试查询: {query}")
        
        # 执行完整 RAG 流程
        try:
            result = rag_pipeline(query, top_k=TEST_PARAMS["top_k"])
            
            # 提取生成的回答
            llm_answer = result.get("answer", "")
            retrieved_docs = result.get("retrieved_docs", [])
            
            # 评估回答准确性
            llm_accuracy = evaluate_llm_answer(query, llm_answer, retrieved_docs)
            
            # 保存结果
            test_result = {
                "query_id": test_case["id"],
                "query": query,
                "llm_answer": llm_answer,
                "llm_accuracy": llm_accuracy,
                "retrieved_docs": retrieved_docs[:3]  # 只保存前 3 个文档
            }
            
            results.append(test_result)
            print(f"LLM 回答准确率: {llm_accuracy:.2f}")
            print(f"回答长度: {len(llm_answer)} 字符")
        except Exception as e:
            print(f"测试失败: {e}")
            test_result = {
                "query_id": test_case["id"],
                "query": query,
                "llm_answer": "",
                "llm_accuracy": 0.0,
                "error": str(e)
            }
            results.append(test_result)
    
    # 计算总体指标
    total_llm_accuracy = sum(r["llm_accuracy"] for r in results) / len(results)
    
    overall = {
        "total_llm_accuracy": total_llm_accuracy
    }
    
    # 保存测试结果
    output_path = Path(__file__).parent / "llm_accuracy_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "overall": overall}, f, ensure_ascii=False, indent=2)
    
    print(f"\n总体结果:")
    print(f"平均 LLM 回答准确率: {total_llm_accuracy:.2f}")
    print(f"测试结果已保存到: {output_path}")

if __name__ == "__main__":
    test_llm_accuracy()
