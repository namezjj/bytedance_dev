"""
RAG系统评估示例

演示如何评估RAG（检索增强生成）系统的性能
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.evaluation_agent import EvaluationAgent, EvaluationInput
from data.database import EvaluationDatabase, QueryFilter
from config.evaluation_config import ConfigManager, create_config_from_template
from core.optimization.parameter_optimizer import ParameterOptimizer
from core.optimization.recommendation_engine import RecommendationEngine
from reporting.report_generator import ReportGenerator
from reporting.visualizer import EvaluationVisualizer

class RAGSystem:
    """模拟RAG系统"""

    def __init__(self, knowledge_base: List[Dict[str, str]], **params):
        """
        初始化RAG系统

        Args:
            knowledge_base: 知识库
            **params: RAG系统参数
        """
        self.knowledge_base = knowledge_base
        self.retrieval_top_k = params.get('retrieval_top_k', 5)
        self.similarity_threshold = params.get('similarity_threshold', 0.7)
        self.embedding_model = params.get('embedding_model', 'text-embedding-ada-002')

    def retrieve(self, query: str) -> List[Dict[str, str]]:
        """
        模拟文档检索

        Args:
            query: 查询语句

        Returns:
            检索到的文档列表
        """
        # 简单的基于关键词匹配的检索
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.knowledge_base:
            doc_words = set(doc['text'].lower().split())
            overlap = len(query_words & doc_words)
            score = overlap / len(query_words) if query_words else 0

            if score >= self.similarity_threshold:
                scored_docs.append({**doc, 'score': score})

        # 按分数排序并返回top_k
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:self.retrieval_top_k]

    def generate_response(self, query: str, retrieved_docs: List[Dict[str, str]]) -> str:
        """
        生成回答

        Args:
            query: 查询语句
            retrieved_docs: 检索到的文档

        Returns:
            生成的回答
        """
        if not retrieved_docs:
            return "抱歉，我没有找到相关信息来回答您的问题。"

        # 简单的基于检索文档的回答生成
        context = "\n".join([f"- {doc['title']}: {doc['text'][:200]}..."
                           for doc in retrieved_docs])

        response = f"""基于相关文档，我来回答您的问题：

{context}

