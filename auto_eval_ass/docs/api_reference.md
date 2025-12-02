# API参考文档

## 核心API

### EvaluationAgent

评估Agent是系统的核心类，负责协调整个评估流程。

#### 构造函数

```python
EvaluationAgent(
    llm: BaseLLM,
    config: EvaluationConfig,
    database: Optional[EvaluationDatabase] = None
)
```

**参数：**
- `llm`: 语言模型实例，用于评估
- `config`: 评估配置对象
- `database`: 数据库连接（可选）

#### 主要方法

##### evaluate_single

```python
async evaluate_single(
    evaluation_input: EvaluationInput,
    model_response: str
) -> EvaluationResult
```

执行单次评估。

**参数：**
- `evaluation_input`: 评估输入对象
- `model_response`: 模型回答字符串

**返回：**
- `EvaluationResult`: 评估结果对象

**示例：**
```python
eval_input = EvaluationInput(
    question="什么是人工智能？",
    context="基础概念问题"
)
result = await agent.evaluate_single(eval_input, "人工智能是...")
print(f"得分: {result.overall_score}")
```

##### evaluate_batch

```python
async evaluate_batch(
    evaluation_inputs: List[EvaluationInput],
    model_responses: List[str]
) -> List[EvaluationResult]
```

执行批量评估。

**参数：**
- `evaluation_inputs`: 评估输入列表
- `model_responses`: 模型回答列表

**返回：**
- `List[EvaluationResult]`: 评估结果列表

##### evaluate_comparative

```python
async evaluate_comparative(
    evaluation_input: EvaluationInput,
    model_responses: Dict[str, str],
    model_names: Optional[List[str]] = None
) -> Dict[str, EvaluationResult]
```

执行对比评估。

**参数：**
- `evaluation_input`: 评估输入对象
- `model_responses`: 模型回答字典
- `model_names`: 模型名称列表（可选）

**返回：**
- `Dict[str, EvaluationResult]`: 各模型的评估结果字典

### EvaluationInput

评估输入数据结构。

```python
@dataclass
class EvaluationInput:
    question: str
    ground_truth: Optional[str] = None
    context: Optional[str] = None
    conversation_history: Optional[List[BaseMessage]] = None
    metadata: Optional[Dict[str, Any]] = None
```

**字段说明：**
- `question`: 待评估的问题
- `ground_truth`: 参考答案（可选）
- `context`: 上下文信息（可选）
- `conversation_history`: 对话历史（可选）
- `metadata`: 元数据（可选）

### EvaluationResult

评估结果数据结构。

```python
@dataclass
class EvaluationResult:
    input_data: EvaluationInput
    model_response: str
    overall_score: float
    dimension_scores: Dict[str, float]
    detailed_feedback: Dict[str, str]
    evaluation_timestamp: datetime
    metadata: Dict[str, Any]
```

**字段说明：**
- `input_data`: 评估输入数据
- `model_response`: 模型回答
- `overall_score`: 综合得分（0-1）
- `dimension_scores`: 各维度得分
- `detailed_feedback`: 详细反馈
- `evaluation_timestamp`: 评估时间戳
- `metadata`: 元数据

## 数据库API

### EvaluationDatabase

数据库管理类，提供评估数据的CRUD操作。

#### 构造函数

```python
EvaluationDatabase(db_path: str = "evaluation_results.db")
```

#### 主要方法

##### save_evaluation_result

```python
async save_evaluation_result(result: EvaluationResult) -> str
```

保存评估结果。

**参数：**
- `result`: 评估结果对象

**返回：**
- `str`: 记录ID

##### get_evaluation_result

```python
async get_evaluation_result(record_id: Union[str, int]) -> Optional[EvaluationResult]
```

根据ID获取评估结果。

**参数：**
- `record_id`: 记录ID

**返回：**
- `Optional[EvaluationResult]`: 评估结果对象或None

##### query_evaluation_results

```python
async query_evaluation_results(
    filter: QueryFilter,
    limit: int = 100,
    offset: int = 0
) -> List[EvaluationResult]
```

查询评估结果。

**参数：**
- `filter`: 查询过滤器
- `limit`: 返回数量限制
- `offset`: 偏移量

**返回：**
- `List[EvaluationResult]`: 评估结果列表

##### get_evaluation_statistics

```python
async get_evaluation_statistics(
    filter: Optional[QueryFilter] = None
) -> Dict[str, Any]
```

获取评估统计信息。

**参数：**
- `filter`: 查询过滤器（可选）

