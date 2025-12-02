"""
评估系统配置

定义评估系统的各种配置参数和默认值
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import os
from pathlib import Path

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    AZURE = "azure"
    DOUBAO = "doubao"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"

@dataclass
class EvaluatorConfig:
    """评估器配置"""
    enabled: bool = True
    weight: float = 1.0
    timeout: int = 30
    max_retries: int = 3
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationConfig:
    """
    主评估配置类

    包含评估系统的所有配置参数
    """

    # 基础配置
    version: str = "1.0.0"
    log_level: LogLevel = LogLevel.INFO
    output_dir: str = "evaluation_output"

    # 数据库配置
    database_path: str = "evaluation_results.db"
    database_backup_enabled: bool = True
    database_backup_interval: int = 24  # 小时

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

    # 评估器详细配置
    accuracy_config: EvaluatorConfig = field(default_factory=lambda: EvaluatorConfig(
        enabled=True, weight=0.3, timeout=30
    ))
    relevance_config: EvaluatorConfig = field(default_factory=lambda: EvaluatorConfig(
        enabled=True, weight=0.25, timeout=25
    ))
    completeness_config: EvaluatorConfig = field(default_factory=lambda: EvaluatorConfig(
        enabled=True, weight=0.25, timeout=20
    ))
    fluency_config: EvaluatorConfig = field(default_factory=lambda: EvaluatorConfig(
        enabled=True, weight=0.2, timeout=15
    ))

    # LLM配置
    default_provider: ModelProvider = ModelProvider.DOUBAO
    default_model: str = "ep-20250614210935-8mthr"
    max_concurrent_evaluations: int = 5
    evaluation_timeout: int = 120
    
    # 裁判LLM配置（用于评估）
    evaluator_provider: ModelProvider = ModelProvider.DOUBAO
    evaluator_model: str = "ep-20250614210935-8mthr"
    evaluator_api_key: Optional[str] = None
    
    # 参评LLM配置（被评估的模型）
    evaluated_provider: ModelProvider = ModelProvider.DEEPSEEK
    evaluated_model: str = "deepseek-chat"
    evaluated_api_key: Optional[str] = None

    # 报告配置
    generate_html_report: bool = True
    generate_json_report: bool = True
    generate_visualizations: bool = True
    report_template_dir: str = "templates"

    # 优化配置
    enable_auto_optimization: bool = False
    optimization_strategy: str = "bayesian"  # grid_search, random_search, bayesian
    max_optimization_trials: int = 100
    optimization_sample_size: int = 10

    # 批处理配置
    batch_size: int = 50
    enable_progress_bar: bool = True
    save_intermediate_results: bool = True

    # 质量控制
    min_confidence_threshold: float = 0.5
    enable_outlier_detection: bool = True
    outlier_threshold: float = 2.0

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒
    cache_max_size: int = 1000

    # API配置
    api_rate_limit: int = 60  # 每分钟请求次数
    api_retry_delay: float = 1.0  # 秒

    def __post_init__(self):
        """初始化后的处理"""
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # 验证权重总和
        total_weight = (
            self.accuracy_weight +
            self.relevance_weight +
            self.completeness_weight +
            self.fluency_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            # 归一化权重
            self.accuracy_weight /= total_weight
            self.relevance_weight /= total_weight
            self.completeness_weight /= total_weight
            self.fluency_weight /= total_weight

class ConfigManager:
    """
    配置管理器

    支持从文件、环境变量等多种方式加载配置
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径（可选）
        """
        self.config = EvaluationConfig()

        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)

        # 从环境变量加载配置
        self.load_from_env()

    def load_from_file(self, config_file: str):
        """从配置文件加载配置"""
        try:
            import json

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            self._update_config_from_dict(config_data)

        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            'EVAL_LOG_LEVEL': ('log_level', LogLevel),
            'EVAL_OUTPUT_DIR': ('output_dir', str),
            'EVAL_DATABASE_PATH': ('database_path', str),
            'EVAL_ENABLE_ACCURACY': ('enable_accuracy', bool),
            'EVAL_ENABLE_RELEVANCE': ('enable_relevance', bool),
            'EVAL_ENABLE_COMPLETENESS': ('enable_completeness', bool),
            'EVAL_ENABLE_FLUENCY': ('enable_fluency', bool),
            'EVAL_ACCURACY_WEIGHT': ('accuracy_weight', float),
            'EVAL_RELEVANCE_WEIGHT': ('relevance_weight', float),
            'EVAL_COMPLETENESS_WEIGHT': ('completeness_weight', float),
            'EVAL_FLUENCY_WEIGHT': ('fluency_weight', float),
            'EVAL_DEFAULT_PROVIDER': ('default_provider', ModelProvider),
            'EVAL_DEFAULT_MODEL': ('default_model', str),
            'EVAL_MAX_CONCURRENT': ('max_concurrent_evaluations', int),
            'EVAL_BATCH_SIZE': ('batch_size', int),
            'EVAL_ENABLE_CACHE': ('enable_cache', bool),
            'EVAL_API_RATE_LIMIT': ('api_rate_limit', int),
            'EVALUATOR_PROVIDER': ('evaluator_provider', ModelProvider),
            'EVALUATOR_MODEL_NAME': ('evaluator_model', str),
            'EVALUATOR_API_KEY': ('evaluator_api_key', str),
            'EVALUATED_PROVIDER': ('evaluated_provider', ModelProvider),
            'EVALUATED_MODEL_NAME': ('evaluated_model', str),
            'EVALUATED_API_KEY': ('evaluated_api_key', str),
        }

        for env_var, (config_attr, type_converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if type_converter == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif type_converter in (LogLevel, ModelProvider):
                        value = type_converter(value.upper())
                    else:
                        value = type_converter(value)

                    setattr(self.config, config_attr, value)

                except Exception as e:
                    print(f"解析环境变量 {env_var} 失败: {e}")

    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """从字典更新配置"""
        for key, value in config_data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def save_to_file(self, config_file: str):
        """保存配置到文件"""
        try:
            import json

            # 转换为字典，处理特殊类型
            config_dict = self._config_to_dict(self.config)

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def _config_to_dict(self, config: EvaluationConfig) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        result = {}

        for key, value in config.__dict__.items():
            if isinstance(value, (LogLevel, ModelProvider)):
                result[key] = value.value
            elif isinstance(value, EvaluatorConfig):
                result[key] = value.__dict__
            elif isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value

        return result

    def get_model_config(self, provider: ModelProvider, model_name: str) -> Dict[str, Any]:
        """获取特定模型的配置"""
        model_configs = {
            ModelProvider.OPENAI: {
                'api_key_env': 'OPENAI_API_KEY',
                'base_url': 'https://api.openai.com/v1',
                'default_models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                'max_tokens': 4096,
                'temperature_range': (0.0, 2.0),
            },
            ModelProvider.ANTHROPIC: {
                'api_key_env': 'ANTHROPIC_API_KEY',
                'base_url': 'https://api.anthropic.com',
                'default_models': ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'],
                'max_tokens': 4096,
                'temperature_range': (0.0, 1.0),
            },
            ModelProvider.HUGGINGFACE: {
                'api_key_env': 'HUGGINGFACE_API_KEY',
                'base_url': 'https://api-inference.huggingface.co',
                'default_models': ['mistralai/Mistral-7B-Instruct-v0.1'],
                'max_tokens': 2048,
                'temperature_range': (0.0, 2.0),
            },
            ModelProvider.DOUBAO: {
                'api_key_env': 'DOUBAO_API_KEY',
                'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                'default_models': ['ep-20250614210935-8mthr'],
                'max_tokens': 4096,
                'temperature_range': (0.0, 1.0),
            },
            ModelProvider.DEEPSEEK: {
                'api_key_env': 'DEEPSEEK_API_KEY',
                'base_url': 'https://api.deepseek.com',
                'default_models': ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
                'max_tokens': 4096,
                'temperature_range': (0.0, 2.0),
            }
        }

        config = model_configs.get(provider, {})
        config['model_name'] = model_name

        return config

# 默认配置实例
DEFAULT_CONFIG = EvaluationConfig()

# 预定义的配置模板
TEMPLATES = {
    'quick_eval': EvaluationConfig(
        enable_accuracy=True,
        enable_relevance=True,
        enable_completeness=False,  # 快速评估禁用完整性
        enable_fluency=True,
        batch_size=10,
        max_concurrent_evaluations=3
    ),

    'comprehensive_eval': EvaluationConfig(
        enable_accuracy=True,
        enable_relevance=True,
        enable_completeness=True,
        enable_fluency=True,
        batch_size=20,
        max_concurrent_evaluations=2,
        generate_html_report=True,
        generate_visualizations=True
    ),

    'accuracy_focused': EvaluationConfig(
        enable_accuracy=True,
        enable_relevance=False,
        enable_completeness=False,
        enable_fluency=False,
        accuracy_weight=1.0,
        relevance_weight=0.0,
        completeness_weight=0.0,
        fluency_weight=0.0
    ),

    'performance_optimized': EvaluationConfig(
        max_concurrent_evaluations=10,
        batch_size=100,
        evaluation_timeout=60,
        enable_cache=True,
        cache_ttl=7200
    ),

    'development': EvaluationConfig(
        log_level=LogLevel.DEBUG,
        enable_progress_bar=True,
        save_intermediate_results=True,
        generate_html_report=True,
        generate_visualizations=True
    ),

    'production': EvaluationConfig(
        log_level=LogLevel.INFO,
        enable_progress_bar=False,
        save_intermediate_results=False,
        batch_size=50,
        max_concurrent_evaluations=5,
        enable_auto_optimization=True
    )
}

def get_template(template_name: str) -> EvaluationConfig:
    """获取配置模板"""
    if template_name not in TEMPLATES:
        raise ValueError(f"未知的配置模板: {template_name}")

    return TEMPLATES[template_name]

def create_config_from_template(template_name: str, **kwargs) -> EvaluationConfig:
    """基于模板创建配置"""
    config = get_template(template_name)

    # 应用自定义参数
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config