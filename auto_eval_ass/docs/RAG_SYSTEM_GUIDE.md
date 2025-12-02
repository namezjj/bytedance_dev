# RAG系统使用指南

## 📖 概述

本文档介绍如何使用DeepSeek作为RAG系统回答问题的功能。

## 🎯 核心功能

### 1. DeepSeek回答问题（已完成✅）

使用DeepSeek生成对问题的回答，支持两种模式：
- **直接回答模式**: 直接回答问题，不使用额外上下文
- **RAG模式**: 基于检索到的上下文生成回答

## 📁 文件结构

```
core/
├── rag_system.py              # RAG系统核心实现
└── llm_providers/             # LLM提供商
    ├── deepseek_provider.py   # DeepSeek实现
    └── ...

examples/
├── rag_system_demo.py         # 完整演示示例
└── ...

test_deepseek_answer.py        # 测试脚本
```

## 💻 使用方法

### 基础使用

```python
import asyncio
from core.rag_system import RAGSystem

async def main():
    # 创建RAG系统（自动使用环境变量中的DeepSeek配置）
    rag = RAGSystem()
    
    # 生成回答
    output = await rag.generate_answer("什么是人工智能？")
    
    # 查看结果
    print(f"回答: {output.answer}")
    print(f"用时: {output.response_time:.2f}秒")
    print(f"Token: {output.token_usage}")

asyncio.run(main())
```

### 带上下文的RAG

```python
async def rag_with_context():
    rag = RAGSystem()
    
    # 模拟检索到的上下文
    context = """
    人工智能（AI）是计算机科学的一个分支，
    致力于创建能够执行通常需要人类智能的任务的系统。
    """
    
    # 基于上下文生成回答
    output = await rag.generate_answer(
        question="什么是人工智能？",
        context=context,
        use_context=True  # 启用上下文
    )
    
    print(output.answer)
```

### 批量处理

```python
async def batch_questions():
    rag = RAGSystem()
    
    questions = [
        "什么是机器学习？",
        "什么是深度学习？",
        "什么是神经网络？"
    ]
    
    # 批量生成回答（并发执行）
    outputs = await rag.batch_generate(questions)
    
    for q, output in zip(questions, outputs):
        print(f"Q: {q}")
        print(f"A: {output.answer}\n")
```

### Mock RAG（带自动检索）

```python
from core.rag_system import MockRAGSystem

async def mock_rag():
    # Mock RAG系统内置了知识库
    mock_rag = MockRAGSystem()
    
    # 自动检索并生成回答
    output = await mock_rag.generate_answer(
        question="什么是深度学习？",
        auto_retrieve=True  # 自动从知识库检索
    )
    
    print(f"检索到的上下文: {output.context_used}")
    print(f"回答: {output.answer}")
```

## 🔧 配置参数

### RAGSystem 初始化参数

```python
rag = RAGSystem(
    llm_provider="deepseek",      # LLM提供商（可选，默认使用环境变量）
    model_name="deepseek-chat",   # 模型名称
    api_key="your-api-key",       # API密钥
    temperature=0.7,               # 温度参数 (0.0-2.0)
    max_tokens=1000,              # 最大token数
    timeout=60,                   # 超时时间（秒）
    max_retries=3                 # 最大重试次数
)
```

### generate_answer 参数

```python
output = await rag.generate_answer(
    question="你的问题",           # 必需：问题文本
    context="相关上下文",          # 可选：上下文信息
    use_context=True,             # 是否使用上下文
    temperature=0.7,              # 覆盖默认温度
    max_tokens=500,               # 覆盖默认max_tokens
)
```

## 📊 输出结果

### RAGOutput 数据结构

```python
@dataclass
class RAGOutput:
    question: str                    # 原始问题
    answer: str                      # 生成的回答
    context_used: str                # 使用的上下文
    response_time: float             # 响应时间（秒）
    token_usage: Dict[str, int]      # Token使用情况
    metadata: Dict[str, Any]         # 元数据
    timestamp: datetime              # 时间戳
```

### 访问输出信息

```python
output = await rag.generate_answer(question)

# 基本信息
print(f"回答: {output.answer}")
print(f"问题: {output.question}")

# 性能信息
print(f"响应时间: {output.response_time:.2f}秒")

# Token使用
print(f"输入tokens: {output.token_usage['prompt_tokens']}")
print(f"输出tokens: {output.token_usage['completion_tokens']}")
print(f"总tokens: {output.token_usage['total_tokens']}")

# 元数据
print(f"模型: {output.metadata['model']}")
print(f"提供商: {output.metadata['provider']}")
print(f"温度: {output.metadata['temperature']}")
```

