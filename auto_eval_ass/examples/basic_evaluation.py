"""
基础评估示例

演示如何使用评估系统进行单次和批量评估
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.evaluation_agent import EvaluationAgent, EvaluationInput
from data.database import EvaluationDatabase
from config.evaluation_config import ConfigManager, create_config_from_template
from reporting.report_generator import ReportGenerator
from reporting.visualizer import EvaluationVisualizer

async def basic_single_evaluation():
    """基础单次评估示例"""
    print("=" * 50)
    print("基础单次评估示例")
    print("=" * 50)

    try:
        # 1. 初始化配置
        config_manager = ConfigManager()
        config = create_config_from_template('quick_eval')

        # 2. 设置API密钥（实际使用时请从环境变量或配置文件中获取）
        # os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

        # 3. 初始化数据库
        database = EvaluationDatabase("examples/demo_eval.db")

        # 4. 初始化LLM（这里使用模拟实现，实际使用时需要真实的LLM）
        from unittest.mock import Mock
        llm = Mock()
        llm.acall = Mock(return_value={'text': '分数：0.85\n评估：回答质量良好，内容相关且准确。'})

        # 5. 初始化评估Agent
        agent = EvaluationAgent(
            llm=llm,
            config=config,
            database=database
        )

        # 6. 创建评估输入
        evaluation_input = EvaluationInput(
            question="什么是人工智能？",
            context="这是一个关于AI基础概念的问题。",
            ground_truth="人工智能（AI）是指由计算机系统表现出的智能行为。",
            metadata={"model_name": "demo-model", "session_id": "demo-session-1"}
        )

        # 7. 模拟模型回答
        model_response = """
        人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
        旨在创建能够执行通常需要人类智能的任务的系统。
        这包括学习、推理、问题解决、感知和语言理解等能力。
        现代AI技术涵盖了机器学习、深度学习、自然语言处理等多个领域。
        """

        # 8. 执行评估
        result = await agent.evaluate_single(evaluation_input, model_response)

        # 9. 显示结果
        print(f"问题: {evaluation_input.question}")
        print(f"模型回答: {model_response[:100]}...")
        print(f"综合得分: {result.overall_score:.3f}")
        print("维度得分:")
        for dimension, score in result.dimension_scores.items():
            print(f"  {dimension}: {score:.3f}")
        print(f"评估时间: {result.evaluation_timestamp}")

        return result

    except Exception as e:
        print(f"单次评估失败: {e}")
        return None

async def basic_batch_evaluation():
    """基础批量评估示例"""
    print("\n" + "=" * 50)
    print("基础批量评估示例")
    print("=" * 50)

    try:
        # 1. 准备评估数据
        evaluation_data = [
            {
                "question": "什么是机器学习？",
                "context": "基础AI概念问题",
                "model_response": "机器学习是人工智能的一个子领域，通过算法使计算机从数据中学习。"
            },
            {
                "question": "如何提高代码质量？",
                "context": "编程最佳实践",
                "model_response": "提高代码质量可以通过编写清晰的注释、遵循编码规范、进行代码审查等方式实现。"
            },
            {
                "question": "解释什么是云计算？",
                "context": "技术概念解释",
                "model_response": "云计算是通过互联网提供计算服务的模式，包括服务器、存储、数据库等资源。"
            }
        ]

        # 2. 初始化组件（复用之前的配置）
        config_manager = ConfigManager()
        config = create_config_from_template('comprehensive_eval')
        database = EvaluationDatabase("examples/demo_eval.db")

        # 模拟LLM
        from unittest.mock import Mock
        llm = Mock()
        llm.acall = Mock(return_value={'text': '分数：0.78\n评估：回答基本正确，可以更详细一些。'})

        # 3. 初始化评估Agent
        agent = EvaluationAgent(llm=llm, config=config, database=database)

        # 4. 创建评估输入列表
        evaluation_inputs = []
        model_responses = []

        for i, data in enumerate(evaluation_data):
            eval_input = EvaluationInput(
                question=data["question"],
                context=data["context"],
                metadata={"model_name": "demo-model", "sample_id": i}
            )
            evaluation_inputs.append(eval_input)
            model_responses.append(data["model_response"])

        # 5. 执行批量评估
        print(f"开始批量评估 {len(evaluation_inputs)} 个样本...")
        results = await agent.evaluate_batch(evaluation_inputs, model_responses)

        # 6. 显示统计结果
        avg_score = sum(r.overall_score for r in results) / len(results)
        print(f"批量评估完成！")
        print(f"总样本数: {len(results)}")
        print(f"平均得分: {avg_score:.3f}")
        print(f"最高分: {max(r.overall_score for r in results):.3f}")
        print(f"最低分: {min(r.overall_score for r in results):.3f}")

        # 7. 显示详细结果
        print("\n详细结果:")
        for i, result in enumerate(results):
            print(f"{i+1}. 问题: {evaluation_inputs[i].question}")
            print(f"   得分: {result.overall_score:.3f}")
            print(f"   维度: {result.dimension_scores}")

        return results

    except Exception as e:
        print(f"批量评估失败: {e}")
        return []

async def generate_reports_and_visualizations():
    """生成报告和可视化"""
    print("\n" + "=" * 50)
    print("报告和可视化生成示例")
    print("=" * 50)

    try:
        # 1. 初始化数据库和报告生成器
        database = EvaluationDatabase("examples/demo_eval.db")
        report_generator = ReportGenerator(database, "examples/reports")
        visualizer = EvaluationVisualizer("examples/visualizations")

        # 2. 获取评估结果
        results = await database.query_evaluation_results(
            database.QueryFilter(),  # 无过滤条件，获取所有结果
            limit=100
        )

        if not results:
            print("没有找到评估结果，请先运行基础评估示例")
            return

        print(f"找到 {len(results)} 个评估结果")

        # 3. 生成综合报告
        print("生成综合报告...")
        json_report = await report_generator.generate_comprehensive_report(
            filter=None,
            format="json"
        )
        html_report = await report_generator.generate_comprehensive_report(
            filter=None,
            format="html"
        )
        print(f"JSON报告: {json_report}")
        print(f"HTML报告: {html_report}")

        # 4. 生成可视化
        print("生成可视化图表...")
        distribution_chart = visualizer.create_score_distribution_plot(results)
        radar_chart = visualizer.create_dimension_radar_chart(results)
        trend_chart = visualizer.create_time_trend_plot(results)
        correlation_chart = visualizer.create_correlation_heatmap(results)

        print(f"分数分布图: {distribution_chart}")
        print(f"维度雷达图: {radar_chart}")
        print(f"时间趋势图: {trend_chart}")
        print(f"相关性热力图: {correlation_chart}")

        # 5. 生成交互式仪表板
        dashboard = visualizer.create_interactive_dashboard(results)
        print(f"交互式仪表板: {dashboard}")

        print("\n报告和可视化生成完成！")

    except Exception as e:
        print(f"生成报告和可视化失败: {e}")

async def performance_analysis_example():
    """性能分析示例"""
    print("\n" + "=" * 50)
    print("性能分析示例")
    print("=" * 50)

    try:
        # 1. 初始化组件
        database = EvaluationDatabase("examples/demo_eval.db")

        # 2. 获取统计数据
        statistics = await database.get_evaluation_statistics()

        print("评估统计信息:")
        print(f"总评估数: {statistics.get('total_evaluations', 0)}")
        print(f"平均得分: {statistics.get('average_score', 0):.3f}")
        print(f"最高分: {statistics.get('max_score', 0):.3f}")
        print(f"最低分: {statistics.get('min_score', 0):.3f}")
        print(f"标准差: {statistics.get('score_std', 0):.3f}")

        # 3. 模型性能对比
        model_stats = statistics.get('model_statistics', [])
        if model_stats:
            print("\n模型性能对比:")
            for stats in model_stats:
                print(f"模型: {stats['model_name']}")
                print(f"  评估次数: {stats['count']}")
                print(f"  平均分: {stats['avg_score']:.3f}")

        # 4. 时间分布分析
        time_stats = statistics.get('time_distribution', [])
        if time_stats:
            print(f"\n最近30天的评估活动:")
            for stats in time_stats[:5]:  # 显示最近5天
                print(f"日期: {stats['date']}, 评估数: {stats['count']}, 平均分: {stats['avg_score']:.3f}")

    except Exception as e:
        print(f"性能分析失败: {e}")

async def main():
    """主函数，运行所有示例"""
    print("开始运行评估系统示例...")

    # 确保输出目录存在
    Path("examples").mkdir(exist_ok=True)
    Path("examples/reports").mkdir(exist_ok=True)
    Path("examples/visualizations").mkdir(exist_ok=True)

    try:
        # 1. 基础单次评估
        await basic_single_evaluation()

        # 2. 基础批量评估
        await basic_batch_evaluation()

        # 3. 性能分析
        await performance_analysis_example()

        # 4. 生成报告和可视化
        await generate_reports_and_visualizations()

        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
    except Exception as e:
        print(f"\n运行示例时出错: {e}")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())