"""
测试DeepSeek回答问题功能

用于验证RAG系统的DeepSeek回答部分是否正常工作
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.rag_system import RAGSystem


async def test_single_question():
    """测试单个问题"""
    print("="*80)
    print("测试1: DeepSeek回答单个问题")
    print("="*80)
    
    # 创建RAG系统（使用DeepSeek）
    rag = RAGSystem()
    
    # 测试问题
    question = "什么是人工智能？请用简洁的语言解释。"
    
    print(f"\n📝 问题: {question}\n")
    print("🤖 DeepSeek正在生成回答...\n")
    
    # 生成回答
    output = await rag.generate_answer(question)
    
    # 显示结果
    print("="*80)
    print("✅ 回答生成成功！")
    print("="*80)
    print(f"\n💬 DeepSeek的回答:\n")
    print(output.answer)
    print("\n" + "="*80)
    print("📊 响应信息:")
    print("="*80)
    print(f"  ⏱️  响应时间: {output.response_time:.2f}秒")
    print(f"  🔢 Token使用:")
    print(f"     - 输入tokens: {output.token_usage['prompt_tokens']}")
    print(f"     - 输出tokens: {output.token_usage['completion_tokens']}")
    print(f"     - 总计tokens: {output.token_usage['total_tokens']}")
    print(f"  🏷️  模型信息:")
    print(f"     - 提供商: {output.metadata['provider']}")
    print(f"     - 模型: {output.metadata['model']}")
    print(f"  ⚙️  生成参数:")
    print(f"     - 温度: {output.metadata['temperature']}")
    print(f"     - 最大tokens: {output.metadata['max_tokens']}")


async def test_multiple_questions():
    """测试多个问题"""
    print("\n\n" + "="*80)
    print("测试2: DeepSeek回答多个问题")
    print("="*80)
    
    rag = RAGSystem()
    
    questions = [
        "什么是机器学习？",
        "解释一下深度学习。",
        "Python为什么流行？"
    ]
    
    print(f"\n准备测试 {len(questions)} 个问题...\n")
    
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] 问题: {question}")
        
        output = await rag.generate_answer(question, max_tokens=200)
        
        print(f"    回答: {output.answer[:150]}...")
        print(f"    用时: {output.response_time:.2f}秒")
        print(f"    Tokens: {output.token_usage['total_tokens']}")
        print()


async def test_with_context():
    """测试带上下文的回答"""
    print("\n" + "="*80)
    print("测试3: DeepSeek基于上下文回答（模拟RAG）")
    print("="*80)
    
    rag = RAGSystem()
    
    question = "RAG系统有什么优势？"
    
    # 模拟检索到的上下文
    context = """
    RAG（检索增强生成）系统结合了信息检索和文本生成技术。
    主要优势包括：
    1. 减少幻觉：通过检索真实文档，降低模型生成虚假信息的概率
    2. 知识更新：无需重新训练，只需更新知识库即可
    3. 可追溯性：回答有明确的信息来源
    4. 领域专业性：可以针对特定领域构建专业知识库
    """
    
    print(f"\n📝 问题: {question}")
    print(f"\n📚 检索到的上下文:\n{context}")
    print("\n🤖 DeepSeek基于上下文生成回答...\n")
    
    output = await rag.generate_answer(
        question=question,
        context=context,
        use_context=True
    )
    
    print("="*80)
    print("✅ 基于上下文的回答:")
    print("="*80)
    print(f"\n{output.answer}\n")
    print(f"⏱️  用时: {output.response_time:.2f}秒")


async def main():
    """主测试函数"""
    print("\n🚀 DeepSeek回答功能测试")
    print("="*80)
    
    try:
        await test_single_question()
        await test_multiple_questions()
        await test_with_context()
        
        print("\n" + "="*80)
        print("🎉 所有测试完成！DeepSeek回答功能正常")
        print("="*80)
        
        print("\n💡 下一步:")
        print("  ✓ DeepSeek回答问题功能已验证")
        print("  → 接下来可以添加Doubao评估功能")
        print("  → 运行 python examples/rag_system_demo.py 查看更多示例")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

