# AlphaOPT 测试配置

# 测试用例
TEST_CASES = [
    {
        "id": "Q1",
        "query": "AlphaOPT 是什么？",
        "expected_sections": ["1. 引言", "3.1 AlphaOPT 框架"]
    },
    {
        "id": "Q2",
        "query": "AlphaOPT 的核心功能是什么？",
        "expected_sections": ["3.1.1 库学习", "3.1.2 库进化"]
    },
    {
        "id": "Q3",
        "query": "AlphaOPT 如何从有限的演示中学习？",
        "expected_sections": ["3.1.1 库学习", "4.3 有限监督下的学习"]
    },
    {
        "id": "Q4",
        "query": "AlphaOPT 的库学习阶段如何工作？",
        "expected_sections": ["3.1.1 库学习"]
    },
    {
        "id": "Q5",
        "query": "AlphaOPT 的库进化阶段如何工作？",
        "expected_sections": ["3.1.2 库进化"]
    },
    {
        "id": "Q6",
        "query": "AlphaOPT 在哪些基准测试上表现如何？",
        "expected_sections": ["4.2 分布外泛化", "4.5 整体性能"]
    },
    {
        "id": "Q7",
        "query": "AlphaOPT 的经验库包含哪些类型的洞察？",
        "expected_sections": ["5. 库分析"]
    },
    {
        "id": "Q8",
        "query": "AlphaOPT 与其他方法相比有哪些优势？",
        "expected_sections": ["4.2 分布外泛化", "4.3 有限监督下的学习", "4.4 随数据持续增长"]
    }
]

# 评估标准
EVALUATION_METRICS = {
    "recall": "找到的相关文档数 / 总相关文档数",
    "precision": "相关文档数 / 返回的文档数",
    "f1_score": "2 * (准确率 * 召回率) / (准确率 + 召回率)",
    "llm_accuracy": "基于关键词匹配和内容相关性的评分（0-1）"
}

# 测试参数
TEST_PARAMS = {
    "top_k": 5,  # 检索返回的文档数
    "rerank_top_k": 3,  # 重排后保留的文档数
    "llm_temperature": 0.0  # LLM 生成温度
}
