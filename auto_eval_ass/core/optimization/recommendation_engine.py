"""
智能推荐引擎

基于评估历史和模式分析，提供智能化的系统改进建议
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
import json

from ..evaluation_agent import EvaluationResult
from ...data.database import EvaluationDatabase, QueryFilter
from ...data.models import ModelConfiguration

logger = logging.getLogger(__name__)

@dataclass
class Recommendation:
    """推荐建议"""
    id: str
    type: str
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    confidence: float  # 0-1
    expected_improvement: float  # 预期改进幅度
    implementation_effort: str  # 'low', 'medium', 'high'
    parameters: List[str]
    evidence: List[str]  # 支撑证据
    action_steps: List[str]  # 具体行动步骤
    created_at: datetime

@dataclass
class PerformancePattern:
    """性能模式"""
    pattern_type: str
    description: str
    conditions: Dict[str, Any]
    impact_level: float
    frequency: int

class RecommendationEngine:
    """
    智能推荐引擎

    基于多维度分析生成改进建议：
    - 历史性能趋势分析
    - 维度相关性分析
    - 参数敏感性分析
    - 模式识别和预测
    """

    def __init__(self, database: EvaluationDatabase):
        """
        初始化推荐引擎

        Args:
            database: 评估数据库
        """
        self.database = database
        self.recommendations_history: List[Recommendation] = []
        self.patterns: List[PerformancePattern] = []

    async def generate_recommendations(
        self,
        model_name: str,
        time_window_days: int = 30,
        min_evaluations: int = 10
    ) -> List[Recommendation]:
        """
        生成智能推荐建议

        Args:
            model_name: 模型名称
            time_window_days: 分析时间窗口（天）
            min_evaluations: 最小评估数量

        Returns:
            推荐建议列表
        """
        try:
            logger.info(f"开始为模型 {model_name} 生成推荐建议")

            # 获取评估数据
            filter = QueryFilter(
                model_name=model_name,
                date_from=datetime.now() - timedelta(days=time_window_days)
            )
            results = await self.database.query_evaluation_results(filter, limit=1000)

            if len(results) < min_evaluations:
                logger.warning(f"评估数据不足 ({len(results)} < {min_evaluations})，无法生成可靠推荐")
                return []

            # 生成各类推荐
            recommendations = []

            # 1. 基于趋势分析的推荐
            trend_recommendations = await self._analyze_trends_and_recommend(model_name, results)
            recommendations.extend(trend_recommendations)

            # 2. 基于维度表现的推荐
            dimension_recommendations = await self._analyze_dimensions_and_recommend(results)
            recommendations.extend(dimension_recommendations)

            # 3. 基于参数敏感性的推荐
            parameter_recommendations = await self._analyze_parameter_sensitivity(model_name, results)
            recommendations.extend(parameter_recommendations)

            # 4. 基于异常检测的推荐
            anomaly_recommendations = await self._detect_anomalies_and_recommend(results)
            recommendations.extend(anomaly_recommendations)

            # 5. 基于最佳实践的推荐
            practice_recommendations = await self._generate_best_practice_recommendations(model_name, results)
            recommendations.extend(practice_recommendations)

            # 排序和去重
            final_recommendations = self._rank_and_deduplicate_recommendations(recommendations)

            # 保存推荐历史
            self.recommendations_history.extend(final_recommendations)

            logger.info(f"生成了 {len(final_recommendations)} 条推荐建议")
            return final_recommendations

        except Exception as e:
            logger.error(f"生成推荐建议失败: {e}")
            raise

    async def _analyze_trends_and_recommend(self, model_name: str, results: List[EvaluationResult]) -> List[Recommendation]:
        """基于趋势分析生成推荐"""
        recommendations = []

        if len(results) < 5:
            return recommendations

        # 分析分数趋势
        sorted_results = sorted(results, key=lambda r: r.evaluation_timestamp)
        scores = [r.overall_score for r in sorted_results]
        timestamps = [r.evaluation_timestamp for r in sorted_results]

        # 计算趋势
        if len(scores) >= 3:
            # 简单线性趋势
            x = np.arange(len(scores))
            trend_slope = np.polyfit(x, scores, 1)[0]

            if trend_slope < -0.01:  # 下降趋势
                recommendations.append(Recommendation(
                    id=f"trend_decline_{model_name}_{int(datetime.now().timestamp())}",
                    type="trend_improvement",
                    title="性能下降趋势检测",
                    description=f"检测到模型性能呈下降趋势 (趋势斜率: {trend_slope:.4f})，建议及时干预",
                    priority="high",
                    confidence=abs(trend_slope) * 10,
                    expected_improvement=0.1,
                    implementation_effort="medium",
                    parameters=["temperature", "max_tokens", "retrieval_top_k"],
                    evidence=[f"趋势斜率: {trend_slope:.4f}", f"样本数量: {len(scores)}"],
                    action_steps=[
                        "1. 检查最近的模型配置变更",
                        "2. 分析数据质量变化",
                        "3. 考虑重新校准参数",
                        "4. 增加监控频率"
                    ],
                    created_at=datetime.now()
                ))
            elif trend_slope > 0.01:  # 上升趋势
                recommendations.append(Recommendation(
                    id=f"trend_improvement_{model_name}_{int(datetime.now().timestamp())}",
                    type="trend_maintenance",
                    title="性能上升趋势确认",
                    description=f"模型性能呈上升趋势 (趋势斜率: {trend_slope:.4f})，建议保持当前配置",
                    priority="low",
                    confidence=trend_slope * 10,
                    expected_improvement=0.05,
                    implementation_effort="low",
                    parameters=[],
                    evidence=[f"趋势斜率: {trend_slope:.4f}", f"性能持续改善"],
                    action_steps=[
                        "1. 记录当前有效配置",
                        "2. 继续监控性能表现",
                        "3. 考虑将配置设为默认值"
                    ],
                    created_at=datetime.now()
                ))

        # 分析稳定性
        if len(scores) >= 5:
            score_std = np.std(scores)
            score_mean = np.mean(scores)
            cv = score_std / score_mean if score_mean > 0 else 0  # 变异系数

            if cv > 0.3:  # 高波动性
                recommendations.append(Recommendation(
                    id=f"stability_{model_name}_{int(datetime.now().timestamp())}",
                    type="stability_improvement",
                    title="输出稳定性问题",
                    description=f"模型输出波动较大 (变异系数: {cv:.3f})，建议提高稳定性",
                    priority="medium",
                    confidence=cv,
                    expected_improvement=0.08,
                    implementation_effort="medium",
                    parameters=["temperature", "top_p"],
                    evidence=[f"变异系数: {cv:.3f}", f"标准差: {score_std:.3f}"],
                    action_steps=[
                        "1. 降低temperature参数以减少随机性",
                        "2. 调整top_p参数",
                        "3. 增加输出长度限制",
                        "4. 改进提示词一致性"
                    ],
                    created_at=datetime.now()
                ))

        return recommendations

    async def _analyze_dimensions_and_recommend(self, results: List[EvaluationResult]) -> List[Recommendation]:
        """基于维度分析生成推荐"""
        recommendations = []

        if not results:
            return recommendations

        # 收集维度数据
        dimension_scores = defaultdict(list)
        for result in results:
            for dimension, score in result.dimension_scores.items():
                dimension_scores[dimension].append(score)

        # 分析每个维度
        for dimension, scores in dimension_scores.items():
            if len(scores) < 3:
                continue

            avg_score = np.mean(scores)
            score_std = np.std(scores)

            # 维度表现不佳的推荐
            if avg_score < 0.6:
                priority = "high" if avg_score < 0.4 else "medium"
                expected_improvement = 0.3 - avg_score + 0.1

                rec = self._create_dimension_recommendation(
                    dimension, avg_score, score_std, priority, expected_improvement
                )
                if rec:
                    recommendations.append(rec)

            # 维度稳定性问题
            elif score_std > 0.2:
                rec = Recommendation(
                    id=f"dimension_stability_{dimension}_{int(datetime.now().timestamp())}",
                    type="dimension_stability",
                    title=f"{self._get_dimension_chinese_name(dimension)}稳定性问题",
                    description=f"{self._get_dimension_chinese_name(dimension)}维度波动较大 (标准差: {score_std:.3f})",
                    priority="medium",
                    confidence=min(score_std * 2, 1.0),
                    expected_improvement=0.05,
                    implementation_effort="medium",
                    parameters=self._get_dimension_stability_parameters(dimension),
                    evidence=[f"平均分: {avg_score:.3f}", f"标准差: {score_std:.3f}"],
                    action_steps=[
                        f"1. 分析{self._get_dimension_chinese_name(dimension)}波动原因",
                        "2. 调整相关参数以提高一致性",
                        "3. 增加质量控制检查点"
                    ],
                    created_at=datetime.now()
                )
                recommendations.append(rec)

        return recommendations

    async def _analyze_parameter_sensitivity(self, model_name: str, results: List[EvaluationResult]) -> List[Recommendation]:
        """基于参数敏感性分析生成推荐"""
        recommendations = []

        # 这里需要更复杂的参数敏感性分析
        # 简化实现：基于参数配置变化和性能变化的相关性

        # 分析temperature参数的敏感性
        temp_scores = defaultdict(list)
        for result in results:
            temp = result.metadata.get('temperature')
            if temp is not None:
                temp_scores[round(temp, 1)].append(result.overall_score)

        if len(temp_scores) > 1:
            # 计算不同temperature值的平均性能
            temp_performance = {}
            for temp, scores in temp_scores.items():
                if len(scores) >= 3:  # 需要足够样本
                    temp_performance[temp] = np.mean(scores)

            if len(temp_performance) >= 2:
                temps = sorted(temp_performance.keys())
                performances = [temp_performance[t] for t in temps]

                # 寻找最优temperature
                best_temp_idx = np.argmax(performances)
                best_temp = temps[best_temp_idx]
                best_performance = performances[best_temp]

                # 如果当前配置不是最优的
                current_temp = temp_scores.get(max(temp_scores.keys(), key=lambda k: len(temp_scores[k])))
                if current_temp and best_temp != round(list(current_temp)[0], 1):
                    recommendations.append(Recommendation(
                        id=f"temperature_optimization_{model_name}_{int(datetime.now().timestamp())}",
                        type="parameter_optimization",
                        title="Temperature参数优化",
                        description=f"建议调整temperature参数从当前值到 {best_temp} 以获得更好性能",
                        priority="medium",
                        confidence=0.7,
                        expected_improvement=best_performance - np.mean(performances),
                        implementation_effort="low",
                        parameters=["temperature"],
                        evidence=[f"当前配置性能: {np.mean(performances):.3f}", f"最优配置性能: {best_performance:.3f}"],
                        action_steps=[
                            f"1. 将temperature参数调整为 {best_temp}",
                            "2. 监控性能变化",
                            "3. 如需要可进行微调"
                        ],
                        created_at=datetime.now()
                    ))

        return recommendations

    async def _detect_anomalies_and_recommend(self, results: List[EvaluationResult]) -> List[Recommendation]:
        """基于异常检测生成推荐"""
        recommendations = []

        if len(results) < 10:
            return recommendations

        scores = [r.overall_score for r in results]

        # 使用IQR方法检测异常值
        q1, q3 = np.percentile(scores, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # 找出异常结果
        anomaly_results = []
        for i, result in enumerate(results):
            if result.overall_score < lower_bound or result.overall_score > upper_bound:
                anomaly_results.append(result)

        # 如果异常结果较多，建议系统改进
        anomaly_ratio = len(anomaly_results) / len(results)
        if anomaly_ratio > 0.2:  # 超过20%的异常结果
            recommendations.append(Recommendation(
                id=f"anomaly_detection_{int(datetime.now().timestamp())}",
                type="anomaly_handling",
                title="异常结果比例过高",
                description=f"检测到 {anomaly_ratio:.1%} 的评估结果为异常值，建议改进系统稳定性",
                priority="high",
                confidence=anomaly_ratio * 2,
                expected_improvement=0.1,
                implementation_effort="high",
                parameters=["temperature", "max_tokens", "quality_filters"],
                evidence=[f"异常结果比例: {anomaly_ratio:.1%}", f"异常结果数量: {len(anomaly_results)}"],
                action_steps=[
                    "1. 分析异常结果的共同特征",
                    "2. 改进输入数据质量控制",
                    "3. 增加异常检测和处理机制",
                    "4. 优化模型参数稳定性"
                ],
                created_at=datetime.now()
            ))

        return recommendations

    async def _generate_best_practice_recommendations(self, model_name: str, results: List[EvaluationResult]) -> List[Recommendation]:
        """基于最佳实践生成推荐"""
        recommendations = []

        # 分析整体性能水平
        avg_score = np.mean([r.overall_score for r in results])

        # 基于性能水平的一般建议
        if avg_score < 0.5:
            recommendations.append(Recommendation(
                id=f"best_practice_low_performance_{model_name}_{int(datetime.now().timestamp())}",
                type="best_practice",
                title="低性能最佳实践建议",
                description="当前模型性能偏低，建议遵循以下最佳实践进行改进",
                priority="high",
                confidence=0.8,
                expected_improvement=0.15,
                implementation_effort="high",
                parameters=["temperature", "max_tokens", "prompt_engineering", "data_quality"],
                evidence=[f"当前平均分: {avg_score:.3f}"],
                action_steps=[
                    "1. 全面审查训练数据质量",
                    "2. 优化提示词设计和工程",
                    "3. 考虑使用更大的模型或集成方法",
                    "4. 建立完善的评估和反馈循环",
                    "5. 增加人工审核和校准机制"
                ],
                created_at=datetime.now()
            ))
        elif 0.5 <= avg_score < 0.7:
            recommendations.append(Recommendation(
                id=f"best_practice_medium_performance_{model_name}_{int(datetime.now().timestamp())}",
                type="best_practice",
                title="中等性能优化建议",
                description="模型性能处于中等水平，建议进行针对性优化",
                priority="medium",
                confidence=0.6,
                expected_improvement=0.1,
                implementation_effort="medium",
                parameters=["fine_tuning", "parameter_optimization", "context_optimization"],
                evidence=[f"当前平均分: {avg_score:.3f}"],
                action_steps=[
                    "1. 进行参数细调优化",
                    "2. 改进上下文处理策略",
                    "3. 增强特定任务的能力",
                    "4. 建立持续改进机制"
                ],
                created_at=datetime.now()
            ))

        return recommendations

    def _create_dimension_recommendation(
        self,
        dimension: str,
        avg_score: float,
        score_std: float,
        priority: str,
        expected_improvement: float
    ) -> Optional[Recommendation]:
        """为特定维度创建推荐"""
        dimension_configs = {
            'accuracy': {
                'title': '准确性改进建议',
                'parameters': ['temperature', 'retrieval_top_k', 'knowledge_base'],
                'action_steps': [
                    "1. 降低temperature参数以减少错误信息",
                    "2. 增加检索数量以提高信息覆盖",
                    "3. 检查和更新知识库内容",
                    "4. 增加事实核查机制",
                    "5. 改进提示词的准确性要求"
                ]
            },
            'relevance': {
                'title': '相关性改进建议',
                'parameters': ['context_length', 'prompt_template', 'question_understanding'],
                'action_steps': [
                    "1. 增加上下文长度以提供更多相关信息",
                    "2. 优化提示词模板以提高相关性",
                    "3. 改进问题理解和解析能力",
                    "4. 增强检索策略的精准度",
                    "5. 调整输出控制参数"
                ]
            },
            'completeness': {
                'title': '完整性改进建议',
                'parameters': ['max_tokens', 'instruction_clarity', 'output_format'],
                'action_steps': [
                    "1. 增加max_tokens以提供更完整的回答",
                    "2. 提高指令的明确性和具体性",
                    "3. 优化输出格式要求",
                    "4. 改进信息提取和组织能力",
                    "5. 增加完整性检查机制"
                ]
            },
            'fluency': {
                'title': '流畅性改进建议',
                'parameters': ['temperature', 'language_model', 'post_processing'],
                'action_steps': [
                    "1. 适当提高temperature以增加语言多样性",
                    "2. 考虑使用专门的语言模型",
                    "3. 增加后处理和语法检查",
                    "4. 优化语言风格的训练",
                    "5. 改进文本生成策略"
                ]
            }
        }

        if dimension in dimension_configs:
            config = dimension_configs[dimension]
            return Recommendation(
                id=f"dimension_{dimension}_{int(datetime.now().timestamp())}",
                type="dimension_improvement",
                title=config['title'],
                description=f"{self._get_dimension_chinese_name(dimension)}维度表现不佳 (平均分: {avg_score:.3f})，建议针对性改进",
                priority=priority,
                confidence=1 - avg_score,
                expected_improvement=expected_improvement,
                implementation_effort="medium",
                parameters=config['parameters'],
                evidence=[f"平均分: {avg_score:.3f}", f"标准差: {score_std:.3f}"],
                action_steps=config['action_steps'],
                created_at=datetime.now()
            )

        return None

    def _get_dimension_chinese_name(self, dimension: str) -> str:
        """获取维度的中文名称"""
        names = {
            'accuracy': '准确性',
            'relevance': '相关性',
            'completeness': '完整性',
            'fluency': '流畅性'
        }
        return names.get(dimension, dimension)

    def _get_dimension_stability_parameters(self, dimension: str) -> List[str]:
        """获取维度稳定性相关的参数"""
        params = {
            'accuracy': ['temperature', 'retrieval_strategy'],
            'relevance': ['context_length', 'similarity_threshold'],
            'completeness': ['max_tokens', 'instruction_format'],
            'fluency': ['temperature', 'language_model']
        }
        return params.get(dimension, ['temperature', 'max_tokens'])

    def _rank_and_deduplicate_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """对推荐进行排序和去重"""
        if not recommendations:
            return []

        # 按优先级和置信度排序
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}

        def sort_key(rec):
            priority_weight = priority_weights.get(rec.priority, 1)
            return priority_weight * rec.confidence

        # 排序
        sorted_recommendations = sorted(recommendations, key=sort_key, reverse=True)

        # 去重（基于类型和参数）
        seen = set()
        final_recommendations = []

        for rec in sorted_recommendations:
            # 创建去重键
            dedupe_key = (rec.type, tuple(sorted(rec.parameters)))

            if dedupe_key not in seen:
                seen.add(dedupe_key)
                final_recommendations.append(rec)

        return final_recommendations

    async def get_recommendation_summary(self, model_name: str, days: int = 7) -> Dict[str, Any]:
        """获取推荐摘要统计"""
        try:
            # 获取最近的推荐
            recent_recommendations = [
                rec for rec in self.recommendations_history
                if rec.created_at >= datetime.now() - timedelta(days=days)
            ]

            if not recent_recommendations:
                return {
                    'total_recommendations': 0,
                    'by_priority': {},
                    'by_type': {},
                    'average_confidence': 0.0,
                    'high_priority_count': 0
                }

            # 统计分析
            by_priority = Counter(rec.priority for rec in recent_recommendations)
            by_type = Counter(rec.type for rec in recent_recommendations)
            avg_confidence = np.mean([rec.confidence for rec in recent_recommendations])
            high_priority_count = by_priority.get('high', 0)

            return {
                'total_recommendations': len(recent_recommendations),
                'by_priority': dict(by_priority),
                'by_type': dict(by_type),
                'average_confidence': avg_confidence,
                'high_priority_count': high_priority_count,
                'most_common_type': by_type.most_common(1)[0][0] if by_type else None,
                'recommendation_rate': len(recent_recommendations) / days  # 每天推荐数量
            }

        except Exception as e:
            logger.error(f"获取推荐摘要失败: {e}")
            return {}

    def export_recommendations(self, format: str = "json") -> str:
        """导出推荐数据"""
        try:
            data = [rec.__dict__ for rec in self.recommendations_history]

            if format == "json":
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

        except Exception as e:
            logger.error(f"导出推荐数据失败: {e}")
            return ""