**返回：**
- `Dict[str, Any]`: 统计信息字典

### QueryFilter

查询过滤器。

```python
@dataclass
class QueryFilter:
    model_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    dimension: Optional[str] = None
    tags: Optional[List[str]] = None
```

## 报告API

### ReportGenerator

报告生成器，支持多种格式的报告生成。

#### 构造函数

```python
ReportGenerator(
    database: EvaluationDatabase,
    output_dir: str = "reports"
)
```

#### 主要方法

##### generate_comprehensive_report

```python
async generate_comprehensive_report(
    filter: Optional[QueryFilter] = None,
    format: str = "html"
) -> str
```

生成综合评估报告。

**参数：**
- `filter`: 查询过滤器（可选）
- `format`: 报告格式（json, html, pdf, text）

**返回：**
- `str`: 报告文件路径

##### generate_comparison_report

```python
async generate_comparison_report(
    model_names: List[str],
    format: str = "html"
) -> str
```

生成模型对比报告。

**参数：**
- `model_names`: 模型名称列表
- `format`: 报告格式

**返回：**
- `str`: 报告文件路径

##### generate_session_report

```python
async generate_session_report(
    session_id: str,
    format: str = "html"
) -> str
```

生成会话评估报告。

**参数：**
- `session_id`: 会话ID
- `format`: 报告格式

**返回：**
- `str`: 报告文件路径

## 可视化API

### EvaluationVisualizer

数据可视化器，生成各种图表。

#### 构造函数

```python
EvaluationVisualizer(output_dir: str = "visualizations")
```

#### 主要方法

##### create_score_distribution_plot

```python
create_score_distribution_plot(
    results: List[EvaluationResult],
    save_path: Optional[str] = None
) -> str
```

创建分数分布图。

**参数：**
- `results`: 评估结果列表
- `save_path`: 保存路径（可选）

**返回：**
- `str`: 图片文件路径

##### create_dimension_radar_chart

```python
create_dimension_radar_chart(
    results: List[EvaluationResult],
    save_path: Optional[str] = None
) -> str
```

创建维度雷达图。

**参数：**
- `results`: 评估结果列表
- `save_path`: 保存路径（可选）

**返回：**
- `str`: 图片文件路径

##### create_model_comparison_plot

```python
create_model_comparison_plot(
    model_results: Dict[str, List[EvaluationResult]],
    save_path: Optional[str] = None
) -> str
```

创建模型对比图。

**参数：**
- `model_results`: 模型结果字典
- `save_path`: 保存路径（可选）

**返回：**
- `str`: 图片文件路径

##### create_interactive_dashboard

```python
create_interactive_dashboard(
    results: List[EvaluationResult],
    save_path: Optional[str] = None
) -> str
```

创建交互式仪表板。

**参数：**
- `results`: 评估结果列表
- `save_path`: 保存路径（可选）

**返回：**
- `str`: HTML文件路径

## 参数优化API

### ParameterOptimizer

参数优化器，支持多种优化策略。

#### 构造函数

```python
ParameterOptimizer(
    database: EvaluationDatabase,
    evaluation_function,
    strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN,
    max_trials: int = 100
)
```

**参数：**
- `database`: 数据库连接
- `evaluation_function`: 评估函数
- `strategy`: 优化策略
- `max_trials`: 最大试验次数

#### 主要方法

##### optimize_parameters

```python
async optimize_parameters(
    model_name: str,
    param_names: List[str],
    evaluation_dataset: List[EvaluationInput],
    target_metric: str = 'overall_score',
    baseline_score: Optional[float] = None
) -> OptimizationResult
```

优化模型参数。

**参数：**
- `model_name`: 模型名称
- `param_names`: 要优化的参数名称列表
- `evaluation_dataset`: 评估数据集
- `target_metric`: 目标指标
- `baseline_score`: 基准分数（可选）

**返回：**
- `OptimizationResult`: 优化结果

##### optimize_for_target_score

```python
async optimize_for_target_score(
    model_name: str,
    target_score: float,
    param_names: List[str],
    evaluation_dataset: List[EvaluationInput],
    max_iterations: int = 50
) -> OptimizationResult
```

针对目标分数进行优化。

**参数：**
- `model_name`: 模型名称
- `target_score`: 目标分数
- `param_names`: 优化参数列表
- `evaluation_dataset`: 评估数据集
- `max_iterations`: 最大迭代次数

**返回：**
- `OptimizationResult`: 优化结果

### RecommendationEngine

