"""
基准数据集系统测试脚本

快速验证基准数据集系统是否正常工作
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType


async def test_benchmark_system():
    """测试基准数据集系统"""
    
    print("="*60)
    print("基准数据集系统测试")
    print("="*60)
    
    # 初始化
    print("\n[1/6] 初始化数据库...")
    db = EvaluationDatabase("test_benchmark.db")
    manager = BenchmarkDatasetManager(db)
    print("✓ 数据库初始化成功")
    
    # 导入数据集
    print("\n[2/6] 导入测试数据集...")
    json_path = "data/benchmark/qa_structured.json"
    
    dataset_id = await manager.import_from_json(
        json_path=json_path,
        dataset_name="test_materials_science",
        evaluation_type=EvaluationType.LLM,
        metadata={"test": True}
    )
    
    if dataset_id:
        print(f"✓ 数据集导入成功 (ID: {dataset_id})")
    else:
        print("✗ 数据集导入失败")
        return
    
    # 查询数据集
    print("\n[3/6] 查询数据集...")
    dataset = await manager.get_dataset_by_name("test_materials_science")
    if dataset:
        print(f"✓ 数据集查询成功")
        print(f"  - 名称: {dataset.name}")
        print(f"  - 标题: {dataset.title}")
        print(f"  - 类型: {dataset.evaluation_type.value}")
        print(f"  - 问题数: {dataset.total_questions}")
    else:
        print("✗ 数据集查询失败")
        return
    
    # 获取问题
    print("\n[4/6] 获取问题...")
    questions = await manager.get_questions(dataset.id, limit=5)
    if questions:
        print(f"✓ 成功获取 {len(questions)} 个问题")
        for i, q in enumerate(questions[:3], 1):
            print(f"\n  问题 {i}:")
            print(f"    编号: {q.question_number}")
            print(f"    分类: {', '.join(q.category)}")
            print(f"    难度: {q.difficulty_level}")
            print(f"    问题: {q.question[:60]}...")
    else:
        print("✗ 获取问题失败")
        return
    
    # 统计信息
    print("\n[5/6] 获取统计信息...")
    stats = await manager.get_dataset_statistics(dataset.id)
    if stats:
        print("✓ 统计信息:")
        print(f"  - 总问题数: {stats['total_questions']}")
        print(f"  - 计算题数: {stats['calculation_questions']}")
        print(f"  - 难度分布: {stats['difficulty_distribution']}")
        print(f"  - 分类数量: {len(stats['category_distribution'])}")
    else:
        print("✗ 获取统计信息失败")
    
    # 搜索测试
    print("\n[6/6] 测试搜索功能...")
    search_results = await manager.search_questions(
        dataset.id,
        keyword="晶体"
    )
    print(f"✓ 搜索到 {len(search_results)} 个包含'晶体'的问题")
    
    # 清理
    print("\n清理测试数据...")
    await manager.delete_dataset(dataset.id)
    db.close()
    
    # 删除测试数据库
    import os
    if os.path.exists("test_benchmark.db"):
        os.remove("test_benchmark.db")
    
    print("\n" + "="*60)
    print("✓ 所有测试通过!")
    print("="*60)
    print("\n基准数据集系统工作正常,可以开始使用。")
    print("\n下一步:")
    print("1. 运行 'python examples/import_benchmark.py' 导入数据集")
    print("2. 查看 'BENCHMARK_README.md' 了解详细用法")
    print("3. 查看 'docs/BENCHMARK_GUIDE.md' 获取完整文档")


if __name__ == "__main__":
    try:
        asyncio.run(test_benchmark_system())
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
