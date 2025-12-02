# 基准数据集系统更新说明

## 更新概览

本次更新为评估系统添加了完整的基准数据集管理功能,支持从JSON文件导入、存储、查询和使用基准测试数据集。

## 主要新增功能

### 1. 评测类型分类系统

新增 `EvaluationType` 枚举,支持四种评测类型:

- **LLM** - 大模型基础问答能力评测
- **RAG** - RAG系统检索和问答评测
- **AGENT** - Agent推理和执行能力评测
- **GENERAL** - 通用评测

### 2. 基准数据集管理

- **数据导入**: 从JSON文件批量导入问答数据
- **灵活查询**: 支持按类型、分类、难度、是否计算题等多维度筛选
- **全文搜索**: 在问题和答案中搜索关键词
- **统计分析**: 自动统计难度分布、分类分布等
- **数据导出**: 将数据集导出为JSON格式

### 3. 数据模型扩展

新增两个核心数据模型:

- **BenchmarkDataset**: 数据集元信息
  - 名称、标题、描述
  - 评测类型
  - 章节信息
  - 问题总数
  - 自定义元数据

- **BenchmarkQuestion**: 问题详情
  - 问题编号、分类
  - 问题和答案内容
  - 关键词列表
  - 是否计算题
  - 难度级别
  - 自定义元数据

## 文件变更

### 新增文件

1. **data/benchmark_dataset_manager.py**
   - 基准数据集管理类
   - 提供导入、查询、搜索、导出等功能

2. **examples/import_benchmark.py**
   - 数据集导入示例
   - 演示如何导入和查看数据集

3. **examples/benchmark_evaluation.py**
   - 评测运行示例
   - 演示如何使用数据集进行评测

4. **docs/BENCHMARK_GUIDE.md**
   - 详细使用指南
   - API参考文档
   - 最佳实践

5. **BENCHMARK_README.md**
   - 快速入门指南
   - 常见用例
   - API快速参考

6. **test_benchmark_system.py**
   - 系统测试脚本
   - 验证功能是否正常

### 修改文件

1. **data/models.py**
   - 新增 `EvaluationType` 枚举
   - 新增 `BenchmarkDataset` 数据类
   - 新增 `BenchmarkQuestion` 数据类
   - 更新 `JSONEncoder` 支持新枚举类型

2. **data/database.py**
   - 新增 `benchmark_datasets` 表
   - 新增 `benchmark_questions` 表
   - 新增相关索引
   - 新增数据集CRUD方法:
     - `save_benchmark_dataset()`
     - `save_benchmark_question()`
     - `get_benchmark_dataset()`
     - `get_benchmark_dataset_by_name()`
     - `list_benchmark_datasets()`
     - `get_benchmark_questions()`
     - `get_benchmark_question_by_number()`
     - `get_benchmark_dataset_statistics()`
     - `search_benchmark_questions()`
     - `delete_benchmark_dataset()`

## 数据库Schema变更

### 新增表: benchmark_datasets

```sql
CREATE TABLE benchmark_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    evaluation_type TEXT NOT NULL,
    chapter_info TEXT,
    total_questions INTEGER DEFAULT 0,
    metadata TEXT,
    created_at DATETIME,
    updated_at DATETIME
)
```

### 新增表: benchmark_questions

```sql
CREATE TABLE benchmark_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    question_number INTEGER,
    category TEXT,
    chapter_info TEXT,
    question TEXT NOT NULL,
    answer TEXT,
    key_words TEXT,
    has_calculation BOOLEAN DEFAULT 0,
    difficulty_level TEXT,
    metadata TEXT,
    FOREIGN KEY (dataset_id) REFERENCES benchmark_datasets(id) ON DELETE CASCADE,
    UNIQUE(dataset_id, question_number)
)
```

### 新增索引

- `idx_benchmark_dataset_type` - 评测类型索引
- `idx_benchmark_questions_dataset` - 数据集ID索引
- `idx_benchmark_questions_difficulty` - 难度级别索引

## 使用示例

### 快速开始

```bash
# 1. 测试系统
python test_benchmark_system.py

# 2. 导入数据集
python examples/import_benchmark.py

# 3. 运行评测
python examples/benchmark_evaluation.py
```

### 代码示例

```python
import asyncio
from data.database import EvaluationDatabase
from data.benchmark_dataset_manager import BenchmarkDatasetManager
from data.models import EvaluationType

async def main():
    # 初始化
    db = EvaluationDatabase("evaluation_results.db")
    manager = BenchmarkDatasetManager(db)
    
    # 导入数据集
    dataset_id = await manager.import_from_json(
        json_path="data/benchmark/qa_structured.json",
        dataset_name="my_benchmark",
        evaluation_type=EvaluationType.LLM
    )
    
    # 查询问题
    questions = await manager.get_questions(dataset_id, limit=10)
    
    # 获取统计
    stats = await manager.get_dataset_statistics(dataset_id)
    print(f"总问题数: {stats['total_questions']}")
    
    db.close()

asyncio.run(main())
```

## 向后兼容性

- 所有新增功能完全向后兼容
- 现有代码无需修改
- 数据库会自动创建新表
- 不影响现有评估流程

## 升级步骤

1. 更新代码到最新版本
2. 首次运行时数据库会自动创建新表
3. 使用 `test_benchmark_system.py` 验证功能
4. 开始使用新功能

## 注意事项

1. **数据集名称唯一性**: 每个数据集名称必须唯一
2. **JSON格式**: 导入的JSON必须符合规定格式
3. **评测类型**: 根据实际用途选择合适的评测类型
4. **元数据**: 建议记录详细元数据便于追踪

## 文档资源

- **快速入门**: `BENCHMARK_README.md`
- **详细指南**: `docs/BENCHMARK_GUIDE.md`
- **示例代码**: `examples/` 目录
- **测试脚本**: `test_benchmark_system.py`

## 常见问题

### Q: 如何导入自己的数据集?

A: 准备符合格式的JSON文件,然后使用:
```python
await manager.import_from_json(
    json_path="your_data.json",
    dataset_name="unique_name",
    evaluation_type=EvaluationType.LLM
)
```

### Q: 如何区分不同类型的评测?

A: 使用 `evaluation_type` 参数:
- `EvaluationType.LLM` - 大模型问答
- `EvaluationType.RAG` - RAG系统
- `EvaluationType.AGENT` - Agent任务

### Q: 可以筛选特定难度的问题吗?

A: 可以,使用:
```python
questions = await manager.get_questions(
    dataset_id,
    difficulty="hard"  # easy/medium/hard
)
```

### Q: 如何搜索包含特定关键词的问题?

A: 使用搜索功能:
```python
results = await manager.search_questions(
    dataset_id,
    keyword="关键词",
    search_in_answer=True  # 同时搜索答案
)
```

## 下一步计划

未来可能的扩展:
- 支持更多数据格式(CSV, Excel等)
- 批量评测工具
- 评测结果可视化
- 数据集版本管理
- 自动难度评估

## 技术支持

如有问题请参考:
- 文档: `docs/BENCHMARK_GUIDE.md`
- 示例: `examples/` 目录
- 测试: `test_benchmark_system.py`
