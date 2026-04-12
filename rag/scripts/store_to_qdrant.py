"""
步骤 3：将切分后的 Chunk 向量化并存储到 Qdrant
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import time

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    CHUNKS_DIR,
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    VECTOR_DISTANCE,
    DASHSCOPE_API_KEY,
)

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import dashscope


def get_embedding(text: str) -> List[float]:
    """
    使用 DashScope 生成文本向量
    """
    resp = dashscope.TextEmbedding.call(
        model=EMBEDDING_MODEL,
        input=text,
        text_type="document",
        dimensions=EMBEDDING_DIMENSION,
    )
    if resp.status_code != 200:
        raise Exception(f"Embedding failed: {resp}")
    return resp.output["embeddings"][0]["embedding"]


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    批量生成向量
    """
    embeddings = []
    for i, text in enumerate(texts):
        print(f"  生成向量 {i+1}/{len(texts)}")
        embedding = get_embedding(text)
        embeddings.append(embedding)
        time.sleep(0.1)
    return embeddings


def init_qdrant_collection(client: QdrantClient):
    """
    初始化 Qdrant Collection
    """
    if client.collection_exists(COLLECTION_NAME):
        print(f"⚠️  集合 {COLLECTION_NAME} 已存在，正在删除...")
        client.delete_collection(COLLECTION_NAME)
    
    print(f"✅ 创建集合 {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE if VECTOR_DISTANCE == "Cosine" else Distance.DOT,
        ),
    )


def store_chunks_to_qdrant(chunks: List[Dict]):
    """
    将 Chunk 存储到 Qdrant
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    init_qdrant_collection(client)
    
    print(f"\n开始处理 {len(chunks)} 个 Chunk...")
    
    texts = [chunk["content"] for chunk in chunks]
    embeddings = get_embeddings_batch(texts)
    
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=i,
            vector=embedding,
            payload={
                "content": chunk["content"],
                **chunk["metadata"],
            },
        )
        points.append(point)
    
    print(f"\n正在上传到 Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )
    
    print(f"✅ 完成！共存储 {len(points)} 个向量")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    
    return client


def main():
    """主函数"""
    chunks_path = CHUNKS_DIR / "all_chunks.json"
    
    if not chunks_path.exists():
        print(f"❌ 没有找到切分结果，请先运行 2_chunk_markdown.py")
        return
    
    if not DASHSCOPE_API_KEY:
        print(f"❌ 请在 .env 文件中配置 DASHSCOPE_API_KEY")
        print(f"   获取方式：https://dashscope.aliyun.com/")
        return
    
    print(f"="*50)
    print(f"步骤 3：存储到 Qdrant")
    print(f"="*50)
    
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    print(f"读取到 {len(chunks)} 个 Chunk")
    
    try:
        store_chunks_to_qdrant(chunks)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
