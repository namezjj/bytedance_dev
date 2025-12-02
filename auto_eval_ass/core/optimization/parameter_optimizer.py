"""
参数优化器

基于评估结果自动优化模型参数和系统配置
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from datetime import datetime
import json
from enum import Enum
import asyncio

from sklearn.model_selection import ParameterGrid
from scipy.optimize import minimize
import optuna

from ..evaluation_agent import EvaluationResult, EvaluationInput
from ...data.database import EvaluationDatabase, QueryFilter
from ...data.models import ModelConfiguration, OptimizationResult

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """优化策略枚举"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    GRADIENT = "gradient"

@dataclass
class ParameterSpace:
    """参数空间定义"""
    name: str
    param_type: str  # 'categorical', 'continuous', 'integer', 'boolean'
    low: Optional[Union[float, int]] = None
    high: Optional[Union[float, int]] = None
    choices: Optional[List[Any]] = None
    default: Any = None

    def sample(self) -> Any:
        """从参数空间中采样"""
        if self.param_type == 'categorical':
            return np.random.choice(self.choices) if self.choices else self.default
        elif self.param_type == 'continuous':
            return np.random.uniform(self.low, self.high) if self.low is not None and self.high is not None else self.default
        elif self.param_type == 'integer':
            return np.random.randint(self.low, self.high + 1) if self.low is not None and self.high is not None else self.default
        elif self.param_type == 'boolean':
            return np.random.choice([True, False])
        else:
            return self.default

