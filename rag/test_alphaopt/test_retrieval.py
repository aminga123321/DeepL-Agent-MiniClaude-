import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fusion import multi_channel_recall
from test_config import TEST_CASES, TEST_PARAMS

def evaluate_relevance(query, result):
    """
    评估文档与查询的相关性
    """
    content = result["content"].lower()
    query_lower = query.lower()
    
    # 关键词映射
    keyword_mappings = {
        "alphaopt": ["alphaopt"],
        "核心功能": ["core", "function", "feature"],
        "库学习": ["library learning"],
        "库进化": ["library evolution"],
        "有限演示": ["limited demonstration", "answer-only"],
        "基准测试": ["benchmark", "evaluation"],
        "经验库": ["experience library", "insight"],
        "优势": ["advantage", "benefit", "improvement"]
    }
    
    score = 0.0
    
    # 检查关键词
    for chinese_keyword, english_keywords in keyword_mappings.items():
        if chinese_keyword in query_lower:
            for english_keyword in english_keywords:
                if english_keyword in content:
                    score += 1.0 / len(english_keywords)
    
    # 检查标题中的关键词
    breadcrumbs = result.get("breadcrumbs", [])
    for breadcrumb in breadcrumbs:
        breadcrumb_lower = breadcrumb.lower()
        for chinese_keyword, english_keywords in keyword_mappings.items():
            if chinese_keyword in query_lower:
                for english_keyword in english_keywords:
                    if english_keyword in breadcrumb_lower:
                        score += 0.3
    
    # 归一化分数
    return min(1.0, score)

def test_retrieval():
    """
    测试检索性能
    """
    results = []
    
    for test_case in TEST_CASES:
        query = test_case["query"]
        print(f"\n测试查询: {query}")
        
        # 执行多路召回
        retrieved_docs = multi_channel_recall(query, top_n=TEST_PARAMS["top_k"])
        
        # 评估相关性
        evaluated_docs = []
        for doc in retrieved_docs:
            relevance_score = evaluate_relevance(query, doc)
            doc["relevance_score"] = relevance_score
            evaluated_docs.append(doc)
        
        # 按相关性分数排序
        evaluated_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # 计算召回率和准确率
        relevant_docs = [doc for doc in evaluated_docs if doc["relevance_score"] >= 0.5]
        total_relevant_docs = len(test_case["expected_sections"])
        
        recall = min(len(relevant_docs) / total_relevant_docs, 1.0) if total_relevant_docs > 0 else 0.0
        precision = len(relevant_docs) / len(evaluated_docs) if len(evaluated_docs) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # 保存结果
        result = {
            "query_id": test_case["id"],
            "query": query,
            "retrieved_docs": evaluated_docs[:TEST_PARAMS["rerank_top_k"]],
            "recall": recall,
            "precision": precision,
            "f1_score": f1_score
        }
        
        results.append(result)
        print(f"召回率: {recall:.2f}, 准确率: {precision:.2f}, F1 分数: {f1_score:.2f}")
    
    # 计算总体指标
    total_recall = sum(r["recall"] for r in results) / len(results)
    total_precision = sum(r["precision"] for r in results) / len(results)
    total_f1_score = sum(r["f1_score"] for r in results) / len(results)
    
    overall = {
        "total_recall": total_recall,
        "total_precision": total_precision,
        "total_f1_score": total_f1_score
    }
    
    # 保存测试结果
    output_path = Path(__file__).parent / "retrieval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "overall": overall}, f, ensure_ascii=False, indent=2)
    
    print(f"\n总体结果:")
    print(f"平均召回率: {total_recall:.2f}")
    print(f"平均准确率: {total_precision:.2f}")
    print(f"平均 F1 分数: {total_f1_score:.2f}")
    print(f"测试结果已保存到: {output_path}")

if __name__ == "__main__":
    test_retrieval()
