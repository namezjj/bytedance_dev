"""
评估报告生成器

生成详细的评估报告，包括统计分析、趋势分析和改进建议
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import logging

from ..core.evaluation_agent import EvaluationResult
from ..data.database import QueryFilter, EvaluationDatabase
from ..data.models import EvaluationSession, BenchmarkResult

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    评估报告生成器

    提供多种格式的报告生成功能：
    - JSON格式报告
    - HTML格式报告
    - PDF格式报告
    - 文本格式报告
    """

    def __init__(self, database: EvaluationDatabase, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            database: 数据库连接
            output_dir: 报告输出目录
        """
        self.database = database
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建报告输出目录: {self.output_dir}")

    async def generate_comprehensive_report(
        self,
        filter: Optional[QueryFilter] = None,
        format: str = "html"
    ) -> str:
        """
        生成综合评估报告

        Args:
            filter: 查询过滤器
            format: 报告格式 (json, html, pdf, text)

        Returns:
            报告文件路径
        """
        try:
            # 获取评估数据
            statistics = await self.database.get_evaluation_statistics(filter)
            results = await self.database.query_evaluation_results(filter or QueryFilter(), limit=1000)

            if not results:
                logger.warning("没有找到符合条件的评估数据")
                return ""

            # 生成报告数据
            report_data = await self._generate_report_data(results, statistics)

            # 根据格式生成报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_report_{timestamp}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "json":
                await self._generate_json_report(report_data, filepath)
            elif format == "html":
                await self._generate_html_report(report_data, filepath)
            elif format == "text":
                await self._generate_text_report(report_data, filepath)
            elif format == "pdf":
                await self._generate_pdf_report(report_data, filepath)
            else:
                raise ValueError(f"不支持的报告格式: {format}")

            logger.info(f"综合报告已生成: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"生成综合报告失败: {e}")
            raise

    async def generate_session_report(self, session_id: str, format: str = "html") -> str:
        """
        生成会话评估报告

        Args:
            session_id: 会话ID
            format: 报告格式

        Returns:
            报告文件路径
        """
        try:
            # 获取会话相关的评估数据
            filter = QueryFilter()
            # 这里需要根据session_id查询，但目前数据库结构需要调整
            results = await self.database.query_evaluation_results(filter, limit=1000)

            # 过滤出属于指定会话的结果
            session_results = [r for r in results if r.metadata.get('session_id') == session_id]

            if not session_results:
                logger.warning(f"会话 {session_id} 没有找到评估数据")
                return ""

            # 生成会话报告数据
            report_data = await self._generate_session_report_data(session_id, session_results)

            # 生成报告文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_report_{session_id}_{timestamp}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "json":
                await self._generate_json_report(report_data, filepath)
            elif format == "html":
                await self._generate_html_report(report_data, filepath)
            elif format == "text":
                await self._generate_text_report(report_data, filepath)
            else:
                raise ValueError(f"不支持的报告格式: {format}")

            logger.info(f"会话报告已生成: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"生成会话报告失败: {e}")
            raise

    async def generate_comparison_report(
        self,
        model_names: List[str],
        format: str = "html"
    ) -> str:
        """
        生成模型对比报告

        Args:
            model_names: 模型名称列表
            format: 报告格式

        Returns:
            报告文件路径
        """
        try:
            # 获取各模型的评估数据
            model_results = {}
            for model_name in model_names:
                filter = QueryFilter(model_name=model_name)
                results = await self.database.query_evaluation_results(filter, limit=1000)
                model_results[model_name] = results

            # 生成对比报告数据
            report_data = await self._generate_comparison_report_data(model_results)

            # 生成报告文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            models_str = "_vs_".join(model_names)
            filename = f"comparison_report_{models_str}_{timestamp}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "json":
                await self._generate_json_report(report_data, filepath)
            elif format == "html":
                await self._generate_html_report(report_data, filepath)
            elif format == "text":
                await self._generate_text_report(report_data, filepath)
            else:
                raise ValueError(f"不支持的报告格式: {format}")

            logger.info(f"对比报告已生成: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"生成对比报告失败: {e}")
            raise

    async def _generate_report_data(
        self,
        results: List[EvaluationResult],
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成报告数据"""
        if not results:
            return {}

        # 基础统计信息
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_evaluations': len(results),
                'date_range': {
                    'start': min(r.evaluation_timestamp for r in results).isoformat(),
                    'end': max(r.evaluation_timestamp for r in results).isoformat()
                }
            },
            'overall_statistics': statistics,
            'score_analysis': self._analyze_score_distribution(results),
            'dimension_analysis': self._analyze_dimension_performance(results),
            'time_trends': self._analyze_time_trends(results),
            'model_performance': self._analyze_model_performance(results),
            'improvement_suggestions': self._generate_improvement_suggestions(results),
            'quality_assessment': self._assess_overall_quality(results)
        }

        return report_data

    async def _generate_session_report_data(self, session_id: str, results: List[EvaluationResult]) -> Dict[str, Any]:
        """生成会话报告数据"""
        if not results:
            return {}

        session_stats = {
            'session_id': session_id,
            'total_evaluations': len(results),
            'duration_minutes': (max(r.evaluation_timestamp for r in results) -
                                min(r.evaluation_timestamp for r in results)).total_seconds() / 60,
            'average_score': sum(r.overall_score for r in results) / len(results),
            'start_time': min(r.evaluation_timestamp for r in results).isoformat(),
            'end_time': max(r.evaluation_timestamp for r in results).isoformat()
        }

        return {
            'session_metadata': session_stats,
            'score_analysis': self._analyze_score_distribution(results),
            'dimension_analysis': self._analyze_dimension_performance(results),
            'progress_analysis': self._analyze_session_progress(results),
            'session_summary': self._generate_session_summary(results)
        }

    async def _generate_comparison_report_data(self, model_results: Dict[str, List[EvaluationResult]]) -> Dict[str, Any]:
        """生成对比报告数据"""
        comparison_data = {
            'comparison_metadata': {
                'models': list(model_results.keys()),
                'comparison_date': datetime.now().isoformat(),
                'total_evaluations': sum(len(results) for results in model_results.values())
            },
            'model_statistics': {},
            'head_to_head_comparison': {},
            'dimension_comparison': {},
            'statistical_significance': {}
        }

        # 为每个模型生成统计信息
        for model_name, results in model_results.items():
            if results:
                comparison_data['model_statistics'][model_name] = {
                    'total_evaluations': len(results),
                    'average_score': sum(r.overall_score for r in results) / len(results),
                    'score_std': self._calculate_score_std(results),
                    'dimension_averages': self._calculate_dimension_averages(results)
                }

        # 生成头对头对比
        if len(model_results) >= 2:
            models = list(model_results.keys())
            for i in range(len(models)):
                for j in range(i + 1, len(models)):
                    model1, model2 = models[i], models[j]
                    comparison_key = f"{model1}_vs_{model2}"
                    comparison_data['head_to_head_comparison'][comparison_key] = self._compare_models(
                        model_results[model1], model_results[model2]
                    )

        return comparison_data

    def _analyze_score_distribution(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """分析分数分布"""
        if not results:
            return {}

        scores = [r.overall_score for r in results]

        # 分数区间分布
        score_ranges = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }

        for score in scores:
            if score < 0.2:
                score_ranges['0.0-0.2'] += 1
            elif score < 0.4:
                score_ranges['0.2-0.4'] += 1
            elif score < 0.6:
                score_ranges['0.4-0.6'] += 1
            elif score < 0.8:
                score_ranges['0.6-0.8'] += 1
            else:
                score_ranges['0.8-1.0'] += 1

        return {
            'distribution': score_ranges,
            'statistics': {
                'mean': sum(scores) / len(scores),
                'median': sorted(scores)[len(scores) // 2],
                'min': min(scores),
                'max': max(scores),
                'std': self._calculate_score_std(results)
            },
            'percentiles': self._calculate_percentiles(scores)
        }

    def _analyze_dimension_performance(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """分析维度表现"""
        if not results:
            return {}

        dimension_scores = {}
        dimension_stats = {}

        # 收集所有维度的分数
        for result in results:
            for dimension, score in result.dimension_scores.items():
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = []
                dimension_scores[dimension].append(score)

        # 计算每个维度的统计信息
        for dimension, scores in dimension_scores.items():
            if scores:
                dimension_stats[dimension] = {
                    'average': sum(scores) / len(scores),
                    'min': min(scores),
                    'max': max(scores),
                    'std': self._calculate_std(scores),
                    'sample_count': len(scores)
                }

        return {
            'dimension_statistics': dimension_stats,
            'dimension_correlation': self._calculate_dimension_correlation(results),
            'weak_dimensions': self._identify_weak_dimensions(dimension_stats),
            'strong_dimensions': self._identify_strong_dimensions(dimension_stats)
        }

    def _analyze_time_trends(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """分析时间趋势"""
        if not results:
            return {}

        # 按时间排序
        sorted_results = sorted(results, key=lambda r: r.evaluation_timestamp)

        # 按天分组计算平均分
        daily_scores = {}
        for result in sorted_results:
            date_key = result.evaluation_timestamp.date().isoformat()
            if date_key not in daily_scores:
                daily_scores[date_key] = []
            daily_scores[date_key].append(result.overall_score)

        # 计算每日平均分
        daily_averages = {
            date: sum(scores) / len(scores)
            for date, scores in daily_scores.items()
        }

        return {
            'daily_trends': daily_averages,
            'trend_analysis': self._analyze_trend_direction(daily_averages),
            'improvement_rate': self._calculate_improvement_rate(sorted_results)
        }

    def _analyze_model_performance(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """分析模型表现"""
        if not results:
            return {}

        model_scores = {}
        for result in results:
            model_name = result.metadata.get('model_name', 'unknown')
            if model_name not in model_scores:
                model_scores[model_name] = []
            model_scores[model_name].append(result.overall_score)

        model_stats = {}
        for model_name, scores in model_scores.items():
            if scores:
                model_stats[model_name] = {
                    'average_score': sum(scores) / len(scores),
                    'total_evaluations': len(scores),
                    'score_std': self._calculate_std(scores),
                    'best_score': max(scores),
                    'worst_score': min(scores)
                }

        # 排序模型
        ranked_models = sorted(
            model_stats.items(),
            key=lambda x: x[1]['average_score'],
            reverse=True
        )

        return {
            'model_statistics': model_stats,
            'ranking': ranked_models,
            'performance_gaps': self._calculate_performance_gaps(ranked_models)
        }

    def _generate_improvement_suggestions(self, results: List[EvaluationResult]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        if not results:
            return suggestions

        # 基于维度表现生成建议
        dimension_stats = self._analyze_dimension_performance(results)
        weak_dimensions = dimension_stats.get('weak_dimensions', [])

        for dimension, stats in weak_dimensions:
            suggestions.append({
                'type': 'dimension_improvement',
                'dimension': dimension,
                'current_score': stats['average'],
                'suggestion': self._get_dimension_improvement_suggestion(dimension, stats),
                'priority': 'high' if stats['average'] < 0.5 else 'medium'
            })

        # 基于分数分布生成建议
        score_analysis = self._analyze_score_distribution(results)
        low_score_percentage = score_analysis['distribution'].get('0.0-0.4', 0) / len(results)

        if low_score_percentage > 0.3:
            suggestions.append({
                'type': 'quality_improvement',
                'issue': f'{low_score_percentage:.1%} 的评估得分低于0.4',
                'suggestion': '建议检查模型配置、提示词设计或训练数据质量',
                'priority': 'high'
            })

        return suggestions

    def _assess_overall_quality(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """评估整体质量"""
        if not results:
            return {}

        avg_score = sum(r.overall_score for r in results) / len(results)

        quality_levels = {
            (0.9, 1.0): 'excellent',
            (0.8, 0.9): 'good',
            (0.6, 0.8): 'satisfactory',
            (0.4, 0.6): 'needs_improvement',
            (0.0, 0.4): 'poor'
        }

        quality_level = 'unknown'
        for (min_score, max_score), level in quality_levels.items():
            if min_score <= avg_score < max_score:
                quality_level = level
                break

        return {
            'overall_score': avg_score,
            'quality_level': quality_level,
            'assessment': self._get_quality_assessment(quality_level, avg_score),
            'recommendation': self._get_quality_recommendation(quality_level)
        }

    # 辅助方法
    def _calculate_score_std(self, results: List[EvaluationResult]) -> float:
        """计算分数标准差"""
        if not results:
            return 0.0
        scores = [r.overall_score for r in results]
        return self._calculate_std(scores)

    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _calculate_percentiles(self, scores: List[float]) -> Dict[str, float]:
        """计算百分位数"""
        if not scores:
            return {}
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        return {
            'p25': sorted_scores[int(n * 0.25)],
            'p50': sorted_scores[int(n * 0.5)],
            'p75': sorted_scores[int(n * 0.75)],
            'p90': sorted_scores[int(n * 0.9)]
        }

    def _get_dimension_improvement_suggestion(self, dimension: str, stats: Dict[str, Any]) -> str:
        """获取维度改进建议"""
        suggestions = {
            'accuracy': '建议增加事实核查机制，改进知识库质量，优化检索策略',
            'relevance': '建议优化提示词设计，改进上下文理解，增强问题解析能力',
            'completeness': '建议增加回答长度控制，完善信息提取，提供更详细的解释',
            'fluency': '建议改进语言模型训练，优化后处理规则，增强语法检查'
        }
        return suggestions.get(dimension, '建议进一步分析该维度的具体问题')

    def _get_quality_assessment(self, quality_level: str, avg_score: float) -> str:
        """获取质量评估描述"""
        assessments = {
            'excellent': f'模型表现优异，平均得分{avg_score:.3f}，达到了高质量标准',
            'good': f'模型表现良好，平均得分{avg_score:.3f}，有进一步优化空间',
            'satisfactory': f'模型表现基本满意，平均得分{avg_score:.3f}，需要针对性改进',
            'needs_improvement': f'模型表现需要改进，平均得分{avg_score:.3f}，建议全面优化',
            'poor': f'模型表现较差，平均得分{avg_score:.3f}，需要重大改进'
        }
        return assessments.get(quality_level, '模型表现需要评估')

    def _get_quality_recommendation(self, quality_level: str) -> str:
        """获取质量建议"""
        recommendations = {
            'excellent': '保持当前配置，持续监控性能变化',
            'good': '微调参数，进一步提升关键维度表现',
            'satisfactory': '针对性优化薄弱环节，改进整体表现',
            'needs_improvement': '全面审查配置和训练数据，制定改进计划',
            'poor': '重新设计系统架构，考虑更换或重新训练模型'
        }
        return recommendations.get(quality_level, '需要进一步评估')

    # 报告格式生成方法
    async def _generate_json_report(self, data: Dict[str, Any], filepath: str):
        """生成JSON格式报告"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    async def _generate_html_report(self, data: Dict[str, Any], filepath: str):
        """生成HTML格式报告"""
        html_content = self._generate_html_content(data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

    async def _generate_text_report(self, data: Dict[str, Any], filepath: str):
        """生成文本格式报告"""
        text_content = self._generate_text_content(data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)

    async def _generate_pdf_report(self, data: Dict[str, Any], filepath: str):
        """生成PDF格式报告"""
        # 这里可以集成reportlab或其他PDF生成库
        # 暂时生成HTML然后转换为PDF
        html_filepath = filepath.replace('.pdf', '.html')
        await self._generate_html_report(data, html_filepath)
        # TODO: 实现HTML到PDF的转换

    def _generate_html_content(self, data: Dict[str, Any]) -> str:
        """生成HTML内容"""
        # 简化的HTML模板
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>评估报告</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>评估报告</h1>
                <p>生成时间: {generated_at}</p>
                <p>总评估数: {total_evaluations}</p>
            </div>

            <div class="section">
                <h2>整体统计</h2>
                <div class="metric">平均得分: {average_score:.3f}</div>
                <div class="metric">最高分: {max_score:.3f}</div>
                <div class="metric">最低分: {min_score:.3f}</div>
            </div>
        </body>
        </html>
        """

        # 提取关键数据
        metadata = data.get('report_metadata', {})
        stats = data.get('overall_statistics', {})

        return html_template.format(
            generated_at=metadata.get('generated_at', ''),
            total_evaluations=metadata.get('total_evaluations', 0),
            average_score=stats.get('average_score', 0),
            max_score=stats.get('max_score', 0),
            min_score=stats.get('min_score', 0)
        )

    def _generate_text_content(self, data: Dict[str, Any]) -> str:
        """生成文本内容"""
        lines = []
        lines.append("=" * 50)
        lines.append("评估报告")
        lines.append("=" * 50)

        metadata = data.get('report_metadata', {})
        stats = data.get('overall_statistics', {})

        lines.append(f"生成时间: {metadata.get('generated_at', '')}")
        lines.append(f"总评估数: {metadata.get('total_evaluations', 0)}")
        lines.append(f"平均得分: {stats.get('average_score', 0):.3f}")
        lines.append(f"最高分: {stats.get('max_score', 0):.3f}")
        lines.append(f"最低分: {stats.get('min_score', 0):.3f}")

        return "\n".join(lines)