class ParameterOptimizer:
    """
    参数优化器

    基于历史评估结果自动优化模型参数，支持多种优化策略
    """

    def __init__(
        self,
        database: EvaluationDatabase,
        evaluation_function,
        strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN,
        max_trials: int = 100
    ):
        """
        初始化参数优化器

        Args:
            database: 评估数据库
            evaluation_function: 评估函数，接受参数配置返回评估结果
            strategy: 优化策略
            max_trials: 最大试验次数
        """
        self.database = database
        self.evaluation_function = evaluation_function
        self.strategy = strategy
        self.max_trials = max_trials
        self.optimization_history: List[OptimizationResult] = []
        self.parameter_spaces: Dict[str, ParameterSpace] = {}
        self._initialize_parameter_spaces()

    def _initialize_parameter_spaces(self):
        """初始化常用参数空间"""
        self.parameter_spaces = {
            # LLM通用参数
            'temperature': ParameterSpace(
                name='temperature',
                param_type='continuous',
                low=0.0,
                high=2.0,
                default=0.7
            ),
            'max_tokens': ParameterSpace(
                name='max_tokens',
                param_type='integer',
                low=100,
                high=4000,
                default=2000
            ),
            'top_p': ParameterSpace(
                name='top_p',
                param_type='continuous',
                low=0.1,
                high=1.0,
                default=0.9
            ),
            'frequency_penalty': ParameterSpace(
                name='frequency_penalty',
                param_type='continuous',
                low=-2.0,
                high=2.0,
                default=0.0
            ),
            'presence_penalty': ParameterSpace(
                name='presence_penalty',
                param_type='continuous',
                low=-2.0,
                high=2.0,
                default=0.0
            ),

            # RAG系统参数
            'retrieval_top_k': ParameterSpace(
                name='retrieval_top_k',
                param_type='integer',
                low=1,
                high=20,
                default=5
            ),
            'embedding_model': ParameterSpace(
                name='embedding_model',
                param_type='categorical',
                choices=['text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large'],
                default='text-embedding-ada-002'
            ),
            'similarity_threshold': ParameterSpace(
                name='similarity_threshold',
                param_type='continuous',
                low=0.1,
                high=0.9,
                default=0.7
            ),

            # 提示词参数
            'context_length': ParameterSpace(
                name='context_length',
                param_type='integer',
                low=500,
                high=8000,
                default=2000
            ),
            'instruction_template': ParameterSpace(
                name='instruction_template',
                param_type='categorical',
                choices=['standard', 'cot', 'react', 'custom'],
                default='standard'
            )
        }

    async def optimize_parameters(
        self,
        model_name: str,
        param_names: List[str],
        evaluation_dataset: List[EvaluationInput],
        target_metric: str = 'overall_score',
        baseline_score: Optional[float] = None
    ) -> OptimizationResult:
        """
        优化模型参数

        Args:
            model_name: 模型名称
            param_names: 要优化的参数名称列表
            evaluation_dataset: 评估数据集
            target_metric: 目标指标
            baseline_score: 基准分数（可选）

        Returns:
            优化结果
        """
        try:
            logger.info(f"开始优化 {model_name} 的参数: {param_names}")

            # 获取基准配置
            baseline_config = await self._get_baseline_config(model_name)
            if baseline_score is None:
                baseline_score = await self._evaluate_baseline(baseline_config, evaluation_dataset)

            # 选择优化策略
            if self.strategy == OptimizationStrategy.GRID_SEARCH:
                best_config, best_score = await self._grid_search_optimization(
                    param_names, evaluation_dataset, target_metric
                )
            elif self.strategy == OptimizationStrategy.RANDOM_SEARCH:
                best_config, best_score = await self._random_search_optimization(
                    param_names, evaluation_dataset, target_metric
                )
            elif self.strategy == OptimizationStrategy.BAYESIAN:
                best_config, best_score = await self._bayesian_optimization(
                    param_names, evaluation_dataset, target_metric
                )
            else:
                raise ValueError(f"不支持的优化策略: {self.strategy}")

            # 计算改进幅度
            improvement = best_score - baseline_score

            # 记录参数变化
            parameter_changes = {}
            for param_name in param_names:
                if param_name in baseline_config and param_name in best_config:
                    parameter_changes[param_name] = {
                        'from': baseline_config[param_name],
                        'to': best_config[param_name],
                        'change_type': self._classify_change_type(
                            baseline_config[param_name],
                            best_config[param_name]
                        )
                    }

            # 创建优化结果
            optimization_result = OptimizationResult(
                original_score=baseline_score,
                optimized_score=best_score,
                improvement=improvement,
                parameter_changes=parameter_changes,
                metadata={
                    'model_name': model_name,
                    'optimized_parameters': param_names,
                    'strategy': self.strategy.value,
                    'trials': len(self.optimization_history) + 1,
                    'dataset_size': len(evaluation_dataset),
                    'target_metric': target_metric
                }
            )

            # 保存优化结果
            await self._save_optimization_result(optimization_result)
            self.optimization_history.append(optimization_result)

            logger.info(f"参数优化完成: {improvement:+.3f} ({baseline_score:.3f} -> {best_score:.3f})")
            return optimization_result

        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            raise

    async def _grid_search_optimization(
        self,
        param_names: List[str],
        evaluation_dataset: List[EvaluationInput],
        target_metric: str
    ) -> Tuple[Dict[str, Any], float]:
        """网格搜索优化"""
        # 构建参数网格
        param_grid = {}
        for param_name in param_names:
            if param_name in self.parameter_spaces:
                param_space = self.parameter_spaces[param_name]
                if param_space.param_type == 'categorical':
                    param_grid[param_name] = param_space.choices[:5]  # 限制选择数量
                elif param_space.param_type in ['continuous', 'integer']:
                    # 对于连续参数，选择几个代表性值
                    if param_space.low is not None and param_space.high is not None:
                        if param_space.param_type == 'continuous':
                            param_grid[param_name] = np.linspace(param_space.low, param_space.high, 5).tolist()
                        else:
                            param_grid[param_name] = list(range(param_space.low, param_space.high + 1,
                                                              max(1, (param_space.high - param_space.low) // 4)))
                elif param_space.param_type == 'boolean':
                    param_grid[param_name] = [True, False]

        best_score = 0.0
        best_config = {}

        # 网格搜索
        for params in ParameterGrid(param_grid):
            try:
                score = await self._evaluate_configuration(params, evaluation_dataset, target_metric)
                if score > best_score:
                    best_score = score
                    best_config = params.copy()
                    logger.debug(f"发现更好配置: {params}, 分数: {score:.3f}")

            except Exception as e:
                logger.warning(f"评估配置失败 {params}: {e}")
                continue

        return best_config, best_score

    async def _random_search_optimization(
        self,
        param_names: List[str],
        evaluation_dataset: List[EvaluationInput],
        target_metric: str
    ) -> Tuple[Dict[str, Any], float]:
        """随机搜索优化"""
        best_score = 0.0
        best_config = {}

        for trial in range(self.max_trials):
            # 随机采样参数
            params = {}
            for param_name in param_names:
                if param_name in self.parameter_spaces:
                    params[param_name] = self.parameter_spaces[param_name].sample()

            try:
                score = await self._evaluate_configuration(params, evaluation_dataset, target_metric)
                if score > best_score:
                    best_score = score
                    best_config = params.copy()
                    logger.debug(f"随机搜索第 {trial+1} 轮: {params}, 分数: {score:.3f}")

            except Exception as e:
                logger.warning(f"随机搜索评估失败 {params}: {e}")
                continue

        return best_config, best_score

    async def _bayesian_optimization(
        self,
        param_names: List[str],
        evaluation_dataset: List[EvaluationInput],
        target_metric: str
    ) -> Tuple[Dict[str, Any], float]:
        """贝叶斯优化（使用Optuna）"""
        def objective(trial):
            # 建议参数
            params = {}
            for param_name in param_names:
                if param_name in self.parameter_spaces:
                    param_space = self.parameter_spaces[param_name]

                    if param_space.param_type == 'categorical':
                        params[param_name] = trial.suggest_categorical(param_name, param_space.choices)
                    elif param_space.param_type == 'continuous':
                        params[param_name] = trial.suggest_float(param_name, param_space.low, param_space.high)
                    elif param_space.param_type == 'integer':
                        params[param_name] = trial.suggest_int(param_name, param_space.low, param_space.high)
                    elif param_space.param_type == 'boolean':
                        params[param_name] = trial.suggest_categorical(param_name, [True, False])

            # 异步评估需要在同步函数中处理
            try:
                # 这里需要实际调用评估函数，简化处理
                score = asyncio.run(self._evaluate_configuration(params, evaluation_dataset, target_metric))
                return score
            except Exception as e:
                logger.warning(f"贝叶斯优化评估失败: {e}")
                return 0.0

        # 创建Optuna研究
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.max_trials)

        best_params = study.best_params
        best_score = study.best_value

        logger.info(f"贝叶斯优化完成，最佳分数: {best_score:.3f}")

        return best_params, best_score

    async def _evaluate_configuration(
        self,
        params: Dict[str, Any],
        evaluation_dataset: List[EvaluationInput],
        target_metric: str
    ) -> float:
        """评估参数配置"""
        try:
            # 使用评估函数进行评估
            total_score = 0.0
            valid_evaluations = 0

            # 对数据集进行抽样以加速评估
            sample_size = min(10, len(evaluation_dataset))  # 最多评估10个样本
            sampled_inputs = np.random.choice(evaluation_dataset, sample_size, replace=False)

            for eval_input in sampled_inputs:
                try:
                    result = await self.evaluation_function(eval_input, params)

                    if target_metric == 'overall_score':
                        total_score += result.overall_score
                    elif target_metric in result.dimension_scores:
                        total_score += result.dimension_scores[target_metric]
                    else:
                        total_score += result.overall_score  # 回退到总分

                    valid_evaluations += 1

                except Exception as e:
                    logger.warning(f"单个评估失败: {e}")
                    continue

            return total_score / valid_evaluations if valid_evaluations > 0 else 0.0

        except Exception as e:
            logger.error(f"参数配置评估失败: {e}")
            return 0.0

    async def _get_baseline_config(self, model_name: str) -> Dict[str, Any]:
        """获取基准配置"""
        try:
            config = await self.database.get_model_config(model_name)
            return config if config else {}
        except Exception as e:
            logger.warning(f"获取基准配置失败: {e}")
            return {}

    async def _evaluate_baseline(self, config: Dict[str, Any], dataset: List[EvaluationInput]) -> float:
        """评估基准配置"""
        try:
            return await self._evaluate_configuration(config, dataset, 'overall_score')
        except Exception as e:
            logger.warning(f"基准评估失败: {e}")
            return 0.5  # 默认基准分数

    def _classify_change_type(self, old_value: Any, new_value: Any) -> str:
        """分类参数变化类型"""
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            diff = new_value - old_value
            if abs(diff) < 0.01:
                return 'minimal'
            elif diff > 0:
                return 'increase'
            else:
                return 'decrease'
        elif old_value == new_value:
            return 'no_change'
        else:
            return 'type_change'

    async def _save_optimization_result(self, result: OptimizationResult):
        """保存优化结果"""
        try:
            # 这里可以保存到数据库或文件
            # 简化处理，记录到日志
            logger.info(f"优化结果已保存: {result.to_dict()}")
        except Exception as e:
            logger.warning(f"保存优化结果失败: {e}")

    async def get_optimization_recommendations(
        self,
        model_name: str,
        recent_results: List[EvaluationResult]
    ) -> List[Dict[str, Any]]:
        """
        基于最近的评估结果生成优化建议

        Args:
            model_name: 模型名称
            recent_results: 最近的评估结果

        Returns:
            优化建议列表
        """
        recommendations = []

        if not recent_results:
            return recommendations

        # 分析维度表现
        dimension_scores = {}
        for result in recent_results:
            for dimension, score in result.dimension_scores.items():
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = []
                dimension_scores[dimension].append(score)

        # 为表现差的维度生成建议
        for dimension, scores in dimension_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.6:  # 低于60分认为需要改进
                recommendation = self._generate_dimension_recommendation(dimension, avg_score, model_name)
                if recommendation:
                    recommendations.append(recommendation)

        # 分析分数分布
        overall_scores = [r.overall_score for r in recent_results]
        avg_overall = sum(overall_scores) / len(overall_scores)
        score_std = np.std(overall_scores)

        # 分数波动大时建议稳定性改进
        if score_std > 0.2:
            recommendations.append({
                'type': 'stability_improvement',
                'issue': f'分数波动较大 (标准差: {score_std:.3f})',
                'suggestion': '建议降低temperature参数，增加max_tokens以提高输出稳定性',
                'priority': 'medium',
                'parameters': ['temperature', 'max_tokens']
            })

        # 整体分数偏低时建议全面优化
        if avg_overall < 0.5:
            recommendations.append({
                'type': 'overall_improvement',
                'issue': f'整体分数偏低 (平均: {avg_overall:.3f})',
                'suggestion': '建议进行全面参数优化，考虑调整模型或改进提示词设计',
                'priority': 'high',
                'parameters': list(self.parameter_spaces.keys())
            })

        return recommendations

    def _generate_dimension_recommendation(self, dimension: str, avg_score: float, model_name: str) -> Dict[str, Any]:
        """为特定维度生成优化建议"""
        dimension_recommendations = {
            'accuracy': {
                'suggestion': '准确性较低，建议：1) 检查知识库质量和覆盖度 2) 优化检索策略 3) 降低temperature以减少错误信息',
                'parameters': ['temperature', 'retrieval_top_k', 'similarity_threshold']
            },
            'relevance': {
                'suggestion': '相关性不足，建议：1) 优化提示词设计 2) 增加上下文长度 3) 改进问题解析',
                'parameters': ['context_length', 'instruction_template', 'top_p']
            },
            'completeness': {
                'suggestion': '完整性不够，建议：1) 增加max_tokens 2) 优化指令明确性 3) 调整frequency_penalty',
                'parameters': ['max_tokens', 'frequency_penalty', 'instruction_template']
            },
            'fluency': {
                'suggestion': '流畅性有待提升，建议：1) 适当提高temperature 2) 调整presence_penalty 3) 优化后处理',
                'parameters': ['temperature', 'presence_penalty']
            }
        }

        if dimension in dimension_recommendations:
            rec = dimension_recommendations[dimension]
            return {
                'type': 'dimension_improvement',
                'dimension': dimension,
                'issue': f'{dimension}维度得分偏低 (平均: {avg_score:.3f})',
                'suggestion': rec['suggestion'],
                'priority': 'high' if avg_score < 0.4 else 'medium',
                'parameters': rec['parameters']
            }

        return {}

    async def optimize_for_target_score(
        self,
        model_name: str,
        target_score: float,
        param_names: List[str],
        evaluation_dataset: List[EvaluationInput],
        max_iterations: int = 50
    ) -> OptimizationResult:
        """
        针对目标分数进行优化

        Args:
            model_name: 模型名称
            target_score: 目标分数
            param_names: 优化参数列表
            evaluation_dataset: 评估数据集
            max_iterations: 最大迭代次数

        Returns:
            优化结果
        """
        try:
            logger.info(f"开始针对目标分数 {target_score} 进行优化")

            baseline_config = await self._get_baseline_config(model_name)
            baseline_score = await self._evaluate_baseline(baseline_config, evaluation_dataset)

            if baseline_score >= target_score:
                logger.info(f"当前配置已达到目标分数 {target_score:.3f}")
                return OptimizationResult(
                    original_score=baseline_score,
                    optimized_score=baseline_score,
                    improvement=0.0,
                    parameter_changes={},
                    metadata={'message': 'already_achieved_target'}
                )

            best_config = baseline_config.copy()
            best_score = baseline_score
            current_config = baseline_config.copy()

            for iteration in range(max_iterations):
                # 基于梯度信息调整参数
                improved = False
                for param_name in param_names:
                    if param_name not in self.parameter_spaces:
                        continue

                    param_space = self.parameter_spaces[param_name]
                    old_value = current_config.get(param_name, param_space.default)

                    # 尝试调整参数
                    for delta in [-0.1, -0.05, 0.05, 0.1]:
                        if param_space.param_type in ['continuous', 'integer']:
                            if isinstance(old_value, (int, float)):
                                new_value = old_value + (old_value * delta if param_space.param_type == 'continuous' else int(old_value * delta))

                                # 检查范围
                                if param_space.low is not None:
                                    new_value = max(param_space.low, new_value)
                                if param_space.high is not None:
                                    new_value = min(param_space.high, new_value)

                                test_config = current_config.copy()
                                test_config[param_name] = new_value

                                test_score = await self._evaluate_configuration(
                                    test_config, evaluation_dataset, 'overall_score'
                                )

                                if test_score > best_score:
                                    best_score = test_score
                                    best_config = test_config.copy()
                                    improved = True

                                    logger.debug(f"改进发现: {param_name} {old_value} -> {new_value}, 分数: {test_score:.3f}")

                                if test_score >= target_score:
                                    logger.info(f"达到目标分数 {target_score:.3f}，提前结束优化")
                                    break

                    if best_score >= target_score:
                        break

                if not improved:
                    # 如果没有改进，尝试随机跳跃
                    for param_name in param_names:
                        if param_name in self.parameter_spaces:
                            current_config[param_name] = self.parameter_spaces[param_name].sample()
                else:
                    current_config = best_config.copy()

                if best_score >= target_score:
                    break

                logger.debug(f"迭代 {iteration+1}: 当前最佳分数 {best_score:.3f}")

            improvement = best_score - baseline_score
            parameter_changes = self._calculate_parameter_changes(baseline_config, best_config)

            result = OptimizationResult(
                original_score=baseline_score,
                optimized_score=best_score,
                improvement=improvement,
                parameter_changes=parameter_changes,
                metadata={
                    'target_score': target_score,
                    'target_achieved': best_score >= target_score,
                    'iterations': iteration + 1,
                    'model_name': model_name
                }
            )

            logger.info(f"目标优化完成: {improvement:+.3f} ({baseline_score:.3f} -> {best_score:.3f}), 目标: {target_score:.3f}")
            return result

        except Exception as e:
            logger.error(f"目标分数优化失败: {e}")
            raise

    def _calculate_parameter_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """计算参数变化"""
        changes = {}
        for param_name in set(old_config.keys()) | set(new_config.keys()):
            old_value = old_config.get(param_name)
            new_value = new_config.get(param_name)

            if old_value != new_value:
                changes[param_name] = {
                    'from': old_value,
                    'to': new_value,
                    'change_type': self._classify_change_type(old_value, new_value)
                }

        return changes