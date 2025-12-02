"""
评估数据库管理模块

负责评估数据的存储、查询和管理
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging

from ..core.evaluation_agent import EvaluationResult, EvaluationInput
from .models import (
    EvaluationRecord,
    ModelConfig,
    EvaluationSession,
    BenchmarkDataset,
    BenchmarkQuestion,
    EvaluationType
)

logger = logging.getLogger(__name__)

@dataclass
class QueryFilter:
    """查询过滤器"""
    model_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    dimension: Optional[str] = None
    tags: Optional[List[str]] = None

class EvaluationDatabase:
    """
    评估数据库管理类

    提供评估数据的CRUD操作、统计查询和历史管理功能
    """

    def __init__(self, db_path: str = "evaluation_results.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """初始化数据库表结构"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问

            # 创建评估记录表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    question TEXT NOT NULL,
                    context TEXT,
                    ground_truth TEXT,
                    model_response TEXT NOT NULL,
                    model_name TEXT,
                    model_config TEXT,
                    overall_score REAL,
                    dimension_scores TEXT,
                    detailed_feedback TEXT,
                    evaluation_timestamp DATETIME,
                    metadata TEXT,
                    tags TEXT
                )
            """)

            # 创建模型配置表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS model_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT UNIQUE NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)

            # 创建评估会话表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    model_name TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    total_evaluations INTEGER,
                    average_score REAL,
                    status TEXT,
                    metadata TEXT
                )
            """)

            # 创建基准数据集表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_datasets (
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
            """)

            # 创建基准数据集问题表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_questions (
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
            """)

            # 创建索引
            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluation_timestamp
                ON evaluation_records(evaluation_timestamp)
            """)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_name
                ON evaluation_records(model_name)
            """)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_overall_score
                ON evaluation_records(overall_score)
            """)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_dataset_type
                ON benchmark_datasets(evaluation_type)
            """)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_questions_dataset
                ON benchmark_questions(dataset_id)
            """)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_questions_difficulty
                ON benchmark_questions(difficulty_level)
            """)

            self.connection.commit()
            logger.info("数据库初始化完成")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    async def save_evaluation_result(self, result: EvaluationResult) -> str:
        """
        保存评估结果

        Args:
            result: 评估结果对象

        Returns:
            记录ID
        """
        try:
            cursor = self.connection.cursor()

            # 序列化复杂对象
            dimension_scores_json = json.dumps(result.dimension_scores, ensure_ascii=False)
            detailed_feedback_json = json.dumps(result.detailed_feedback, ensure_ascii=False)
            metadata_json = json.dumps(result.metadata, ensure_ascii=False)

            # 提取标签
            tags = result.metadata.get('tags', [])
            tags_json = json.dumps(tags, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO evaluation_records (
                    question, context, ground_truth, model_response, model_name,
                    overall_score, dimension_scores, detailed_feedback,
                    evaluation_timestamp, metadata, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.input_data.question,
                result.input_data.context,
                result.input_data.ground_truth,
                result.model_response,
                result.metadata.get('model_name'),
                result.overall_score,
                dimension_scores_json,
                detailed_feedback_json,
                result.evaluation_timestamp,
                metadata_json,
                tags_json
            ))

            record_id = cursor.lastrowid
            self.connection.commit()

            logger.debug(f"评估结果已保存，记录ID: {record_id}")
            return str(record_id)

        except Exception as e:
            logger.error(f"保存评估结果失败: {e}")
            self.connection.rollback()
            raise

    async def get_evaluation_result(self, record_id: Union[str, int]) -> Optional[EvaluationResult]:
        """
        根据ID获取评估结果

        Args:
            record_id: 记录ID

        Returns:
            评估结果对象或None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM evaluation_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_evaluation_result(row)

        except Exception as e:
            logger.error(f"获取评估结果失败: {e}")
            return None

    async def query_evaluation_results(
        self,
        filter: QueryFilter,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationResult]:
        """
        查询评估结果

        Args:
            filter: 查询过滤器
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            评估结果列表
        """
        try:
            cursor = self.connection.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            if filter.model_name:
                where_conditions.append("model_name = ?")
                params.append(filter.model_name)

            if filter.date_from:
                where_conditions.append("evaluation_timestamp >= ?")
                params.append(filter.date_from)

            if filter.date_to:
                where_conditions.append("evaluation_timestamp <= ?")
                params.append(filter.date_to)

            if filter.min_score is not None:
                where_conditions.append("overall_score >= ?")
                params.append(filter.min_score)

            if filter.max_score is not None:
                where_conditions.append("overall_score <= ?")
                params.append(filter.max_score)

            if filter.tags:
                # 检查是否包含指定标签
                tag_conditions = []
                for tag in filter.tags:
                    tag_conditions.append("JSON_EXTRACT(tags, '$') LIKE ?")
                    params.append(f'%{tag}%')
                where_conditions.append(f"({' OR '.join(tag_conditions)})")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT * FROM evaluation_records
                {where_clause}
                ORDER BY evaluation_timestamp DESC
                LIMIT ? OFFSET ?
            """

            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_evaluation_result(row) for row in rows]

        except Exception as e:
            logger.error(f"查询评估结果失败: {e}")
            return []

    async def get_evaluation_statistics(self, filter: Optional[QueryFilter] = None) -> Dict[str, Any]:
        """
        获取评估统计信息

        Args:
            filter: 查询过滤器（可选）

        Returns:
            统计信息字典
        """
        try:
            cursor = self.connection.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            if filter:
                if filter.model_name:
                    where_conditions.append("model_name = ?")
                    params.append(filter.model_name)

                if filter.date_from:
                    where_conditions.append("evaluation_timestamp >= ?")
                    params.append(filter.date_from)

                if filter.date_to:
                    where_conditions.append("evaluation_timestamp <= ?")
                    params.append(filter.date_to)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 基础统计
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_evaluations,
                    AVG(overall_score) as average_score,
                    MIN(overall_score) as min_score,
                    MAX(overall_score) as max_score,
                    STDDEV(overall_score) as score_std
                FROM evaluation_records
                {where_clause}
            """, params)

            stats_row = cursor.fetchone()

            # 按模型统计
            cursor.execute(f"""
                SELECT
                    model_name,
                    COUNT(*) as count,
                    AVG(overall_score) as avg_score
                FROM evaluation_records
                {where_clause}
                GROUP BY model_name
                ORDER BY count DESC
            """, params)

            model_stats = [dict(row) for row in cursor.fetchall()]

            # 时间分布统计
            cursor.execute(f"""
                SELECT
                    DATE(evaluation_timestamp) as date,
                    COUNT(*) as count,
                    AVG(overall_score) as avg_score
                FROM evaluation_records
                {where_clause}
                GROUP BY DATE(evaluation_timestamp)
                ORDER BY date DESC
                LIMIT 30
            """, params)

            time_stats = [dict(row) for row in cursor.fetchall()]

            return {
                'total_evaluations': stats_row['total_evaluations'] or 0,
                'average_score': stats_row['average_score'] or 0.0,
                'min_score': stats_row['min_score'] or 0.0,
                'max_score': stats_row['max_score'] or 0.0,
                'score_std': stats_row['score_std'] or 0.0,
                'model_statistics': model_stats,
                'time_distribution': time_stats
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    async def save_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """
        保存模型配置

        Args:
            model_name: 模型名称
            config: 配置字典

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            config_json = json.dumps(config, ensure_ascii=False)
            now = datetime.now()

            cursor.execute("""
                INSERT OR REPLACE INTO model_configs
                (model_name, config_json, created_at, updated_at)
                VALUES (?, ?,
                    COALESCE((SELECT created_at FROM model_configs WHERE model_name = ?), ?),
                    ?
                )
            """, (model_name, config_json, model_name, now, now))

            self.connection.commit()
            logger.debug(f"模型配置已保存: {model_name}")
            return True

        except Exception as e:
            logger.error(f"保存模型配置失败: {e}")
            return False

    async def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置

        Args:
            model_name: 模型名称

        Returns:
            配置字典或None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT config_json FROM model_configs WHERE model_name = ?", (model_name,))
            row = cursor.fetchone()

            if row:
                return json.loads(row['config_json'])
            return None

        except Exception as e:
            logger.error(f"获取模型配置失败: {e}")
            return None

    async def create_evaluation_session(
        self,
        session_id: str,
        name: str,
        description: str = "",
        model_name: str = ""
    ) -> bool:
        """
        创建评估会话

        Args:
            session_id: 会话ID
            name: 会话名称
            description: 会话描述
            model_name: 模型名称

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            now = datetime.now()

            cursor.execute("""
                INSERT INTO evaluation_sessions
                (id, name, description, model_name, start_time, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, name, description, model_name, now, "active"))

            self.connection.commit()
            logger.debug(f"评估会话已创建: {session_id}")
            return True

        except Exception as e:
            logger.error(f"创建评估会话失败: {e}")
            return False

    async def update_evaluation_session(self, session_id: str, **kwargs) -> bool:
        """
        更新评估会话

        Args:
            session_id: 会话ID
            **kwargs: 更新字段

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()

            # 构建更新语句
            set_clauses = []
            params = []

            for key, value in kwargs.items():
                if key in ['name', 'description', 'model_name', 'end_time', 'status']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)

            if not set_clauses:
                return False

            set_clause = ", ".join(set_clauses)
            params.append(session_id)

            cursor.execute(f"""
                UPDATE evaluation_sessions
                SET {set_clause}
                WHERE id = ?
            """, params)

            self.connection.commit()
            logger.debug(f"评估会话已更新: {session_id}")
            return True

        except Exception as e:
            logger.error(f"更新评估会话失败: {e}")
            return False

    async def delete_old_records(self, days: int = 30) -> int:
        """
        删除旧的评估记录

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        try:
            cursor = self.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)

            cursor.execute("""
                DELETE FROM evaluation_records
                WHERE evaluation_timestamp < ?
            """, (cutoff_date,))

            deleted_count = cursor.rowcount
            self.connection.commit()

            logger.info(f"已删除 {deleted_count} 条旧记录（{days}天前）")
            return deleted_count

        except Exception as e:
            logger.error(f"删除旧记录失败: {e}")
            return 0

    def _row_to_evaluation_result(self, row) -> EvaluationResult:
        """
        将数据库行转换为评估结果对象

        Args:
            row: 数据库行

        Returns:
            评估结果对象
        """
        # 反序列化JSON字段
        dimension_scores = json.loads(row['dimension_scores'])
        detailed_feedback = json.loads(row['detailed_feedback'])
        metadata = json.loads(row['metadata'])

        # 创建评估输入对象
        input_data = EvaluationInput(
            question=row['question'],
            context=row['context'],
            ground_truth=row['ground_truth'],
            metadata=metadata
        )

        return EvaluationResult(
            input_data=input_data,
            model_response=row['model_response'],
            overall_score=row['overall_score'],
            dimension_scores=dimension_scores,
            detailed_feedback=detailed_feedback,
            evaluation_timestamp=datetime.fromisoformat(row['evaluation_timestamp']),
            metadata=metadata
        )

    # ========== 基准数据集管理方法 ==========

    async def save_benchmark_dataset(self, dataset: BenchmarkDataset) -> Optional[int]:
        """
        保存基准数据集

        Args:
            dataset: 基准数据集对象

        Returns:
            数据集ID或None
        """
        try:
            cursor = self.connection.cursor()
            now = datetime.now()

            metadata_json = json.dumps(dataset.metadata, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO benchmark_datasets
                (name, title, description, evaluation_type, chapter_info,
                 total_questions, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset.name,
                dataset.title,
                dataset.description,
                dataset.evaluation_type.value,
                dataset.chapter_info,
                dataset.total_questions,
                metadata_json,
                now,
                now
            ))

            dataset_id = cursor.lastrowid
            self.connection.commit()

            logger.debug(f"基准数据集已保存: {dataset.name} (ID: {dataset_id})")
            return dataset_id

        except Exception as e:
            logger.error(f"保存基准数据集失败: {e}")
            self.connection.rollback()
            return None

    async def save_benchmark_question(self, question: BenchmarkQuestion) -> bool:
        """
        保存基准数据集问题

        Args:
            question: 问题对象

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()

            category_json = json.dumps(question.category, ensure_ascii=False)
            key_words_json = json.dumps(question.key_words, ensure_ascii=False)
            metadata_json = json.dumps(question.metadata, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO benchmark_questions
                (dataset_id, question_number, category, chapter_info,
                 question, answer, key_words, has_calculation,
                 difficulty_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question.dataset_id,
                question.question_number,
                category_json,
                question.chapter_info,
                question.question,
                question.answer,
                key_words_json,
                question.has_calculation,
                question.difficulty_level,
                metadata_json
            ))

            self.connection.commit()
            return True

        except Exception as e:
            logger.error(f"保存基准问题失败: {e}")
            self.connection.rollback()
            return False

    async def get_benchmark_dataset(self, dataset_id: int) -> Optional[BenchmarkDataset]:
        """
        获取基准数据集

        Args:
            dataset_id: 数据集ID

        Returns:
            BenchmarkDataset对象或None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM benchmark_datasets WHERE id = ?", (dataset_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_benchmark_dataset(row)

        except Exception as e:
            logger.error(f"获取基准数据集失败: {e}")
            return None

    async def get_benchmark_dataset_by_name(self, name: str) -> Optional[BenchmarkDataset]:
        """
        根据名称获取基准数据集

        Args:
            name: 数据集名称

        Returns:
            BenchmarkDataset对象或None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM benchmark_datasets WHERE name = ?", (name,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_benchmark_dataset(row)

        except Exception as e:
            logger.error(f"获取基准数据集失败: {e}")
            return None

    async def list_benchmark_datasets(
        self,
        evaluation_type: Optional[EvaluationType] = None
    ) -> List[BenchmarkDataset]:
        """
        列出所有基准数据集

        Args:
            evaluation_type: 可选的评估类型过滤

        Returns:
            数据集列表
        """
        try:
            cursor = self.connection.cursor()

            if evaluation_type:
                cursor.execute(
                    "SELECT * FROM benchmark_datasets WHERE evaluation_type = ? ORDER BY created_at DESC",
                    (evaluation_type.value,)
                )
            else:
                cursor.execute("SELECT * FROM benchmark_datasets ORDER BY created_at DESC")

            rows = cursor.fetchall()
            return [self._row_to_benchmark_dataset(row) for row in rows]

        except Exception as e:
            logger.error(f"列出基准数据集失败: {e}")
            return []

    async def get_benchmark_questions(
        self,
        dataset_id: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        has_calculation: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BenchmarkQuestion]:
        """
        获取数据集中的问题

        Args:
            dataset_id: 数据集ID
            category: 可选的分类过滤
            difficulty: 可选的难度过滤
            has_calculation: 可选的计算题过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            问题列表
        """
        try:
            cursor = self.connection.cursor()

            where_conditions = ["dataset_id = ?"]
            params = [dataset_id]

            if category:
                where_conditions.append("category LIKE ?")
                params.append(f'%{category}%')

            if difficulty:
                where_conditions.append("difficulty_level = ?")
                params.append(difficulty)

            if has_calculation is not None:
                where_conditions.append("has_calculation = ?")
                params.append(has_calculation)

            where_clause = " AND ".join(where_conditions)
            query = f"SELECT * FROM benchmark_questions WHERE {where_clause} ORDER BY question_number"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_benchmark_question(row) for row in rows]

        except Exception as e:
            logger.error(f"获取基准问题失败: {e}")
            return []

    async def get_benchmark_question_by_number(
        self,
        dataset_id: int,
        question_number: int
    ) -> Optional[BenchmarkQuestion]:
        """
        根据题号获取问题

        Args:
            dataset_id: 数据集ID
            question_number: 题号

        Returns:
            BenchmarkQuestion对象或None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM benchmark_questions WHERE dataset_id = ? AND question_number = ?",
                (dataset_id, question_number)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_benchmark_question(row)

        except Exception as e:
            logger.error(f"获取基准问题失败: {e}")
            return None

    async def get_benchmark_dataset_statistics(self, dataset_id: int) -> Dict[str, Any]:
        """
        获取数据集统计信息

        Args:
            dataset_id: 数据集ID

        Returns:
            统计信息字典
        """
        try:
            cursor = self.connection.cursor()

            # 基本统计
            cursor.execute("""
                SELECT
                    COUNT(*) as total_questions,
                    SUM(CASE WHEN has_calculation = 1 THEN 1 ELSE 0 END) as calculation_questions,
                    SUM(CASE WHEN difficulty_level = 'easy' THEN 1 ELSE 0 END) as easy_count,
                    SUM(CASE WHEN difficulty_level = 'medium' THEN 1 ELSE 0 END) as medium_count,
                    SUM(CASE WHEN difficulty_level = 'hard' THEN 1 ELSE 0 END) as hard_count
                FROM benchmark_questions
                WHERE dataset_id = ?
            """, (dataset_id,))

            stats_row = cursor.fetchone()

            # 分类统计
            cursor.execute("""
                SELECT category
                FROM benchmark_questions
                WHERE dataset_id = ?
            """, (dataset_id,))

            categories = {}
            for row in cursor.fetchall():
                cat_list = json.loads(row['category'])
                for cat in cat_list:
                    categories[cat] = categories.get(cat, 0) + 1

            return {
                'total_questions': stats_row['total_questions'] or 0,
                'calculation_questions': stats_row['calculation_questions'] or 0,
                'difficulty_distribution': {
                    'easy': stats_row['easy_count'] or 0,
                    'medium': stats_row['medium_count'] or 0,
                    'hard': stats_row['hard_count'] or 0
                },
                'category_distribution': categories
            }

        except Exception as e:
            logger.error(f"获取数据集统计信息失败: {e}")
            return {}

    async def search_benchmark_questions(
        self,
        dataset_id: int,
        keyword: str,
        search_in_answer: bool = False
    ) -> List[BenchmarkQuestion]:
        """
        在数据集中搜索问题

        Args:
            dataset_id: 数据集ID
            keyword: 搜索关键词
            search_in_answer: 是否同时搜索答案

        Returns:
            匹配的问题列表
        """
        try:
            cursor = self.connection.cursor()

            if search_in_answer:
                query = """
                    SELECT * FROM benchmark_questions
                    WHERE dataset_id = ? AND (question LIKE ? OR answer LIKE ?)
                    ORDER BY question_number
                """
                params = (dataset_id, f'%{keyword}%', f'%{keyword}%')
            else:
                query = """
                    SELECT * FROM benchmark_questions
                    WHERE dataset_id = ? AND question LIKE ?
                    ORDER BY question_number
                """
                params = (dataset_id, f'%{keyword}%')

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_benchmark_question(row) for row in rows]

        except Exception as e:
            logger.error(f"搜索基准问题失败: {e}")
            return []

    async def delete_benchmark_dataset(self, dataset_id: int) -> bool:
        """
        删除数据集及其所有问题

        Args:
            dataset_id: 数据集ID

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM benchmark_datasets WHERE id = ?", (dataset_id,))
            self.connection.commit()

            logger.info(f"数据集已删除: {dataset_id}")
            return True

        except Exception as e:
            logger.error(f"删除数据集失败: {e}")
            self.connection.rollback()
            return False

    def _row_to_benchmark_dataset(self, row) -> BenchmarkDataset:
        """将数据库行转换为BenchmarkDataset对象"""
        metadata = json.loads(row['metadata']) if row['metadata'] else {}

        return BenchmarkDataset(
            id=row['id'],
            name=row['name'],
            title=row['title'],
            description=row['description'],
            evaluation_type=EvaluationType(row['evaluation_type']),
            chapter_info=row['chapter_info'],
            total_questions=row['total_questions'],
            metadata=metadata,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def _row_to_benchmark_question(self, row) -> BenchmarkQuestion:
        """将数据库行转换为BenchmarkQuestion对象"""
        category = json.loads(row['category']) if row['category'] else []
        key_words = json.loads(row['key_words']) if row['key_words'] else []
        metadata = json.loads(row['metadata']) if row['metadata'] else {}

        return BenchmarkQuestion(
            id=row['id'],
            dataset_id=row['dataset_id'],
            question_number=row['question_number'],
            category=category,
            chapter_info=row['chapter_info'],
            question=row['question'],
            answer=row['answer'],
            key_words=key_words,
            has_calculation=bool(row['has_calculation']),
            difficulty_level=row['difficulty_level'],
            metadata=metadata
        )

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()