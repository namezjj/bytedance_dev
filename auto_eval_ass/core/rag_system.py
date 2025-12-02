"""
RAG系统模拟和评估

用于模拟RAG系统并进行评估
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from core.llm_providers import LLMProviderFactory, LLMResponse


@dataclass
class RAGInput:
    """RAG系统输入"""
    question: str
    context: Optional[str] = None  # 检索到的上下文（可选）
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RAGOutput:
    """RAG系统输出"""
    question: str
    answer: str
    context_used: Optional[str] = None
    response_time: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RAGSystem:
    """
    RAG系统模拟器
    
    使用DeepSeek模拟RAG系统的回答生成
    当前版本直接使用LLM生成回答，未来可以添加真实的检索功能
    """
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        初始化RAG系统
        
        Args:
            llm_provider: LLM提供商名称（默认使用EVALUATED_PROVIDER）
            model_name: 模型名称
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他配置参数
        """
        # 创建LLM实例
        if llm_provider:
            self.llm = LLMProviderFactory.create(
                provider_name=llm_provider,
                model_name=model_name,
                api_key=api_key,
                **kwargs
            )
        else:
            # 默认使用被评估的LLM配置
            self.llm = LLMProviderFactory.create_evaluated_llm(**kwargs)
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.config = kwargs
        
        print(f"RAG系统初始化完成:")
        print(f"  提供商: {self.llm.get_provider_name()}")
        print(f"  模型: {self.llm.model_name}")
        print(f"  温度: {self.temperature}")
        print(f"  最大tokens: {self.max_tokens}")
    
    async def generate_answer(
        self,
        question: str,
        context: Optional[str] = None,
        use_context: bool = True,
        **kwargs
    ) -> RAGOutput:
        """
        生成回答（模拟RAG系统）
        
        Args:
            question: 问题
            context: 检索到的上下文（可选）
            use_context: 是否使用上下文
            **kwargs: 其他参数
            
        Returns:
            RAGOutput: RAG输出结果
        """
        # 构建提示词
        if context and use_context:
            # 有上下文的RAG模式
            prompt = self._build_rag_prompt(question, context)
            context_used = context
        else:
            # 无上下文的直接回答模式
            prompt = question
            context_used = None
        
        # 获取温度和max_tokens参数
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        # 调用LLM生成回答
        import time
        start_time = time.time()
        
        response: LLMResponse = await self.llm.acall(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        response_time = time.time() - start_time
        
        # 构建输出
        output = RAGOutput(
            question=question,
            answer=response.text,
            context_used=context_used,
            response_time=response_time,
            token_usage=response.usage,
            metadata={
                'model': response.model,
                'provider': response.provider,
                'latency': response.latency,
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
        )
        
        return output
    
    def _build_rag_prompt(self, question: str, context: str) -> str:
        """
        构建RAG提示词
        
        Args:
            question: 问题
            context: 上下文
            
        Returns:
            str: 完整的提示词
        """
        prompt = f"""请基于以下上下文信息回答问题。

上下文信息：
{context}

问题：{question}

请根据上下文信息给出准确、完整的回答。如果上下文信息不足以回答问题，请明确说明。

回答："""
        return prompt
    
    async def batch_generate(
        self,
        questions: List[str],
        contexts: Optional[List[str]] = None,
        **kwargs
    ) -> List[RAGOutput]:
        """
        批量生成回答
        
        Args:
            questions: 问题列表
            contexts: 上下文列表（可选）
            **kwargs: 其他参数
            
        Returns:
            List[RAGOutput]: RAG输出列表
        """
        if contexts is None:
            contexts = [None] * len(questions)
        
        if len(questions) != len(contexts):
            raise ValueError("问题和上下文的数量必须一致")
        
        # 并发生成回答
        tasks = [
            self.generate_answer(q, c, **kwargs)
            for q, c in zip(questions, contexts)
        ]
        
        results = await asyncio.gather(*tasks)
        return results


class MockRAGSystem(RAGSystem):
    """
    Mock RAG系统
    
    用于测试，可以模拟检索和回答生成的完整流程
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mock的知识库
        self.knowledge_base = self._create_mock_knowledge_base()
    
    def _create_mock_knowledge_base(self) -> Dict[str, str]:
        """创建Mock知识库"""
        return {
            "人工智能": """人工智能(Artificial Intelligence, AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
            主要包括：机器学习、深度学习、自然语言处理、计算机视觉等技术。
            人工智能的发展经历了多个阶段，从早期的符号主义到现在的深度学习时代。""",
            
            "机器学习": """机器学习是人工智能的一个子领域，它使计算机系统能够从数据中学习并改进，而无需明确编程。
            主要类型包括：监督学习、无监督学习、强化学习。
            常用算法有：决策树、随机森林、支持向量机、神经网络等。""",
            
            "深度学习": """深度学习是机器学习的一个分支，基于人工神经网络，特别是深度神经网络。
            核心概念包括：卷积神经网络(CNN)、循环神经网络(RNN)、Transformer等架构。
            在图像识别、自然语言处理、语音识别等领域取得了突破性进展。""",
            
            "自然语言处理": """自然语言处理(NLP)是人工智能和语言学的交叉领域，致力于让计算机理解、解释和生成人类语言。
            主要任务包括：文本分类、情感分析、机器翻译、问答系统、文本生成等。
            现代NLP主要基于深度学习，特别是Transformer架构和大语言模型。""",
            
            "云计算": """云计算是一种通过互联网提供计算资源的模式，用户可以按需获取和使用计算能力、存储空间和应用程序。
            主要服务模式：IaaS(基础设施即服务)、PaaS(平台即服务)、SaaS(软件即服务)。
            优势包括：弹性扩展、按需付费、降低IT成本、提高资源利用率。
            主要提供商有：AWS、Azure、Google Cloud、阿里云等。""",
        }
    
    def retrieve_context(self, question: str, top_k: int = 1) -> str:
        """
        模拟检索上下文
        
        Args:
            question: 问题
            top_k: 返回top-k个结果
            
        Returns:
            str: 检索到的上下文
        """
        # 简单的关键词匹配
        matched_contexts = []
        
        for keyword, context in self.knowledge_base.items():
            if keyword in question:
                matched_contexts.append(context)
        
        if matched_contexts:
            # 返回匹配的上下文（这里简化处理，实际应该做相似度排序）
            return "\n\n".join(matched_contexts[:top_k])
        else:
            # 如果没有匹配，返回通用提示
            return "未找到直接相关的上下文信息。"
    
    async def generate_answer(
        self,
        question: str,
        context: Optional[str] = None,
        use_context: bool = True,
        auto_retrieve: bool = True,
        **kwargs
    ) -> RAGOutput:
        """
        生成回答（带自动检索）
        
        Args:
            question: 问题
            context: 上下文（如果提供则使用，否则自动检索）
            use_context: 是否使用上下文
            auto_retrieve: 是否自动检索
            **kwargs: 其他参数
            
        Returns:
            RAGOutput: RAG输出结果
        """
        # 如果没有提供上下文且需要自动检索
        if context is None and use_context and auto_retrieve:
            context = self.retrieve_context(question)
            print(f"自动检索到上下文: {context[:100]}...")
        
        # 调用父类方法生成回答
        return await super().generate_answer(
            question=question,
            context=context,
            use_context=use_context,
            **kwargs
        )


async def test_rag_system():
    """测试RAG系统"""
    print("="*80)
    print("测试RAG系统")
    print("="*80)
    
    # 创建RAG系统
    rag = RAGSystem()
    
    # 测试问题
    test_questions = [
        "什么是人工智能？",
        "机器学习和深度学习有什么区别？",
        "云计算的主要优势是什么？",
    ]
    
    print(f"\n开始测试 {len(test_questions)} 个问题...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] 问题: {question}")
        
        # 生成回答
        output = await rag.generate_answer(question)
        
        print(f"  回答: {output.answer[:200]}...")
        print(f"  响应时间: {output.response_time:.2f}秒")
        print(f"  Token使用: {output.token_usage}")
        print()


async def test_mock_rag_system():
    """测试Mock RAG系统（带检索功能）"""
    print("="*80)
    print("测试Mock RAG系统（带检索）")
    print("="*80)
    
    # 创建Mock RAG系统
    mock_rag = MockRAGSystem()
    
    # 测试问题
    test_questions = [
        "请介绍一下人工智能",
        "什么是机器学习？",
        "云计算有什么优势？",
    ]
    
    print(f"\n开始测试 {len(test_questions)} 个问题...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] 问题: {question}")
        
        # 使用自动检索生成回答
        output = await mock_rag.generate_answer(
            question,
            auto_retrieve=True,
            use_context=True
        )
        
        print(f"  上下文: {output.context_used[:100] if output.context_used else '无'}...")
        print(f"  回答: {output.answer[:200]}...")
        print(f"  响应时间: {output.response_time:.2f}秒")
        print()


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 运行测试
    asyncio.run(test_rag_system())
    print("\n")
    asyncio.run(test_mock_rag_system())

