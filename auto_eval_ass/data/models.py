"""
数据模型定义

定义评估系统使用的各种数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

class ModelType(Enum):
    """模型类型枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"

class EvaluationStatus(Enum):
    """评估状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EvaluationType(Enum):
    """评估类型枚举"""
    LLM = "llm"  # 大模型评测
    RAG = "rag"  # RAG系统评测
    AGENT = "agent"  # Agent评测
    GENERAL = "general"  # 通用评测

@dataclass
class ModelConfiguration:
    """模型配置"""
    name: str
    model_type: ModelType
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'model_type': self.model_type.value,
            'version': self.version,
            'parameters': self.parameters,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfiguration':
        """从字典创建对象"""
        return cls(
            name=data['name'],
            model_type=ModelType(data['model_type']),
            version=data['version'],
            parameters=data.get('parameters', {}),
            api_key=data.get('api_key'),
            endpoint=data.get('endpoint'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens'),
            top_p=data.get('top_p'),
            frequency_penalty=data.get('frequency_penalty', 0.0),
            presence_penalty=data.get('presence_penalty', 0.0),
            timeout=data.get('timeout', 30),
            retry_count=data.get('retry_count', 3),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )

@dataclass
class EvaluationRecord:
    """评估记录"""
    id: Optional[int] = None
    session_id: Optional[str] = None
    question: str = ""
    context: Optional[str] = None
    ground_truth: Optional[str] = None
    model_response: str = ""
    model_name: str = ""
    model_config: Optional[Dict[str, Any]] = None
    overall_score: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    detailed_feedback: Dict[str, str] = field(default_factory=dict)
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question': self.question,
            'context': self.context,
            'ground_truth': self.ground_truth,
            'model_response': self.model_response,
            'model_name': self.model_name,
            'model_config': self.model_config,
            'overall_score': self.overall_score,
            'dimension_scores': self.dimension_scores,
            'detailed_feedback': self.detailed_feedback,
            'evaluation_timestamp': self.evaluation_timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationRecord':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            session_id=data.get('session_id'),
            question=data.get('question', ''),
            context=data.get('context'),
            ground_truth=data.get('ground_truth'),
            model_response=data.get('model_response', ''),
            model_name=data.get('model_name', ''),
            model_config=data.get('model_config'),
            overall_score=data.get('overall_score', 0.0),
            dimension_scores=data.get('dimension_scores', {}),
            detailed_feedback=data.get('detailed_feedback', {}),
            evaluation_timestamp=datetime.fromisoformat(data['evaluation_timestamp']) if data.get('evaluation_timestamp') else datetime.now(),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )

@dataclass
class EvaluationSession:
    """评估会话"""
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

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_name': self.model_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_evaluations': self.total_evaluations,
            'average_score': self.average_score,
            'status': self.status.value,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationSession':
        """从字典创建对象"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            model_name=data.get('model_name', ''),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else datetime.now(),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            total_evaluations=data.get('total_evaluations', 0),
            average_score=data.get('average_score', 0.0),
            status=EvaluationStatus(data.get('status', 'pending')),
            metadata=data.get('metadata', {})
        )

@dataclass
class DatasetItem:
    """数据集项目"""
    id: Optional[str] = None
    question: str = ""
    context: Optional[str] = None
    ground_truth: Optional[str] = None
    difficulty_level: str = "medium"  # easy, medium, hard
    category: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'question': self.question,
            'context': self.context,
            'ground_truth': self.ground_truth,
            'difficulty_level': self.difficulty_level,
            'category': self.category,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetItem':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            question=data.get('question', ''),
            context=data.get('context'),
            ground_truth=data.get('ground_truth'),
            difficulty_level=data.get('difficulty_level', 'medium'),
            category=data.get('category', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )

@dataclass
class BenchmarkDataset:
    """基准数据集"""
    id: Optional[int] = None
    name: str = ""
    title: str = ""
    description: str = ""
    evaluation_type: EvaluationType = EvaluationType.GENERAL
    chapter_info: Optional[str] = None
    total_questions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'evaluation_type': self.evaluation_type.value,
            'chapter_info': self.chapter_info,
            'total_questions': self.total_questions,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkDataset':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            evaluation_type=EvaluationType(data.get('evaluation_type', 'general')),
            chapter_info=data.get('chapter_info'),
            total_questions=data.get('total_questions', 0),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )

@dataclass
class BenchmarkQuestion:
    """基准数据集问题"""
    id: Optional[int] = None
    dataset_id: Optional[int] = None
    question_number: int = 0
    category: List[str] = field(default_factory=list)
    chapter_info: Optional[str] = None
    question: str = ""
    answer: str = ""
    key_words: List[str] = field(default_factory=list)
    has_calculation: bool = False
    difficulty_level: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'question_number': self.question_number,
            'category': self.category,
            'chapter_info': self.chapter_info,
            'question': self.question,
            'answer': self.answer,
            'key_words': self.key_words,
            'has_calculation': self.has_calculation,
            'difficulty_level': self.difficulty_level,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkQuestion':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            dataset_id=data.get('dataset_id'),
            question_number=data.get('question_number', 0),
            category=data.get('category', []),
            chapter_info=data.get('chapter_info'),
            question=data.get('question', ''),
            answer=data.get('answer', ''),
            key_words=data.get('key_words', []),
            has_calculation=data.get('has_calculation', False),
            difficulty_level=data.get('difficulty_level', 'medium'),
            metadata=data.get('metadata', {})
        )

@dataclass
class OptimizationResult:
    """优化结果"""
    original_score: float
    optimized_score: float
    improvement: float
    parameter_changes: Dict[str, Any]
    optimization_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'original_score': self.original_score,
            'optimized_score': self.optimized_score,
            'improvement': self.improvement,
            'parameter_changes': self.parameter_changes,
            'optimization_timestamp': self.optimization_timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationResult':
        """从字典创建对象"""
        return cls(
            original_score=data['original_score'],
            optimized_score=data['optimized_score'],
            improvement=data['improvement'],
            parameter_changes=data['parameter_changes'],
            optimization_timestamp=datetime.fromisoformat(data['optimization_timestamp']) if data.get('optimization_timestamp') else datetime.now(),
            metadata=data.get('metadata', {})
        )

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    model_name: str
    dataset_name: str
    total_samples: int
    average_score: float
    dimension_scores: Dict[str, float]
    score_distribution: Dict[str, int]
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'dataset_name': self.dataset_name,
            'total_samples': self.total_samples,
            'average_score': self.average_score,
            'dimension_scores': self.dimension_scores,
            'score_distribution': self.score_distribution,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """从字典创建对象"""
        return cls(
            model_name=data['model_name'],
            dataset_name=data['dataset_name'],
            total_samples=data['total_samples'],
            average_score=data['average_score'],
            dimension_scores=data['dimension_scores'],
            score_distribution=data['score_distribution'],
            execution_time=data['execution_time'],
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            metadata=data.get('metadata', {})
        )

class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (ModelType, EvaluationStatus, EvaluationType)):
            return obj.value
        return super().default(obj)

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