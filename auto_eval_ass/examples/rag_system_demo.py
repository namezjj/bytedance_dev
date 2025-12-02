"""
RAG系统演示

演示如何使用DeepSeek作为RAG系统回答问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.rag_system import RAGSystem, MockRAGSystem, RAGInput, RAGOutput


async def demo_basic_rag():
    """演示基础RAG功能"""
    print("="*80)
    print("演示1: 基础RAG功能（DeepSeek直接回答）")
    print("="*80)
    
    # 创建RAG系统（使用DeepSeek）
    rag = RAGSystem(
        temperature=0.7,
        max_tokens=500
    )
    
    # 测试问题
    question = "什么是人工智能？请简要介绍。"
    
    print(f"\n问题: {question}\n")
    
    # 生成回答
    output = await rag.generate_answer(question)
    
    # 显示结果
    print(f"DeepSeek回答:\n{output.answer}\n")
    print(f"响应信息:")
    print(f"  - 响应时间: {output.response_time:.2f}秒")
    print(f"  - Token使用: 输入{output.token_usage['prompt_tokens']}, "
          f"输出{output.token_usage['completion_tokens']}, "
          f"总计{output.token_usage['total_tokens']}")
    print(f"  - 模型: {output.metadata['model']}")
    print(f"  - 提供商: {output.metadata['provider']}")


async def demo_rag_with_context():
    """演示带上下文的RAG"""
    print("\n" + "="*80)
    print("演示2: 带上下文的RAG（模拟检索后的回答）")
    print("="*80)
    
    # 创建RAG系统
    rag = RAGSystem(
        temperature=0.7,
        max_tokens=500
    )
    
    # 问题
    question = "机器学习的主要类型有哪些？"
    
    # 模拟检索到的上下文
    context = """
    机器学习是人工智能的一个重要分支。根据学习方式的不同，机器学习主要分为以下几类：
    
    1. 监督学习(Supervised Learning)：使用标注数据进行训练，学习输入到输出的映射关系。
       常见算法包括：线性回归、逻辑回归、决策树、随机森林、支持向量机等。
    
    2. 无监督学习(Unsupervised Learning)：从未标注的数据中发现隐藏的模式和结构。
       常见算法包括：K-means聚类、层次聚类、主成分分析(PCA)、自编码器等。
    
    3. 强化学习(Reinforcement Learning)：通过与环境交互，学习如何采取行动以最大化累积奖励。
       典型应用：游戏AI、机器人控制、自动驾驶等。
    
    4. 半监督学习(Semi-supervised Learning)：结合少量标注数据和大量未标注数据进行学习。
    
    5. 迁移学习(Transfer Learning)：将在一个任务上学到的知识应用到另一个相关任务上。
    """
    
    print(f"\n问题: {question}")
    print(f"\n检索到的上下文:\n{context[:200]}...\n")
    
    # 使用上下文生成回答
    output = await rag.generate_answer(
        question=question,
        context=context,
        use_context=True
    )
    
    print(f"DeepSeek回答（基于上下文）:\n{output.answer}\n")
    print(f"响应时间: {output.response_time:.2f}秒")


async def demo_mock_rag_with_auto_retrieve():
    """演示带自动检索的Mock RAG"""
    print("\n" + "="*80)
    print("演示3: Mock RAG系统（带自动检索）")
    print("="*80)
    
    # 创建Mock RAG系统（内置知识库）
    mock_rag = MockRAGSystem(
        temperature=0.7,
        max_tokens=500
    )
    
    # 测试问题列表
    questions = [
        "什么是深度学习？",
        "自然语言处理主要应用在哪些领域？",
        "云计算的服务模式有哪些？",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] 问题: {question}")
        
        # 自动检索并生成回答
        output = await mock_rag.generate_answer(
            question=question,
            auto_retrieve=True,
            use_context=True
        )
        
        print(f"\n检索到的上下文:")
        if output.context_used:
            print(f"{output.context_used[:150]}...")
        else:
            print("无")
        
        print(f"\nDeepSeek回答:")
        print(f"{output.answer}")
        
        print(f"\n响应时间: {output.response_time:.2f}秒")
        print("-" * 80)


async def demo_batch_questions():
    """演示批量问题处理"""
    print("\n" + "="*80)
    print("演示4: 批量问题处理")
    print("="*80)
    
    # 创建RAG系统
    rag = RAGSystem(temperature=0.7, max_tokens=300)
    
    # 批量问题
    questions = [
        "什么是Python？",
        "什么是Docker？",
        "什么是Git？",
        "什么是RESTful API？",
    ]
    
    print(f"\n处理 {len(questions)} 个问题...\n")
    
    # 批量生成回答
    import time
    start_time = time.time()
    
    outputs = await rag.batch_generate(questions)
    
    total_time = time.time() - start_time
    
    # 显示结果
    for i, (question, output) in enumerate(zip(questions, outputs), 1):
        print(f"[{i}] {question}")
        print(f"    回答: {output.answer[:100]}...")
        print(f"    用时: {output.response_time:.2f}秒")
        print()
    
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均每题: {total_time/len(questions):.2f}秒")


async def demo_compare_with_without_context():
    """演示有无上下文的对比"""
    print("\n" + "="*80)
    print("演示5: 对比有无上下文的回答质量")
    print("="*80)
    
    rag = RAGSystem(temperature=0.7, max_tokens=400)
    
    question = "RAG系统的工作原理是什么？"
    
    context = """
    RAG(Retrieval-Augmented Generation)检索增强生成是一种结合了信息检索和文本生成的技术。
    
    工作流程：
    1. 检索阶段：根据用户查询，从知识库中检索相关文档或段落
    2. 增强阶段：将检索到的信息作为上下文，与用户问题一起输入到语言模型
    3. 生成阶段：语言模型基于检索到的上下文生成更准确、更有依据的回答
    
    优势：
    - 减少模型幻觉（生成虚假信息）
    - 提供可追溯的信息来源
    - 能够回答特定领域的专业问题
    - 无需重新训练模型即可更新知识
    """
    
    # 无上下文回答
    print(f"\n问题: {question}")
    print("\n【场景1：无上下文 - 直接回答】")
    output1 = await rag.generate_answer(question, use_context=False)
    print(f"{output1.answer}\n")
    
    # 有上下文回答
    print("【场景2：有上下文 - 基于检索信息回答】")
    output2 = await rag.generate_answer(question, context=context, use_context=True)
    print(f"{output2.answer}\n")
    
    print(f"对比:")
    print(f"  无上下文用时: {output1.response_time:.2f}秒, Tokens: {output1.token_usage['total_tokens']}")
    print(f"  有上下文用时: {output2.response_time:.2f}秒, Tokens: {output2.token_usage['total_tokens']}")


async def main():
    """主函数"""
    print("\n🤖 RAG系统演示 - 使用DeepSeek")
    print("="*80)
    
    try:
        # 运行各个演示
        await demo_basic_rag()
        await demo_rag_with_context()
        await demo_mock_rag_with_auto_retrieve()
        await demo_batch_questions()
        await demo_compare_with_without_context()
        
        print("\n" + "="*80)
        print("✅ 所有演示完成！")
        print("="*80)
        
        print("\n💡 下一步：")
        print("  1. 查看 core/rag_system.py 了解实现细节")
        print("  2. 运行 python examples/rag_evaluation.py 查看评估功能")
        print("  3. 自定义你的RAG系统和知识库")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

