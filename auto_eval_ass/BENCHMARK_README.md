# 基准数据集系统使用说明

## 概述

本系统已扩展支持基准数据集的存储和管理,可以方便地导入、查询和使用基准测试数据集进行各类评测。

## 核心功能

### 1. 评测类型分类

系统支持以下评测类型:

- **LLM评测** (`EvaluationType.LLM`) - 大模型基础问答能力评测
- **RAG评测** (`EvaluationType.RAG`) - RAG系统检索和问答评测  
- **Agent评测** (`EvaluationType.AGENT`) - Agent推理和执行能力评测
- **通用评测** (`EvaluationType.GENERAL`) - 通用评测

### 2. 数据集管理

- 从JSON文件导入基准数据集
- 按评测类型、分类、难度等条件查询问题
- 搜索问题内容
- 导出数据集为JSON
- 统计分析(总数、难度分布、分类分布等)

### 3. 数据结构

每个基准数据集包含:
- 数据集元信息(名称、标题、描述、评测类型等)
- 问题列表(问题、答案、分类、难度、是否计算题等)

## 快速开始

### 步骤1: 导入数据集

```bash
python examples/import_benchmark.py
```

这会从 `data/benchmark/qa_structured.json` 导入数据集,并自动创建三个版本:
- `materials_science_qa_llm` (LLM评测)
- `materials_science_qa_rag` (RAG评测)
- `materials_science_qa_agent` (Agent评测)

### 步骤2: 运行评测

```python
import asyncio
from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType

async def main():
    db = EvaluationDatabase("evaluation_results.db")
    manager = BenchmarkDatasetManager(db)
    
    # 获取数据集
    dataset = await manager.get_dataset_by_name("materials_science_qa_llm")
    
    # 获取问题
    questions = await manager.get_questions(dataset.id, limit=10)
    
    # 查看统计
    stats = await manager.get_dataset_statistics(dataset.id)
    print(f"总问题数: {stats['total_questions']}")
    print(f"难度分布: {stats['difficulty_distribution']}")
    
    db.close()

asyncio.run(main())
```

## 文件结构

新增/修改的文件:

```
data/
├── models.py                          # 新增 EvaluationType, BenchmarkDataset, BenchmarkQuestion
├── database.py                        # 新增基准数据集相关数据库操作方法
├── benchmark_dataset_manager.py       # 新增基准数据集管理类
└── benchmark/
    └── qa_structured.json            # 示例基准数据集

examples/
├── import_benchmark.py               # 新增导入示例
└── benchmark_evaluation.py           # 新增评测示例

docs/
└── BENCHMARK_GUIDE.md                # 新增详细使用指南
```

## 数据库Schema

新增两张表:

### benchmark_datasets 表
- 存储数据集元信息
- 字段: id, name, title, description, evaluation_type, chapter_info, total_questions, metadata, created_at, updated_at

### benchmark_questions 表  
- 存储问题详情
- 字段: id, dataset_id, question_number, category, chapter_info, question, answer, key_words, has_calculation, difficulty_level, metadata

## API 快速参考

### 导入数据集

```python
dataset_id = await manager.import_from_json(
    json_path="path/to/dataset.json",
    dataset_name="my_benchmark",
    evaluation_type=EvaluationType.LLM,
    metadata={"domain": "math"}
)
```

### 查询数据集

```python
# 按名称获取
dataset = await manager.get_dataset_by_name("my_benchmark")

# 列出所有LLM评测数据集
llm_datasets = await manager.list_datasets(EvaluationType.LLM)
```

### 查询问题

```python
# 基本查询
questions = await manager.get_questions(dataset_id, limit=10)

# 按条件筛选
hard_questions = await manager.get_questions(
    dataset_id=dataset_id,
    difficulty="hard",
    has_calculation=True
)

# 按分类筛选
category_questions = await manager.get_questions(
    dataset_id=dataset_id,
    category="晶体结构"
)

# 搜索
results = await manager.search_questions(
    dataset_id=dataset_id,
    keyword="晶体",
    search_in_answer=False
)
```

### 统计信息

```python
stats = await manager.get_dataset_statistics(dataset_id)
# 返回:
# {
#   'total_questions': 100,
#   'calculation_questions': 20,
#   'difficulty_distribution': {'easy': 30, 'medium': 50, 'hard': 20},
#   'category_distribution': {'分类1': 40, '分类2': 60}
# }
```

## JSON格式要求

基准数据集JSON格式:

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

## 常见用例

### 用例1: LLM问答能力评测

```python
# 1. 导入LLM评测数据集
dataset_id = await manager.import_from_json(
    json_path="qa_dataset.json",
    dataset_name="qa_benchmark_llm",
    evaluation_type=EvaluationType.LLM
)

# 2. 获取问题并评测
questions = await manager.get_questions(dataset_id)
for q in questions:
    # 让LLM回答
    response = await llm.acall(q.question)
    # 评估答案质量
    result = await agent.evaluate_single(
        EvaluationInput(question=q.question, ground_truth=q.answer),
        response.text
    )
```

### 用例2: RAG系统评测

```python
# 1. 导入RAG评测数据集
dataset_id = await manager.import_from_json(
    json_path="rag_dataset.json",
    dataset_name="rag_benchmark",
    evaluation_type=EvaluationType.RAG
)

# 2. 评测RAG系统
questions = await manager.get_questions(dataset_id)
for q in questions:
    # 检索相关文档
    docs = rag_system.retrieve(q.question)
    # 生成答案
    answer = rag_system.generate(q.question, docs)
    # 评估
    result = await agent.evaluate_single(
        EvaluationInput(question=q.question, ground_truth=q.answer, context=docs),
        answer
    )
```

### 用例3: 按难度分级评测

```python
# 分别评测不同难度
for difficulty in ['easy', 'medium', 'hard']:
    questions = await manager.get_questions(
        dataset_id=dataset_id,
        difficulty=difficulty
    )
    
    scores = []
    for q in questions:
        result = await evaluate(q)
        scores.append(result.overall_score)
    
    print(f"{difficulty} 难度平均分: {sum(scores)/len(scores):.2f}")
```

## 详细文档

查看 `docs/BENCHMARK_GUIDE.md` 获取完整的使用指南和API文档。

## 示例代码

- `examples/import_benchmark.py` - 数据集导入示例
- `examples/benchmark_evaluation.py` - 评测运行示例

## 注意事项

1. **数据集名称唯一性**: 每个数据集名称必须唯一,重复导入会失败
2. **评测类型选择**: 根据实际评测目的选择合适的评测类型
3. **元数据记录**: 建议在导入和评测时记录详细的元数据,便于后续分析
4. **批量处理**: 对于大规模数据集,建议分批处理避免内存问题

## 技术支持

如有问题,请参考:
- 详细文档: `docs/BENCHMARK_GUIDE.md`
- 示例代码: `examples/` 目录
- 数据模型: `data/models.py`
