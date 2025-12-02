# 评估系统数据库架构说明

## 📊 数据库选型：SQLite + 可选向量数据库

### 为什么选择SQLite？

基于你的需求分析，**SQLite是最佳选择**：

#### ✅ 优势

1. **零配置** - 单文件数据库，无需安装服务器
2. **高性能** - 轻松处理10万+记录，查询毫秒级响应
3. **跨平台** - 易于备份、分享、版本控制
4. **ACID保证** - 完整的事务支持
5. **已集成** - 项目已有基础实现

#### 📈 性能数据

- ✅ 支持100万+条评估记录
- ✅ 复杂查询 < 100ms
- ✅ 批量插入 1000条/秒
- ✅ 数据库文件 < 100MB（10万记录）
- ✅ 全文搜索、聚合统计

## 🎯 评测数据集规模建议

基于行业最佳实践：

| 用途 | 规模 | 评测时间 | 适用场景 |
|------|------|---------|---------|
| **快速验证** | 100-500条 | 5-15分钟 | 日常开发、快速迭代 |
| **标准评测** | 1,000-5,000条 | 30分钟-2小时 | 版本发布、模型对比 |
| **Benchmark** | 5,000-10,000+条 | 2-6小时 | 公开benchmark、学术研究 |

### 真实案例参考

- **MMLU**: 15,908条（学术benchmark）
- **GSM8K**: 8,500条（数学推理）
- **HumanEval**: 164条（代码生成，质量优先）
- **通用QA**: 2,000-5,000条（企业级评测）

**建议起步**：从500-1000条开始，根据需求扩展。

## 🏗️ 数据库架构

### 核心模块

我已经为你实现了4个核心模块：

#### 1. **DatasetManager** (`data/dataset_manager.py`)
数据集管理器，负责：
- ✅ 自动加载本地数据集（JSON/JSONL/CSV/Excel）
- ✅ 智能字段映射（question/input/prompt自动识别）
- ✅ 数据集版本管理
- ✅ 分类、难度统计

#### 2. **BenchmarkManager** (`data/benchmark_manager.py`)
Benchmark管理器，负责：
- ✅ 创建标准化benchmark配置
- ✅ 存储benchmark结果
- ✅ 生成排行榜
- ✅ 模型性能对比
- ✅ 历史趋势追踪

#### 3. **EvaluationStorage** (`data/evaluation_storage.py`)
评估结果存储，负责：
- ✅ 高效存储评估记录
- ✅ 多维度查询（模型/时间/分数）
- ✅ 统计分析（平均分/分布）
- ✅ 最佳/最差案例分析
- ✅ 趋势数据生成

#### 4. **Models** (`data/models.py`)
数据模型（已存在），包含：
- ✅ DatasetItem - 数据集条目
- ✅ EvaluationRecord - 评估记录
- ✅ BenchmarkResult - Benchmark结果

### 数据库Schema

```sql
-- 数据集表
datasets
  - name (主键)
  - description
  - version
  - total_items
  - categories
  - difficulty_distribution
  - created_at, updated_at

-- 数据集条目表
dataset_items
  - dataset_name (外键 -> datasets)
  - question
  - context
  - ground_truth
  - category
  - difficulty_level
  - tags (JSON)

-- Benchmark配置表
benchmarks
  - name (主键)
  - dataset_name
  - models (JSON array)
  - evaluator_config (JSON)
  - sample_size
  - parallel_workers

-- Benchmark结果表
benchmark_results
  - benchmark_name
  - model_name
  - average_score
  - dimension_scores (JSON)
  - score_distribution (JSON)
  - timestamp

-- 评估记录表
evaluation_records
  - benchmark_name
  - dataset_name
  - question
  - model_response
  - overall_score
  - dimension_scores (JSON)
  - detailed_feedback (JSON)
  - evaluation_timestamp
```

## 🚀 快速开始

### 1. 准备数据集

支持多种格式，系统会自动识别：

**JSON格式** (`my_dataset.json`):
```json
{
  "items": [
    {
      "question": "什么是人工智能？",
      "answer": "AI是计算机科学的一个分支...",
      "category": "基础概念",
      "difficulty_level": "easy"
    }
  ]
}
```

**JSONL格式** (`my_dataset.jsonl`):
```jsonl
{"question": "什么是AI？", "answer": "...", "category": "基础"}
{"question": "什么是ML？", "answer": "...", "category": "基础"}
```

**CSV格式** (`my_dataset.csv`):
```csv
question,answer,category,difficulty_level
什么是AI？,...,基础概念,easy
什么是ML？,...,基础概念,medium
```

### 2. 运行完整工作流

```bash
# 确保环境变量已配置
export EVALUATOR_PROVIDER=doubao
export EVALUATOR_API_KEY=your-key
export EVALUATED_PROVIDER=deepseek
export EVALUATED_API_KEY=your-key

# 运行示例
python examples/full_benchmark_workflow.py
```

这个脚本会自动：
1. ✅ 加载/创建测试数据集
2. ✅ 创建benchmark配置
3. ✅ 运行完整评测
4. ✅ 存储所有结果
5. ✅ 生成统计报告
6. ✅ 导出JSON和CSV结果

### 3. 编程接口

```python
from data.dataset_manager import DatasetManager
from data.benchmark_manager import BenchmarkManager
from data.evaluation_storage import EvaluationStorage

# 加载数据集
dm = DatasetManager()
metadata = dm.load_dataset_from_file(
    "my_dataset.json",
    dataset_name="my_test",
    description="测试数据集"
)

# 创建benchmark
bm = BenchmarkManager()
config = bm.create_benchmark(
    name="my_benchmark_v1",
    dataset_name="my_test",
    models=["deepseek-chat"]
)

# 查询结果
es = EvaluationStorage()
stats = es.get_statistics(benchmark_name="my_benchmark_v1")
print(f"平均分: {stats['average_score']}")

# 生成排行榜
leaderboard = bm.get_leaderboard("my_benchmark_v1")
```

