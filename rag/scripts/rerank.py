"""
步骤 3：重排（Rerank）
使用 BGE-reranker-large 进行精排
"""

import sys
from pathlib import Path
from typing import List, Dict
import time
import requests
from dashscope import TextReRank
sys.path.insert(0, str(Path(__file__).parent))
from fusion import multi_channel_recall
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DASHSCOPE_API_KEY


def bge_rerank(query: str, passages: List[str]) -> List[float]:
    """
    使用 TextReRank 进行重排
    """
    print("使用 TextReRank 进行重排...")
    
    try:
        if DASHSCOPE_API_KEY:
            # 调用 TextReRank
            response = TextReRank.call(
                model="qwen3-rerank",
                query=query,
                documents=passages,
                top_k=len(passages)
            )
            
            # 处理结果
            if response and response.status_code == 200 and response.output:
                # 构建分数映射
                score_map = {item["index"]: item["relevance_score"] for item in response.output["results"]}
                # 按原始顺序返回分数
                scores = [score_map.get(i, 0.0) for i in range(len(passages))]
                return scores
            else:
                print("⚠️  TextReRank 调用失败，使用默认分数")
                return [1.0 for _ in passages]
        else:
            print("⚠️  未配置 DASHSCOPE_API_KEY，使用默认分数")
            return [1.0 for _ in passages]
    except Exception as e:
        print(f"⚠️  TextReRank 调用失败: {e}")
        return [1.0 for _ in passages]


def rerank_results(query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    重排结果
    """
    if not results:
        return []
    
    passages = [r["content"] for r in results]
    
    print(f"  开始重排 {len(passages)} 个段落...")
    rerank_scores = bge_rerank(query, passages)
    
    for i, res in enumerate(results):
        res["rerank_score"] = rerank_scores[i]
    
    reranked_results = sorted(
        results,
        key=lambda x: x["rerank_score"],
        reverse=True
    )
    
    return reranked_results[:top_k]


def retrieve(query: str, top_k: int = 5, top_n_recall: int = 20) -> List[Dict]:
    """
    完整的检索流程：召回 -> 融合 -> 重排
    """
    print("="*50)
    print(f"查询: {query}")
    print("="*50)
    
    print("\n[1/3] 多路召回...")
    recalled = multi_channel_recall(query, top_n=top_n_recall)
    
    print(f"\n[2/3] 重排 (Top {top_k})...")
    final_results = rerank_results(query, recalled, top_k=top_k)
    
    print("\n[3/3] 完成！")
    
    return final_results


def generate_answer(query: str, retrieved_docs: List[Dict]) -> str:
    """
    使用 LLM 基于检索到的文档生成回答
    """
    try:
        # 构建上下文
        context = "\n\n".join([doc["content"] for doc in retrieved_docs])
        
        # 构建 prompt
        prompt = f"""你是一个专业的知识助手，基于以下文档内容回答用户问题。

文档内容：
{context}

用户问题：{query}

请基于文档内容给出详细、准确的回答。"""
        
        # 使用 DeepSeek API
        if DEEPSEEK_API_KEY:
            print("使用 DeepSeek 模型...")
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.3
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            # 回退到 DashScope
            import dashscope
            print("使用 DashScope 模型...")
            response = dashscope.Generation.call(
                model="qwen-turbo",
                prompt=prompt,
                max_tokens=1024,
                temperature=0.3,
            )
            if response.status_code != 200:
                raise Exception(f"LLM 调用失败: {response}")
            return response.output["text"]
    except Exception as e:
        print(f"⚠️  LLM 调用失败: {e}")
        # 返回基于检索结果的简单总结
        return f"基于检索到的信息，关于 '{query}' 的内容如下：\n\n" + "\n\n".join([f"- {doc['content'][:100]}..." for doc in retrieved_docs[:3]])


def rag_pipeline(query: str, top_k: int = 5) -> Dict:
    """
    完整的 RAG 流程：检索 -> 重排 -> 生成回答
    """
    # 1. 检索相关文档
    retrieved_docs = retrieve(query, top_k=top_k)
    
    # 2. 使用 LLM 生成回答
    answer = generate_answer(query, retrieved_docs)
    
    return {
        "query": query,
        "answer": answer,
        "retrieved_docs": retrieved_docs,
    }


def main():
    """测试完整 RAG 流程"""
    query = "什么是统一力位控制？"
    
    try:
        result = rag_pipeline(query, top_k=5)
        
        print(f"\n最终回答:")
        print("="*50)
        print(result["answer"])
        
        print(f"\n参考文档 (Top {len(result['retrieved_docs'])}):")
        print("-"*50)
        
        for i, doc in enumerate(result["retrieved_docs"]):
            print(f"\n{i+1}. [来源: {doc['source']}]")
            print(f"   标题: {' > '.join(doc.get('breadcrumbs', []))}")
            print(f"   内容: {doc['content'][:150]}...")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
