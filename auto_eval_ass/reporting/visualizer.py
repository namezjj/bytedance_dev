"""
评估数据可视化模块

提供各种图表和可视化功能
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.evaluation_agent import EvaluationResult

logger = logging.getLogger(__name__)

class EvaluationVisualizer:
    """
    评估数据可视化器

    提供多种图表类型：
    - 分数分布图
    - 维度雷达图
    - 时间趋势图
    - 模型对比图
    - 相关性热力图
    """

    def __init__(self, output_dir: str = "visualizations"):
        """
        初始化可视化器

        Args:
            output_dir: 图片输出目录
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        self._setup_style()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建可视化输出目录: {self.output_dir}")

    def _setup_style(self):
        """设置图表样式"""
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置seaborn样式
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def create_score_distribution_plot(
        self,
        results: List[EvaluationResult],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建分数分布图

        Args:
            results: 评估结果列表
            save_path: 保存路径（可选）

        Returns:
            图片保存路径
        """
        try:
            if not results:
                logger.warning("没有评估数据用于可视化")
                return ""

            scores = [r.overall_score for r in results]

            # 创建子图
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('评估分数分布分析', fontsize=16, fontweight='bold')

            # 直方图
            axes[0, 0].hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('分数分布直方图')
            axes[0, 0].set_xlabel('分数')
            axes[0, 0].set_ylabel('频次')
            axes[0, 0].axvline(np.mean(scores), color='red', linestyle='--', label=f'平均值: {np.mean(scores):.3f}')
            axes[0, 0].legend()

            # 箱线图
            axes[0, 1].boxplot(scores, patch_artist=True, boxprops=dict(facecolor='lightblue'))
            axes[0, 1].set_title('分数箱线图')
            axes[0, 1].set_ylabel('分数')
            axes[0, 1].grid(True, alpha=0.3)

            # 分数区间饼图
            score_ranges = {
                '0.0-0.2': sum(1 for s in scores if s < 0.2),
                '0.2-0.4': sum(1 for s in scores if 0.2 <= s < 0.4),
                '0.4-0.6': sum(1 for s in scores if 0.4 <= s < 0.6),
                '0.6-0.8': sum(1 for s in scores if 0.6 <= s < 0.8),
                '0.8-1.0': sum(1 for s in scores if s >= 0.8)
            }

            # 过滤掉值为0的区间
            filtered_ranges = {k: v for k, v in score_ranges.items() if v > 0}
            if filtered_ranges:
                axes[1, 0].pie(filtered_ranges.values(), labels=filtered_ranges.keys(), autopct='%1.1f%%')
                axes[1, 0].set_title('分数区间分布')

            # Q-Q图（正态性检验）
            from scipy import stats
            stats.probplot(scores, dist="norm", plot=axes[1, 1])
            axes[1, 1].set_title('Q-Q图（正态性检验）')
            axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()

            # 保存图片
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"score_distribution_{timestamp}.png")

            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"分数分布图已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建分数分布图失败: {e}")
            raise

    def create_dimension_radar_chart(
        self,
        results: List[EvaluationResult],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建维度雷达图

        Args:
            results: 评估结果列表
            save_path: 保存路径（可选）

        Returns:
            图片保存路径
        """
        try:
            if not results:
                return ""

            # 计算各维度平均分
            dimension_scores = {}
            for result in results:
                for dimension, score in result.dimension_scores.items():
                    if dimension not in dimension_scores:
                        dimension_scores[dimension] = []
                    dimension_scores[dimension].append(score)

            dimension_averages = {
                dim: np.mean(scores) for dim, scores in dimension_scores.items()
            }

            if not dimension_averages:
                logger.warning("没有维度数据用于雷达图")
                return ""

            # 创建雷达图
            dimensions = list(dimension_averages.keys())
            values = list(dimension_averages.values())

            # 闭合数据
            dimensions += [dimensions[0]]
            values += [values[0]]

            # 计算角度
            angles = np.linspace(0, 2 * np.pi, len(dimensions))

            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            ax.plot(angles, values, 'o-', linewidth=2, color='blue', alpha=0.7)
            ax.fill(angles, values, alpha=0.25, color='blue')

            # 设置标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(dimensions[:-1])
            ax.set_ylim(0, 1)

            # 添加网格线和标签
            ax.grid(True)
            ax.set_title('评估维度雷达图', size=16, fontweight='bold', pad=20)

            # 添加数值标签
            for angle, value, dim in zip(angles[:-1], values[:-1], dimensions[:-1]):
                ax.text(angle, value + 0.05, f'{value:.3f}', ha='center', va='center')

            plt.tight_layout()

            # 保存图片
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"dimension_radar_{timestamp}.png")

            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"维度雷达图已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建维度雷达图失败: {e}")
            raise

    def create_time_trend_plot(
        self,
        results: List[EvaluationResult],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建时间趋势图

        Args:
            results: 评估结果列表
            save_path: 保存路径（可选）

        Returns:
            图片保存路径
        """
        try:
            if not results:
                return ""

            # 按时间排序
            sorted_results = sorted(results, key=lambda r: r.evaluation_timestamp)

            # 创建时间序列数据
            timestamps = [r.evaluation_timestamp for r in sorted_results]
            scores = [r.overall_score for r in sorted_results]

            # 创建DataFrame
            df = pd.DataFrame({
                'timestamp': timestamps,
                'score': scores
            })

            # 按天聚合计算移动平均
            df['date'] = df['timestamp'].dt.date
            daily_avg = df.groupby('date')['score'].agg(['mean', 'count']).reset_index()

            # 创建图表
            fig, axes = plt.subplots(2, 1, figsize=(15, 12))
            fig.suptitle('评估分数时间趋势分析', fontsize=16, fontweight='bold')

            # 原始分数散点图 + 移动平均线
            axes[0].scatter(timestamps, scores, alpha=0.6, s=30, color='lightblue', label='原始分数')

            # 7天移动平均
            window_size = min(7, len(scores))
            if window_size > 1:
                moving_avg = pd.Series(scores).rolling(window=window_size).mean()
                axes[0].plot(timestamps, moving_avg, color='red', linewidth=2, label=f'{window_size}天移动平均')

            axes[0].set_title('分数时间趋势')
            axes[0].set_xlabel('时间')
            axes[0].set_ylabel('分数')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # 每日平均分数
            axes[1].bar(daily_avg['date'], daily_avg['mean'], alpha=0.7, color='skyblue')
            axes[1].set_title('每日平均分数')
            axes[1].set_xlabel('日期')
            axes[1].set_ylabel('平均分数')
            axes[1].grid(True, alpha=0.3)

            # 添加数值标签
            for i, (date, avg_score, count) in enumerate(zip(daily_avg['date'], daily_avg['mean'], daily_avg['count'])):
                axes[1].text(date, avg_score + 0.01, f'{avg_score:.3f}\n(n={count})',
                            ha='center', va='bottom', fontsize=8)

            plt.tight_layout()

            # 保存图片
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"time_trend_{timestamp}.png")

            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"时间趋势图已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建时间趋势图失败: {e}")
            raise

    def create_model_comparison_plot(
        self,
        model_results: Dict[str, List[EvaluationResult]],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建模型对比图

        Args:
            model_results: 模型结果字典
            save_path: 保存路径（可选）

        Returns:
            图片保存路径
        """
        try:
            if not model_results:
                return ""

            # 创建对比图表
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('模型性能对比分析', fontsize=16, fontweight='bold')

            model_names = list(model_results.keys())
            model_stats = {}

            # 计算每个模型的统计信息
            for model_name, results in model_results.items():
                if results:
                    scores = [r.overall_score for r in results]
                    model_stats[model_name] = {
                        'mean': np.mean(scores),
                        'std': np.std(scores),
                        'median': np.median(scores),
                        'scores': scores
                    }

            # 1. 平均分数对比条形图
            means = [model_stats[name]['mean'] for name in model_names]
            bars = axes[0, 0].bar(model_names, means, alpha=0.7, color='skyblue')
            axes[0, 0].set_title('模型平均分数对比')
            axes[0, 0].set_ylabel('平均分数')
            axes[0, 0].grid(True, alpha=0.3)

            # 添加数值标签
            for bar, mean in zip(bars, means):
                axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                               f'{mean:.3f}', ha='center', va='bottom')

            # 2. 分数分布箱线图
            score_data = [model_stats[name]['scores'] for name in model_names]
            bp = axes[0, 1].boxplot(score_data, labels=model_names, patch_artist=True)

            # 设置颜色
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
            for patch, color in zip(bp['boxes'], colors[:len(model_names)]):
                patch.set_facecolor(color)

            axes[0, 1].set_title('模型分数分布对比')
            axes[0, 1].set_ylabel('分数')
            axes[0, 1].grid(True, alpha=0.3)

            # 3. 维度对比雷达图
            if len(model_names) >= 2:
                # 计算各模型各维度平均分
                all_dimensions = set()
                for results in model_results.values():
                    for result in results:
                        all_dimensions.update(result.dimension_scores.keys())

                dimension_data = {}
                for dimension in all_dimensions:
                    dimension_data[dimension] = {}
                    for model_name in model_names:
                        dimension_scores = [
                            r.dimension_scores.get(dimension, 0)
                            for r in model_results[model_name]
                            if dimension in r.dimension_scores
                        ]
                        dimension_data[dimension][model_name] = np.mean(dimension_scores) if dimension_scores else 0

                # 简化的维度对比（选择前6个维度）
                selected_dimensions = list(all_dimensions)[:6]
                if selected_dimensions:
                    x = np.arange(len(selected_dimensions))
                    width = 0.8 / len(model_names)

                    for i, model_name in enumerate(model_names):
                        values = [dimension_data[dim].get(model_name, 0) for dim in selected_dimensions]
                        axes[1, 0].bar(x + i * width, values, width, label=model_name, alpha=0.7)

                    axes[1, 0].set_title('关键维度对比')
                    axes[1, 0].set_xlabel('评估维度')
                    axes[1, 0].set_ylabel('平均分数')
                    axes[1, 0].set_xticks(x + width * (len(model_names) - 1) / 2)
                    axes[1, 0].set_xticklabels(selected_dimensions, rotation=45)
                    axes[1, 0].legend()
                    axes[1, 0].grid(True, alpha=0.3)

            # 4. 统计摘要表格
            axes[1, 1].axis('off')
            table_data = []
            for model_name in model_names:
                stats = model_stats[model_name]
                table_data.append([
                    model_name,
                    f"{stats['mean']:.3f}",
                    f"{stats['median']:.3f}",
                    f"{stats['std']:.3f}",
                    len(stats['scores'])
                ])

            table = axes[1, 1].table(
                cellText=table_data,
                colLabels=['模型', '均值', '中位数', '标准差', '样本数'],
                cellLoc='center',
                loc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2)
            axes[1, 1].set_title('统计摘要', pad=20)

            plt.tight_layout()

            # 保存图片
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"model_comparison_{timestamp}.png")

            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"模型对比图已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建模型对比图失败: {e}")
            raise

    def create_correlation_heatmap(
        self,
        results: List[EvaluationResult],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建维度相关性热力图

        Args:
            results: 评估结果列表
            save_path: 保存路径（可选）

        Returns:
            图片保存路径
        """
        try:
            if not results:
                return ""

            # 构建维度分数矩阵
            all_dimensions = set()
            for result in results:
                all_dimensions.update(result.dimension_scores.keys())

            dimension_list = sorted(list(all_dimensions))
            data_matrix = []

            for result in results:
                row = [result.dimension_scores.get(dim, np.nan) for dim in dimension_list]
                data_matrix.append(row)

            if not data_matrix or not dimension_list:
                logger.warning("没有足够的维度数据用于相关性分析")
                return ""

            # 创建DataFrame
            df = pd.DataFrame(data_matrix, columns=dimension_list)

            # 计算相关性矩阵
            correlation_matrix = df.corr()

            # 创建热力图
            plt.figure(figsize=(12, 10))
            sns.heatmap(
                correlation_matrix,
                annot=True,
                cmap='coolwarm',
                center=0,
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": .8},
                fmt='.3f'
            )
            plt.title('评估维度相关性热力图', fontsize=16, fontweight='bold')
            plt.tight_layout()

            # 保存图片
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"correlation_heatmap_{timestamp}.png")

            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"相关性热力图已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建相关性热力图失败: {e}")
            raise

    def create_interactive_dashboard(
        self,
        results: List[EvaluationResult],
        save_path: Optional[str] = None
    ) -> str:
        """
        创建交互式仪表板（使用Plotly）

        Args:
            results: 评估结果列表
            save_path: 保存路径（可选）

        Returns:
            HTML文件路径
        """
        try:
            if not results:
                return ""

            # 准备数据
            scores = [r.overall_score for r in results]
            timestamps = [r.evaluation_timestamp for r in results]

            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('分数分布', '时间趋势', '维度分析', '统计摘要'),
                specs=[
                    [{"type": "histogram"}, {"type": "scatter"}],
                    [{"type": "bar"}, {"type": "table"}]
                ]
            )

            # 1. 分数分布直方图
            fig.add_trace(
                go.Histogram(x=scores, name='分数分布', nbinsx=20),
                row=1, col=1
            )

            # 2. 时间趋势
            fig.add_trace(
                go.Scatter(x=timestamps, y=scores, mode='markers', name='分数时间序列'),
                row=1, col=2
            )

            # 3. 维度分析（条形图）
            dimension_scores = {}
            for result in results:
                for dimension, score in result.dimension_scores.items():
                    if dimension not in dimension_scores:
                        dimension_scores[dimension] = []
                    dimension_scores[dimension].append(score)

            dimension_averages = {dim: np.mean(scores) for dim, scores in dimension_scores.items()}

            fig.add_trace(
                go.Bar(
                    x=list(dimension_averages.keys()),
                    y=list(dimension_averages.values()),
                    name='维度平均分'
                ),
                row=2, col=1
            )

            # 4. 统计摘要表格
            stats = {
                '统计指标': ['总数', '平均分', '中位数', '标准差', '最小值', '最大值'],
                '数值': [
                    len(scores),
                    np.mean(scores),
                    np.median(scores),
                    np.std(scores),
                    np.min(scores),
                    np.max(scores)
                ]
            }

            fig.add_trace(
                go.Table(
                    header=dict(values=list(stats.keys())),
                    cells=dict(values=list(stats.values()))
                ),
                row=2, col=2
            )

            # 更新布局
            fig.update_layout(
                title_text="评估结果交互式仪表板",
                showlegend=True,
                height=800
            )

            # 保存文件
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.output_dir, f"interactive_dashboard_{timestamp}.html")

            fig.write_html(save_path)

            logger.info(f"交互式仪表板已保存: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"创建交互式仪表板失败: {e}")
            raise

    def create_comprehensive_visualization_report(
        self,
        results: List[EvaluationResult],
        model_results: Optional[Dict[str, List[EvaluationResult]]] = None
    ) -> Dict[str, str]:
        """
        创建综合可视化报告

        Args:
            results: 评估结果列表
            model_results: 模型结果字典（可选）

        Returns:
            生成的图片路径字典
        """
        try:
            generated_files = {}

            # 生成各种图表
            generated_files['score_distribution'] = self.create_score_distribution_plot(results)
            generated_files['dimension_radar'] = self.create_dimension_radar_chart(results)
            generated_files['time_trend'] = self.create_time_trend_plot(results)
            generated_files['correlation_heatmap'] = self.create_correlation_heatmap(results)
            generated_files['interactive_dashboard'] = self.create_interactive_dashboard(results)

            # 如果有模型对比数据，生成对比图
            if model_results:
                generated_files['model_comparison'] = self.create_model_comparison_plot(model_results)

            logger.info(f"综合可视化报告已生成，包含 {len(generated_files)} 个图表")
            return generated_files

        except Exception as e:
            logger.error(f"生成综合可视化报告失败: {e}")
            raise