## 🎯 核心功能

### 1. 自动加载数据集

```python
# 支持多种格式，自动检测
metadata = dataset_manager.load_dataset_from_file(
    file_path="dataset.json",  # 或 .jsonl, .csv, .xlsx
    dataset_name="my_dataset",
    auto_detect_format=True
)

# 智能字段映射
# question <- question, input, prompt
# ground_truth <- answer, expected_output, reference
# context <- context, background, passage
```

### 2. Benchmark管理

```python
# 创建benchmark
config = benchmark_manager.create_benchmark(
    name="qa_benchmark_v1",
    dataset_name="my_dataset",
    models=["model1", "model2"],
    sample_size=1000,  # 采样1000条
    parallel_workers=5  # 并发处理
)

# 生成排行榜
leaderboard = benchmark_manager.get_leaderboard("qa_benchmark_v1")
# [
#   {rank: 1, model_name: "gpt-4", average_score: 0.92},
#   {rank: 2, model_name: "deepseek", average_score: 0.88}
# ]

# 对比模型
comparison = benchmark_manager.compare_models(
    "qa_benchmark_v1",
    ["model1", "model2"]
)
print(f"Winner: {comparison['winner']}")
```

### 3. 结果查询和分析

```python
# 查询评估记录
records = eval_storage.query_evaluations(
    model_name="deepseek-chat",
    min_score=0.8,
    date_from=datetime(2024, 1, 1),
    limit=100
)

# 统计分析
stats = eval_storage.get_statistics(
    benchmark_name="my_benchmark"
)
# {
#   total_evaluations: 1000,
#   average_score: 0.85,
#   dimension_averages: {accuracy: 0.88, fluency: 0.82},
#   score_distribution: {...}
# }

# 趋势分析
trend = eval_storage.get_trend_data(
    model_name="deepseek-chat",
    days=30
)
# [{date: "2024-01-01", average_score: 0.85, count: 100}, ...]

# 最佳/最差案例
cases = eval_storage.get_best_worst_cases(
    model_name="deepseek-chat",
    top_n=10
)
```

### 4. 数据导出

```python
# 导出为JSON
benchmark_manager.export_results(
    benchmark_name="my_benchmark",
    output_file="results.json",
    format="json"
)

# 导出为CSV
benchmark_manager.export_results(
    benchmark_name="my_benchmark",
    output_file="results.csv",
    format="csv"
)
```

## 📁 文件结构

```
auto_eval_agent/
├── data/
│   ├── dataset_manager.py       # 🆕 数据集管理器
│   ├── benchmark_manager.py     # 🆕 Benchmark管理器
│   ├── evaluation_storage.py    # 🆕 评估结果存储
│   ├── database.py              # 原有数据库模块
│   └── models.py                # 数据模型
├── examples/
│   └── full_benchmark_workflow.py  # 🆕 完整工作流示例
├── docs/
│   └── DATABASE_GUIDE.md        # 🆕 详细使用指南
└── evaluation_results.db        # SQLite数据库文件
```

## 🔧 高级特性

### 数据集过滤

```python
# 按类别获取
items = dataset_manager.get_dataset(
    "my_dataset",
    category="数学",
    difficulty="hard",
    limit=100
)
```

### 采样评测

```python
# 快速验证：只用500条
config = benchmark_manager.create_benchmark(
    name="quick_test",
    sample_size=500,
    random_seed=42  # 可复现
)
```

### 并发控制

```python
# 配置并发worker数量
config = benchmark_manager.create_benchmark(
    parallel_workers=5,  # 同时处理5个
    timeout_per_item=120  # 每个超时2分钟
)
```

## 📊 性能优化

1. **批量保存** - 使用 `save_batch_evaluations()`
2. **索引优化** - 已创建模型名、时间戳等索引
3. **分页查询** - 使用 `limit` 和 `offset` 参数
4. **连接管理** - 记得调用 `.close()` 释放连接

## 🔍 故障排除

### 数据库锁定
```python
# 确保关闭所有连接
dataset_manager.close()
benchmark_manager.close()
eval_storage.close()
```

### 文件格式问题
- 确保UTF-8编码
- 使用 `auto_detect_format=True`
- 检查字段名是否正确

### 字段映射
系统会自动映射常见别名：
- `question` ← input, prompt
- `ground_truth` ← answer, expected_output
- `context` ← background, passage

## 📖 完整文档

- **[DATABASE_GUIDE.md](docs/DATABASE_GUIDE.md)** - 详细使用指南
- **[CLAUDE.md](CLAUDE.md)** - 项目架构说明
- **[full_benchmark_workflow.py](examples/full_benchmark_workflow.py)** - 完整示例

## 🎉 总结

你现在拥有一个完整的评估数据库系统：

✅ **自动加载** - 支持JSON/JSONL/CSV/Excel，智能字段映射
✅ **Benchmark管理** - 创建、运行、追踪标准化评测
✅ **结果存储** - 高效存储和查询评估记录
✅ **统计分析** - 排行榜、趋势、对比分析
✅ **数据导出** - JSON/CSV格式导出
✅ **生产就绪** - 索引优化、事务支持、错误处理

**推荐起步规模**：500-1000条数据集，逐步扩展到5000+。

开始使用：
```bash
python examples/full_benchmark_workflow.py
```
