"""
记忆管理器 - 协调短记忆、长记忆、摘要生成和检索
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from .models import (
    DialogueUnit, DialogueRole, MemoryPayload, TopicSummary, MemoryConfig
)
from .qdrant_client import MemoryQdrantClient
from .dashscope_embedder import DashScopeEmbedder
from openai import OpenAI

logger = logging.getLogger(__name__)

# 尝试导入 tiktoken 用于 tokens 计算
try:
    import tiktoken
except ImportError:
    tiktoken = None


class MemoryManager:
    """记忆管理器 - 统一管理三层记忆"""

    def __init__(
        self,
        session_id: str,
        config: Optional[MemoryConfig] = None,
        context=None  # 现有 Context 对象引用
    ):
        """
        初始化记忆管理器

        Args:
            session_id: 会话ID
            config: 记忆配置
            context: 现有的 Context 对象引用（用于短记忆）
        """
        self.session_id = session_id
        self.config = config or MemoryConfig.from_env()
        self.context = context  # 引用现有 Context

        # 会话管理
        self.session_start_time = datetime.now()
        self.session_activity_time = datetime.now()

        # 初始化组件
        self.embedder = DashScopeEmbedder(
            model=self.config.embedding_model,
            dimensions=1024
        )
        
        # 初始化 DeepSeek LLM 客户端（用于摘要生成）
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
        deepseek_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
        
        if deepseek_api_key:
            try:
                self.llm_client = OpenAI(
                    api_key=deepseek_api_key,
                    base_url=deepseek_base_url
                )
                logger.info(f"DeepSeek LLM 客户端初始化成功")
            except Exception as e:
                logger.warning(f"DeepSeek LLM 客户端初始化失败: {e}")
                self.llm_client = None
        else:
            logger.warning("未配置 DeepSeek API Key，摘要生成将使用简单实现")
            self.llm_client = None
        
        # 健壮的 Qdrant 初始化
        self.qdrant_client = None
        self.qdrant_retry_count = 0
        self.qdrant_last_attempt = datetime.now()
        
        # 异步初始化 Qdrant
        asyncio.create_task(self._initialize_qdrant())

        # 内存状态
        self.topic_summaries: List[TopicSummary] = []  # 主题摘要缓存
        self.pending_dialogues: List[DialogueUnit] = []  # 待摘要队列
        self.current_topic: Optional[str] = None  # 当前主题
        self.last_topic_change_time = datetime.now()

        # 缓存
        self._embedding_cache: Dict[str, List[float]] = {}
        self._summary_cache: Dict[str, str] = {}

        # 启动定期维护任务
        asyncio.create_task(self._periodic_maintenance())

        logger.info(f"初始化记忆管理器，会话: {session_id}")

    # ===== 初始化和维护 =====

    async def _initialize_qdrant(self):
        """异步初始化 Qdrant"""
        while self.qdrant_retry_count < 3:
            try:
                self.qdrant_client = MemoryQdrantClient(self.config)
                logger.info(f"Qdrant 初始化成功")
                break
            except Exception as e:
                self.qdrant_retry_count += 1
                wait_time = min(60, 2 ** self.qdrant_retry_count)
                logger.warning(f"Qdrant 连接失败 (尝试 {self.qdrant_retry_count}/3): {e}")
                logger.info(f"将在 {wait_time} 秒后重试")
                await asyncio.sleep(wait_time)
                self.qdrant_last_attempt = datetime.now()

    async def _periodic_maintenance(self):
        """定期维护任务"""
        while True:
            try:
                # 压缩记忆
                await self._compress_memories()
                
                # 每小时执行一次
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"定期维护失败: {e}")
                await asyncio.sleep(3600)

    def _count_tokens(self, text: str) -> int:
        """计算文本的 tokens 数量"""
        try:
            if tiktoken:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                return len(encoding.encode(text))
            else:
                # 降级方案：基于字符数估算
                return len(text) // 4  # 粗略估算，1 token ≈ 4 字符
        except Exception:
            # 异常时使用简单估算
            return len(text) // 4

    # ===== 短记忆管理 =====

    async def record_user_message(self, content: str) -> DialogueUnit:
        """记录用户消息"""
        now = datetime.now()
        
        # 更新会话活动时间
        self.session_activity_time = now
        
        # 检查是否是新会话
        session_duration = (now - self.session_start_time).total_seconds()
        if session_duration > 86400:  # 超过24小时认为是新会话
            self.session_start_time = now
            # 清空短记忆，开始新会话
            self.pending_dialogues.clear()
            logger.info(f"开始新会话，会话: {self.session_id}")
        
        dialogue = DialogueUnit(
            role=DialogueRole.USER,
            content=content,
            timestamp=now,
            tools_used=[]
        )
        
        # 检查对话断点
        if self.pending_dialogues and await self._check_dialogue_break(dialogue):
            # 检测到断点，生成当前主题摘要
            await self._generate_topic_summary()
        
        self.pending_dialogues.append(dialogue)
        
        # 优化：只有当 pending_dialogues 达到阈值或时间间隔时才检查
        if (len(self.pending_dialogues) >= 3 and 
            (datetime.now() - self.last_topic_change_time).total_seconds() > 60):
            await self._check_topic_change()
        
        return dialogue

    async def record_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> DialogueUnit:
        """记录助手消息"""
        tools_used = []
        if tool_calls:
            tools_used = [tc.get("name", "") for tc in tool_calls]

        dialogue = DialogueUnit(
            role=DialogueRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            tools_used=tools_used
        )
        self.pending_dialogues.append(dialogue)
        await self._check_topic_change()
        return dialogue

    async def record_tool_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: str
    ) -> DialogueUnit:
        """记录工具执行结果"""
        dialogue = DialogueUnit(
            role=DialogueRole.TOOL_RESULT,
            content={
                "tool_name": tool_name,
                "args": args,
                "result": result
            },
            timestamp=datetime.now(),
            tools_used=[tool_name]
        )
        self.pending_dialogues.append(dialogue)
        await self._check_topic_change()
        return dialogue

    async def _check_dialogue_break(self, new_dialogue: DialogueUnit) -> bool:
        """检测对话断点"""
        if not self.pending_dialogues:
            return False
        
        last_dialogue = self.pending_dialogues[-1]
        
        # 检查时间间隔
        time_gap = (new_dialogue.timestamp - last_dialogue.timestamp).total_seconds()
        if time_gap > 3600:  # 超过1小时
            logger.info(f"检测到对话断点（时间间隔 {time_gap:.1f} 秒）")
            return True
        
        # 检查内容相似度
        try:
            last_content = str(last_dialogue.content)
            new_content = str(new_dialogue.content)
            
            if len(last_content) > 50 and len(new_content) > 50:
                vectors = self.embedder.embed_batch([last_content, new_content])
                similarity = self.embedder.similarity(vectors[0], vectors[1])
                logger.debug(f"对话内容相似度: {similarity}")
                if similarity < 0.4:
                    logger.info(f"检测到对话断点（相似度 {similarity:.3f}）")
                    return True
        except Exception as e:
            logger.error(f"对话断点检测失败: {e}")
        
        return False

    def get_short_term_memories(self, limit: Optional[int] = None) -> List[DialogueUnit]:
        """获取短记忆（基于 tokens 的动态窗口）"""
        if not self.pending_dialogues:
            return []
        
        # 如果指定了固定限制，使用指定值
        if limit:
            return self.pending_dialogues[-limit:]
        
        # 基于 tokens 的动态窗口
        total_tokens = 0
        selected_dialogues = []
        
        # 从最近的对话开始往回计算
        for dialogue in reversed(self.pending_dialogues):
            content = str(dialogue.content)
            tokens = self._count_tokens(content)
            
            # 检查是否超过 token 限制
            if total_tokens + tokens > self.config.max_short_term_tokens:
                if len(selected_dialogues) >= self.config.min_short_term_rounds:
                    break
            else:
                total_tokens += tokens
                selected_dialogues.append(dialogue)
        
        # 检查是否达到最小轮数
        if len(selected_dialogues) < self.config.min_short_term_rounds:
            # 即使超过 token 限制，也要保证最小轮数
            selected_dialogues = list(reversed(self.pending_dialogues))[:self.config.min_short_term_rounds]
        
        # 反转回原始顺序
        selected_dialogues.reverse()
        
        # 确保不超过最大轮数
        if len(selected_dialogues) > self.config.max_short_term_rounds:
            selected_dialogues = selected_dialogues[-self.config.max_short_term_rounds:]
        
        logger.debug(f"短记忆窗口：{len(selected_dialogues)} 轮，约 {total_tokens} tokens")
        return selected_dialogues

    # ===== 主题检测 =====

    async def _check_topic_change(self):
        """检测主题变化（优化版）"""
        if len(self.pending_dialogues) < 3:
            return

        # 提取最近对话的文本（批量处理）
        recent_texts = []
        for dialogue in self.pending_dialogues[-3:]:
            if isinstance(dialogue.content, str):
                recent_texts.append(dialogue.content)
            elif isinstance(dialogue.content, dict):
                recent_texts.append(str(dialogue.content))

        if len(recent_texts) < 2:
            return

        # 批量生成向量
        try:
            vectors = self.embedder.embed_batch(recent_texts)
            if len(vectors) >= 2:
                similarity = self.embedder.similarity(vectors[-1], vectors[-2])
                logger.debug(f"主题相似度: {similarity}")

                if similarity < self.config.topic_change_threshold:
                    await self._generate_topic_summary()
        except Exception as e:
            logger.error(f"主题检测失败: {e}")

    # ===== 摘要生成和存储 =====

    async def _generate_topic_summary(self):
        """生成主题摘要（使用 LLM）"""
        if not self.pending_dialogues:
            return

        # 提取当前主题的对话
        topic_dialogues = self.pending_dialogues.copy()
        self.pending_dialogues.clear()

        # 使用 LLM 生成摘要
        if self.llm_client:
            summary_data = await self._generate_llm_summary(topic_dialogues)
            summary_text = summary_data["summary"]
            topic_name = summary_data["topic_name"]
            key_points = summary_data["key_points"]
        else:
            # 降级到简单实现
            summary_text = self._generate_simple_summary(topic_dialogues)
            topic_name = self._extract_topic_name(topic_dialogues)
            key_points = self._extract_key_points(topic_dialogues)

        # 创建主题摘要
        topic_id = f"topic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        summary = TopicSummary(
            topic_id=topic_id,
            topic_name=topic_name,
            timestamp=datetime.now(),
            last_updated=datetime.now(),
            summary_text=summary_text,
            key_points=key_points,
            related_tools=self._extract_related_tools(topic_dialogues),
            dialogue_count=len(topic_dialogues)
        )

        # 存储到摘要缓存
        self.topic_summaries.append(summary)
        self._trim_topic_summaries()

        # 存储原文到 Qdrant
        await self._store_to_qdrant(topic_dialogues, summary)

        # 更新当前主题
        self.current_topic = topic_name
        self.last_topic_change_time = datetime.now()

        logger.info(f"生成主题摘要: {topic_name}")

    async def _generate_llm_summary(self, dialogues: List[DialogueUnit]) -> Dict[str, Any]:
        """使用 LLM 生成高质量摘要"""
        # 构建对话文本
        dialogue_texts = []
        for i, d in enumerate(dialogues):
            role = "用户" if d.role == DialogueRole.USER else "助手"
            content = str(d.content)[:500]  # 限制每条消息长度
            dialogue_texts.append(f"【{role}】{content}")
        
        dialogue_context = "\n".join(dialogue_texts)
        
        # LLM 摘要生成提示词
        summary_prompt = f"""基于以下对话记录，请生成一个简洁的主题摘要。