智能推荐引擎，提供优化建议。

#### 构造函数

```python
RecommendationEngine(database: EvaluationDatabase)
```

#### 主要方法

##### generate_recommendations

```python
async generate_recommendations(
    model_name: str,
    time_window_days: int = 30,
    min_evaluations: int = 10
) -> List[Recommendation]
```

生成智能推荐建议。

**参数：**
- `model_name`: 模型名称
- `time_window_days`: 分析时间窗口（天）
- `min_evaluations`: 最小评估数量

**返回：**
- `List[Recommendation]`: 推荐建议列表

##### get_recommendation_summary

```python
async get_recommendation_summary(
    model_name: str,
    days: int = 7
) -> Dict[str, Any]
```

获取推荐摘要统计。

**参数：**
- `model_name`: 模型名称
- `days`: 统计天数

**返回：**
- `Dict[str, Any]`: 摘要统计字典

## 配置API

### ConfigManager

配置管理器，支持多种配置加载方式。

#### 构造函数

```python
ConfigManager(config_file: Optional[str] = None)
```

**参数：**
- `config_file`: 配置文件路径（可选）

#### 主要方法

##### load_from_file

```python
load_from_file(config_file: str)
```

从配置文件加载配置。

##### load_from_env

```python
load_from_env()
```

从环境变量加载配置。

##### save_to_file

```python
save_to_file(config_file: str)
```

保存配置到文件。

### EvaluationConfig

评估配置类。

```python
@dataclass
class EvaluationConfig:
    version: str = "1.0.0"
    log_level: LogLevel = LogLevel.INFO
    output_dir: str = "evaluation_output"
    database_path: str = "evaluation_results.db"

    # 评估器配置
    enable_accuracy: bool = True
    enable_relevance: bool = True
    enable_completeness: bool = True
    enable_fluency: bool = True

    # 权重配置
    accuracy_weight: float = 0.3
    relevance_weight: float = 0.25
    completeness_weight: float = 0.25
    fluency_weight: float = 0.2

    # 其他配置...
```

### 配置模板

```python
# 快速评估模板
quick_eval_config = create_config_from_template('quick_eval')

# 综合评估模板
comprehensive_config = create_config_from_template('comprehensive_eval')

# 开发环境模板
development_config = create_config_from_template('development')

# 生产环境模板
production_config = create_config_from_template('production')
```

## 评估器API

### BaseEvaluator

基础评估器抽象类。

#### 抽象方法

```python
@abstractmethod
async evaluate(
    evaluation_input: EvaluationInput,
    model_response: str
) -> Tuple[float, str]
```

执行评估。

**参数：**
- `evaluation_input`: 评估输入
- `model_response`: 模型回答

**返回：**
- `Tuple[float, str]`: (分数, 反馈) 元组

```python
@abstractmethod
def _get_evaluation_prompt() -> str
```

获取评估提示词模板。

**返回：**
- `str`: 提示词模板字符串

```python
@abstractmethod
def get_dimension_name() -> str
```

获取评估维度名称。

**返回：**
- `str`: 维度名称

```python
@abstractmethod
def get_dimension_description() -> str
```

获取评估维度描述。

**返回：**
- `str`: 维度描述

### 具体评估器

#### AccuracyEvaluator

准确性评估器。

```python
class AccuracyEvaluator(BaseEvaluator):
    def get_dimension_name(self) -> str:
        return "准确性"

    def get_dimension_description(self) -> str:
        return "评估回答的事实准确性和信息正确性"
```

#### RelevanceEvaluator

相关性评估器。

```python
class RelevanceEvaluator(BaseEvaluator):
    def get_dimension_name(self) -> str:
        return "相关性"

    def get_dimension_description(self) -> str:
        return "评估回答与问题的相关性和切题程度"
```

#### CompletenessEvaluator

完整性评估器。

```python
class CompletenessEvaluator(BaseEvaluator):
    def get_dimension_name(self) -> str:
        return "完整性"

    def get_dimension_description(self) -> str:
        return "评估回答的信息完整性和覆盖度"
```

#### FluencyEvaluator

流畅性评估器。

```python
class FluencyEvaluator(BaseEvaluator):
    def get_dimension_name(self) -> str:
        return "流畅性"

    def get_dimension_description(self) -> str:
        return "评估回答的语言流畅度和表达自然度"
```

## 工具API

### 数据模型

#### ModelConfiguration

```python
@dataclass
class ModelConfiguration:
    name: str
    model_type: ModelType
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    # ... 其他字段
```

