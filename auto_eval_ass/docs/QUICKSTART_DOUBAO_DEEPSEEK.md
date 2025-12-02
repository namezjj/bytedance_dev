# Doubao + DeepSeek 快速开始指南

本指南将帮助你快速配置和使用Doubao（裁判LLM）和DeepSeek（参评LLM）进行自动化评估。

## 📋 目录

- [环境配置](#环境配置)
- [API密钥获取](#api密钥获取)
- [快速测试](#快速测试)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

## 🔧 环境配置

### 1. 安装依赖

```bash
cd /Users/tal/zjj/tal_dev/df/auto_eval_agent
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑项目根目录下的 `.env` 文件：

```bash
# Doubao配置（火山引擎）
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_MODEL_NAME=ep-20250614210935-8mthr
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# DeepSeek配置
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 评估器配置（裁判LLM - 使用Doubao）
EVALUATOR_PROVIDER=doubao
EVALUATOR_MODEL_NAME=ep-20250614210935-8mthr
EVALUATOR_API_KEY=your-doubao-api-key

# 被评估模型配置（参评LLM - 使用DeepSeek）
EVALUATED_PROVIDER=deepseek
EVALUATED_MODEL_NAME=deepseek-chat
EVALUATED_API_KEY=your-deepseek-api-key
```

**重要**: 请将 `your-doubao-api-key` 和 `your-deepseek-api-key` 替换为你的实际API密钥。

## 🔑 API密钥获取

### Doubao（火山引擎）

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 进入"机器学习平台" > "模型服务"
3. 创建或选择已有的endpoint
4. 复制API密钥和endpoint ID

### DeepSeek

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入"API密钥"页面
4. 创建新的API密钥

## ⚡ 快速测试

### 测试基本功能

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def quick_test():
    # 测试Doubao
    evaluator = LLMProviderFactory.create_evaluator_llm()
    response = await evaluator.acall("你好，介绍一下你自己", max_tokens=100)
    print(f"Doubao: {response.text}")
    
    # 测试DeepSeek
    evaluated = LLMProviderFactory.create_evaluated_llm()
    response = await evaluated.acall("你好，介绍一下你自己", max_tokens=100)
    print(f"DeepSeek: {response.text}")

asyncio.run(quick_test())
```

### 运行完整示例

```bash
python examples/doubao_deepseek_evaluation.py
```

## 📚 使用示例

### 示例1: 基本评估流程

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def basic_evaluation():
    # 创建LLM实例
    evaluator_llm = LLMProviderFactory.create_evaluator_llm()
    evaluated_llm = LLMProviderFactory.create_evaluated_llm()
    
    # 准备问题
    question = "什么是人工智能？"
    
    # 1. 获取DeepSeek的回答
    answer = await evaluated_llm.acall(
        question,
        temperature=0.7,
        max_tokens=500
    )
    print(f"问题: {question}")
    print(f"DeepSeek回答: {answer.text}\n")
    
    # 2. 使用Doubao评估
    eval_prompt = f"""请评估以下回答的质量（1-10分）：

问题: {question}
回答: {answer.text}

请从准确性、相关性、完整性、流畅性四个维度评分。"""
    
    evaluation = await evaluator_llm.acall(
        eval_prompt,
        temperature=0.3,
        max_tokens=500
    )
    print(f"Doubao评估: {evaluation.text}")

asyncio.run(basic_evaluation())
```

### 示例2: 批量评估

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def batch_evaluation():
    evaluator = LLMProviderFactory.create_evaluator_llm()
    evaluated = LLMProviderFactory.create_evaluated_llm()
    
    questions = [
        "什么是机器学习？",
        "解释一下区块链技术。",
        "云计算的主要优势是什么？"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q}")
        
        # 获取回答
        answer = await evaluated.acall(q, max_tokens=300)
        
        # 评估
        eval_prompt = f"请给以下回答打分(1-10):\n问题:{q}\n回答:{answer.text}"
        score = await evaluator.acall(eval_prompt, temperature=0.2, max_tokens=100)
        
        print(f"回答: {answer.text[:100]}...")
        print(f"评分: {score.text}")

asyncio.run(batch_evaluation())
```

### 示例3: 使用不同模型参数

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def parameter_comparison():
    llm = LLMProviderFactory.create("deepseek")
    
    question = "什么是量子计算？"
    
    # 测试不同温度参数
    for temp in [0.3, 0.7, 1.0]:
        response = await llm.acall(
            question,
            temperature=temp,
            max_tokens=200
        )
        print(f"\n温度={temp}:")
        print(response.text)

asyncio.run(parameter_comparison())
```

### 示例4: 直接创建指定提供商

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def direct_provider():
    # 直接创建Doubao提供商
    doubao = LLMProviderFactory.create(
        provider_name="doubao",
        api_key="your-api-key",
        model_name="ep-20250614210935-8mthr"
    )
    
    # 直接创建DeepSeek提供商
    deepseek = LLMProviderFactory.create(
        provider_name="deepseek",
        api_key="your-api-key",
        model_name="deepseek-chat"
    )
    
    # 使用
    response = await doubao.acall("测试问题")
    print(response.text)

asyncio.run(direct_provider())
```

## 🎯 架构说明

### LLM提供商架构

```
core/llm_providers/
├── __init__.py              # 模块初始化
├── base_provider.py         # 基类定义
├── doubao_provider.py       # Doubao实现
├── deepseek_provider.py     # DeepSeek实现
└── provider_factory.py      # 工厂类
```

### 配置文件

```
config/
├── evaluation_config.py     # 主配置文件
└── model_configs/
    ├── doubao_config.json   # Doubao配置
    └── deepseek_config.json # DeepSeek配置
```

## 🔍 常见问题

### 1. API调用失败

**问题**: `调用失败，状态码: 401`

**解决**: 检查API密钥是否正确配置在 `.env` 文件中

### 2. 模型名称错误

**问题**: `模型名称不是标准格式`

**解决**: 
- Doubao: 使用endpoint ID格式，如 `ep-20250614210935-8mthr`
- DeepSeek: 使用 `deepseek-chat`, `deepseek-coder` 等官方模型名

### 3. 请求超时

**问题**: `请求超时`

**解决**: 增加timeout参数
```python
llm = LLMProviderFactory.create(
    "deepseek",
    timeout=120  # 增加到120秒
)
```

### 4. 速率限制

**问题**: `Rate limit exceeded`

**解决**: 
- 降低并发数
- 增加请求间隔
- 升级API计划

### 5. 环境变量未加载

**问题**: 环境变量读取为None

**解决**: 确保在代码开始处加载环境变量
```python
from dotenv import load_dotenv
load_dotenv()
```

## 📊 性能优化建议

### 1. 批量处理优化

```python
import asyncio

async def optimized_batch():
    tasks = []
    for question in questions:
        task = evaluated_llm.acall(question)
        tasks.append(task)
    
    # 并发执行
    results = await asyncio.gather(*tasks)
```

### 2. 缓存重复请求

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_call(question):
    return asyncio.run(llm.acall(question))
```

### 3. 使用连接池

```python
# aiohttp会自动管理连接池
# 可以通过配置调整
llm = LLMProviderFactory.create(
    "deepseek",
    max_retries=3,
    timeout=60
)
```

## 🚀 下一步

- 查看 [完整API文档](api_reference.md)
- 了解 [评估维度配置](../config/evaluation_config.py)
- 探索 [更多示例](../examples/)
- 阅读 [开发指南](development_guide.md)

## 💡 提示

1. **温度参数**: 评估时建议使用较低温度(0.2-0.3)以获得稳定结果
2. **Token限制**: 根据任务复杂度合理设置max_tokens
3. **错误处理**: 生产环境建议增加完善的错误处理和重试机制
4. **日志记录**: 启用详细日志以便调试问题

## 📞 获取帮助

- 查看 [Issues](https://github.com/your-repo/auto_eval_agent/issues)
- 阅读 [FAQ文档](../docs/FAQ.md)
- 加入讨论组

---

**祝你使用愉快！** 🎉

