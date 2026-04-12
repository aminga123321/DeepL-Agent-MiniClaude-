# RAG 系统使用文档

## 1. 系统概述

本系统是一个基于 Retrieval-Augmented Generation (RAG) 技术的智能问答系统，能够从文档中检索相关信息并生成准确的回答。

### 核心功能
- **知识库构建**：将 PDF 文档转换为 Markdown，智能切分，并存储到向量数据库
- **智能检索**：采用多路召回（向量召回 + BM25 关键词召回）和 RRF 融合算法
- **重排优化**：使用基于关键词匹配的重排方法
- **LLM 集成**：支持 DeepSeek 和 DashScope 模型生成回答
- **性能评估**：提供检索质量和性能压测工具

### 技术栈
- **PDF 解析**：pymupdf4llm
- **文本切分**：langchain-text-splitters
- **向量嵌入**：DashScope text-embedding-v3
- **向量存储**：Qdrant
- **LLM**：DeepSeek、DashScope

## 2. 环境配置

### 2.1 虚拟环境
系统使用 Conda 虚拟环境 `rag`：

```bash
# 激活虚拟环境
& 'D:\Anaconda\Anaconda3\Scripts\conda.exe' activate rag

# 安装依赖
& 'D:\Anaconda\Anaconda3\envs\rag\python.exe' -m pip install -r requirements.txt
```

### 2.2 环境变量
创建 `.env` 文件，配置 API Key 和 Qdrant 信息：

```env
# DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_api_key

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Qdrant 配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2.3 Qdrant 服务
确保 Qdrant 服务正在运行：

```bash
# 启动 Qdrant 服务
# 参考 Qdrant 官方文档
```

## 3. 知识库构建

### 3.1 PDF 转 Markdown
将 PDF 文档转换为 Markdown 格式：

```bash
python scripts/pdf_to_markdown.py
```

**功能**：
- 支持批量处理 PDF 文件
- 提取图片并保存
- 保留文档结构

### 3.2 Markdown 切分
将 Markdown 文档按标题结构智能切分：

```bash
python scripts/chunk_markdown.py
```

**功能**：
- 按标题层级切分
- 合并小片段
- 添加面包屑前缀

### 3.3 向量存储
将切分后的片段向量化并存储到 Qdrant：

```bash
python scripts/store_to_qdrant.py
```

**功能**：
- 使用 DashScope 生成向量
- 批量存储到 Qdrant
- 创建集合和索引

## 4. 智能检索

### 4.1 完整检索流程
执行完整的 RAG 流程（检索 + 重排 + 生成回答）：

```bash
python scripts/rerank.py
```

**功能**：
- 多路召回（向量 + BM25）
- RRF 融合
- 基于关键词匹配的重排
- 使用 DeepSeek 生成回答

### 4.2 自定义查询
修改 `scripts/rerank.py` 中的 `main()` 函数，设置自定义查询：

```python
def main():
    """测试完整 RAG 流程"""
    query = "你的自定义查询"
    
    try:
        result = rag_pipeline(query, top_k=5)
        # 输出结果
        ...
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
```

## 5. 性能评估

### 5.1 检索质量评估
评估检索质量，计算相关性分数：

```bash
python scripts/evaluate/test_retrieval.py
```

**输出**：
- 每个测试用例的相关性分数
- 准确率和召回率
- 结果保存到 `output/retrieval_results.json`

### 5.2 性能压测
测试系统性能，统计检索延迟：

```bash
python scripts/evaluate/bench_performance.py
```

**输出**：
- 平均延迟
- 中位数、最小、最大延迟
- 标准差和 P95 延迟

## 6. 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  知识库构建流程  │     │   智能检索流程  │     │   性能评估流程  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ 1. PDF 转 Markdown │  → 1. 多路召回    │  → 1. 检索质量评估  │
│ 2. Markdown 切分  │     2. RRF 融合    │     2. 性能压测    │
│ 3. 向量存储到 Qdrant │  3. 重排优化    │                 │
│                 │     4. LLM 生成回答  │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 7. 目录结构

```
rag/
├── data/                  # 数据目录
│   ├── raw/              # 原始 PDF 文件
│   ├── markdown/         # 转换后的 Markdown 文件
│   ├── images/           # 提取的图片
│   └── chunks/           # 切分后的片段
├── scripts/              # 脚本目录
│   ├── pdf_to_markdown.py  # PDF 转 Markdown
│   ├── chunk_markdown.py   # Markdown 切分
│   ├── store_to_qdrant.py  # 向量存储
│   ├── retrieve.py         # 向量召回
│   ├── fusion.py           # 多路召回融合
│   ├── rerank.py           # 重排和 LLM 集成
│   ├── config.py           # 配置文件
│   └── evaluate/           # 评估脚本
│       ├── test_retrieval.py     # 检索质量评估
│       └── bench_performance.py  # 性能压测
├── output/               # 输出目录
├── .env                  # 环境变量
├── requirements.txt      # 依赖清单
└── README.md             # 本说明文档
```

## 8. 常见问题

### 8.1 Qdrant 连接失败
**问题**：无法连接到 Qdrant 服务
**解决方案**：
- 检查 Qdrant 服务是否正在运行
- 确认 `.env` 文件中的 Qdrant 配置正确
- 验证网络连接

### 8.2 API Key 错误
**问题**：DashScope 或 DeepSeek API Key 错误
**解决方案**：
- 检查 `.env` 文件中的 API Key 是否正确
- 确保 API Key 未过期
- 验证网络连接

### 8.3 检索结果不相关
**问题**：检索结果与查询不相关
**解决方案**：
- 检查文档是否正确构建到知识库
- 调整切分参数（CHUNK_SIZE、CHUNK_OVERLAP）
- 考虑添加更多相关文档

### 8.4 性能问题
**问题**：系统响应速度慢
**解决方案**：
- 检查 Qdrant 服务性能
- 考虑使用更轻量级的 Embedding 模型
- 实现缓存机制

## 9. 扩展建议

### 9.1 多模态支持
- 集成 CLIP 模型处理图片
- 支持表格提取和结构化

### 9.2 用户界面
- 构建 Web 界面
- 提供 CLI 工具

### 9.3 模型优化
- 尝试更先进的重排模型
- 探索本地部署的 LLM

### 9.4 系统监控
- 添加日志记录
- 建立性能监控机制

## 10. 联系方式

如果您在使用过程中遇到问题，请联系系统管理员。

---

**文档版本**：1.0
**最后更新**：2026-04-12