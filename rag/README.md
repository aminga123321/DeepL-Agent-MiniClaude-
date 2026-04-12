# RAG 系统：智能知识库问答系统

## 项目介绍

这是一个基于 Retrieval-Augmented Generation (RAG) 技术的智能知识库问答系统，能够处理 PDF 文档，构建知识库，并提供准确的问答功能。

## 功能特性

- **知识库构建**：支持 PDF 转 Markdown、Markdown 切分、向量存储
- **多路召回**：向量召回 + BM25 关键词召回，使用 RRF 融合
- **智能重排**：使用 DashScope TextReRank 进行结果重排
- **LLM 集成**：集成 DeepSeek 模型，生成高质量回答
- **动态 BM25 索引**：使用 SQLite 构建关键词库，支持中英文查询
- **性能优化**：多路召回提高召回率，重排提高准确率

## 技术栈

- **Python 3.11+**
- **Qdrant**：向量数据库
- **DashScope**：Embedding 和 TextReRank API
- **DeepSeek**：大语言模型 API
- **pymupdf4llm**：PDF 转 Markdown
- **langchain-text-splitters**：Markdown 切分

## 安装步骤

### 1. 克隆仓库

```bash
git clone <your-repository-url>
cd rag
```

### 2. 创建虚拟环境

```bash
# 使用 Anaconda
conda create -n rag python=3.11
conda activate rag

# 或使用 venv
python -m venv venv
# Windows
env\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写相关 API 密钥：

```bash
cp .env.example .env
```

在 `.env` 文件中填写：
- `DASHSCOPE_API_KEY`：阿里云 DashScope API 密钥
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥
- `QDRANT_HOST`：Qdrant 服务地址
- `QDRANT_PORT`：Qdrant 服务端口

### 5. 启动 Qdrant 服务

```bash
# 下载 Qdrant
# Windows
iwr https://github.com/qdrant/qdrant/releases/download/v1.10.1/qdrant-windows-amd64.zip -OutFile qdrant.zip
Expand-Archive qdrant.zip -DestinationPath .

# 启动 Qdrant
./qdrant.exe

# macOS/Linux
# 参考 Qdrant 官方文档安装
```

## 使用方法

### 1. 构建知识库

```python
from scripts.rag import rag_system

# 构建知识库（处理所有 PDF 文件）
build_result = rag_system.build_knowledge_base()
print(f"知识库构建结果: {build_result}")

# 构建知识库（处理指定 PDF 文件）
pdf_paths = ["path/to/pdf1.pdf", "path/to/pdf2.pdf"]
build_result = rag_system.build_knowledge_base(pdf_paths)
```

### 2. 智能问答

```python
from scripts.rag import rag_system

# 执行完整 RAG 流程
result = rag_system.rag_pipeline("AlphaOPT 是什么？")
print(f"回答: {result['answer']}")
print(f"检索到的文档数: {len(result['retrieved_docs'])}")

# 仅执行检索（不生成回答）
retrieved_docs = rag_system.retrieve("AlphaOPT 是什么？", top_k=5)
print(f"检索到的文档数: {len(retrieved_docs)}")
```

### 3. 运行测试

```bash
# 测试 RAG 类
python test_rag_class.py

# 测试 BM25 索引
python test_bm25_simple.py

# 测试检索质量
python scripts/evaluate/test_retrieval.py

# 测试性能
python scripts/evaluate/bench_performance.py
```

## 项目结构

```
rag/
├── data/              # 数据目录
│   ├── raw/           # 原始 PDF 文件
│   ├── markdown/      # 转换后的 Markdown 文件
│   └── chunks/        # 切分后的文本块
├── scripts/           # 核心脚本
│   ├── config.py      # 配置文件
│   ├── convert_pdf_to_md.py  # PDF 转 Markdown
│   ├── chunk_markdown.py     # Markdown 切分
│   ├── store_to_qdrant.py    # 向量存储
│   ├── retrieve.py    # 向量召回
│   ├── fusion.py      # 多路召回融合
│   ├── rerank.py      # 重排
│   ├── bm25_index.py  # BM25 索引
│   └── rag.py         # RAG 系统类
├── test_rag_class.py  # RAG 类测试
├── test_bm25_simple.py  # BM25 索引测试
├── requirements.txt   # 依赖文件
├── .env.example       # 环境变量示例
└── .gitignore         # Git 忽略文件
```

## 性能指标

- **召回率**：100%
- **准确率**：89%
- **平均响应时间**：295.40 ms
- **系统稳定性**：良好

## 常见问题

### Q1: 终端无法识别 conda 命令

A: 使用 conda 完整路径执行命令，例如：
```bash
& 'D:\Anaconda\Anaconda3\Scripts\conda.exe' activate rag
```

### Q2: Qdrant 客户端 search 方法不存在

A: 使用 HTTP API 进行向量搜索，参考 `scripts/retrieve.py` 中的实现。

### Q3: BM25 召回无结果

A: 系统使用动态关键词库，会自动从文档中提取关键词，支持中英文查询。

### Q4: TextReRank 导入失败

A: 使用 DashScope TextReRank API，需要配置 `DASHSCOPE_API_KEY`。

## 未来扩展

- **多模态支持**：处理图片、表格等
- **用户界面**：Web 或 CLI 界面
- **评估系统**：更完善的评估指标
- **缓存机制**：缓存常见查询结果，提高响应速度

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎联系项目维护者。
