"""
Qdrant 客户端封装 - 记忆系统专用
"""
import json
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance,
    Filter, FieldCondition, MatchValue
)

from .models import MemoryPayload, MemoryConfig

logger = logging.getLogger(__name__)


class MemoryQdrantClient:
    """记忆系统专用的 Qdrant 客户端"""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            timeout=10.0
        )
        self._ensure_collections()

    def _ensure_collections(self):
        """确保集合存在"""
        # 主记忆集合
        if not self.client.collection_exists(self.config.memory_collection):
            logger.info(f"创建记忆集合: {self.config.memory_collection}")
            self.client.create_collection(
                collection_name=self.config.memory_collection,
                vectors_config=VectorParams(
                    size=1024,  # DashScope text-embedding-v3 维度
                    distance=Distance.COSINE
                )
            )

        # 可选：摘要集合
        if self.config.summary_collection and not self.client.collection_exists(self.config.summary_collection):
            logger.info(f"创建摘要集合: {self.config.summary_collection}")
            self.client.create_collection(
                collection_name=self.config.summary_collection,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )

    def store_memory(self, memory: MemoryPayload, vector: List[float]) -> int:
        """存储记忆到 Qdrant"""
        # 生成点ID（可以使用时间戳哈希或递增ID）
        import hashlib
        import time
        point_id = int(hashlib.md5(str(time.time()).encode()).hexdigest()[:8], 16)

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "original_content": memory.original_content,
                "summary": memory.summary,
                "keywords": memory.keywords,
                "metadata": memory.metadata,
                "timestamp": memory.metadata.get("timestamp", ""),
                "topic": memory.metadata.get("topic", ""),
                "session_id": memory.metadata.get("session_id", ""),
            }
        )

        self.client.upsert(
            collection_name=self.config.memory_collection,
            points=[point]
        )

        logger.info(f"存储记忆到 Qdrant，ID: {point_id}")
        return point_id

    def search_memories(
        self,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[MemoryPayload]:
        """搜索相似记忆"""
        # 构建查询过滤器
        query_filter = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # 列表值：使用 MatchAny（简化版）
                    for v in value:
                        must_conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=v))
                        )
                else:
                    must_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )

            if must_conditions:
                query_filter = Filter(must=must_conditions)

        # 执行搜索（使用新版本 API）
        search_result = self.client.query_points(
            collection_name=self.config.memory_collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )

        # 转换为 MemoryPayload 对象
        memories = []
        # 新版本 API 返回 QueryResponse，包含 points 属性
        points = getattr(search_result, 'points', search_result) if search_result else []
        for result in points:
            memory = MemoryPayload.from_qdrant_point({
                "id": result.id,
                "vector": result.vector,
                "score": result.score,
                "payload": result.payload
            })
            memories.append(memory)

        return memories

    def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[MemoryPayload]:
        """基于关键词搜索（全量扫描，适用于小规模数据）"""
        # 注意：这不是向量搜索，是全量扫描关键词匹配
        # 对于生产环境，应考虑更好的关键词索引方案

        # 获取所有点（仅适用于小规模数据）
        all_points = self.client.scroll(
            collection_name=self.config.memory_collection,
            limit=1000  # 限制数量
        )[0]

        # 关键词匹配
        matched_memories = []
        for point in all_points:
            payload = point.payload
            point_keywords = payload.get("keywords", [])

            # 计算匹配度
            matched_keywords = set(keywords) & set(point_keywords)
            if matched_keywords:
                memory = MemoryPayload.from_qdrant_point({
                    "id": point.id,
                    "vector": point.vector,
                    "score": len(matched_keywords) / len(keywords) if keywords else 0,
                    "payload": payload
                })
                matched_memories.append(memory)

        # 按匹配度排序
        matched_memories.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        return matched_memories[:limit]

    def delete_memory(self, point_id: int) -> bool:
        """删除记忆"""
        try:
            self.client.delete(
                collection_name=self.config.memory_collection,
                points_selector=[point_id]
            )
            logger.info(f"删除记忆，ID: {point_id}")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            info = self.client.get_collection(self.config.memory_collection)
            vectors_config = getattr(info.config, 'params', None)
            vectors_params = getattr(vectors_config, 'vectors', None) if vectors_config else None
            return {
                "name": self.config.memory_collection,
                "vectors_size": getattr(vectors_params, 'size', 0) if vectors_params else 0,
                "vectors_count": getattr(info, 'vectors_count', 0),
                "points_count": getattr(info, 'points_count', 0),
                "status": getattr(info, 'status', 'unknown')
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}

    def clear_collection(self) -> bool:
        """清空集合（测试用）"""
        try:
            self.client.delete_collection(self.config.memory_collection)
            self._ensure_collections()
            logger.info(f"清空集合: {self.config.memory_collection}")
            return True
        except Exception as e:
            logger.error(f"清空集合失败: {e}")
            return False