## 🚀 运行示例

### 1. 测试基本功能

```bash
python test_deepseek_answer.py
```

### 2. 运行完整演示

```bash
python examples/rag_system_demo.py
```

演示包含：
- ✅ 基础RAG功能（直接回答）
- ✅ 带上下文的RAG
- ✅ Mock RAG（自动检索）
- ✅ 批量问题处理
- ✅ 有无上下文对比

## ⚙️ 环境配置

### .env 文件配置

```bash
# DeepSeek配置
DEEPSEEK_API_KEY=sk-your-real-api-key-here
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 被评估模型配置（RAG系统使用）
EVALUATED_PROVIDER=deepseek
EVALUATED_MODEL_NAME=deepseek-chat
EVALUATED_API_KEY=sk-your-real-api-key-here
```

### 获取DeepSeek API密钥

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入"API密钥"页面
4. 创建新的API密钥
5. 复制密钥并更新到 `.env` 文件

## 🎨 完整示例代码

### 示例1：简单问答

```python
import asyncio
from core.rag_system import RAGSystem

async def simple_qa():
    rag = RAGSystem()
    
    output = await rag.generate_answer(
        "请用一句话解释什么是Python"
    )
    
    print(output.answer)

asyncio.run(simple_qa())
```

### 示例2：RAG模式

```python
async def rag_mode():
    rag = RAGSystem()
    
    # 假设这是从向量数据库检索到的内容
    retrieved_context = """
    Python是一种高级编程语言，由Guido van Rossum于1991年创建。
    它强调代码可读性，使用缩进来定义代码块。
    Python支持多种编程范式，包括面向对象、命令式、函数式编程。
    """
    
    output = await rag.generate_answer(
        question="Python有哪些特点？",
        context=retrieved_context,
        use_context=True
    )
    
    print(f"基于检索内容的回答:\n{output.answer}")

asyncio.run(rag_mode())
```

### 示例3：对比测试

```python
async def compare_modes():
    rag = RAGSystem()
    question = "什么是RAG系统？"
    
    # 模式1：无上下文
    output1 = await rag.generate_answer(question, use_context=False)
    
    # 模式2：有上下文
    context = "RAG是检索增强生成，结合了检索和生成..."
    output2 = await rag.generate_answer(question, context=context, use_context=True)
    
    print("无上下文回答:")
    print(output1.answer)
    print(f"\n有上下文回答:")
    print(output2.answer)

asyncio.run(compare_modes())
```

## 📈 性能特性

### 1. 异步并发

支持高并发异步调用：

```python
# 并发处理多个问题
tasks = [rag.generate_answer(q) for q in questions]
results = await asyncio.gather(*tasks)
```

### 2. 自动重试

内置指数退避重试机制，提高稳定性。

### 3. 性能监控

自动记录：
- 响应时间
- Token使用量
- 模型信息
- 请求元数据

## 🔍 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

rag = RAGSystem()
```

### 查看原始响应

```python
output = await rag.generate_answer(question)
print(f"元数据: {output.metadata}")
```

## ⚠️ 注意事项

1. **API密钥安全**: 不要将API密钥提交到版本控制
2. **速率限制**: 注意API的速率限制
3. **Token限制**: 根据模型调整max_tokens参数
4. **错误处理**: 生产环境建议增加完善的错误处理

## 🐛 常见问题

### Q: 401 Authentication Error

**A**: API密钥无效或未设置
- 检查 `.env` 文件中的API密钥
- 确保已执行 `load_dotenv()`

### Q: 连接超时

**A**: 网络问题或服务不可用
- 增加 `timeout` 参数
- 检查网络连接
- 确认API服务状态

### Q: Token超限

**A**: 输入或输出超过模型限制
- 减少 `max_tokens` 参数
- 精简输入文本或上下文

## 📝 下一步

现在DeepSeek回答问题的功能已经完成，接下来可以：

1. ✅ **已完成**: DeepSeek生成回答
2. ⏭️ **待实现**: Doubao评估回答质量
3. ⏭️ **待实现**: 完整的RAG评估流程
4. ⏭️ **待实现**: 评估结果存储和可视化

## 📞 获取帮助

- 查看代码: `core/rag_system.py`
- 运行示例: `examples/rag_system_demo.py`
- 测试功能: `python test_deepseek_answer.py`

---

**文档更新时间**: 2025-11-21

