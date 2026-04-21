"""
RAG 配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# 路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
MARKDOWN_DIR = DATA_DIR / "markdown"
IMAGES_DIR = DATA_DIR / "images"
CHUNKS_DIR = DATA_DIR / "chunks"

# 创建目录
for dir_path in [RAW_DIR, MARKDOWN_DIR, IMAGES_DIR, CHUNKS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Qdrant 配置
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "company_knowledge"

# Embedding 配置
EMBEDDING_MODEL = "text-embedding-v3"
EMBEDDING_DIMENSION = 1024  # v3 支持 64-1024
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# DeepSeek 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-chat"

# 切分配置
CHUNK_SIZE = 1000          # 目标字符数
CHUNK_OVERLAP = 200        # 重叠字符数
MIN_CHUNK_SIZE = 100       # 最小 chunk 大小

# Qdrant Collection 配置
VECTOR_DISTANCE = "Cosine"  # 余弦相似度