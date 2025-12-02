# 数据库和Benchmark管理指南

本指南介绍如何使用评估系统的数据库管理功能。

## 概述

评估系统使用SQLite作为主数据库，提供以下功能：

1. **数据集管理** - 自动加载和管理评测数据集
2. **Benchmark管理** - 创建和运行标准化评测
3. **结果存储** - 高效存储和查询评估结果
4. **统计分析** - 生成排行榜、趋势分析等

## 评测数据集规模建议

基于行业实践，推荐以下数据集规模：

### 快速验证
- **100-500条** - 用于快速验证模型基本能力
- 适合：日常开发、快速迭代
- 评测时间：5-15分钟

### 标准评测
- **1,000-5,000条** - 全面评估模型性能
- 适合：版本发布前评测、模型对比
- 评测时间：30分钟-2小时

### Benchmark级别
- **5,000-10,000+条** - 行业级benchmark
- 适合：公开benchmark、学术研究
- 评测时间：2-6小时

### 数据库性能
SQLite可轻松处理：
- ✅ 10万+条评估记录
- ✅ 1000+个benchmark结果
- ✅ 复杂查询和统计分析
- ✅ 单文件，易于备份和分享

## 数据库架构

### 核心表结构

```
datasets                    # 数据集元数据
├── name (主键)
├── description
├── total_items
├── categories
└── difficulty_distribution

dataset_items              # 数据集条目
├── dataset_name (外键)
├── question
├── ground_truth
├── category
├── difficulty_level
└── tags

benchmarks                 # Benchmark配置
├── name (主键)
├── dataset_name
├── models
└── evaluator_config

benchmark_results          # Benchmark结果
├── benchmark_name
├── model_name
├── average_score
├── dimension_scores
└── timestamp

evaluation_records         # 详细评估记录
├── benchmark_name
├── model_name
├── question
├── model_response
├── overall_score
└── dimension_scores
```

## 支持的数据集格式

### 1. JSON格式

```json
{
  "items": [
    {
      "id": "q1",
      "question": "什么是人工智能？",
      "ground_truth": "人工智能是...",
      "category": "基础概念",
      "difficulty_level": "easy",
      "tags": ["AI", "概念"]
    }
  ]
}
```

### 2. JSONL格式（每行一个JSON对象）

```jsonl
{"id": "q1", "question": "什么是AI？", "answer": "...", "category": "基础"}
{"id": "q2", "question": "什么是ML？", "answer": "...", "category": "基础"}
```

### 3. CSV格式

```csv
id,question,ground_truth,category,difficulty_level
q1,什么是人工智能？,人工智能是...,基础概念,easy
q2,什么是机器学习？,机器学习是...,基础概念,medium
```

### 4. Excel格式（.xlsx）

支持标准Excel文件，列名同CSV格式。

### 字段映射

系统会自动识别以下字段别名：

| 标准字段 | 可识别别名 |
|---------|-----------|
| question | input, prompt |
| ground_truth | answer, expected_output, reference |
| context | background, passage |

## 快速开始

### 1. 加载数据集

```python
from data.dataset_manager import DatasetManager

# 初始化管理器
dataset_manager = DatasetManager()

# 从文件加载
metadata = dataset_manager.load_dataset_from_file(
    file_path="my_dataset.json",
    dataset_name="my_test_dataset",
    description="我的测试数据集",
    version="1.0"
)

print(f"加载了 {metadata.total_items} 条数据")
```

### 2. 创建Benchmark

```python
from data.benchmark_manager import BenchmarkManager

benchmark_manager = BenchmarkManager()

# 创建benchmark配置
config = benchmark_manager.create_benchmark(
    name="my_benchmark_v1",
    dataset_name="my_test_dataset",
    models=["deepseek-chat", "gpt-4"],
    evaluator_config={
        "enable_accuracy": True,
        "enable_relevance": True,
        "enable_completeness": True,
        "enable_fluency": True
    }
)
```

### 3. 运行评测并保存结果

```python
from data.evaluation_storage import EvaluationStorage
from core.evaluation_agent import EvaluationAgent, EvaluationInput
from core.llm_providers import LLMProviderFactory

# 初始化
eval_storage = EvaluationStorage()
evaluator_llm = LLMProviderFactory.create_evaluator_llm()
evaluated_llm = LLMProviderFactory.create_evaluated_llm()

agent = EvaluationAgent(llm=evaluator_llm, config=config)

# 获取数据集
items = dataset_manager.get_dataset("my_test_dataset")

# 运行评测
for item in items:
    # 生成回答
    response = await evaluated_llm.acall(item.question)

    # 评估
    eval_input = EvaluationInput(
        question=item.question,
        ground_truth=item.ground_truth
    )

    result = await agent.evaluate_single(eval_input, response.text)

    # 保存
    record = EvaluationRecord(
        question=item.question,
        model_response=response.text,
        overall_score=result.overall_score,
        dimension_scores=result.dimension_scores,
        # ... 其他字段
    )

    eval_storage.save_evaluation(
        record,
        benchmark_name="my_benchmark_v1",
        dataset_name="my_test_dataset"
    )
```

### 4. 查询和分析

