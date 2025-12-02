"""
完整的Benchmark工作流示例

演示如何：
1. 加载本地数据集
2. 创建benchmark
3. 运行评测
4. 存储结果
5. 查询和分析结果
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.dataset_manager import DatasetManager
from data.benchmark_manager import BenchmarkManager, BenchmarkConfig
from data.evaluation_storage import EvaluationStorage
from data.models import DatasetItem, EvaluationRecord, BenchmarkResult
from core.llm_providers import LLMProviderFactory
from core.evaluation_agent import EvaluationAgent, EvaluationInput
from config.evaluation_config import EvaluationConfig


async def main():
    """主函数"""
    print("=" * 80)
    print("完整Benchmark评测工作流")
    print("=" * 80)

    # ============================================
    # 步骤1: 加载本地数据集
    # ============================================
    print("\n[步骤1] 加载数据集...")

    dataset_manager = DatasetManager()

    # 示例：创建一个简单的测试数据集
    test_dataset_path = project_root / "data" / "test_dataset.json"

    # 如果测试数据集不存在，创建一个
    if not test_dataset_path.exists():
        test_dataset_path.parent.mkdir(exist_ok=True)
        sample_data = {
            "items": [
                {
                    "id": "q1",
                    "question": "什么是人工智能？",
                    "ground_truth": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                    "category": "基础概念",
                    "difficulty_level": "easy"
                },
                {
                    "id": "q2",
                    "question": "请解释什么是机器学习？",
                    "ground_truth": "机器学习是人工智能的一个子领域，通过算法和统计模型使计算机系统能够从数据中学习和改进，而无需明确编程。",
                    "category": "基础概念",
                    "difficulty_level": "medium"
                },
                {
                    "id": "q3",
                    "question": "深度学习与传统机器学习的主要区别是什么？",
                    "ground_truth": "深度学习使用多层神经网络自动学习数据的层次化特征表示，而传统机器学习通常需要手动特征工程。",
                    "category": "技术对比",
                    "difficulty_level": "medium"
                },
                {
                    "id": "q4",
                    "question": "解释Transformer架构在NLP中的重要性",
                    "ground_truth": "Transformer通过自注意力机制实现了并行化处理和长距离依赖建模，彻底改变了NLP领域，成为BERT、GPT等模型的基础架构。",
                    "category": "高级技术",
                    "difficulty_level": "hard"
                },
                {
                    "id": "q5",
                    "question": "什么是提示工程（Prompt Engineering）？",
                    "ground_truth": "提示工程是设计和优化输入提示词的技术，以引导大语言模型生成期望的输出，是使用LLM的关键技能。",
                    "category": "实践应用",
                    "difficulty_level": "medium"
                }
            ]
        }

        with open(test_dataset_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 创建了测试数据集: {test_dataset_path}")

    # 加载数据集
    metadata = dataset_manager.load_dataset_from_file(
        file_path=str(test_dataset_path),
        dataset_name="ai_qa_test",
        description="AI基础问答测试集",
        version="1.0"
    )

    print(f"✓ 数据集已加载: {metadata.name}")
    print(f"  - 总数: {metadata.total_items} 条")
    print(f"  - 类别: {', '.join(metadata.categories)}")
    print(f"  - 难度分布: {metadata.difficulty_distribution}")

    # 获取数据集统计
    stats = dataset_manager.get_dataset_stats("ai_qa_test")
    print(f"\n数据集统计:")
    print(f"  - 平均问题长度: {stats['avg_question_length']} 字符")
    print(f"  - 平均答案长度: {stats['avg_answer_length']} 字符")

    # ============================================
    # 步骤2: 创建Benchmark
    # ============================================
    print("\n[步骤2] 创建Benchmark配置...")

    benchmark_manager = BenchmarkManager()

    benchmark_config = benchmark_manager.create_benchmark(
        name="ai_qa_benchmark_v1",
        dataset_name="ai_qa_test",
        models=["deepseek-chat", "gpt-4"],  # 要评测的模型列表
        evaluator_config={
            "enable_accuracy": True,
            "enable_relevance": True,
            "enable_completeness": True,
            "enable_fluency": True
        },
        sample_size=None,  # 使用全部数据
        parallel_workers=3,
        timeout_per_item=120
    )

    print(f"✓ Benchmark创建成功: {benchmark_config.name}")
    print(f"  - 数据集: {benchmark_config.dataset_name}")
    print(f"  - 模型: {', '.join(benchmark_config.models)}")

    # ============================================
    # 步骤3: 运行评测
    # ============================================
    print("\n[步骤3] 运行评测...")

    # 初始化评估存储
    eval_storage = EvaluationStorage()

    # 创建评估Agent
    try:
        evaluator_llm = LLMProviderFactory.create_evaluator_llm()
        evaluated_llm = LLMProviderFactory.create_evaluated_llm()

        config = EvaluationConfig()
        agent = EvaluationAgent(llm=evaluator_llm, config=config)

        # 获取数据集
        dataset_items = dataset_manager.get_dataset("ai_qa_test")

        print(f"\n开始评测 {len(dataset_items)} 个问题...")

        all_results = []
        dimension_scores_sum = {}
        dimension_count = 0

        for idx, item in enumerate(dataset_items, 1):
            print(f"\n[{idx}/{len(dataset_items)}] 评测中...")
            print(f"问题: {item.question[:50]}...")

            # 使用被评估模型生成回答
            try:
                model_response = await evaluated_llm.acall(
                    prompt=item.question,
                    temperature=0.7,
                    max_tokens=500
                )

                response_text = model_response.text
                print(f"模型回答: {response_text[:100]}...")

                # 创建评估输入
                eval_input = EvaluationInput(
                    question=item.question,
                    ground_truth=item.ground_truth,
                    context=item.context
                )

                # 执行评估
                start_time = datetime.now()
                result = await agent.evaluate_single(eval_input, response_text)
                execution_time = (datetime.now() - start_time).total_seconds()

                print(f"✓ 综合得分: {result.overall_score:.3f}")
                print(f"  维度得分: {', '.join([f'{k}={v:.2f}' for k, v in result.dimension_scores.items()])}")

                # 累计维度分数
                for dim, score in result.dimension_scores.items():
                    dimension_scores_sum[dim] = dimension_scores_sum.get(dim, 0) + score
                dimension_count += 1

                # 转换为EvaluationRecord并保存
                record = EvaluationRecord(
                    session_id=f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    question=item.question,
                    context=item.context,
                    ground_truth=item.ground_truth,
                    model_response=response_text,
                    model_name=evaluated_llm.model_name,
                    overall_score=result.overall_score,
                    dimension_scores=result.dimension_scores,
                    detailed_feedback=result.detailed_feedback,
                    evaluation_timestamp=datetime.now(),
                    metadata={
                        'category': item.category,
                        'difficulty': item.difficulty_level
                    },
                    tags=[item.category, item.difficulty_level]
                )

                # 保存到数据库
                eval_storage.save_evaluation(
                    record,
                    benchmark_name=benchmark_config.name,
                    dataset_name=benchmark_config.dataset_name,
                    execution_time=execution_time
                )

                all_results.append(result)

            except Exception as e:
                print(f"✗ 评测失败: {e}")
                continue

        # 计算平均分数
        if all_results:
            avg_score = sum(r.overall_score for r in all_results) / len(all_results)
            dimension_averages = {
                dim: score_sum / dimension_count
                for dim, score_sum in dimension_scores_sum.items()
            }

            print(f"\n✓ 评测完成！")
            print(f"  - 总数: {len(all_results)}")
            print(f"  - 平均分: {avg_score:.3f}")
            print(f"  - 维度平均: {', '.join([f'{k}={v:.2f}' for k, v in dimension_averages.items()])}")

            # 保存Benchmark结果
            benchmark_result = BenchmarkResult(
                model_name=evaluated_llm.model_name,
                dataset_name=benchmark_config.dataset_name,
                total_samples=len(all_results),
                average_score=avg_score,
                dimension_scores=dimension_averages,
                score_distribution={},  # 可以添加详细的分数分布
                execution_time=sum(r.metadata.get('execution_time', 0) for r in all_results),
                timestamp=datetime.now(),
                metadata={'benchmark_name': benchmark_config.name}
            )

            benchmark_manager.save_benchmark_result(benchmark_result)
            print(f"✓ Benchmark结果已保存")

    except Exception as e:
        print(f"\n✗ 评测初始化失败: {e}")
        print("请检查环境变量配置（EVALUATOR_* 和 EVALUATED_*）")

    # ============================================
    # 步骤4: 查询和分析结果
    # ============================================
    print("\n[步骤4] 查询和分析结果...")

    # 获取统计信息
    stats = eval_storage.get_statistics(
        benchmark_name=benchmark_config.name
    )

    print(f"\n统计信息:")
    print(f"  - 总评测数: {stats['total_evaluations']}")
    print(f"  - 平均分: {stats['average_score']:.3f}")
    print(f"  - 最高分: {stats.get('max_score', 0):.3f}")
    print(f"  - 最低分: {stats.get('min_score', 0):.3f}")
    print(f"  - 维度平均: {stats['dimension_averages']}")

    # 获取排行榜
    leaderboard = benchmark_manager.get_leaderboard(benchmark_config.name)

    print(f"\n排行榜:")
    for entry in leaderboard:
        print(f"  {entry['rank']}. {entry['model_name']}: {entry['average_score']:.3f}")

    # ============================================
    # 步骤5: 导出结果
    # ============================================
    print("\n[步骤5] 导出结果...")

    output_dir = project_root / "evaluation_output"
    output_dir.mkdir(exist_ok=True)

    # 导出为JSON
    json_file = output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    benchmark_manager.export_results(
        benchmark_name=benchmark_config.name,
        output_file=str(json_file),
        format="json"
    )
    print(f"✓ 结果已导出到: {json_file}")

    # 导出为CSV
    csv_file = output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    benchmark_manager.export_results(
        benchmark_name=benchmark_config.name,
        output_file=str(csv_file),
        format="csv"
    )
    print(f"✓ 结果已导出到: {csv_file}")

    # ============================================
    # 清理
    # ============================================
    dataset_manager.close()
    benchmark_manager.close()
    eval_storage.close()

    print("\n" + "=" * 80)
    print("工作流完成！")
    print("=" * 80)


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()

    # 运行主函数
    asyncio.run(main())
