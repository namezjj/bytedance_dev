"""
使用Doubao和DeepSeek进行评估的示例

演示如何使用Doubao作为裁判LLM，评估DeepSeek的回答质量
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from core.llm_providers import LLMProviderFactory


async def test_llm_providers():
    """测试LLM提供商的基本功能"""
    print("="*80)
    print("测试LLM提供商")
    print("="*80)
    
    # 1. 测试Doubao（裁判LLM）
    print("\n1. 测试Doubao（裁判LLM）...")
    try:
        evaluator_llm = LLMProviderFactory.create_evaluator_llm()
        print(f"   提供商: {evaluator_llm.get_provider_name()}")
        print(f"   模型: {evaluator_llm.model_name}")
        
        prompt = "请简单介绍一下人工智能。"
        response = await evaluator_llm.acall(prompt, temperature=0.7, max_tokens=200)
        
        print(f"   响应: {response.text[:100]}...")
        print(f"   延迟: {response.latency:.2f}秒")
        print(f"   Token使用: {response.usage}")
        print("   ✓ Doubao测试成功")
        
    except Exception as e:
        print(f"   ✗ Doubao测试失败: {e}")
        return
    
    # 2. 测试DeepSeek（参评LLM）
    print("\n2. 测试DeepSeek（参评LLM）...")
    try:
        evaluated_llm = LLMProviderFactory.create_evaluated_llm()
        print(f"   提供商: {evaluated_llm.get_provider_name()}")
        print(f"   模型: {evaluated_llm.model_name}")
        
        prompt = "请简单介绍一下人工智能。"
        response = await evaluated_llm.acall(prompt, temperature=0.7, max_tokens=200)
        
        print(f"   响应: {response.text[:100]}...")
        print(f"   延迟: {response.latency:.2f}秒")
        print(f"   Token使用: {response.usage}")
        print("   ✓ DeepSeek测试成功")
        
    except Exception as e:
        print(f"   ✗ DeepSeek测试失败: {e}")
        return
    
    print("\n✓ 所有测试通过！")


async def evaluation_demo():
    """演示评估流程"""
    print("\n" + "="*80)
    print("评估流程演示")
    print("="*80)
    
    # 创建LLM实例
    evaluator_llm = LLMProviderFactory.create_evaluator_llm()
    evaluated_llm = LLMProviderFactory.create_evaluated_llm()
    
    # 测试问题
    test_question = "什么是机器学习？它与深度学习有什么区别？"
    
    # 1. 获取DeepSeek的回答
    print(f"\n问题: {test_question}")
    print("\n步骤1: 获取DeepSeek的回答...")
    
    model_response = await evaluated_llm.acall(
        test_question,
        temperature=0.7,
        max_tokens=500
    )
    
    print(f"DeepSeek回答:\n{model_response.text}\n")
    print(f"响应时间: {model_response.latency:.2f}秒")
    print(f"Token使用: 输入{model_response.usage['prompt_tokens']}, "
          f"输出{model_response.usage['completion_tokens']}")
    
    # 2. 使用Doubao评估回答质量
    print("\n步骤2: 使用Doubao评估回答质量...")
    
    evaluation_prompt = f"""请评估以下回答的质量。

问题: {test_question}

回答: {model_response.text}

请从以下维度进行评估（每个维度给出1-10分）：
1. 准确性：回答是否准确、有事实错误
2. 相关性：回答是否切题、与问题相关
3. 完整性：回答是否完整、是否遗漏重要信息
4. 流畅性：语言表达是否流畅、易懂

请按照以下格式回复：
准确性: X/10
相关性: X/10
完整性: X/10
流畅性: X/10
综合评价: [简要评价]
"""
    
    evaluation_result = await evaluator_llm.acall(
        evaluation_prompt,
        temperature=0.3,  # 评估时使用较低的温度
        max_tokens=500
    )
    
    print(f"Doubao评估结果:\n{evaluation_result.text}\n")
    print(f"评估时间: {evaluation_result.latency:.2f}秒")
    
    print("\n" + "="*80)
    print("评估完成！")
    print("="*80)


async def batch_evaluation_demo():
    """演示批量评估"""
    print("\n" + "="*80)
    print("批量评估演示")
    print("="*80)
    
    evaluator_llm = LLMProviderFactory.create_evaluator_llm()
    evaluated_llm = LLMProviderFactory.create_evaluated_llm()
    
    # 多个测试问题
    test_questions = [
        "什么是Python？",
        "解释一下什么是神经网络。",
        "云计算的主要优势是什么？",
    ]
    
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}/{len(test_questions)}] 评估问题: {question}")
        
        # 获取回答
        response = await evaluated_llm.acall(question, temperature=0.7, max_tokens=200)
        print(f"   回答: {response.text[:80]}...")
        
        # 简单评估
        eval_prompt = f"问题：{question}\n回答：{response.text}\n\n请给这个回答打分（1-10分）并说明理由。"
        evaluation = await evaluator_llm.acall(eval_prompt, temperature=0.3, max_tokens=200)
        print(f"   评估: {evaluation.text[:80]}...")
        
        results.append({
            'question': question,
            'answer': response.text,
            'evaluation': evaluation.text
        })
    
    print(f"\n完成 {len(results)} 个问题的评估！")


async def compare_models_demo():
    """演示模型对比"""
    print("\n" + "="*80)
    print("模型对比演示（使用不同温度参数）")
    print("="*80)
    
    evaluated_llm = LLMProviderFactory.create_evaluated_llm()
    evaluator_llm = LLMProviderFactory.create_evaluator_llm()
    
    question = "请用一句话解释什么是区块链。"
    temperatures = [0.3, 0.7, 1.0]
    
    responses = []
    
    for temp in temperatures:
        print(f"\n温度参数: {temp}")
        response = await evaluated_llm.acall(
            question,
            temperature=temp,
            max_tokens=100
        )
        print(f"回答: {response.text}")
        responses.append({'temp': temp, 'text': response.text})
    
    # 让评估器选择最佳回答
    print("\n请Doubao评估哪个回答最好...")
    
    comparison_prompt = f"""问题: {question}

以下是三个不同的回答：
1. (温度0.3) {responses[0]['text']}
2. (温度0.7) {responses[1]['text']}
3. (温度1.0) {responses[2]['text']}

请评估哪个回答最好，并说明理由。
"""
    
    comparison_result = await evaluator_llm.acall(
        comparison_prompt,
        temperature=0.3,
        max_tokens=300
    )
    
    print(f"\n评估结果:\n{comparison_result.text}")


async def main():
    """主函数"""
    try:
        # 检查环境变量
        required_env_vars = [
            "EVALUATOR_API_KEY",
            "EVALUATOR_MODEL_NAME",
            "EVALUATED_API_KEY",
            "EVALUATED_MODEL_NAME"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            print("错误: 以下环境变量未设置:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\n请在 .env 文件中配置这些变量。")
            return
        
        # 运行各个演示
        await test_llm_providers()
        await evaluation_demo()
        await batch_evaluation_demo()
        await compare_models_demo()
        
        print("\n" + "="*80)
        print("所有演示完成！")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

