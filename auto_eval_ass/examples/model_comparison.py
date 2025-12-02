"""
模型对比评估示例

演示如何对比不同模型的性能，并进行基准测试
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.evaluation_agent import EvaluationAgent, EvaluationInput
from data.database import EvaluationDatabase, QueryFilter
from config.evaluation_config import ConfigManager, create_config_from_template
from reporting.report_generator import ReportGenerator
from reporting.visualizer import EvaluationVisualizer

class MockModelProvider:
    """模拟模型提供者"""

    def __init__(self, model_name: str, characteristics: Dict[str, Any]):
        """
        初始化模拟模型

        Args:
            model_name: 模型名称
            characteristics: 模型特征
        """
        self.model_name = model_name
        self.characteristics = characteristics

    def generate_response(self, question: str, context: str = None) -> str:
        """
        生成回答

        Args:
            question: 问题
            context: 上下文（可选）

        Returns:
            生成的回答
        """
        # 根据模型特征生成不同质量的回答
        base_quality = self.characteristics.get('base_quality', 0.7)
        accuracy_boost = self.characteristics.get('accuracy_boost', 0.0)
        creativity = self.characteristics.get('creativity', 0.5)
        verbosity = self.characteristics.get('verbosity', 1.0)

        # 基础回答内容
        response_parts = [
            f"根据{self.model_name}模型的分析，",
        ]

        # 根据准确性调整内容
        if base_quality + accuracy_boost > 0.8:
            response_parts.append("这是一个很好的问题。")
            response_parts.append("基于我的知识库，我可以为您提供详细的解释。")
        elif base_quality > 0.6:
            response_parts.append("这个问题值得探讨。")
        else:
            response_parts.append("让我想想这个问题。")

        # 根据创造性添加内容
        if creativity > 0.7:
            response_parts.append("从创新的角度来看，")
            response_parts.append("我们可以考虑多个不同的观点。")
        elif creativity > 0.4:
            response_parts.append("通常来说，")
        else:
            response_parts.append("简单来说，")

        # 添加具体内容
        if "人工智能" in question or "AI" in question:
            response_parts.extend([
                "人工智能（AI）是指由计算机系统表现出的智能行为。",
                "它包括学习、推理、问题解决、感知和语言理解等能力。",
                "现代AI技术涵盖了机器学习、深度学习、自然语言处理等多个领域。"
            ])
        elif "机器学习" in question:
            response_parts.extend([
                "机器学习是人工智能的一个子领域。",
                "它使计算机能够在没有明确编程的情况下学习和改进。",
                "常见的机器学习类型包括监督学习、无监督学习和强化学习。"
            ])
        else:
            # 通用回答
            response_parts.extend([
                "这涉及到相关的技术知识和实践经验。",
                "需要考虑多个因素的影响和相互作用。",
                "建议进一步深入研究相关领域的最新发展。"
            ])

        # 根据冗长度调整回答长度
        target_length = int(len(" ".join(response_parts)) * verbosity)
        current_response = " ".join(response_parts)

        if len(current_response) < target_length:
            # 添加更多内容
            additional_content = [
                "这个领域正在快速发展。",
                "新技术和方法不断涌现。",
                "实际应用中需要根据具体情况选择合适的方案。"
            ]
            current_response += " " + " ".join(additional_content)

        return current_response.strip()

async def model_comparison_demo():
    """模型对比评估演示"""
    print("=" * 60)
    print("模型对比评估演示")
    print("=" * 60)

    try:
        # 1. 定义要对比的模型
        models = {
            "gpt-3.5-turbo": MockModelProvider("gpt-3.5-turbo", {
                'base_quality': 0.75,
                'accuracy_boost': 0.0,
                'creativity': 0.6,
                'verbosity': 1.2,
                'cost': 0.002
            }),
            "gpt-4": MockModelProvider("gpt-4", {
                'base_quality': 0.85,
                'accuracy_boost': 0.1,
                'creativity': 0.8,
                'verbosity': 1.5,
                'cost': 0.03
            }),
            "claude-3-sonnet": MockModelProvider("claude-3-sonnet", {
                'base_quality': 0.82,
                'accuracy_boost': 0.05,
                'creativity': 0.7,
                'verbosity': 1.3,
                'cost': 0.015
            }),
            "claude-3-haiku": MockModelProvider("claude-3-haiku", {
                'base_quality': 0.70,
                'accuracy_boost': -0.05,
                'creativity': 0.4,
                'verbosity': 0.8,
                'cost': 0.00025
            })
        }

        # 2. 准备测试数据集
        test_dataset = [
            {
                "id": "q1",
                "question": "什么是人工智能？请简要解释其核心概念。",
                "category": "basic_concept",
                "difficulty": "easy",
                "expected_length": "medium"
            },
            {
                "id": "q2",
                "question": "比较监督学习和无监督学习的主要区别和应用场景。",
                "category": "comparison",
                "difficulty": "medium",
                "expected_length": "long"
            },
            {
                "id": "q3",
                "question": "深度学习在计算机视觉中有哪些典型应用？",
                "category": "application",
                "difficulty": "medium",
                "expected_length": "medium"
            },
            {
                "id": "q4",
                "question": "如何评估机器学习模型的性能？请介绍主要的评估指标。",
                "category": "methodology",
                "difficulty": "hard",
                "expected_length": "long"
            },
            {
                "id": "q5",
                "question": "自然语言处理面临的主要挑战是什么？",
                "category": "challenge",
                "difficulty": "medium",
                "expected_length": "medium"
            },
            {
                "id": "q6",
                "question": "简述强化学习的基本原理和应用实例。",
                "category": "basic_concept",
                "difficulty": "medium",
                "expected_length": "medium"
            },
            {
                "id": "q7",
                "question": "数据预处理在机器学习中的重要性及常用方法。",
                "category": "methodology",
                "difficulty": "hard",
                "expected_length": "long"
            },
            {
                "id": "q8",
                "question": "什么是过拟合？如何避免过拟合问题？",
                "category": "problem",
                "difficulty": "medium",
                "expected_length": "medium"
            }
        ]

        # 3. 初始化评估系统
        config_manager = ConfigManager()
        config = create_config_from_template('comprehensive_eval')
        database = EvaluationDatabase("examples/model_comparison.db")

        # 模拟LLM评估器
        from unittest.mock import Mock
        llm = Mock()

        def mock_evaluation_response(prompt, model_name=None):
            """根据模型名称和提示词生成评估响应"""
            # 基础分数基于模型特征
            base_scores = {
                "gpt-3.5-turbo": 0.75,
                "gpt-4": 0.85,
                "claude-3-sonnet": 0.82,
                "claude-3-haiku": 0.70
            }

            base_score = base_scores.get(model_name, 0.75)

            # 添加随机变化
            import random
            variation = random.uniform(-0.1, 0.1)
            final_score = max(0.0, min(1.0, base_score + variation))

            # 生成维度分数
            dimension_scores = {
                "accuracy": final_score - 0.05,
                "relevance": final_score - 0.03,
                "completeness": final_score - 0.02,
                "fluency": final_score + 0.02
            }

            # 构建评估反馈
            feedback = f"分数：{final_score:.3f}\n评估："
            if final_score > 0.8:
                feedback += "回答质量优秀，内容准确全面，表达清晰流畅。"
            elif final_score > 0.6:
                feedback += "回答质量良好，基本准确，可以进一步改进。"
            else:
                feedback += "回答质量一般，需要在准确性和完整性方面进行改进。"

            return {'text': feedback}

        llm.acall = Mock(side_effect=lambda prompt: mock_evaluation_response(prompt, getattr(mock_evaluation_response, 'current_model', None)))

        # 4. 执行模型对比评估
        all_results = {}

        for model_name, model_provider in models.items():
            print(f"\n评估模型: {model_name}")
            print("-" * 40)

            # 设置当前模型
            mock_evaluation_response.current_model = model_name

            # 初始化评估Agent
            agent = EvaluationAgent(llm=llm, config=config, database=database)

            model_results = []

            for i, test_case in enumerate(test_dataset):
                print(f"  处理问题 {i+1}/{len(test_dataset)}: {test_case['question'][:50]}...")

                # 生成回答
                response = model_provider.generate_response(
                    test_case['question'],
                    test_case.get('context')
                )

                # 创建评估输入
                eval_input = EvaluationInput(
                    question=test_case['question'],
                    context=test_case.get('context'),
                    metadata={
                        'model_name': model_name,
                        'question_id': test_case['id'],
                        'category': test_case['category'],
                        'difficulty': test_case['difficulty']
                    }
                )

                # 执行评估
                result = await agent.evaluate_single(eval_input, response)
                model_results.append(result)

                print(f"    得分: {result.overall_score:.3f}")

            # 计算模型统计信息
            avg_score = sum(r.overall_score for r in model_results) / len(model_results)
            print(f"  {model_name} 平均得分: {avg_score:.3f}")

            all_results[model_name] = model_results

        # 5. 生成对比分析报告
        print("\n" + "=" * 60)
        print("模型对比分析报告")
        print("=" * 60)

        # 计算各模型的详细统计
        model_stats = {}
        for model_name, results in all_results.items():
            scores = [r.overall_score for r in results]
            dimension_scores = {}

            for result in results:
                for dimension, score in result.dimension_scores.items():
                    if dimension not in dimension_scores:
                        dimension_scores[dimension] = []
                    dimension_scores[dimension].append(score)

            model_stats[model_name] = {
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'std_score': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))**0.5,
                'dimension_averages': {
                    dim: sum(scores) / len(scores) for dim, scores in dimension_scores.items()
                },
                'total_cost': len(results) * models[model_name].characteristics['cost']
            }

        # 按平均分排序
        sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['avg_score'], reverse=True)

        print("\n模型性能排名:")
        for i, (model_name, stats) in enumerate(sorted_models, 1):
            print(f"{i}. {model_name}")
            print(f"   平均得分: {stats['avg_score']:.3f}")
            print(f"   得分范围: {stats['min_score']:.3f} - {stats['max_score']:.3f}")
            print(f"   标准差: {stats['std_score']:.3f}")
            print(f"   评估成本: ${stats['total_cost']:.4f}")
            print(f"   维度得分:")
            for dimension, avg_score in stats['dimension_averages'].items():
                print(f"     {dimension}: {avg_score:.3f}")
            print()

        # 6. 生成可视化对比
        print("生成对比可视化...")
        visualizer = EvaluationVisualizer("examples/model_comparison_visuals")

        comparison_chart = visualizer.create_model_comparison_plot(all_results)
        print(f"模型对比图: {comparison_chart}")

        # 7. 生成详细报告
        print("\n生成详细对比报告...")
        report_generator = ReportGenerator(database, "examples/model_comparison_reports")

        # 使用第一个模型的结果生成综合报告
        if all_results:
            # 生成HTML报告
            all_model_results = []
            for results in all_results.values():
                all_model_results.extend(results)

            html_report = await report_generator.generate_comprehensive_report(
                filter=None,
                format="html"
            )
            print(f"综合报告: {html_report}")

        # 8. 成本效益分析
        print("\n" + "=" * 40)
        print("成本效益分析")
        print("=" * 40)

        print(f"{'模型':<15} {'平均得分':<10} {'成本/评估':<10} {'成本效益比':<12} {'推荐度':<10}")
        print("-" * 60)

        for model_name, stats in model_stats.items():
            cost_per_eval = models[model_name].characteristics['cost']
            cost_benefit = stats['avg_score'] / (cost_per_eval + 0.0001)  # 避免除零

            # 计算推荐度（考虑性能和成本）
            if stats['avg_score'] > 0.8 and cost_per_eval < 0.02:
                recommendation = "高"
            elif stats['avg_score'] > 0.7:
                recommendation = "中"
            else:
                recommendation = "低"

            print(f"{model_name:<15} {stats['avg_score']:<10.3f} ${cost_per_eval:<9.4f} {cost_benefit:<12.1f} {recommendation:<10}")

        # 9. 保存对比结果
        comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'models': list(models.keys()),
            'test_dataset_size': len(test_dataset),
            'model_statistics': {
                name: {
                    'avg_score': stats['avg_score'],
                    'dimension_scores': stats['dimension_averages'],
                    'cost': stats['total_cost'],
                    'characteristics': models[name].characteristics
                }
                for name, stats in model_stats.items()
            },
            'ranking': [model[0] for model in sorted_models]
        }

        # 保存到文件
        results_file = Path("examples/model_comparison_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_results, f, ensure_ascii=False, indent=2)

        print(f"\n对比结果已保存到: {results_file}")

        return all_results, model_stats

    except Exception as e:
        print(f"模型对比评估失败: {e}")
        import traceback
        traceback.print_exc()
        return {}, {}

async def main():
    """主函数"""
    print("开始模型对比评估演示...")

    # 确保输出目录存在
    Path("examples").mkdir(exist_ok=True)
    Path("examples/model_comparison_reports").mkdir(exist_ok=True)
    Path("examples/model_comparison_visuals").mkdir(exist_ok=True)

    try:
        # 运行模型对比评估
        await model_comparison_demo()

        print("\n" + "=" * 60)
        print("模型对比评估演示完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
    except Exception as e:
        print(f"\n运行模型对比评估时出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())