# 重构说明文档

## 重构概述

本次重构的主要目标是配置裁判LLM（Doubao）和参评LLM（DeepSeek），实现基于环境变量的灵活配置系统。

## 🔄 主要变更

### 1. 新增LLM提供商系统

创建了统一的LLM提供商架构，支持多种LLM的接入：

```
core/llm_providers/
├── __init__.py              # 模块入口
├── base_provider.py         # 基础提供商抽象类
├── doubao_provider.py       # Doubao（豆包）实现
├── deepseek_provider.py     # DeepSeek实现
└── provider_factory.py      # 工厂模式创建提供商
```

**特性**:
- 统一的异步调用接口
- 自动重试机制
- 性能监控（延迟、Token使用）
- 灵活的配置管理

### 2. 环境变量配置系统

更新了 `.env` 文件，新增以下配置项：

```bash
# DeepSeek配置
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 评估器配置（裁判LLM）
EVALUATOR_PROVIDER=doubao
EVALUATOR_MODEL_NAME=ep-20250614210935-8mthr
EVALUATOR_API_KEY=your-doubao-key

# 被评估模型配置（参评LLM）
EVALUATED_PROVIDER=deepseek
EVALUATED_MODEL_NAME=deepseek-chat
EVALUATED_API_KEY=your-deepseek-key
```

### 3. 更新配置管理器

扩展了 `config/evaluation_config.py`：

- 新增 `ModelProvider.DOUBAO` 和 `ModelProvider.DEEPSEEK`
- 添加 `evaluator_provider` 和 `evaluated_provider` 配置项
- 支持从环境变量自动加载配置

### 4. 模型配置文件

创建了专门的模型配置文件：

- `config/model_configs/doubao_config.json` - Doubao模型参数
- `config/model_configs/deepseek_config.json` - DeepSeek模型参数

包含：
- 模型能力描述
- 价格信息
- 推荐使用场景
- 评估优化参数
- 速率限制配置

### 5. 示例代码和文档

创建了完整的示例和文档：

- `examples/doubao_deepseek_evaluation.py` - 完整使用示例
- `docs/QUICKSTART_DOUBAO_DEEPSEEK.md` - 快速开始指南
- `test_setup.py` - 配置验证工具

## 📦 新增依赖

更新了 `requirements.txt`，主要依赖：

```
python-dotenv>=1.0.0  # 环境变量管理
aiohttp>=3.9.0        # 异步HTTP客户端
asyncio               # 异步支持
```

## 🎯 使用方式

### 基本使用

```python
import asyncio
from core.llm_providers import LLMProviderFactory

async def main():
    # 自动从环境变量创建
    evaluator = LLMProviderFactory.create_evaluator_llm()
    evaluated = LLMProviderFactory.create_evaluated_llm()
    
    # 使用
    response = await evaluated.acall("你的问题")
    print(response.text)

asyncio.run(main())
```

### 手动创建

```python
# 创建特定提供商
doubao = LLMProviderFactory.create(
    provider_name="doubao",
    api_key="your-key",
    model_name="ep-xxxxx"
)

deepseek = LLMProviderFactory.create(
    provider_name="deepseek",
    api_key="your-key",
    model_name="deepseek-chat"
)
```

## 🔍 架构优势

### 1. 松耦合设计
- 提供商之间相互独立
- 易于添加新的LLM提供商
- 配置与代码分离

### 2. 统一接口
- 所有提供商实现相同的接口
- 方便切换不同的LLM
- 简化测试和维护

### 3. 灵活配置
- 支持环境变量配置
- 支持代码中动态配置
- 支持配置文件加载

### 4. 生产就绪
- 完善的错误处理
- 自动重试机制
- 性能监控和日志

## 🚀 扩展指南

### 添加新的LLM提供商

1. 创建提供商类：

```python
# core/llm_providers/new_provider.py
from .base_provider import BaseLLMProvider, LLMResponse

class NewProvider(BaseLLMProvider):
    def get_provider_name(self) -> str:
        return "new_provider"
    
    async def acall(self, prompt, temperature=0.7, max_tokens=2000, **kwargs):
        # 实现调用逻辑
        pass
```

2. 注册提供商：

```python
# 在 provider_factory.py 中
_providers = {
    "doubao": DoubaoProvider,
    "deepseek": DeepSeekProvider,
    "new_provider": NewProvider,  # 添加这行
}
```

3. 添加配置：

```bash
# .env
NEW_PROVIDER_API_KEY=xxx
NEW_PROVIDER_MODEL_NAME=xxx
```

## 📊 性能特性

### 异步支持
所有LLM调用都是异步的，支持高并发：

```python
# 并发执行多个请求
tasks = [llm.acall(q) for q in questions]
results = await asyncio.gather(*tasks)
```

### 自动重试
内置指数退避重试机制：

```python
llm = LLMProviderFactory.create(
    "doubao",
    max_retries=3,  # 最多重试3次
    timeout=60      # 超时60秒
)
```

### 性能监控
自动记录延迟和Token使用：

```python
response = await llm.acall(prompt)
print(f"延迟: {response.latency:.2f}秒")
print(f"Token: {response.usage}")
```

## 🔒 安全考虑

1. **API密钥管理**: 
   - 使用环境变量存储
   - `.env` 文件应加入 `.gitignore`
   - 永远不要硬编码API密钥

2. **输入验证**:
   - 验证API密钥格式
   - 验证模型名称
   - 检查参数范围

3. **错误处理**:
   - 不在错误信息中暴露敏感信息
   - 详细日志记录用于调试
   - 优雅降级机制

## 📝 待办事项

- [ ] 添加更多LLM提供商（OpenAI、Claude等）
- [ ] 实现请求缓存机制
- [ ] 添加流式响应支持
- [ ] 完善单元测试
- [ ] 添加性能基准测试
- [ ] 实现配置热加载

## 🐛 已知问题

1. `.env` 文件被 `.cursorignore` 过滤，需要特殊权限访问
2. 部分LLM提供商的API可能有区域限制
3. 异步调用在某些环境下可能需要额外配置

## 📞 联系方式

如有问题或建议，请：
- 提交 Issue
- 发起 Pull Request
- 查阅文档 `docs/QUICKSTART_DOUBAO_DEEPSEEK.md`

## 🎉 总结

本次重构实现了：
✅ 灵活的LLM提供商系统
✅ 基于环境变量的配置管理
✅ Doubao（裁判）+ DeepSeek（参评）集成
✅ 完整的示例和文档
✅ 生产级的错误处理和重试机制
✅ 异步高性能设计

---

**重构完成时间**: 2025-11-21
**重构负责人**: Claude Sonnet 4.5
**版本**: v1.0.0-refactored

