"""
Benchmark管理器

负责评测benchmark的创建、运行和结果管理
"""

import sqlite3
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

from .models import BenchmarkResult, DatasetItem, EvaluationRecord
from .dataset_manager import DatasetManager

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Benchmark配置"""
    name: str
    dataset_name: str
    models: List[str]
    evaluator_config: Dict[str, Any]
    sample_size: Optional[int] = None  # None表示使用全部数据
    random_seed: int = 42
    parallel_workers: int = 5
    timeout_per_item: int = 120


class BenchmarkManager:
    """
    Benchmark管理器

    功能：
    1. 创建和管理benchmark配置
    2. 运行benchmark评测
    3. 存储评测结果
    4. 对比不同模型/版本的性能
    5. 生成benchmark排行榜
    """

    def __init__(self, db_path: str = "evaluation_results.db"):
        """
        初始化Benchmark管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """初始化数据库表结构"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

        # 创建benchmark配置表
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                dataset_name TEXT NOT NULL,
                models TEXT,
                evaluator_config TEXT,
                sample_size INTEGER,
                random_seed INTEGER,
                parallel_workers INTEGER,
                timeout_per_item INTEGER,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)

        # 创建benchmark结果表
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                total_samples INTEGER,
                average_score REAL,
                dimension_scores TEXT,
                score_distribution TEXT,
                execution_time REAL,
                timestamp DATETIME,
                metadata TEXT,
                UNIQUE(benchmark_name, model_name, timestamp)
            )
        """)

        # 创建benchmark运行历史表
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_name TEXT NOT NULL,
                run_id TEXT UNIQUE NOT NULL,
                status TEXT,
                start_time DATETIME,
                end_time DATETIME,
                total_models INTEGER,
                completed_models INTEGER,
                error_message TEXT,
                metadata TEXT
            )
        """)

        # 创建索引
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_benchmark_results_model
            ON benchmark_results(model_name)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_benchmark_results_benchmark
            ON benchmark_results(benchmark_name)
        """)

        self.connection.commit()
        logger.info(f"Benchmark数据库初始化成功: {self.db_path}")

    def create_benchmark(
        self,
        name: str,
        dataset_name: str,
        models: List[str],
        evaluator_config: Dict[str, Any],
        sample_size: Optional[int] = None,
        random_seed: int = 42,
        parallel_workers: int = 5,
        timeout_per_item: int = 120
    ) -> BenchmarkConfig:
        """
        创建benchmark配置

        Args:
            name: Benchmark名称
            dataset_name: 数据集名称
            models: 要评测的模型列表
            evaluator_config: 评估器配置
            sample_size: 采样大小（None表示全部）
            random_seed: 随机种子
            parallel_workers: 并行worker数量
            timeout_per_item: 每项超时时间（秒）

        Returns:
            BenchmarkConfig: Benchmark配置
        """
        config = BenchmarkConfig(
            name=name,
            dataset_name=dataset_name,
            models=models,
            evaluator_config=evaluator_config,
            sample_size=sample_size,
            random_seed=random_seed,
            parallel_workers=parallel_workers,
            timeout_per_item=timeout_per_item
        )

        # 保存到数据库
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO benchmarks
            (name, dataset_name, models, evaluator_config, sample_size,
             random_seed, parallel_workers, timeout_per_item, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.name,
            config.dataset_name,
            json.dumps(config.models),
            json.dumps(config.evaluator_config),
            config.sample_size,
            config.random_seed,
            config.parallel_workers,
            config.timeout_per_item,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        self.connection.commit()
        logger.info(f"Benchmark创建成功: {name}")

        return config

    def get_benchmark(self, name: str) -> Optional[BenchmarkConfig]:
        """获取benchmark配置"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM benchmarks WHERE name = ?", (name,))

        row = cursor.fetchone()
        if not row:
            return None

        return BenchmarkConfig(
            name=row['name'],
            dataset_name=row['dataset_name'],
            models=json.loads(row['models']),
            evaluator_config=json.loads(row['evaluator_config']),
            sample_size=row['sample_size'],
            random_seed=row['random_seed'],
            parallel_workers=row['parallel_workers'],
            timeout_per_item=row['timeout_per_item']
        )

    def list_benchmarks(self) -> List[BenchmarkConfig]:
        """列出所有benchmark"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM benchmarks")

        benchmarks = []
        for row in cursor.fetchall():
            benchmarks.append(BenchmarkConfig(
                name=row['name'],
                dataset_name=row['dataset_name'],
                models=json.loads(row['models']),
                evaluator_config=json.loads(row['evaluator_config']),
                sample_size=row['sample_size'],
                random_seed=row['random_seed'],
                parallel_workers=row['parallel_workers'],
                timeout_per_item=row['timeout_per_item']
            ))

        return benchmarks

    def save_benchmark_result(self, result: BenchmarkResult):
        """
        保存benchmark结果

        Args:
            result: Benchmark结果
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO benchmark_results
            (benchmark_name, model_name, dataset_name, total_samples,
             average_score, dimension_scores, score_distribution,
             execution_time, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.metadata.get('benchmark_name', ''),
            result.model_name,
            result.dataset_name,
            result.total_samples,
            result.average_score,
            json.dumps(result.dimension_scores),
            json.dumps(result.score_distribution),
            result.execution_time,
            result.timestamp.isoformat(),
            json.dumps(result.metadata)
        ))

        self.connection.commit()
        logger.info(f"Benchmark结果已保存: {result.model_name} on {result.dataset_name}")

    def get_benchmark_results(
        self,
        benchmark_name: Optional[str] = None,
        model_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        limit: int = 100
    ) -> List[BenchmarkResult]:
        """
        查询benchmark结果

        Args:
            benchmark_name: Benchmark名称
            model_name: 模型名称
            dataset_name: 数据集名称
            limit: 返回数量限制

        Returns:
            List[BenchmarkResult]: 结果列表
        """
        query = "SELECT * FROM benchmark_results WHERE 1=1"
        params = []

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        if dataset_name:
            query += " AND dataset_name = ?"
            params.append(dataset_name)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(BenchmarkResult(
                model_name=row['model_name'],
                dataset_name=row['dataset_name'],
                total_samples=row['total_samples'],
                average_score=row['average_score'],
                dimension_scores=json.loads(row['dimension_scores']),
                score_distribution=json.loads(row['score_distribution']),
                execution_time=row['execution_time'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))

        return results

    def get_leaderboard(
        self,
        benchmark_name: str,
        order_by: str = "average_score"
    ) -> List[Dict[str, Any]]:
        """
        生成benchmark排行榜

        Args:
            benchmark_name: Benchmark名称
            order_by: 排序字段（average_score或其他维度）

        Returns:
            List[Dict]: 排行榜数据
        """
        # 获取每个模型的最新结果
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT *
            FROM benchmark_results
            WHERE benchmark_name = ?
              AND timestamp IN (
                  SELECT MAX(timestamp)
                  FROM benchmark_results
                  WHERE benchmark_name = ?
                  GROUP BY model_name
              )
            ORDER BY average_score DESC
        """, (benchmark_name, benchmark_name))

        leaderboard = []
        for rank, row in enumerate(cursor.fetchall(), 1):
            dimension_scores = json.loads(row['dimension_scores'])

            leaderboard.append({
                'rank': rank,
                'model_name': row['model_name'],
                'average_score': round(row['average_score'], 4),
                'dimension_scores': {k: round(v, 4) for k, v in dimension_scores.items()},
                'total_samples': row['total_samples'],
                'execution_time': round(row['execution_time'], 2),
                'timestamp': row['timestamp']
            })

        return leaderboard

    def compare_models(
        self,
        benchmark_name: str,
        model_names: List[str]
    ) -> Dict[str, Any]:
        """
        对比多个模型的性能

        Args:
            benchmark_name: Benchmark名称
            model_names: 要对比的模型列表

        Returns:
            Dict: 对比结果
        """
        comparison = {
            'benchmark_name': benchmark_name,
            'models': {},
            'dimension_comparison': {},
            'winner': None
        }

        best_score = 0
        best_model = None

        for model_name in model_names:
            results = self.get_benchmark_results(
                benchmark_name=benchmark_name,
                model_name=model_name,
                limit=1
            )

            if not results:
                logger.warning(f"未找到模型 {model_name} 在 {benchmark_name} 上的结果")
                continue

            result = results[0]
            comparison['models'][model_name] = {
                'average_score': result.average_score,
                'dimension_scores': result.dimension_scores,
                'total_samples': result.total_samples,
                'timestamp': result.timestamp.isoformat()
            }

            # 记录每个维度的分数
            for dim, score in result.dimension_scores.items():
                if dim not in comparison['dimension_comparison']:
                    comparison['dimension_comparison'][dim] = {}
                comparison['dimension_comparison'][dim][model_name] = score

            # 找出最佳模型
            if result.average_score > best_score:
                best_score = result.average_score
                best_model = model_name

        comparison['winner'] = best_model

        return comparison

    def get_model_history(
        self,
        model_name: str,
        benchmark_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取模型的历史评测结果

        Args:
            model_name: 模型名称
            benchmark_name: Benchmark名称（可选）

        Returns:
            List[Dict]: 历史记录
        """
        query = "SELECT * FROM benchmark_results WHERE model_name = ?"
        params = [model_name]

        if benchmark_name:
            query += " AND benchmark_name = ?"
            params.append(benchmark_name)

        query += " ORDER BY timestamp ASC"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        history = []
        for row in cursor.fetchall():
            history.append({
                'benchmark_name': row['benchmark_name'],
                'timestamp': row['timestamp'],
                'average_score': row['average_score'],
                'dimension_scores': json.loads(row['dimension_scores']),
                'total_samples': row['total_samples']
            })

        return history

    def delete_benchmark(self, name: str):
        """删除benchmark及其所有结果"""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM benchmark_results WHERE benchmark_name = ?", (name,))
        cursor.execute("DELETE FROM benchmark_runs WHERE benchmark_name = ?", (name,))
        cursor.execute("DELETE FROM benchmarks WHERE name = ?", (name,))
        self.connection.commit()
        logger.info(f"Benchmark已删除: {name}")

    def export_results(
        self,
        benchmark_name: str,
        output_file: str,
        format: str = "json"
    ):
        """
        导出benchmark结果

        Args:
            benchmark_name: Benchmark名称
            output_file: 输出文件路径
            format: 输出格式（json/csv）
        """
        results = self.get_benchmark_results(benchmark_name=benchmark_name)

        if format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [asdict(r) for r in results],
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=str
                )
        elif format == "csv":
            import csv
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                if not results:
                    return

                fieldnames = ['model_name', 'dataset_name', 'average_score',
                             'total_samples', 'execution_time', 'timestamp']

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for r in results:
                    writer.writerow({
                        'model_name': r.model_name,
                        'dataset_name': r.dataset_name,
                        'average_score': r.average_score,
                        'total_samples': r.total_samples,
                        'execution_time': r.execution_time,
                        'timestamp': r.timestamp
                    })

        logger.info(f"结果已导出到: {output_file}")

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