```python
# 获取统计信息
stats = eval_storage.get_statistics(
    benchmark_name="my_benchmark_v1"
)

print(f"平均分: {stats['average_score']}")
print(f"维度分数: {stats['dimension_averages']}")

# 获取排行榜
leaderboard = benchmark_manager.get_leaderboard("my_benchmark_v1")

for entry in leaderboard:
    print(f"{entry['rank']}. {entry['model_name']}: {entry['average_score']}")

# 对比模型
comparison = benchmark_manager.compare_models(
    benchmark_name="my_benchmark_v1",
    model_names=["deepseek-chat", "gpt-4"]
)

print(f"最佳模型: {comparison['winner']}")
```

### 5. 导出结果

```python
# 导出为JSON
benchmark_manager.export_results(
    benchmark_name="my_benchmark_v1",
    output_file="results.json",
    format="json"
)

# 导出为CSV
benchmark_manager.export_results(
    benchmark_name="my_benchmark_v1",
    output_file="results.csv",
    format="csv"
)
```

## 完整工作流示例

运行完整的评测工作流：

```bash
python examples/full_benchmark_workflow.py
```

该示例展示：
1. ✅ 自动加载/创建测试数据集
2. ✅ 创建benchmark配置
3. ✅ 运行完整评测
4. ✅ 存储所有结果
5. ✅ 生成统计报告
6. ✅ 导出结果文件

## 高级功能

### 数据集过滤

```python
# 按类别获取
items = dataset_manager.get_dataset(
    "my_dataset",
    category="基础概念"
)

# 按难度获取
items = dataset_manager.get_dataset(
    "my_dataset",
    difficulty="hard",
    limit=100
)
```

### 趋势分析

```python
# 获取模型的历史趋势
trend = eval_storage.get_trend_data(
    model_name="deepseek-chat",
    days=30
)

for point in trend:
    print(f"{point['date']}: {point['average_score']}")
```

### 最佳/最差案例分析

```python
# 获取表现最好和最差的案例
cases = eval_storage.get_best_worst_cases(
    model_name="deepseek-chat",
    benchmark_name="my_benchmark_v1",
    top_n=10
)

print("最佳案例:")
for case in cases['best']:
    print(f"  Q: {case.question}")
    print(f"  Score: {case.overall_score}")

print("\n最差案例:")
for case in cases['worst']:
    print(f"  Q: {case.question}")
    print(f"  Score: {case.overall_score}")
```

### 数据库维护

```python
# 列出所有数据集
datasets = dataset_manager.list_datasets()

# 获取数据集统计
stats = dataset_manager.get_dataset_stats("my_dataset")

# 删除旧数据（保留90天）
eval_storage.delete_old_evaluations(days=90)

# 删除数据集
dataset_manager.delete_dataset("old_dataset")

# 删除benchmark
benchmark_manager.delete_benchmark("old_benchmark")
```

## 性能优化建议

### 1. 批量处理
```python
# 批量保存评估记录
eval_storage.save_batch_evaluations(records_list)
```

### 2. 并发评测
```python
# 在benchmark配置中设置并发数
config = benchmark_manager.create_benchmark(
    # ...
    parallel_workers=5,  # 同时处理5个
    timeout_per_item=120
)
```

### 3. 采样评测
```python
# 只使用部分数据快速验证
config = benchmark_manager.create_benchmark(
    # ...
    sample_size=500,  # 随机采样500条
    random_seed=42    # 固定随机种子
)
```

## 数据库文件管理

### 默认位置
```
evaluation_results.db  # 主数据库文件
```

### 备份
```bash
# 简单复制即可
cp evaluation_results.db evaluation_results_backup.db
```

### 迁移
```bash
# 直接复制数据库文件到新环境
scp evaluation_results.db user@server:/path/to/project/
```

## 故障排除

### 问题1: 数据库锁定
如果遇到 "database is locked" 错误：
```python
# 确保关闭所有连接
dataset_manager.close()
benchmark_manager.close()
eval_storage.close()
```

### 问题2: 文件格式不识别
检查文件编码（应为UTF-8）：
```python
# 加载时自动检测格式
metadata = dataset_manager.load_dataset_from_file(
    file_path="dataset.json",
    auto_detect_format=True  # 自动检测
)
```

### 问题3: 数据集字段缺失
系统会自动映射常见字段别名，如果仍有问题：
```python
# 检查加载的数据
items = dataset_manager.get_dataset("my_dataset", limit=1)
print(items[0].__dict__)
```

## 最佳实践

1. **命名规范**
   - 数据集名: `<domain>_<type>_<version>` (如 `ai_qa_v1`)
   - Benchmark名: `<dataset>_benchmark_<version>` (如 `ai_qa_benchmark_v1`)

2. **版本管理**
   - 数据集更新时增加版本号
   - 保留历史benchmark结果用于对比

3. **定期备份**
   - 每次重要评测后备份数据库
   - 导出关键结果为JSON/CSV

4. **资源清理**
   - 定期删除旧的评估记录
   - 归档不再使用的数据集

## 参考资料

- [完整工作流示例](../examples/full_benchmark_workflow.py)
- [数据集管理API](../data/dataset_manager.py)
- [Benchmark管理API](../data/benchmark_manager.py)
- [评估存储API](../data/evaluation_storage.py)
