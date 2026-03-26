"""
AI回复引擎模块

集成XianyuAutoAgent的AI回复功能到现有项目中
"""

import json
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Any, Tuple

from loguru import logger
from openai import OpenAI

from app.repositories import db_manager
from app.core.constants import (
    INTENT_DETECTION_MAX_TOKENS,
    INTENT_DETECTION_TEMPERATURE,
    AI_REPLY_MAX_TOKENS,
    AI_REPLY_TEMPERATURE,
    CONVERSATION_CONTEXT_LIMIT,
    CONVERSATION_HISTORY_DISPLAY_COUNT,
    INTENT_PRICE,
    INTENT_DEFAULT,
    INTENT_TYPES,
    DEFAULT_MAX_BARGAIN_ROUNDS,
    DEFAULT_MAX_DISCOUNT_PERCENT,
    DEFAULT_MAX_DISCOUNT_AMOUNT,
)


class AIReplyEngine:
    """AI回复引擎

    提供智能回复功能，包括意图检测和多轮议价处理。

    Attributes:
        clients: 存储不同账号的OpenAI客户端（LRU缓存）
        client_timestamps: 记录客户端最后使用时间
        agents: 存储不同账号的Agent实例
        default_prompts: 默认提示词模板
        max_clients: 最大客户端缓存数量
        client_expire_hours: 客户端过期时间（小时）
        cache_hits: 缓存命中次数
        cache_misses: 缓存未命中次数
        cleanup_count: 清理次数
    """

    def __init__(
        self,
        max_clients: int = 100,
        client_expire_hours: int = 24
    ) -> None:
        """初始化AI回复引擎

        Args:
            max_clients: 最大客户端缓存数量，默认100
            client_expire_hours: 客户端过期时间（小时），默认24小时
        """
        self.clients: OrderedDict[str, OpenAI] = OrderedDict()
        self.client_timestamps: Dict[str, float] = {}
        self.agents: Dict[str, Any] = {}
        self.default_prompts: Dict[str, str] = {}
        
        # 缓存配置
        self.max_clients = max_clients
        self.client_expire_hours = client_expire_hours
        
        # 缓存统计
        self.cache_hits = 0
        self.cache_misses = 0
        self.cleanup_count = 0
        
        self._init_default_prompts()

    def _init_default_prompts(self) -> None:
        """初始化默认提示词模板"""
        classify_template = (
            "你是一个意图分类专家，需要判断用户消息的意图类型。"
            "请根据用户消息内容，返回以下意图之一："
            "- price: 价格相关（议价、优惠、降价等）"
            "- tech: 技术相关（产品参数、使用方法、故障等）"
            "- default: 其他一般咨询"
            "只返回意图类型，不要其他内容。"
        )
        price_template = (
            "你是一位经验丰富的销售专家，擅长议价。"
            "语言要求：简短直接，每句10字以内，总字数40字以内。"
            "议价策略："
            "1. 根据议价次数递减优惠：第1次小幅优惠，第2次中等优惠，第3次最大优惠"
            "2. 接近最大议价轮数时要坚持底线，强调商品价值"
            "3. 优惠不能超过设定的最大百分比和金额"
            "4. 语气要友好但坚定，突出商品优势"
            "注意：结合商品信息、对话历史和议价设置，给出合适的回复。"
        )
        tech_template = (
            "你是一位技术专家，专业解答产品相关问题。"
            "语言要求：简短专业，每句10字以内，总字数40字以内。"
            "回答重点：产品功能、使用方法、注意事项。"
            "注意：基于商品信息回答，避免过度承诺。"
        )
        default_template = (
            "你是一位资深电商卖家，提供优质客服。"
            "语言要求：简短友好，每句10字以内，总字数40字以内。"
            "回答重点：商品介绍、物流、售后等常见问题。"
            "注意：结合商品信息，给出实用建议。"
        )
        self.default_prompts = {
            "classify": classify_template,
            "price": price_template,
            "tech": tech_template,
            "default": default_template,
        }

    def get_client(self, cookie_id: str) -> Optional[OpenAI]:
        """获取指定账号的OpenAI客户端

        使用LRU缓存策略，当缓存满时移除最久未使用的客户端。

        Args:
            cookie_id: 账号ID

        Returns:
            OpenAI客户端实例，如果未启用AI或无API Key则返回None
        """
        # 检查缓存中是否存在
        if cookie_id in self.clients:
            # 缓存命中，移动到末尾（表示最近使用）
            self.clients.move_to_end(cookie_id)
            self.client_timestamps[cookie_id] = time.time()
            self.cache_hits += 1
            logger.debug(f"缓存命中: {cookie_id}, 缓存大小: {len(self.clients)}")
            return self.clients[cookie_id]
        
        # 缓存未命中
        self.cache_misses += 1
        
        # 获取AI设置
        settings = db_manager.get_ai_reply_settings(cookie_id)
        if not settings["ai_enabled"] or not settings["api_key"]:
            return None

        try:
            # 检查缓存是否已满
            if len(self.clients) >= self.max_clients:
                # 移除最久未使用的客户端（字典第一个元素）
                oldest_key = next(iter(self.clients))
                del self.clients[oldest_key]
                del self.client_timestamps[oldest_key]
                logger.info(f"缓存已满，移除最久未使用的客户端: {oldest_key}")
            
            # 创建新客户端
            client = OpenAI(
                api_key=settings["api_key"],
                base_url=settings["base_url"]
            )
            self.clients[cookie_id] = client
            self.client_timestamps[cookie_id] = time.time()
            
            logger.info(
                f"为账号 {cookie_id} 创建OpenAI客户端, "
                f"缓存大小: {len(self.clients)}/{self.max_clients}"
            )
            return client
            
        except Exception as e:
            logger.error(f"创建OpenAI客户端失败 {cookie_id}: {e}")
            return None

    def is_ai_enabled(self, cookie_id: str) -> bool:
        """检查指定账号是否启用AI回复

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 是否启用AI回复
        """
        settings = db_manager.get_ai_reply_settings(cookie_id)
        return settings["ai_enabled"]

    def detect_intent(self, message: str, cookie_id: str) -> str:
        """检测用户消息意图

        使用AI模型分析消息内容，判断用户意图类型。

        Args:
            message: 用户发送的消息内容
            cookie_id: 账号ID

        Returns:
            str: 意图类型 (price/tech/default)
        """
        client = self.get_client(cookie_id)
        if not client:
            return INTENT_DEFAULT

        try:
            settings = db_manager.get_ai_reply_settings(cookie_id)
            custom_prompts = json.loads(settings["custom_prompts"]) if settings["custom_prompts"] else {}
            classify_prompt = custom_prompts.get("classify", self.default_prompts["classify"])

            response = client.chat.completions.create(
                model=settings["model_name"],
                messages=[
                    {"role": "system", "content": classify_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=INTENT_DETECTION_MAX_TOKENS,
                temperature=INTENT_DETECTION_TEMPERATURE
            )

            intent = response.choices[0].message.content.strip().lower()
            if intent in INTENT_TYPES:
                return intent
            else:
                return INTENT_DEFAULT

        except Exception as e:
            logger.error(f"意图检测失败 {cookie_id}: {e}")
            return INTENT_DEFAULT

    def generate_reply(
        self,
        message: str,
        item_info: Dict[str, Any],
        chat_id: str,
        cookie_id: str,
        user_id: str,
        item_id: str
    ) -> Optional[str]:
        """生成AI回复

        根据消息内容、商品信息和对话上下文生成智能回复。
        如果是议价意图，会检查议价轮数限制。

        Args:
            message: 用户发送的消息内容
            item_info: 商品信息字典，包含title/price/desc等字段
            chat_id: 对话ID
            cookie_id: 账号ID
            user_id: 用户ID
            item_id: 商品ID

        Returns:
            str: 生成的回复内容，如果未启用AI或生成失败则返回None
        """
        if not self.is_ai_enabled(cookie_id):
            return None

        client = self.get_client(cookie_id)
        if not client:
            return None

        try:
            # 1. 获取AI回复设置
            settings = db_manager.get_ai_reply_settings(cookie_id)

            # 2. 检测意图
            intent = self.detect_intent(message, cookie_id)
            logger.info(f"检测到意图: {intent} (账号: {cookie_id})")

            # 3. 获取对话历史
            context = self.get_conversation_context(chat_id, cookie_id)

            # 4. 获取议价次数
            bargain_count = self.get_bargain_count(chat_id, cookie_id)

            # 5. 检查议价轮数限制
            if intent == INTENT_PRICE:
                max_bargain_rounds = settings.get("max_bargain_rounds", DEFAULT_MAX_BARGAIN_ROUNDS)
                if bargain_count >= max_bargain_rounds:
                    logger.info(f"议价次数已达上限 ({bargain_count}/{max_bargain_rounds})，拒绝继续议价")
                    # 返回拒绝议价的回复
                    refuse_reply = "抱歉，这个价格已经是最优惠的了，不能再便宜了哦！"
                    # 保存对话记录
                    self.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
                    self.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", refuse_reply, intent)
                    return refuse_reply

            # 6. 构建提示词
            custom_prompts = json.loads(settings["custom_prompts"]) if settings["custom_prompts"] else {}
            system_prompt = custom_prompts.get(intent, self.default_prompts[intent])

            # 7. 构建商品信息
            item_title = item_info.get("title", "未知")
            item_price = item_info.get("price", "未知")
            item_desc = item_info.get("desc", "无")
            item_desc = f"商品标题: {item_title}\n商品价格: {item_price}元\n商品描述: {item_desc}"

            # 8. 构建对话历史
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context[-CONVERSATION_HISTORY_DISPLAY_COUNT:]
            ])

            # 9. 构建用户消息
            max_bargain_rounds = settings.get("max_bargain_rounds", DEFAULT_MAX_BARGAIN_ROUNDS)
            max_discount_percent = settings.get("max_discount_percent", DEFAULT_MAX_DISCOUNT_PERCENT)
            max_discount_amount = settings.get("max_discount_amount", DEFAULT_MAX_DISCOUNT_AMOUNT)

            user_prompt = (
                f"商品信息：\n{item_desc}\n\n"
                f"对话历史：\n{context_str}\n\n"
                f"议价设置：\n"
                f"- 当前议价次数：{bargain_count}\n"
                f"- 最大议价轮数：{max_bargain_rounds}\n"
                f"- 最大优惠百分比：{max_discount_percent}%\n"
                f"- 最大优惠金额：{max_discount_amount}元\n\n"
                f"用户消息：{message}\n\n"
                f"请根据以上信息生成回复："
            )

            # 10. 调用AI生成回复
            response = client.chat.completions.create(
                model=settings["model_name"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=AI_REPLY_MAX_TOKENS,
                temperature=AI_REPLY_TEMPERATURE
            )

            reply = response.choices[0].message.content.strip()

            # 11. 保存对话记录
            self.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
            self.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", reply, intent)

            # 12. 更新议价次数
            if intent == INTENT_PRICE:
                self.increment_bargain_count(chat_id, cookie_id)

            logger.info(f"AI回复生成成功 (账号: {cookie_id}): {reply}")
            return reply

        except Exception as e:
            logger.error(f"AI回复生成失败 {cookie_id}: {e}")
            return None

    def get_conversation_context(
        self,
        chat_id: str,
        cookie_id: str,
        limit: int = CONVERSATION_CONTEXT_LIMIT
    ) -> List[Dict[str, Any]]:
        """获取对话上下文

        从数据库获取指定对话的历史消息记录。

        Args:
            chat_id: 对话ID
            cookie_id: 账号ID
            limit: 最大返回消息条数

        Returns:
            List[Dict]: 消息列表，每条消息包含role和content字段
        """
        return db_manager.get_ai_conversation_context(chat_id, cookie_id, limit)

    def save_conversation(
        self,
        chat_id: str,
        cookie_id: str,
        user_id: str,
        item_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None
    ) -> None:
        """保存对话记录

        将用户或助手的回复保存到数据库。

        Args:
            chat_id: 对话ID
            cookie_id: 账号ID
            user_id: 用户ID
            item_id: 商品ID
            role: 角色 (user/assistant)
            content: 消息内容
            intent: 意图类型
        """
        return db_manager.save_ai_conversation(
            chat_id, cookie_id, user_id, item_id, role, content, intent
        )

    def get_bargain_count(self, chat_id: str, cookie_id: str) -> int:
        """获取议价次数

        获取指定对话中用户发起议价的次数。

        Args:
            chat_id: 对话ID
            cookie_id: 账号ID

        Returns:
            int: 议价次数
        """
        return db_manager.get_ai_bargain_count(chat_id, cookie_id)

    def increment_bargain_count(self, chat_id: str, cookie_id: str) -> None:
        """增加议价次数

        议价次数通过查询price意图的用户消息数量来计算，无需单独操作。

        Args:
            chat_id: 对话ID
            cookie_id: 账号ID
        """
        pass

    def clear_client_cache(self, cookie_id: Optional[str] = None) -> None:
        """清理客户端缓存

        清除指定账号或所有账号的OpenAI客户端缓存。

        Args:
            cookie_id: 账号ID，如果为None则清除所有缓存
        """
        if cookie_id:
            if cookie_id in self.clients:
                del self.clients[cookie_id]
                del self.client_timestamps[cookie_id]
                logger.info(f"清理账号 {cookie_id} 的客户端缓存")
        else:
            self.clients.clear()
            self.client_timestamps.clear()
            logger.info("清理所有客户端缓存")

    def cleanup_expired_clients(self) -> int:
        """清理过期客户端

        清理超过指定时间未使用的客户端。

        Returns:
            int: 清理的客户端数量
        """
        current_time = time.time()
        expire_seconds = self.client_expire_hours * 3600
        expired_keys = []
        
        # 找出所有过期的客户端
        for cookie_id, last_used in self.client_timestamps.items():
            if current_time - last_used > expire_seconds:
                expired_keys.append(cookie_id)
        
        # 删除过期客户端
        for cookie_id in expired_keys:
            del self.clients[cookie_id]
            del self.client_timestamps[cookie_id]
        
        if expired_keys:
            self.cleanup_count += 1
            logger.info(
                f"清理过期客户端: {len(expired_keys)} 个, "
                f"剩余缓存大小: {len(self.clients)}"
            )
        
        return len(expired_keys)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            Dict: 包含缓存命中率、大小、清理次数等统计信息
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "cache_size": len(self.clients),
            "max_cache_size": self.max_clients,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "cleanup_count": self.cleanup_count,
            "client_expire_hours": self.client_expire_hours,
        }

    def reset_cache_stats(self) -> None:
        """重置缓存统计信息"""
        self.cache_hits = 0
        self.cache_misses = 0
        self.cleanup_count = 0
        logger.info("缓存统计信息已重置")


# 全局AI回复引擎实例
ai_reply_engine = AIReplyEngine()
