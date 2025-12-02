"""
基础评估器抽象类

定义所有评估器的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import logging

from ...core.evaluation_agent import EvaluationInput

logger = logging.getLogger(__name__)

class BaseEvaluator(ABC):
    """
    基础评估器抽象类

    所有具体的评估器都应该继承此类并实现evaluate方法
    """

    def __init__(self, llm, config):
        """
        初始化评估器

        Args:
            llm: 用于评估的语言模型
            config: 评估配置
        """
        self.llm = llm
        self.config = config
        self.name = self.__class__.__name__.replace('Evaluator', '').lower()
        self.evaluation_prompt = self._get_evaluation_prompt()

    @abstractmethod
    def _get_evaluation_prompt(self) -> str:
        """
        获取评估提示词模板

        子类必须实现此方法来定义具体的评估提示词

        Returns:
            评估提示词模板字符串
        """
        pass

    @abstractmethod
    def _parse_evaluation_result(self, llm_response: str) -> Tuple[float, str]:
        """
        解析LLM的评估结果

        子类必须实现此方法来解析具体的评估格式

        Args:
            llm_response: LLM的原始响应

        Returns:
            (分数, 详细反馈) 的元组
        """
        pass

    @abstractmethod
    def get_dimension_name(self) -> str:
        """
        获取评估维度名称

        Returns:
            维度名称字符串
        """
        pass

    @abstractmethod
    def get_dimension_description(self) -> str:
        """
        获取评估维度描述

        Returns:
            维度描述字符串
        """
        pass

    async def evaluate(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> Tuple[float, str]:
        """
        执行评估

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            (分数, 详细反馈) 的元组，分数范围为0-1
        """
        try:
            # 构建评估提示词
            prompt = self._build_evaluation_prompt(evaluation_input, model_response)

            # 调用LLM进行评估
            llm_response = await self._call_llm(prompt)

            # 解析评估结果
            score, feedback = self._parse_evaluation_result(llm_response)

            # 验证分数范围
            score = max(0.0, min(1.0, score))

            logger.debug(f"{self.name} 评估完成: 分数={score:.3f}, 反馈长度={len(feedback)}")
            return score, feedback

        except Exception as e:
            logger.error(f"{self.name} 评估失败: {e}")
            return 0.0, f"评估失败: {str(e)}"

    def _build_evaluation_prompt(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> str:
        """
        构建完整的评估提示词

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            完整的评估提示词
        """
        context_info = ""
        if evaluation_input.context:
            context_info = f"\n上下文信息:\n{evaluation_input.context}"

        history_info = ""
        if evaluation_input.conversation_history:
            history_info = "\n对话历史:\n"
            for msg in evaluation_input.conversation_history[-5:]:  # 只使用最近5轮对话
                if isinstance(msg, type( evaluation_input.conversation_history[0] )):
                    if hasattr(msg, 'content'):
                        history_info += f"{msg.__class__.__name__}: {msg.content}\n"

        ground_truth_info = ""
        if evaluation_input.ground_truth:
            ground_truth_info = f"\n参考答案:\n{evaluation_input.ground_truth}"

        prompt = self.evaluation_prompt.format(
            question=evaluation_input.question,
            context=context_info,
            conversation_history=history_info,
            ground_truth=ground_truth_info,
            model_response=model_response,
            dimension_name=self.get_dimension_name(),
            dimension_description=self.get_dimension_description()
        )

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """
        调用语言模型

        Args:
            prompt: 输入提示词

        Returns:
            LLM响应
        """
        try:
            # 使用异步调用
            if hasattr(self.llm, 'acall'):
                response = await self.llm.acall(prompt)
            else:
                # 如果不支持异步，使用同步调用
                response = self.llm(prompt)

            # 提取响应内容
            if isinstance(response, dict):
                return response.get('text', '') or response.get('content', '')
            return str(response)

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def validate_input(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> bool:
        """
        验证输入数据的有效性

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            是否有效
        """
        if not evaluation_input.question or not evaluation_input.question.strip():
            logger.warning("问题为空")
            return False

        if not model_response or not model_response.strip():
            logger.warning("模型回答为空")
            return False

        return True

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        获取评估标准说明

        Returns:
            评估标准字典
        """
        return {
            'name': self.get_dimension_name(),
            'description': self.get_dimension_description(),
            'score_range': '0-1',
            'score_interpretation': {
                '0.0-0.2': '很差',
                '0.2-0.4': '较差',
                '0.4-0.6': '一般',
                '0.6-0.8': '良好',
                '0.8-1.0': '优秀'
            }
        }

class RuleBasedEvaluator(BaseEvaluator):
    """
    基于规则的评估器基类

    提供基于预定义规则的评估功能，不依赖LLM
    """

    def __init__(self, config):
        """
        初始化基于规则的评估器

        Args:
            config: 评估配置
        """
        self.config = config
        self.name = self.__class__.__name__.replace('Evaluator', '').lower()

    async def evaluate(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> Tuple[float, str]:
        """
        执行基于规则的评估

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            (分数, 详细反馈) 的元组
        """
        try:
            if not self.validate_input(evaluation_input, model_response):
                return 0.0, "输入数据无效"

            # 调用子类实现的具体评估逻辑
            score, feedback = await self._evaluate_by_rules(evaluation_input, model_response)

            # 验证分数范围
            score = max(0.0, min(1.0, score))

            logger.debug(f"规则评估器 {self.name} 完成: 分数={score:.3f}")
            return score, feedback

        except Exception as e:
            logger.error(f"规则评估器 {self.name} 失败: {e}")
            return 0.0, f"评估失败: {str(e)}"

    @abstractmethod
    async def _evaluate_by_rules(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> Tuple[float, str]:
        """
        基于规则的具体评估逻辑

        子类必须实现此方法

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            (分数, 详细反馈) 的元组
        """
        pass

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0-1)
        """
        # 简单的词汇重叠计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_length_penalty(self, response: str, target_length: Optional[int] = None) -> float:
        """
        计算长度惩罚分数

        Args:
            response: 回答文本
            target_length: 目标长度（可选）

        Returns:
            惩罚分数 (0-1, 1表示无惩罚)
        """
        if not target_length:
            # 如果没有目标长度，基于常见长度范围进行评估
            length = len(response.split())
            if length < 10:
                return 0.5  # 太短
            elif length > 500:
                return 0.7  # 太长
            else:
                return 1.0  # 合适长度

        ratio = len(response) / target_length
        if 0.8 <= ratio <= 1.2:
            return 1.0  # 长度合适
        elif ratio < 0.5:
            return 0.3  # 太短
        elif ratio > 2.0:
            return 0.3  # 太长
        else:
            return 0.7  # 长度不太合适