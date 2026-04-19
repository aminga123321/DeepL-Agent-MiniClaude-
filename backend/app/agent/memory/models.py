"""
记忆系统数据模型
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DialogueRole(str, Enum):
    """对话角色"""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"


@dataclass
class DialogueUnit:
    """单轮对话记录"""
    role: DialogueRole
    content: Any  # 文本或工具调用
    timestamp: datetime
    tools_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tools_used": self.tools_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueUnit":
        """从字典创建"""
        return cls(
            role=DialogueRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tools_used=data.get("tools_used", [])
        )


@dataclass
class MemoryPayload:
    """Qdrant 存储结构"""
    # 向量化字段（用于检索）
    original_content: str  # 多轮对话原文（JSON序列化）

    # 元数据（用于过滤）
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 辅助字段（用于快速筛选）
    summary: str = ""
    keywords: List[str] = field(default_factory=list)

    # Qdrant 相关字段（不存储，仅用于操作）
    vector: Optional[List[float]] = None
    point_id: Optional[int] = None
    similarity_score: Optional[float] = None

    def to_qdrant_point(self, vector: List[float], point_id: int) -> Dict[str, Any]:
        """转换为 Qdrant Point 结构"""
        return {
            "id": point_id,
            "vector": vector,
            "payload": {
                "original_content": self.original_content,
                "summary": self.summary,
                "keywords": self.keywords,
                "metadata": self.metadata
            }
        }

    @classmethod
    def from_qdrant_point(cls, point: Dict[str, Any]) -> "MemoryPayload":
        """从 Qdrant Point 创建"""
        payload = point.get("payload", {})
        return cls(
            original_content=payload.get("original_content", ""),
            metadata=payload.get("metadata", {}),
            summary=payload.get("summary", ""),
            keywords=payload.get("keywords", []),
            vector=point.get("vector"),
            point_id=point.get("id"),
            similarity_score=point.get("score")
        )


@dataclass
class TopicSummary:
    """主题摘要（存储在LLM上下文）"""
    topic_id: str  # 唯一标识
    topic_name: str  # 主题名称
    timestamp: datetime
    last_updated: datetime

    # 内容
    summary_text: str  # 自然语言摘要
    key_points: List[str] = field(default_factory=list)  # 关键点列表
    conclusions: List[str] = field(default_factory=list)  # 结论或待办事项
    related_tools: List[str] = field(default_factory=list)  # 涉及的工具

    # 统计
    reference_count: int = 0  # 被引用次数
    dialogue_count: int = 0   # 包含的对话轮数
    relevance_score: float = 0.0  # 与当前对话的相关性

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "timestamp": self.timestamp.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "summary_text": self.summary_text,
            "key_points": self.key_points,
            "conclusions": self.conclusions,
            "related_tools": self.related_tools,
            "reference_count": self.reference_count,
            "dialogue_count": self.dialogue_count,
            "relevance_score": self.relevance_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicSummary":
        """从字典创建"""
        return cls(
            topic_id=data["topic_id"],
            topic_name=data["topic_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            summary_text=data["summary_text"],
            key_points=data.get("key_points", []),
            conclusions=data.get("conclusions", []),
            related_tools=data.get("related_tools", []),
            reference_count=data.get("reference_count", 0),
            dialogue_count=data.get("dialogue_count", 0),
            relevance_score=data.get("relevance_score", 0.0)
        )

    def format_for_prompt(self) -> str:
        """格式化为提示词"""
        return f"""
主题：{self.topic_name}
时间：{self.timestamp.strftime('%Y-%m-%d %H:%M')}
摘要：{self.summary_text}
关键点：
{chr(10).join(f'• {point}' for point in self.key_points)}
相关工具：{', '.join(self.related_tools) if self.related_tools else '无'}
"""


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    # 短记忆
    short_term_window: int = 10  # 最近对话轮数
    max_short_term_tokens: int = 4000  # 最大短记忆 tokens
    min_short_term_rounds: int = 3  # 最小轮数
    max_short_term_rounds: int = 20  # 最大轮数

    # 主题摘要
    max_topic_summaries: int = 10  # 最大摘要数
    topic_change_threshold: float = 0.6  # 主题变化阈值

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    memory_collection: str = "agent_memories"
    summary_collection: str = "agent_summaries"  # 可选

    # Embedding
    embedding_model: str = "text-embedding-v3"  # DashScope 模型

    # 检索
    retrieval_top_k: int = 3
    similarity_threshold: float = 0.7
    time_decay_factor: float = 0.004  # 时间衰减因子

    # 性能
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    batch_embedding_size: int = 10  # 批量向量化大小
    qdrant_timeout: int = 30  # Qdrant 超时时间

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """从环境变量创建配置"""
        import os
        return cls(
            short_term_window=int(os.getenv("MEMORY_SHORT_TERM_WINDOW", "10")),
            max_short_term_tokens=int(os.getenv("MEMORY_MAX_SHORT_TERM_TOKENS", "4000")),
            min_short_term_rounds=int(os.getenv("MEMORY_MIN_SHORT_TERM_ROUNDS", "3")),
            max_short_term_rounds=int(os.getenv("MEMORY_MAX_SHORT_TERM_ROUNDS", "20")),
            max_topic_summaries=int(os.getenv("MEMORY_MAX_TOPIC_SUMMARIES", "10")),
            topic_change_threshold=float(os.getenv("MEMORY_TOPIC_CHANGE_THRESHOLD", "0.6")),
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            memory_collection=os.getenv("MEMORY_COLLECTION", "agent_memories"),
            summary_collection=os.getenv("SUMMARY_COLLECTION", "agent_summaries"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3"),
            retrieval_top_k=int(os.getenv("MEMORY_RETRIEVAL_TOP_K", "3")),
            similarity_threshold=float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.7")),
            time_decay_factor=float(os.getenv("MEMORY_TIME_DECAY_FACTOR", "0.004")),
            enable_caching=os.getenv("MEMORY_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("MEMORY_CACHE_TTL_SECONDS", "300")),
            batch_embedding_size=int(os.getenv("MEMORY_BATCH_EMBEDDING_SIZE", "10")),
            qdrant_timeout=int(os.getenv("MEMORY_QDRANT_TIMEOUT", "30"))
        )