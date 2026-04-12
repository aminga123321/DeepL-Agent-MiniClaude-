"""
检索评估脚本
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from rerank import retrieve


def load_test_queries() -> List[Dict]:
    """
    加载测试查询
    """
    test_cases = [
        {
            "query": "什么是统一力位控制？",
            "expected_topics": ["力位控制", "统一策略", "位置控制", "力控制"],
        },
        {
            "query": "机器人如何进行擦黑板任务？",
            "expected_topics": ["擦黑板", "wipe-blackboard", "接触力", "力控制"],
        },
        {
            "query": "如何打开抽屉？",
            "expected_topics": ["抽屉", "drawer", "occlusion", "遮挡"],
        },
    ]
    return test_cases


def evaluate_relevance(query: str, result: Dict) -> float:
    """
    评估相关性，支持中英文混合
    """
    content = result["content"].lower()
    query_lower = query.lower()
    
    # 中文关键词到英文关键词的映射
    keyword_mappings = {
        "统一力位控制": ["unified", "force", "position", "control"],
        "擦黑板": ["wipe", "blackboard", "erase"],
        "打开抽屉": ["open", "drawer", "pull"],
        "力位控制": ["force", "position", "control"],
        "统一策略": ["unified", "policy"],
        "位置控制": ["position", "control"],
        "力控制": ["force", "control"],
        "机器人": ["robot", "legged", "manipulation"],
        "任务": ["task", "manipulation"],
    }
    
    score = 0.0
    
    # 检查中文关键词
    for chinese_keyword, english_keywords in keyword_mappings.items():
        if chinese_keyword in query_lower:
            for english_keyword in english_keywords:
                if english_keyword in content:
                    score += 1.0 / len(english_keywords)
    
    # 检查英文关键词
    for word in query_lower.split():
        if word in content:
            score += 0.5
    
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


def main():
    """运行评估"""
    print("="*60)
    print("RAG 检索评估")
    print("="*60)
    
    test_cases = load_test_queries()
    results_log = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n\n测试用例 {i+1}/{len(test_cases)}")
        print("-"*60)
        print(f"查询: {test_case['query']}")
        
        try:
            results = retrieve(test_case["query"], top_k=3)
            
            case_result = {
                "query": test_case["query"],
                "results": [],
            }
            
            for j, res in enumerate(results):
                relevance_score = evaluate_relevance(test_case["query"], res)
                print(f"\n  结果 {j+1}:")
                print(f"    相关性分数: {relevance_score:.2f}")
                print(f"    内容: {res['content'][:100]}...")
                
                case_result["results"].append({
                    "rank": j+1,
                    "relevance_score": relevance_score,
                    "content": res["content"],
                    "source": res["source"],
                })
            
            results_log.append(case_result)
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    print("\n\n" + "="*60)
    print("评估完成！")
    print("="*60)
    
    output_path = Path(__file__).parent.parent.parent / "output" / "retrieval_results.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_log, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
