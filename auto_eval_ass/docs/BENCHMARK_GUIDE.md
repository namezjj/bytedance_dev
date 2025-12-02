# 基准数据集使用指南

本指南介绍如何使用基准数据集系统进行各类评测。

## 目录

- [概述](#概述)
- [数据集类型](#数据集类型)
- [快速开始](#快速开始)
- [导入数据集](#导入数据集)
- [使用数据集进行评测](#使用数据集进行评测)
- [API参考](#api参考)

## 概述

基准数据集系统允许你:

1. **导入标准化的测试数据集** - 从JSON文件导入结构化的问答数据
2. **分类管理评测任务** - 支持LLM、RAG、Agent等不同评测类型
3. **灵活查询和筛选** - 按分类、难度、是否含计算等条件筛选问题
4. **统计分析** - 自动生成数据集统计信息

## 数据集类型

系统支持以下评测类型:

### 1. LLM评测 (`EvaluationType.LLM`)
- **用途**: 评测大模型的基础问答能力
- **特点**: 直接问答,不需要额外上下文
- **示例**: 知识问答、推理题、计算题

### 2. RAG评测 (`EvaluationType.RAG`)
- **用途**: 评测RAG系统的检索和问答能力
- **特点**: 需要从知识库检索相关信息后回答
- **示例**: 文档问答、知识库查询

### 3. Agent评测 (`EvaluationType.AGENT`)
- **用途**: 评测Agent的推理和执行能力
- **特点**: 需要多步推理、工具调用等复杂任务
- **示例**: 多步推理题、需要工具调用的任务

### 4. 通用评测 (`EvaluationType.GENERAL`)
- **用途**: 通用评测,不特定某一类型
- **特点**: 灵活使用

## 快速开始

### 1. 导入数据集

```bash
python examples/import_benchmark.py
```

这将从 `data/benchmark/qa_structured.json` 导入数据集并创建三个评测版本(LLM、RAG、Agent)。

### 2. 运行评测

```bash
python examples/benchmark_evaluation.py
```

这将在导入的数据集上运行示例评测。

## 导入数据集

### JSON格式要求

基准数据集应为以下JSON格式:

```json
{
  "title": "数据集标题",
  "description": "数据集描述",
  "chapter_info": "章节信息(可选)",
  "questions": [
    {
      "id": 1,
      "category": ["分类1", "分类2"],
      "chapter_info": "章节信息",
      "question": "问题内容",
      "answer": "标准答案",
      "key_words": ["关键词1", "关键词2"],
      "has_calculation": false
    }
  ]
}
```

### 使用代码导入

```python
import asyncio
from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType

async def import_dataset():
    db = EvaluationDatabase("evaluation_results.db")
    manager = BenchmarkDatasetManager(db)
    
    # 导入LLM评测数据集
    dataset_id = await manager.import_from_json(
        json_path="path/to/your/dataset.json",
        dataset_name="my_llm_benchmark",
        evaluation_type=EvaluationType.LLM,
        metadata={
            "domain": "领域名称",
            "language": "zh",
            "version": "1.0"
        }
    )
    
    print(f"数据集ID: {dataset_id}")
    db.close()

asyncio.run(import_dataset())
```

## 使用数据集进行评测

### 基本流程

```python
import asyncio
from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from core.evaluation_agent import EvaluationAgent, EvaluationInput
from core.llm_providers import LLMProviderFactory

async def run_evaluation():
    # 1. 初始化
    db = EvaluationDatabase("evaluation_results.db")
    manager = BenchmarkDatasetManager(db)
    
    # 2. 获取数据集
    dataset = await manager.get_dataset_by_name("my_llm_benchmark")
    
    # 3. 获取问题
    questions = await manager.get_questions(dataset.id, limit=10)
    
    # 4. 创建评估代理
    evaluator = LLMProviderFactory.create_evaluator_llm()
    evaluated = LLMProviderFactory.create_evaluated_llm()
    agent = EvaluationAgent(llm=evaluator, evaluated_llm=evaluated)
    
    # 5. 逐个评测
    for q in questions:
        # 让模型回答
        response = await evaluated.acall(q.question)
        
        # 评估回答
        eval_input = EvaluationInput(
            question=q.question,
            ground_truth=q.answer,
            metadata={
                'dataset_id': dataset.id,
                'question_number': q.question_number,
                'difficulty': q.difficulty_level
            }
        )
        
        result = await agent.evaluate_single(eval_input, response.text)
        
        # 保存结果
        await db.save_evaluation_result(result)
        
        print(f"问题 {q.question_number}: {result.overall_score:.2f}")
    
    db.close()

asyncio.run(run_evaluation())
```

### 按条件筛选问题

```python
# 只获取困难的计算题
hard_calc_questions = await manager.get_questions(
    dataset_id=dataset.id,
    difficulty="hard",
    has_calculation=True
)

# 获取特定分类的问题
category_questions = await manager.get_questions(
    dataset_id=dataset.id,
    category="晶体结构"
)

# 分页获取
page1 = await manager.get_questions(
    dataset_id=dataset.id,
    limit=20,
    offset=0
)
```

### 搜索问题

```python
# 搜索包含关键词的问题
results = await manager.search_questions(
    dataset_id=dataset.id,
    keyword="晶体",
    search_in_answer=False  # 只搜索问题,不搜索答案
)
```

## API参考

### BenchmarkDatasetManager

#### `import_from_json(json_path, dataset_name, evaluation_type, metadata)`
从JSON文件导入数据集

**参数:**
- `json_path`: JSON文件路径
- `dataset_name`: 数据集名称(唯一标识)
- `evaluation_type`: 评测类型(LLM/RAG/AGENT/GENERAL)
- `metadata`: 可选的元数据字典

**返回:** 数据集ID

#### `get_dataset_by_name(name)`
根据名称获取数据集

**参数:**
- `name`: 数据集名称

**返回:** BenchmarkDataset对象或None

#### `list_datasets(evaluation_type=None)`
列出所有数据集

**参数:**
- `evaluation_type`: 可选的类型过滤

**返回:** BenchmarkDataset列表

#### `get_questions(dataset_id, category, difficulty, has_calculation, limit, offset)`
获取数据集中的问题

**参数:**
- `dataset_id`: 数据集ID
- `category`: 可选的分类过滤
- `difficulty`: 可选的难度过滤(easy/medium/hard)
- `has_calculation`: 可选的计算题过滤
- `limit`: 返回数量限制
- `offset`: 偏移量

**返回:** BenchmarkQuestion列表

#### `get_dataset_statistics(dataset_id)`
获取数据集统计信息

**参数:**
- `dataset_id`: 数据集ID

**返回:** 统计信息字典,包含:
- `total_questions`: 总问题数
- `calculation_questions`: 计算题数量
- `difficulty_distribution`: 难度分布
- `category_distribution`: 分类分布

#### `search_questions(dataset_id, keyword, search_in_answer)`
搜索问题

**参数:**
- `dataset_id`: 数据集ID
- `keyword`: 搜索关键词
- `search_in_answer`: 是否同时搜索答案

**返回:** 匹配的BenchmarkQuestion列表

#### `export_to_json(dataset_id, output_path)`
导出数据集为JSON

**参数:**
- `dataset_id`: 数据集ID
- `output_path`: 输出文件路径

**返回:** bool(是否成功)

## 最佳实践

### 1. 数据集命名规范

建议使用以下命名规范:
```
{domain}_{topic}_{type}
```

示例:
- `materials_science_qa_llm` - 材料科学问答LLM评测
- `math_reasoning_rag` - 数学推理RAG评测
- `code_generation_agent` - 代码生成Agent评测

### 2. 元数据建议

在导入时添加有用的元数据:

```python
metadata = {
    "domain": "具体领域",
    "language": "zh/en",
    "version": "1.0",
    "created_by": "创建者",
    "source": "数据来源",
    "license": "许可证"
}
```

### 3. 评测结果追踪

在评测时,建议在metadata中记录:

```python
eval_input = EvaluationInput(
    question=q.question,
    ground_truth=q.answer,
    metadata={
        'dataset_id': dataset.id,
        'dataset_name': dataset.name,
        'question_number': q.question_number,
        'category': q.category,
        'difficulty': q.difficulty_level,
        'has_calculation': q.has_calculation,
        'model_name': model_name,
        'model_version': model_version,
        'evaluation_date': datetime.now().isoformat()
    }
)
```

### 4. 批量评测

对于大规模评测,建议分批处理:

```python
async def batch_evaluate(dataset_id, batch_size=10):
    offset = 0
    while True:
        questions = await manager.get_questions(
            dataset_id=dataset_id,
            limit=batch_size,
            offset=offset
        )
        
        if not questions:
            break
        
        # 处理这一批
        for q in questions:
            # ... 评测逻辑
            pass
        
        offset += batch_size
```

## 故障排除

### 问题: 导入失败

**可能原因:**
- JSON格式不正确
- 数据集名称已存在
- 文件路径错误

**解决方案:**
- 验证JSON格式
- 使用唯一的数据集名称
- 检查文件路径

### 问题: 查询结果为空

**可能原因:**
- 数据集不存在
- 筛选条件过于严格

**解决方案:**
- 使用 `list_datasets()` 检查可用数据集
- 放宽筛选条件
- 使用 `get_dataset_statistics()` 查看数据分布

## 更多示例

查看 `examples/` 目录获取更多示例:
- `import_benchmark.py` - 导入数据集
- `benchmark_evaluation.py` - 运行评测
