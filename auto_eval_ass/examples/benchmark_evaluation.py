"""
示例：使用基准数据集进行评测

演示如何从数据库加载基准数据集,并对模型进行评测
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType
from core.evaluation_agent import EvaluationAgent, EvaluationInput
from core.llm_providers import LLMProviderFactory


async def evaluate_on_benchmark(
    dataset_name: str,
    model_name: str,
    max_questions: int = 5
):
    """
    在基准数据集上评测模型
    
    Args:
        dataset_name: 数据集名称
        model_name: 要评测的模型名称
        max_questions: 最多评测多少个问题
    """
    
    # 初始化数据库和管理器
    db = EvaluationDatabase("evaluation_results.db")
    manager = BenchmarkDatasetManager(db)
    
    # 获取数据集
    dataset = await manager.get_dataset_by_name(dataset_name)
    
    if not dataset:
        print(f"错误: 数据集 '{dataset_name}' 不存在")
        print("\n可用的数据集:")
        datasets = await manager.list_datasets()
        for ds in datasets:
            print(f"  - {ds.name} ({ds.evaluation_type.value})")
        db.close()
        return
    
    print(f"使用数据集: {dataset.title}")
    print(f"评测类型: {dataset.evaluation_type.value}")
    print(f"总问题数: {dataset.total_questions}")
    print(f"评测模型: {model_name}")
    print("="*60)
    
    # 创建评估代理
    evaluator_llm = LLMProviderFactory.create_evaluator_llm()
    evaluated_llm = LLMProviderFactory.create(
        provider_name="deepseek",  # 或其他模型
        api_key="your-api-key",
        model_name=model_name
    )
    
    agent = EvaluationAgent(
        llm=evaluator_llm,
        evaluated_llm=evaluated_llm
    )
    
    # 获取问题
    questions = await manager.get_questions(dataset.id, limit=max_questions)
    
    results = []
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] 评测问题 {q.question_number}")
        print(f"分类: {', '.join(q.category)}")
        print(f"问题: {q.question[:100]}...")
        
        # 让被评测模型回答问题
        response = await evaluated_llm.acall(q.question)
        
        # 创建评估输入
        eval_input = EvaluationInput(
            question=q.question,
            ground_truth=q.answer,  # 使用标准答案作为参考
            metadata={
                'dataset_id': dataset.id,
                'dataset_name': dataset.name,
                'question_number': q.question_number,
                'category': q.category,
                'difficulty': q.difficulty_level,
                'has_calculation': q.has_calculation
            }
        )
        
        # 执行评估
        result = await agent.evaluate_single(eval_input, response.text)
        
        print(f"  模型回答: {response.text[:100]}...")
        print(f"  总分: {result.overall_score:.2f}")
        print(f"  维度分数: {result.dimension_scores}")
        
        results.append(result)
        
        # 保存评估结果到数据库
        await db.save_evaluation_result(result)
    
    # 统计结果
    print("\n" + "="*60)
    print("评测总结:")
    print("="*60)
    
    avg_score = sum(r.overall_score for r in results) / len(results)
    print(f"平均分数: {avg_score:.2f}")
    
    # 按难度统计
    by_difficulty = {}
    for q, r in zip(questions, results):
        diff = q.difficulty_level
        if diff not in by_difficulty:
            by_difficulty[diff] = []
        by_difficulty[diff].append(r.overall_score)
    
    print("\n按难度统计:")
    for diff, scores in by_difficulty.items():
        avg = sum(scores) / len(scores)
        print(f"  {diff}: {avg:.2f} ({len(scores)} 题)")
    
    # 按是否有计算统计
    calc_scores = [r.overall_score for q, r in zip(questions, results) if q.has_calculation]
    non_calc_scores = [r.overall_score for q, r in zip(questions, results) if not q.has_calculation]
    
    if calc_scores:
        print(f"\n计算题平均分: {sum(calc_scores)/len(calc_scores):.2f}")
    if non_calc_scores:
        print(f"非计算题平均分: {sum(non_calc_scores)/len(non_calc_scores):.2f}")
    
    db.close()


async def main():
    """主函数"""
    
    # 示例1: LLM评测
    print("\n" + "="*60)
    print("示例 1: LLM 问答能力评测")
    print("="*60)
    
    await evaluate_on_benchmark(
        dataset_name="materials_science_qa_llm",
        model_name="deepseek-chat",
        max_questions=3
    )
    
    # 示例2: RAG评测
    print("\n\n" + "="*60)
    print("示例 2: RAG 系统评测")
    print("="*60)
    
    await evaluate_on_benchmark(
        dataset_name="materials_science_qa_rag",
        model_name="deepseek-chat",
        max_questions=3
    )


if __name__ == "__main__":
    asyncio.run(main())
