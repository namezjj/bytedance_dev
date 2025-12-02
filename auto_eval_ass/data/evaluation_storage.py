"""
评估结果存储和查询模块

扩展原有database.py，提供更强大的查询和分析功能
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from .models import EvaluationRecord, BenchmarkResult

logger = logging.getLogger(__name__)


class EvaluationStorage:
    """
    评估结果存储和查询类

    提供高级查询、统计分析、数据导出等功能
    """

    def __init__(self, db_path: str = "evaluation_results.db"):
        """初始化存储"""
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

        # 扩展评估记录表（如果不存在）
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                benchmark_name TEXT,
                dataset_name TEXT,
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
                execution_time REAL,
                metadata TEXT,
                tags TEXT
            )
        """)

        # 创建性能索引
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_model
            ON evaluation_records(model_name)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_benchmark
            ON evaluation_records(benchmark_name)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_timestamp
            ON evaluation_records(evaluation_timestamp)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_eval_score
            ON evaluation_records(overall_score)
        """)

        self.connection.commit()
        logger.info(f"评估存储数据库初始化成功: {self.db_path}")

    def save_evaluation(
        self,
        record: EvaluationRecord,
        benchmark_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> int:
        """
        保存单个评估记录

        Args:
            record: 评估记录
            benchmark_name: Benchmark名称
            dataset_name: 数据集名称
            execution_time: 执行时间（秒）

        Returns:
            int: 记录ID
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO evaluation_records
            (session_id, benchmark_name, dataset_name, question, context, ground_truth,
             model_response, model_name, model_config, overall_score, dimension_scores,
             detailed_feedback, evaluation_timestamp, execution_time, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.session_id,
            benchmark_name,
            dataset_name,
            record.question,
            record.context,
            record.ground_truth,
            record.model_response,
            record.model_name,
            json.dumps(record.model_config) if record.model_config else None,
            record.overall_score,
            json.dumps(record.dimension_scores),
            json.dumps(record.detailed_feedback),
            record.evaluation_timestamp.isoformat(),
            execution_time,
            json.dumps(record.metadata),
            json.dumps(record.tags)
        ))

        self.connection.commit()
        return cursor.lastrowid

    def save_batch_evaluations(
        self,
        records: List[EvaluationRecord],
        benchmark_name: Optional[str] = None,
        dataset_name: Optional[str] = None
    ):
        """批量保存评估记录"""
        cursor = self.connection.cursor()

        for record in records:
            cursor.execute("""
                INSERT INTO evaluation_records
                (session_id, benchmark_name, dataset_name, question, context, ground_truth,
                 model_response, model_name, model_config, overall_score, dimension_scores,
                 detailed_feedback, evaluation_timestamp, metadata, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.session_id,
                benchmark_name,
                dataset_name,
                record.question,
                record.context,
                record.ground_truth,
                record.model_response,
                record.model_name,
                json.dumps(record.model_config) if record.model_config else None,
                record.overall_score,
                json.dumps(record.dimension_scores),
                json.dumps(record.detailed_feedback),
                record.evaluation_timestamp.isoformat(),
                json.dumps(record.metadata),
                json.dumps(record.tags)
            ))

        self.connection.commit()
        logger.info(f"批量保存了 {len(records)} 条评估记录")

    def query_evaluations(
        self,
        model_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationRecord]:
        """
        查询评估记录

        Args:
            model_name: 模型名称
            benchmark_name: Benchmark名称
            dataset_name: 数据集名称
            min_score: 最低分数
            max_score: 最高分数
            date_from: 开始日期
            date_to: 结束日期
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[EvaluationRecord]: 评估记录列表
        """
        query = "SELECT * FROM evaluation_records WHERE 1=1"
        params = []

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        if dataset_name:
            query += " AND dataset_name = ?"
            params.append(dataset_name)

        if min_score is not None:
            query += " AND overall_score >= ?"
            params.append(min_score)

        if max_score is not None:
            query += " AND overall_score <= ?"
            params.append(max_score)

        if date_from:
            query += " AND evaluation_timestamp >= ?"
            params.append(date_from.isoformat())

        if date_to:
            query += " AND evaluation_timestamp <= ?"
            params.append(date_to.isoformat())

        query += " ORDER BY evaluation_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(self._row_to_record(row))

        return records

    def _row_to_record(self, row) -> EvaluationRecord:
        """将数据库行转换为EvaluationRecord"""
        return EvaluationRecord(
            id=row['id'],
            session_id=row['session_id'],
            question=row['question'],
            context=row['context'],
            ground_truth=row['ground_truth'],
            model_response=row['model_response'],
            model_name=row['model_name'],
            model_config=json.loads(row['model_config']) if row['model_config'] else None,
            overall_score=row['overall_score'],
            dimension_scores=json.loads(row['dimension_scores']) if row['dimension_scores'] else {},
            detailed_feedback=json.loads(row['detailed_feedback']) if row['detailed_feedback'] else {},
            evaluation_timestamp=datetime.fromisoformat(row['evaluation_timestamp']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            tags=json.loads(row['tags']) if row['tags'] else []
        )

    def get_statistics(
        self,
        model_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计数据
        """
        query = "SELECT * FROM evaluation_records WHERE 1=1"
        params = []

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        if date_from:
            query += " AND evaluation_timestamp >= ?"
            params.append(date_from.isoformat())

        if date_to:
            query += " AND evaluation_timestamp <= ?"
            params.append(date_to.isoformat())

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        records = [self._row_to_record(row) for row in cursor.fetchall()]

        if not records:
            return {
                'total_evaluations': 0,
                'average_score': 0,
                'dimension_averages': {},
                'score_distribution': {}
            }

        # 计算统计
        total = len(records)
        avg_score = sum(r.overall_score for r in records) / total

        # 维度平均分
        dimension_sums = {}
        for r in records:
            for dim, score in r.dimension_scores.items():
                dimension_sums[dim] = dimension_sums.get(dim, 0) + score

        dimension_averages = {
            dim: total_score / total
            for dim, total_score in dimension_sums.items()
        }

        # 分数分布（按0.1为区间）
        score_dist = {}
        for r in records:
            bucket = f"{int(r.overall_score * 10) / 10:.1f}-{int(r.overall_score * 10) / 10 + 0.1:.1f}"
            score_dist[bucket] = score_dist.get(bucket, 0) + 1

        return {
            'total_evaluations': total,
            'average_score': round(avg_score, 4),
            'min_score': round(min(r.overall_score for r in records), 4),
            'max_score': round(max(r.overall_score for r in records), 4),
            'dimension_averages': {k: round(v, 4) for k, v in dimension_averages.items()},
            'score_distribution': score_dist
        }

    def get_trend_data(
        self,
        model_name: str,
        benchmark_name: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据

        Args:
            model_name: 模型名称
            benchmark_name: Benchmark名称
            days: 天数

        Returns:
            List[Dict]: 每天的平均分数
        """
        date_from = datetime.now() - timedelta(days=days)

        query = """
            SELECT DATE(evaluation_timestamp) as date,
                   AVG(overall_score) as avg_score,
                   COUNT(*) as count
            FROM evaluation_records
            WHERE model_name = ?
              AND evaluation_timestamp >= ?
        """
        params = [model_name, date_from.isoformat()]

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        query += " GROUP BY DATE(evaluation_timestamp) ORDER BY date ASC"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        trend = []
        for row in cursor.fetchall():
            trend.append({
                'date': row['date'],
                'average_score': round(row['avg_score'], 4),
                'count': row['count']
            })

        return trend

    def get_best_worst_cases(
        self,
        model_name: str,
        benchmark_name: Optional[str] = None,
        top_n: int = 10
    ) -> Dict[str, List[EvaluationRecord]]:
        """
        获取最好和最差的评估案例

        Args:
            model_name: 模型名称
            benchmark_name: Benchmark名称
            top_n: 返回数量

        Returns:
            Dict: {'best': [...], 'worst': [...]}
        """
        query = "SELECT * FROM evaluation_records WHERE model_name = ?"
        params = [model_name]

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        # 最好的案例
        best_query = query + " ORDER BY overall_score DESC LIMIT ?"
        cursor = self.connection.cursor()
        cursor.execute(best_query, params + [top_n])
        best_cases = [self._row_to_record(row) for row in cursor.fetchall()]

        # 最差的案例
        worst_query = query + " ORDER BY overall_score ASC LIMIT ?"
        cursor.execute(worst_query, params + [top_n])
        worst_cases = [self._row_to_record(row) for row in cursor.fetchall()]

        return {
            'best': best_cases,
            'worst': worst_cases
        }

    def delete_old_evaluations(self, days: int = 90):
        """
        删除旧的评估记录

        Args:
            days: 保留天数
        """
        date_threshold = datetime.now() - timedelta(days=days)

        cursor = self.connection.cursor()
        cursor.execute("""
            DELETE FROM evaluation_records
            WHERE evaluation_timestamp < ?
        """, (date_threshold.isoformat(),))

        deleted_count = cursor.rowcount
        self.connection.commit()

        logger.info(f"已删除 {deleted_count} 条超过 {days} 天的评估记录")
        return deleted_count

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
