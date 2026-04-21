"""
DashScope 向量化封装
"""
import os
import time
import logging
from typing import List, Optional
import dashscope
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class DashScopeEmbedder:
    """DashScope 文本向量化"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-v3",
        dimensions: int = 1024,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化 DashScope 向量化器

        Args:
            api_key: DashScope API Key，如果为 None 则从环境变量读取
            model: 向量化模型
            dimensions: 向量维度
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.model = model
        self.dimensions = dimensions
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 获取 API Key
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY 未设置。请设置环境变量或传入 api_key 参数。\n"
                "获取方式：https://dashscope.aliyun.com/"
            )

        dashscope.api_key = self.api_key
        logger.info(f"初始化 DashScope 向量化器，模型: {model}, 维度: {dimensions}")

    def embed(self, text: str) -> List[float]:
        """
        生成单个文本的向量

        Args:
            text: 输入文本

        Returns:
            向量列表

        Raises:
            Exception: 向量化失败
        """
        for attempt in range(self.max_retries):
            try:
                resp = dashscope.TextEmbedding.call(
                    model=self.model,
                    input=text,
                    text_type="document",
                    dimensions=self.dimensions,
                )

                if resp.status_code == 200:
                    return resp.output["embeddings"][0]["embedding"]
                else:
                    error_msg = f"DashScope 向量化失败 (状态码: {resp.status_code}): {resp}"
                    if attempt < self.max_retries - 1:
                        logger.warning(f"第 {attempt + 1} 次尝试失败: {error_msg}")
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise Exception(error_msg)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"第 {attempt + 1} 次尝试异常: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"DashScope 向量化失败: {e}")

        raise Exception("向量化失败，达到最大重试次数")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成向量

        Args:
            texts: 文本列表

        Returns:
            向量列表的列表
        """
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts, 1):
            try:
                embedding = self.embed(text)
                embeddings.append(embedding)
                logger.debug(f"向量化进度: {i}/{total}")

                # 避免速率限制
                if i % 10 == 0:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"文本向量化失败 (第 {i} 个): {e}")
                # 返回零向量作为占位符
                embeddings.append([0.0] * self.dimensions)

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        生成查询向量（使用 query 类型）

        Args:
            query: 查询文本

        Returns:
            查询向量
        """
        for attempt in range(self.max_retries):
            try:
                resp = dashscope.TextEmbedding.call(
                    model=self.model,
                    input=query,
                    text_type="query",  # 查询类型
                    dimensions=self.dimensions,
                )

                if resp.status_code == 200:
                    return resp.output["embeddings"][0]["embedding"]
                else:
                    error_msg = f"DashScope 查询向量化失败 (状态码: {resp.status_code}): {resp}"
                    if attempt < self.max_retries - 1:
                        logger.warning(f"第 {attempt + 1} 次尝试失败: {error_msg}")
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise Exception(error_msg)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"第 {attempt + 1} 次尝试异常: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"DashScope 查询向量化失败: {e}")

        raise Exception("查询向量化失败，达到最大重试次数")

    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            余弦相似度 (0-1)
        """
        import numpy as np

        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # 归一化
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(v1, v2) / (norm1 * norm2)

    def batch_similarity(self, query_vector: List[float], vectors: List[List[float]]) -> List[float]:
        """
        计算查询向量与多个向量的相似度

        Args:
            query_vector: 查询向量
            vectors: 目标向量列表

        Returns:
            相似度列表
        """
        import numpy as np

        query_np = np.array(query_vector)
        similarities = []

        for vec in vectors:
            target_np = np.array(vec)
            norm_query = np.linalg.norm(query_np)
            norm_target = np.linalg.norm(target_np)

            if norm_query == 0 or norm_target == 0:
                similarities.append(0.0)
            else:
                similarity = np.dot(query_np, target_np) / (norm_query * norm_target)
                similarities.append(float(similarity))

        return similarities