## 对话记录
{dialogue_context}

## 要求
请按以下 JSON 格式输出：
{{
    "topic_name": "主题名称（5个字以内）",
    "summary": "主题摘要（100字以内，用中文描述对话的核心内容和结论）",
    "key_points": ["关键点1", "关键点2", "关键点3"]
}}

注意：
1. topic_name 要简洁，能准确反映对话主题
2. summary 要包含对话的主要内容和结论
3. key_points 列出对话中最重要的3个要点
4. 只输出 JSON，不要有其他内容"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的对话摘要助手，擅长提取对话的核心信息和要点。"},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析 JSON 结果
            # 尝试提取 JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            logger.debug(f"LLM 摘要生成成功: {result['topic_name']}")
            return {
                "topic_name": result.get("topic_name", "未命名主题"),
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM 摘要 JSON 解析失败: {e}，使用简单实现")
            return {
                "topic_name": self._extract_topic_name(dialogues),
                "summary": self._generate_simple_summary(dialogues),
                "key_points": self._extract_key_points(dialogues)
            }
        except Exception as e:
            logger.error(f"LLM 摘要生成失败: {e}，使用简单实现")
            return {
                "topic_name": self._extract_topic_name(dialogues),
                "summary": self._generate_simple_summary(dialogues),
                "key_points": self._extract_key_points(dialogues)
            }

    def _generate_simple_summary(self, dialogues: List[DialogueUnit]) -> str:
        """生成简单摘要（占位实现）"""
        # 实际实现应该调用 LLM
        text_parts = []
        for dialogue in dialogues[-5:]:  # 只取最后5轮
            if isinstance(dialogue.content, str):
                text_parts.append(dialogue.content[:100])

        return " | ".join(text_parts)[:500]

    def _extract_topic_name(self, dialogues: List[DialogueUnit]) -> str:
        """提取主题名称（占位实现）"""
        # 实际实现应该调用 LLM 或使用关键词提取
        if dialogues:
            first_content = dialogues[0].content
            if isinstance(first_content, str):
                words = first_content.split()[:3]
                return " ".join(words)
        return "未命名主题"

    def _extract_key_points(self, dialogues: List[DialogueUnit]) -> List[str]:
        """提取关键点（占位实现）"""
        key_points = []
        for i, dialogue in enumerate(dialogues[:3]):  # 取前3轮
            if isinstance(dialogue.content, str):
                key_points.append(f"第{i+1}轮: {dialogue.content[:50]}...")
        return key_points

    def _extract_related_tools(self, dialogues: List[DialogueUnit]) -> List[str]:
        """提取相关工具"""
        tools = set()
        for dialogue in dialogues:
            tools.update(dialogue.tools_used)
        return list(tools)

    async def _store_to_qdrant(self, dialogues: List[DialogueUnit], summary: TopicSummary):
        """存储对话到 Qdrant"""
        if self.qdrant_client is None:
            logger.debug("Qdrant 客户端不可用，跳过存储")
            return
        try:
            # 序列化对话（处理 datetime 对象）
            dialogue_dicts = []
            for dialogue in dialogues:
                d = asdict(dialogue)
                # 转换 datetime 为字符串
                if 'timestamp' in d and hasattr(d['timestamp'], 'isoformat'):
                    d['timestamp'] = d['timestamp'].isoformat()
                dialogue_dicts.append(d)
            original_content = json.dumps(dialogue_dicts, ensure_ascii=False)

            # 生成向量（使用摘要文本）
            vector = self.embedder.embed(summary.summary_text)

            # 创建 MemoryPayload
            memory = MemoryPayload(
                original_content=original_content,
                metadata={
                    "session_id": self.session_id,
                    "topic": summary.topic_name,
                    "timestamp": datetime.now().isoformat(),
                    "dialogue_count": len(dialogues),
                    "tools_used": summary.related_tools,
                    "topic_id": summary.topic_id
                },
                summary=summary.summary_text,
                keywords=self._extract_keywords(summary.summary_text)
            )

            # 存储到 Qdrant
            point_id = self.qdrant_client.store_memory(memory, vector)
            logger.debug(f"存储对话到 Qdrant，点ID: {point_id}")

        except Exception as e:
            logger.error(f"存储到 Qdrant 失败: {e}")

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 实际实现应该使用更高级的关键词提取
        words = text.lower().split()
        # 过滤停用词（简化版）
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一"}
        keywords = [word for word in words if word not in stopwords and len(word) > 1]
        return keywords[:10]  # 最多10个关键词

    def _trim_topic_summaries(self):
        """修剪主题摘要缓存"""
        if len(self.topic_summaries) > self.config.max_topic_summaries:
            # 淘汰最旧的摘要
            self.topic_summaries = self.topic_summaries[-self.config.max_topic_summaries:]
            logger.debug(f"修剪主题摘要缓存，当前数量: {len(self.topic_summaries)}")

    # ===== 记忆检索 =====

    async def retrieve_memories(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[MemoryPayload]:
        """
        检索相关记忆（优化版）

        Args:
            query: 查询文本
            limit: 返回数量限制

        Returns:
            相关记忆列表
        """
        try:
            # 1. 生成查询向量
            query_vector = self.embedder.embed_query(query)

            # 2. 从 Qdrant 检索
            memories = self.qdrant_client.search_memories(
                query_vector=query_vector,
                limit=limit or self.config.retrieval_top_k * 2,  # 多取一些结果
                score_threshold=self.config.similarity_threshold
            )

            # 3. 应用时间衰减
            now = datetime.now()
            for mem in memories:
                # 计算时间衰减因子（越新的记忆权重越高）
                mem_time = datetime.fromisoformat(mem.metadata.get("timestamp", now.isoformat()))
                hours_passed = (now - mem_time).total_seconds() / 3600
                time_decay = max(0.3, 1.0 - (hours_passed * self.config.time_decay_factor))
                
                # 调整相似度分数
                if mem.similarity_score:
                    mem.similarity_score *= time_decay

            # 4. 重新排序并过滤
            memories.sort(key=lambda x: x.similarity_score or 0, reverse=True)
            filtered_memories = [
                mem for mem in memories 
                if (mem.similarity_score or 0) >= self.config.similarity_threshold
            ][:limit or self.config.retrieval_top_k]

            logger.debug(f"检索到 {len(filtered_memories)} 个相关记忆")
            return filtered_memories

        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            # 降级：从主题摘要缓存中搜索
            return self._fallback_retrieval(query, limit)

    def _fallback_retrieval(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[MemoryPayload]:
        """降级检索：从主题摘要缓存搜索"""
        # 简单文本匹配
        query_lower = query.lower()
        matched_summaries = []

        for summary in self.topic_summaries:
            # 检查主题名称和摘要文本
            if (query_lower in summary.topic_name.lower() or
                query_lower in summary.summary_text.lower()):
                matched_summaries.append(summary)

        # 转换为 MemoryPayload（简化版）
        memories = []
        for summary in matched_summaries[:limit or self.config.retrieval_top_k]:
            memory = MemoryPayload(
                original_content="",  # 降级模式不加载原文
                metadata={
                    "topic": summary.topic_name,
                    "timestamp": summary.timestamp.isoformat(),
                    "source": "fallback_cache"
                },
                summary=summary.summary_text,
                keywords=self._extract_keywords(summary.summary_text)
            )
            memories.append(memory)

        return memories

    # ===== 工具方法 =====

    def get_topic_summaries_for_prompt(self, limit: int = 5) -> str:
        """获取主题摘要用于提示词"""
        if not self.topic_summaries:
            return ""

        # 按更新时间排序，取最新的
        recent_summaries = sorted(
            self.topic_summaries,
            key=lambda s: s.last_updated,
            reverse=True
        )[:limit]

        formatted = ["相关历史主题摘要："]
        for i, summary in enumerate(recent_summaries, 1):
            formatted.append(f"{i}. {summary.format_for_prompt()}")

        return "\n\n".join(formatted)

    def get_recent_dialogues_for_prompt(self, limit: int = 5) -> str:
        """获取最近对话用于提示词"""
        dialogues = self.get_short_term_memories(limit=limit)
        if not dialogues:
            return ""

        formatted = ["最近对话："]
        for dialogue in dialogues:
            role_str = {
                DialogueRole.USER: "用户",
                DialogueRole.ASSISTANT: "助手",
                DialogueRole.TOOL_RESULT: "工具结果"
            }.get(dialogue.role, "未知")

            content_preview = str(dialogue.content)[:100]
            formatted.append(f"- {role_str}: {content_preview}...")

        return "\n".join(formatted)

    def clear_session_memories(self):
        """清空会话记忆（保留 Qdrant 中的长记忆）"""
        self.pending_dialogues.clear()
        self.topic_summaries.clear()
        self.current_topic = None
        logger.info(f"清空会话记忆，会话: {self.session_id}")

    async def _compress_memories(self):
        """压缩相似记忆"""
        if len(self.topic_summaries) < 2:
            return
        
        logger.debug(f"开始压缩记忆，当前摘要数量: {len(self.topic_summaries)}")
        
        # 计算主题摘要之间的相似度
        summary_pairs = []
        for i, s1 in enumerate(self.topic_summaries):
            for j, s2 in enumerate(self.topic_summaries[i+1:], i+1):
                try:
                    # 批量生成向量
                    vectors = self.embedder.embed_batch([s1.summary_text, s2.summary_text])
                    if len(vectors) == 2:
                        sim = self.embedder.similarity(vectors[0], vectors[1])
                        if sim > 0.7:  # 相似度高于0.7认为是同一主题
                            summary_pairs.append((i, j, sim))
                except Exception as e:
                    logger.error(f"计算摘要相似度失败: {e}")
        
        # 合并相似主题
        merged_count = 0
        for i, j, sim in sorted(summary_pairs, key=lambda x: x[2], reverse=True):
            if i < len(self.topic_summaries) and j < len(self.topic_summaries):
                # 合并两个主题
                s1 = self.topic_summaries[i]
                s2 = self.topic_summaries[j]
                
                # 创建合并后的主题
                merged_summary = TopicSummary(
                    topic_id=f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    topic_name=s1.topic_name,  # 使用第一个主题的名称
                    timestamp=min(s1.timestamp, s2.timestamp),
                    last_updated=datetime.now(),
                    summary_text=f"{s1.summary_text} | {s2.summary_text}",
                    key_points=s1.key_points + s2.key_points,
                    related_tools=list(set(s1.related_tools + s2.related_tools)),
                    dialogue_count=s1.dialogue_count + s2.dialogue_count
                )
                
                # 替换原主题
                self.topic_summaries[i] = merged_summary
                del self.topic_summaries[j]
                
                merged_count += 1
                logger.info(f"合并相似主题: {s1.topic_name} (相似度: {sim:.3f})")
        
        if merged_count > 0:
            logger.info(f"压缩完成，合并了 {merged_count} 个相似主题")
        else:
            logger.debug("无相似主题需要合并")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "session_id": self.session_id,
            "pending_dialogues": len(self.pending_dialogues),
            "topic_summaries": len(self.topic_summaries),
            "current_topic": self.current_topic,
            "qdrant_info": self.qdrant_client.get_collection_info() if self.qdrant_client else {"status": "unavailable"},
            "session_duration": (datetime.now() - self.session_start_time).total_seconds() / 3600
        }