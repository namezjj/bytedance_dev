"""
LangChain 对话模型自动化评估Agent系统

核心评估Agent类，负责协调整个评估流程
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms.base import BaseLLM

from .evaluators.base_evaluator import BaseEvaluator
from .metrics.base_metrics import EvaluationMetrics
from ..data.database import EvaluationDatabase
from ..config.evaluation_config import EvaluationConfig

logger = logging.getLogger(__name__)

class EvaluationMode(Enum):
    """评估模式枚举"""
    SINGLE = "single"          # 单次评估
    BATCH = "batch"           # 批量评估
    COMPARATIVE = "comparative"  # 对比评估

@dataclass
class EvaluationInput:
    """评估输入数据结构"""
    question: str
    ground_truth: Optional[str] = None
    context: Optional[str] = None
    conversation_history: Optional[List[BaseMessage]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EvaluationResult:
    """单次评估结果"""
    input_data: EvaluationInput
    model_response: str
    overall_score: float
    dimension_scores: Dict[str, float]
    detailed_feedback: Dict[str, str]
    evaluation_timestamp: datetime
    metadata: Dict[str, Any]

class EvaluationAgent:
    """
    对话模型自动化评估Agent

    主要功能：
    1. 协调多维度评估器进行评估
    2. 管理评估流程和状态
    3. 生成综合评估报告
    4. 提供参数优化建议
    """

    def __init__(
        self,
        llm: BaseLLM,
        config: EvaluationConfig,
        database: Optional[EvaluationDatabase] = None
    ):
        """
        初始化评估Agent

        Args:
            llm: 用于评估的语言模型
            config: 评估配置
            database: 数据库连接（可选）
        """
        self.llm = llm
        self.config = config
        self.database = database or EvaluationDatabase()
        self.evaluators: Dict[str, BaseEvaluator] = {}
        self._initialize_evaluators()

    def _initialize_evaluators(self):
        """初始化所有评估器"""
        from .evaluators.accuracy_evaluator import AccuracyEvaluator
        from .evaluators.relevance_evaluator import RelevanceEvaluator
        from .evaluators.completeness_evaluator import CompletenessEvaluator
        from .evaluators.fluency_evaluator import FluencyEvaluator

        # 根据配置启用相应的评估器
        if self.config.enable_accuracy:
            self.evaluators['accuracy'] = AccuracyEvaluator(self.llm, self.config)
        if self.config.enable_relevance:
            self.evaluators['relevance'] = RelevanceEvaluator(self.llm, self.config)
        if self.config.enable_completeness:
            self.evaluators['completeness'] = CompletenessEvaluator(self.llm, self.config)
        if self.config.enable_fluency:
            self.evaluators['fluency'] = FluencyEvaluator(self.llm, self.config)

        logger.info(f"已初始化 {len(self.evaluators)} 个评估器: {list(self.evaluators.keys())}")

    async def evaluate_single(
        self,
        evaluation_input: EvaluationInput,
        model_response: str
    ) -> EvaluationResult:
        """
        执行单次评估

        Args:
            evaluation_input: 评估输入
            model_response: 模型回答

        Returns:
            评估结果
        """
        logger.info(f"开始单次评估: {evaluation_input.question[:50]}...")

        dimension_scores = {}
        detailed_feedback = {}

        # 并行执行所有评估器
        import asyncio
        tasks = []
        for name, evaluator in self.evaluators.items():
            task = asyncio.create_task(
                evaluator.evaluate(evaluation_input, model_response)
            )
            tasks.append((name, task))

        # 收集评估结果
        for name, task in tasks:
            try:
                score, feedback = await task
                dimension_scores[name] = score
                detailed_feedback[name] = feedback
                logger.info(f"评估器 {name} 完成，得分: {score:.3f}")
            except Exception as e:
                logger.error(f"评估器 {name} 执行失败: {e}")
                dimension_scores[name] = 0.0
                detailed_feedback[name] = f"评估失败: {str(e)}"

        # 计算综合得分
        overall_score = self._calculate_overall_score(dimension_scores)

        # 创建评估结果
        result = EvaluationResult(
            input_data=evaluation_input,
            model_response=model_response,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            detailed_feedback=detailed_feedback,
            evaluation_timestamp=datetime.now(),
            metadata={
                'evaluator_count': len(self.evaluators),
                'config_version': self.config.version
            }
        )

        # 保存到数据库
        if self.database:
            await self.database.save_evaluation_result(result)

        logger.info(f"单次评估完成，综合得分: {overall_score:.3f}")
        return result

    async def evaluate_batch(
        self,
        evaluation_inputs: List[EvaluationInput],
        model_responses: List[str]
    ) -> List[EvaluationResult]:
        """
        执行批量评估

        Args:
            evaluation_inputs: 评估输入列表
            model_responses: 模型回答列表

        Returns:
            评估结果列表
        """
        if len(evaluation_inputs) != len(model_responses):
            raise ValueError("输入和回答数量不匹配")

        logger.info(f"开始批量评估，共 {len(evaluation_inputs)} 个样本")

        results = []
        for i, (eval_input, response) in enumerate(zip(evaluation_inputs, model_responses)):
            result = await self.evaluate_single(eval_input, response)
            results.append(result)

            if (i + 1) % 10 == 0:
                logger.info(f"已完成 {i + 1}/{len(evaluation_inputs)} 个评估")

        logger.info(f"批量评估完成，平均得分: {sum(r.overall_score for r in results)/len(results):.3f}")
        return results

    async def evaluate_comparative(
        self,
        evaluation_input: EvaluationInput,
        model_responses: Dict[str, str],
        model_names: Optional[List[str]] = None
    ) -> Dict[str, EvaluationResult]:
        """
        执行对比评估

        Args:
            evaluation_input: 评估输入
            model_responses: 多个模型的回答字典
            model_names: 模型名称列表

        Returns:
            各模型的评估结果字典
        """
        logger.info(f"开始对比评估，共 {len(model_responses)} 个模型")

        results = {}
        for model_id, response in model_responses.items():
            model_name = model_names[model_responses.index(response)] if model_names else model_id
            result = await self.evaluate_single(evaluation_input, response)
            result.metadata['model_name'] = model_name
            results[model_id] = result

        # 生成对比报告
        comparison_report = self._generate_comparison_report(results)
        logger.info("对比评估完成")

        return results

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        计算综合得分

        Args:
            dimension_scores: 各维度得分

        Returns:
            综合得分
        """
        if not dimension_scores:
            return 0.0

        # 使用配置中的权重
        weights = {
            'accuracy': self.config.accuracy_weight,
            'relevance': self.config.relevance_weight,
            'completeness': self.config.completeness_weight,
            'fluency': self.config.fluency_weight
        }

        weighted_sum = 0.0
        weight_sum = 0.0

        for dimension, score in dimension_scores.items():
            weight = weights.get(dimension, 1.0)
            weighted_sum += score * weight
            weight_sum += weight

        return weighted_sum / weight_sum if weight_sum > 0 else 0.0

    def _generate_comparison_report(self, results: Dict[str, EvaluationResult]) -> str:
        """
        生成对比评估报告

        Args:
            results: 各模型评估结果

        Returns:
            对比报告文本
        """
        report_lines = ["=== 模型对比评估报告 ===\n"]

        # 按综合得分排序
        sorted_results = sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True)

        for i, (model_id, result) in enumerate(sorted_results, 1):
            model_name = result.metadata.get('model_name', model_id)
            report_lines.append(f"{i}. {model_name}")
            report_lines.append(f"   综合得分: {result.overall_score:.3f}")

            for dimension, score in result.dimension_scores.items():
                report_lines.append(f"   {dimension}: {score:.3f}")
            report_lines.append("")

        return "\n".join(report_lines)

    def get_evaluation_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        获取评估摘要统计

        Args:
            results: 评估结果列表

        Returns:
            摘要统计信息
        """
        if not results:
            return {}

        summary = {
            'total_evaluations': len(results),
            'average_overall_score': sum(r.overall_score for r in results) / len(results),
            'dimension_statistics': {},
            'score_distribution': {},
            'evaluation_time_range': {
                'start': min(r.evaluation_timestamp for r in results),
                'end': max(r.evaluation_timestamp for r in results)
            }
        }

        # 计算各维度统计
        all_dimensions = set()
        for result in results:
            all_dimensions.update(result.dimension_scores.keys())

        for dimension in all_dimensions:
            scores = [r.dimension_scores.get(dimension, 0.0) for r in results]
            summary['dimension_statistics'][dimension] = {
                'average': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'std': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))**0.5
            }

        return summary