#### EvaluationSession

```python
@dataclass
class EvaluationSession:
    id: str
    name: str
    description: str = ""
    model_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_evaluations: int = 0
    average_score: float = 0.0
    status: EvaluationStatus = EvaluationStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### OptimizationResult

```python
@dataclass
class OptimizationResult:
    original_score: float
    optimized_score: float
    improvement: float
    parameter_changes: Dict[str, Any]
    optimization_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Recommendation

```python
@dataclass
class Recommendation:
    id: str
    type: str
    title: str
    description: str
    priority: str
    confidence: float
    expected_improvement: float
    implementation_effort: str
    parameters: List[str]
    evidence: List[str]
    action_steps: List[str]
    created_at: datetime
```

### 枚举类型

#### ModelType

```python
class ModelType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"
```

#### EvaluationStatus

```python
class EvaluationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

#### OptimizationStrategy

```python
class OptimizationStrategy(Enum):
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    GRADIENT = "gradient"
```

### 工具函数

#### JSON序列化

```python
def serialize_object(obj) -> str:
    """序列化对象为JSON字符串"""
    return json.dumps(obj, cls=JSONEncoder, ensure_ascii=False, indent=2)

def deserialize_object(json_str: str, target_class: type):
    """从JSON字符串反序列化对象"""
    data = json.loads(json_str)
    if hasattr(target_class, 'from_dict'):
        return target_class.from_dict(data)
    else:
        return data
```

#### 数据验证

```python
def validate_evaluation_input(evaluation_input: EvaluationInput) -> bool:
    """验证评估输入的有效性"""
    if not evaluation_input.question or not evaluation_input.question.strip():
        return False
    return True

def validate_score(score: float) -> float:
    """验证分数范围"""
    return max(0.0, min(1.0, score))
```

## 错误处理

### 异常类型

```python
class EvaluationError(Exception):
    """评估相关错误"""
    pass

class ConfigurationError(Exception):
    """配置相关错误"""
    pass

class DatabaseError(Exception):
    """数据库相关错误"""
    pass

class ValidationError(Exception):
    """数据验证错误"""
    pass
```

### 错误处理示例

```python
try:
    result = await agent.evaluate_single(eval_input, model_response)
except EvaluationError as e:
    logger.error(f"评估失败: {e}")
    # 处理评估错误
except ConfigurationError as e:
    logger.error(f"配置错误: {e}")
    # 处理配置错误
except Exception as e:
    logger.error(f"未知错误: {e}")
    # 处理其他错误
```

## 示例代码

### 基础评估示例

```python
import asyncio
from core.evaluation_agent import EvaluationAgent, EvaluationInput
from config.evaluation_config import ConfigManager

async def basic_evaluation_example():
    # 初始化配置
    config_manager = ConfigManager()

    # 初始化评估Agent
    agent = EvaluationAgent(llm=your_llm, config=config_manager.config)

    # 创建评估输入
    eval_input = EvaluationInput(
        question="什么是人工智能？",
        context="基础概念问题"
    )

    # 执行评估
    result = await agent.evaluate_single(eval_input, "人工智能是...")

    # 查看结果
    print(f"综合得分: {result.overall_score}")
    print(f"维度得分: {result.dimension_scores}")
```

### 批量评估示例

```python
async def batch_evaluation_example():
    agent = EvaluationAgent(llm=your_llm, config=config_manager.config)

    # 准备批量数据
    evaluation_inputs = [
        EvaluationInput(question="问题1"),
        EvaluationInput(question="问题2"),
        # ...
    ]

    model_responses = [
        "回答1",
        "回答2",
        # ...
    ]

    # 执行批量评估
    results = await agent.evaluate_batch(evaluation_inputs, model_responses)

    # 分析结果
    avg_score = sum(r.overall_score for r in results) / len(results)
    print(f"平均得分: {avg_score}")
```

### 参数优化示例

```python
async def optimization_example():
    from core.optimization.parameter_optimizer import ParameterOptimizer

    # 初始化优化器
    optimizer = ParameterOptimizer(
        database=database,
        evaluation_function=your_evaluation_function
    )

    # 执行优化
    result = await optimizer.optimize_parameters(
        model_name="gpt-4",
        param_names=["temperature", "max_tokens"],
        evaluation_dataset=test_data
    )

    print(f"优化结果: {result.parameter_changes}")
    print(f"性能提升: {result.improvement}")
```

这份API参考文档涵盖了系统的主要接口和用法，为开发者提供了详细的API使用指南。