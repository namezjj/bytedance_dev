"""
示例：导入基准数据集

演示如何导入JSON格式的基准数据集到数据库
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType


async def main():
    """导入基准数据集示例"""
    
    # 初始化数据库
    db = EvaluationDatabase("evaluation_results.db")
    
    # 创建基准数据集管理器
    manager = BenchmarkDatasetManager(db)
    
    # 导入基准数据集
    json_path = "data/benchmark/qa_structured.json"
    
    print(f"正在导入基准数据集: {json_path}")
    
    # 为不同评测类型导入数据集
    
    # 1. LLM评测 - 大模型问答能力评测
    dataset_id_llm = await manager.import_from_json(
        json_path=json_path,
        dataset_name="materials_science_qa_llm",
        evaluation_type=EvaluationType.LLM,
        metadata={
            "domain": "材料科学",
            "language": "中文",
            "created_by": "auto_import"
        }
    )
    
    if dataset_id_llm:
        print(f"\n✓ LLM评测数据集导入成功 (ID: {dataset_id_llm})")
        
        # 获取统计信息
        stats = await manager.get_dataset_statistics(dataset_id_llm)
        print(f"  - 总问题数: {stats['total_questions']}")
        print(f"  - 计算题数: {stats['calculation_questions']}")
        print(f"  - 难度分布: {stats['difficulty_distribution']}")
        print(f"  - 分类统计: {len(stats['category_distribution'])} 个分类")
    
    # 2. RAG评测 - RAG系统检索和问答评测
    dataset_id_rag = await manager.import_from_json(
        json_path=json_path,
        dataset_name="materials_science_qa_rag",
        evaluation_type=EvaluationType.RAG,
        metadata={
            "domain": "材料科学",
            "language": "中文",
            "retrieval_required": True
        }
    )
    
    if dataset_id_rag:
        print(f"\n✓ RAG评测数据集导入成功 (ID: {dataset_id_rag})")
    
    # 3. Agent评测 - Agent推理和执行能力评测
    dataset_id_agent = await manager.import_from_json(
        json_path=json_path,
        dataset_name="materials_science_qa_agent",
        evaluation_type=EvaluationType.AGENT,
        metadata={
            "domain": "材料科学",
            "language": "中文",
            "requires_reasoning": True
        }
    )
    
    if dataset_id_agent:
        print(f"\n✓ Agent评测数据集导入成功 (ID: {dataset_id_agent})")
    
    # 列出所有数据集
    print("\n" + "="*60)
    print("所有基准数据集:")
    print("="*60)
    
    datasets = await manager.list_datasets()
    for ds in datasets:
        print(f"\n[{ds.id}] {ds.name}")
        print(f"  类型: {ds.evaluation_type.value}")
        print(f"  标题: {ds.title}")
        print(f"  问题数: {ds.total_questions}")
    
    # 查询特定类型的数据集
    print("\n" + "="*60)
    print("LLM评测数据集:")
    print("="*60)
    
    llm_datasets = await manager.list_datasets(EvaluationType.LLM)
    for ds in llm_datasets:
        print(f"\n{ds.name}: {ds.total_questions} 个问题")
    
    # 获取问题示例
    if dataset_id_llm:
        print("\n" + "="*60)
        print("问题示例:")
        print("="*60)
        
        # 获取前3个问题
        questions = await manager.get_questions(dataset_id_llm, limit=3)
        for q in questions:
            print(f"\n[问题 {q.question_number}]")
            print(f"分类: {', '.join(q.category)}")
            print(f"难度: {q.difficulty_level}")
            print(f"问题: {q.question[:100]}...")
            print(f"有计算: {'是' if q.has_calculation else '否'}")
        
        # 搜索示例
        print("\n" + "="*60)
        print("搜索示例 (关键词: '晶体'):")
        print("="*60)
        
        search_results = await manager.search_questions(
            dataset_id_llm,
            keyword="晶体"
        )
        print(f"找到 {len(search_results)} 个相关问题")
        for q in search_results[:3]:
            print(f"\n[{q.question_number}] {q.question[:80]}...")
    
    # 关闭数据库
    db.close()
    print("\n导入完成!")


if __name__ == "__main__":
    asyncio.run(main())