根据以上信息，我可以为您提供以下回答：
这是一个需要结合多个信息源的综合问题。从检索到的文档可以看出，这个问题涉及多个方面的内容。
"""

        return response

async def rag_evaluation_demo():
    """RAG系统评估演示"""
    print("=" * 60)
    print("RAG系统评估演示")
    print("=" * 60)

    try:
        # 1. 准备知识库
        knowledge_base = [
            {
                "id": "1",
                "title": "人工智能基础",
                "text": "人工智能（AI）是指由计算机系统表现出的智能行为，包括学习、推理、问题解决等能力。"
            },
            {
                "id": "2",
                "title": "机器学习概述",
                "text": "机器学习是人工智能的一个子领域，通过算法使计算机能够从数据中学习并改进性能。"
            },
            {
                "id": "3",
                "title": "深度学习介绍",
                "text": "深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。"
            },
            {
                "id": "4",
                "title": "自然语言处理",
                "text": "自然语言处理（NLP）是AI的一个重要应用领域，专注于计算机与人类语言的交互。"
            },
            {
                "id": "5",
                "title": "计算机视觉",
                "text": "计算机视觉使计算机能够从图像和视频中获取、处理和理解视觉信息。"
            }
        ]

        # 2. 初始化组件
        config_manager = ConfigManager()
        config = create_config_from_template('comprehensive_eval')
        database = EvaluationDatabase("examples/rag_eval.db")

        # 模拟LLM
        from unittest.mock import Mock
        llm = Mock()

        def mock_llm_response(prompt):
            # 根据提示词生成合理的评估响应
            if "准确性" in prompt:
                return {'text': '分数：0.82\n评估：回答中的事实基本准确，但可以更详细一些。'}
            elif "相关性" in prompt:
                return {'text': '分数：0.75\n评估：回答与问题相关，但部分内容偏离主题。'}
            else:
                return {'text': '分数：0.78\n评估：回答质量中等，有改进空间。'}

        llm.acall = Mock(side_effect=mock_llm_response)

        # 3. 初始化评估系统
        agent = EvaluationAgent(llm=llm, config=config, database=database)
        optimizer = ParameterOptimizer(database, lambda x, y: asyncio.create_task(mock_evaluation(x, y)))
        recommender = RecommendationEngine(database)

        # 4. 准备测试查询
        test_queries = [
            {
                "question": "什么是人工智能和机器学习的关系？",
                "expected_context": "应该提到机器学习是AI的子领域"
            },
            {
                "question": "深度学习和机器学习有什么区别？",
                "expected_context": "应该解释深度学习是机器学习的分支"
            },
            {
                "question": "AI的主要应用领域有哪些？",
                "expected_context": "应该提到NLP、计算机视觉等应用"
            },
            {
                "question": "如何评价机器学习模型的性能？",
                "expected_context": "这是一个知识库中没有直接答案的问题"
            },
            {
                "question": "自然语言处理有哪些挑战？",
                "expected_context": "应该检索到NLP相关的文档"
            }
        ]

        # 5. 测试不同的RAG参数配置
        parameter_configs = [
            {"retrieval_top_k": 3, "similarity_threshold": 0.8},
            {"retrieval_top_k": 5, "similarity_threshold": 0.6},
            {"retrieval_top_k": 7, "similarity_threshold": 0.5},
        ]

        results_by_config = {}

        for i, params in enumerate(parameter_configs):
            print(f"\n测试配置 {i+1}: {params}")

            # 初始化RAG系统
            rag_system = RAGSystem(knowledge_base, **params)

            config_results = []

            for j, query_data in enumerate(test_queries):
                # 检索文档
                retrieved_docs = rag_system.retrieve(query_data["question"])

                # 生成回答
                response = rag_system.generate_response(query_data["question"], retrieved_docs)

                # 创建评估输入
                eval_input = EvaluationInput(
                    question=query_data["question"],
                    context=f"检索到的文档数: {len(retrieved_docs)}\n" +
                           "\n".join([f"文档{k+1}: {doc['title']}" for k, doc in enumerate(retrieved_docs)]),
                    ground_truth=query_data.get("expected_context"),
                    metadata={
                        "config_id": i,
                        "retrieved_count": len(retrieved_docs),
                        "query_id": j,
                        "retrieval_score": sum(doc.get('score', 0) for doc in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0
                    }
                )

                # 执行评估
                result = await agent.evaluate_single(eval_input, response)
                config_results.append(result)

                print(f"  查询 {j+1}: 得分 {result.overall_score:.3f}, 检索到 {len(retrieved_docs)} 个文档")

            results_by_config[f"config_{i+1}"] = config_results

            # 计算配置平均分
            avg_score = sum(r.overall_score for r in config_results) / len(config_results)
            print(f"配置 {i+1} 平均得分: {avg_score:.3f}")

        # 6. 生成配置对比报告
        print("\n" + "=" * 40)
        print("RAG配置对比分析")
        print("=" * 40)

        for config_name, results in results_by_config.items():
            avg_score = sum(r.overall_score for r in results) / len(results)
            dimension_scores = {}

            for result in results:
                for dimension, score in result.dimension_scores.items():
                    if dimension not in dimension_scores:
                        dimension_scores[dimension] = []
                    dimension_scores[dimension].append(score)

            print(f"\n{config_name}:")
            print(f"  平均得分: {avg_score:.3f}")
            print(f"  准确性: {np.mean(dimension_scores.get('accuracy', [0])):.3f}")
            print(f"  相关性: {np.mean(dimension_scores.get('relevance', [0])):.3f}")
            print(f"  完整性: {np.mean(dimension_scores.get('completeness', [0])):.3f}")
            print(f"  流畅性: {np.mean(dimension_scores.get('fluency', [0])):.3f}")

        # 7. 参数优化建议
        print("\n" + "=" * 40)
        print("参数优化建议")
        print("=" * 40)

        # 选择最佳配置的结果进行分析
        best_config_name = max(results_by_config.keys(),
                              key=lambda k: sum(r.overall_score for r in results_by_config[k]) / len(results_by_config[k]))
        best_results = results_by_config[best_config_name]

        # 生成优化建议
        recommendations = await recommender.generate_recommendations("rag-demo", time_window_days=7)

        print(f"基于 {best_config_name} 的优化建议:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec.title}")
            print(f"   类型: {rec.type}")
            print(f"   优先级: {rec.priority}")
            print(f"   描述: {rec.description}")
            print(f"   预期改进: {rec.expected_improvement:.3f}")
            print(f"   建议步骤:")
            for step in rec.action_steps[:3]:
                print(f"     - {step}")
            print()

        # 8. 生成RAG特定分析报告
        await generate_rag_analysis_report(database, results_by_config, parameter_configs)

        return results_by_config

    except Exception as e:
        print(f"RAG评估演示失败: {e}")
        import traceback
        traceback.print_exc()
        return {}

async def mock_evaluation(eval_input, params):
    """模拟评估函数用于参数优化器"""
    from core.evaluation_agent import EvaluationResult

    # 模拟评估结果
    result = EvaluationResult(
        input_data=eval_input,
        model_response="模拟回答",
        overall_score=0.75 + (hash(str(params)) % 20) / 100,  # 基于参数生成伪随机分数
        dimension_scores={
            "accuracy": 0.8,
            "relevance": 0.75,
            "completeness": 0.7,
            "fluency": 0.8
        },
        detailed_feedback={"default": "模拟评估反馈"},
        evaluation_timestamp=datetime.now(),
        metadata=params
    )

    return result

async def generate_rag_analysis_report(database, results_by_config, parameter_configs):
    """生成RAG分析报告"""
    try:
        report_generator = ReportGenerator(database, "examples/rag_reports")

        # 收集所有结果用于报告生成
        all_results = []
        for results in results_by_config.values():
            all_results.extend(results)

        if all_results:
            # 生成HTML报告
            html_report = await report_generator.generate_comprehensive_report(
                filter=None,
                format="html"
            )

            print(f"\nRAG评估报告已生成: {html_report}")

            # 生成可视化
            visualizer = EvaluationVisualizer("examples/rag_visualizations")

            # 生成配置对比图
            import numpy as np
            model_results = {}
            for config_name, results in results_by_config.items():
                model_results[config_name] = results

            comparison_chart = visualizer.create_model_comparison_plot(model_results)
            print(f"配置对比图: {comparison_chart}")

    except Exception as e:
        print(f"生成RAG分析报告失败: {e}")

def import_numpy():
    """动态导入numpy，如果不可用则提供替代实现"""
    try:
        import numpy as np
        return np
    except ImportError:
        # 提供简单的替代实现
        class MockNumpy:
            @staticmethod
            def mean(data):
                return sum(data) / len(data) if data else 0

            @staticmethod
            def std(data):
                if not data:
                    return 0
                mean_val = sum(data) / len(data)
                variance = sum((x - mean_val) ** 2 for x in data) / len(data)
                return variance ** 0.5
        return MockNumpy()

# 全局numpy引用
np = import_numpy()

async def main():
    """主函数"""
    print("开始RAG系统评估演示...")

    # 确保输出目录存在
    Path("examples").mkdir(exist_ok=True)
    Path("examples/rag_reports").mkdir(exist_ok=True)
    Path("examples/rag_visualizations").mkdir(exist_ok=True)

    try:
        # 运行RAG评估演示
        await rag_evaluation_demo()

        print("\n" + "=" * 60)
        print("RAG系统评估演示完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
    except Exception as e:
        print(f"\n运行RAG评估演示时出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())