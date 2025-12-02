"""
数据集管理器

负责评测数据集的加载、存储和管理
支持多种格式：JSON, JSONL, CSV, Excel
"""

import json
import csv
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from .models import DatasetItem

logger = logging.getLogger(__name__)


@dataclass
class DatasetMetadata:
    """数据集元数据"""
    name: str
    description: str
    version: str
    total_items: int
    categories: List[str]
    difficulty_distribution: Dict[str, int]
    created_at: datetime
    updated_at: datetime
    source: str
    metadata: Dict[str, Any]


class DatasetManager:
    """
    数据集管理器

    功能：
    1. 自动加载本地数据集文件（JSON/JSONL/CSV/Excel）
    2. 存储数据集到SQLite
    3. 管理多个数据集版本
    4. 支持数据集的增删改查
    5. 数据集统计和分析
    """

    def __init__(self, db_path: str = "evaluation_results.db"):
        """
        初始化数据集管理器

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

        # 创建数据集元数据表
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                version TEXT,
                total_items INTEGER,
                categories TEXT,
                difficulty_distribution TEXT,
                source TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                metadata TEXT
            )
        """)

        # 创建数据集项目表
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS dataset_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT NOT NULL,
                item_id TEXT,
                question TEXT NOT NULL,
                context TEXT,
                ground_truth TEXT,
                difficulty_level TEXT DEFAULT 'medium',
                category TEXT,
                tags TEXT,
                metadata TEXT,
                created_at DATETIME,
                FOREIGN KEY (dataset_name) REFERENCES datasets(name)
            )
        """)

        # 创建索引以提高查询性能
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_dataset_name
            ON dataset_items(dataset_name)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_category
            ON dataset_items(category)
        """)

        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_difficulty
            ON dataset_items(difficulty_level)
        """)

        self.connection.commit()
        logger.info(f"数据集数据库初始化成功: {self.db_path}")

    def load_dataset_from_file(
        self,
        file_path: str,
        dataset_name: str,
        description: str = "",
        version: str = "1.0",
        auto_detect_format: bool = True
    ) -> DatasetMetadata:
        """
        从文件加载数据集

        支持格式：
        - JSON: {"items": [...]}
        - JSONL: 每行一个JSON对象
        - CSV: 标准CSV格式
        - Excel: .xlsx格式

        Args:
            file_path: 文件路径
            dataset_name: 数据集名称
            description: 数据集描述
            version: 版本号
            auto_detect_format: 自动检测文件格式

        Returns:
            DatasetMetadata: 数据集元数据
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {file_path}")

        logger.info(f"开始加载数据集: {file_path}")

        # 检测文件格式
        if auto_detect_format:
            format_type = self._detect_format(file_path)
        else:
            format_type = file_path.suffix.lower()

        # 根据格式加载数据
        if format_type in ['.json']:
            items = self._load_json(file_path)
        elif format_type in ['.jsonl']:
            items = self._load_jsonl(file_path)
        elif format_type in ['.csv']:
            items = self._load_csv(file_path)
        elif format_type in ['.xlsx', '.xls']:
            items = self._load_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {format_type}")

        # 存储到数据库
        metadata = self.save_dataset(
            dataset_name=dataset_name,
            items=items,
            description=description,
            version=version,
            source=str(file_path)
        )

        logger.info(f"数据集加载成功: {dataset_name}, 共 {len(items)} 条数据")

        return metadata

    def _detect_format(self, file_path: Path) -> str:
        """检测文件格式"""
        suffix = file_path.suffix.lower()

        # 对于.json文件，检测是否为JSONL格式
        if suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # 如果第一行是完整的JSON对象，可能是JSONL
                try:
                    json.loads(first_line)
                    # 检查第二行
                    second_line = f.readline().strip()
                    if second_line and second_line.startswith('{'):
                        return '.jsonl'
                except:
                    pass

        return suffix

    def _load_json(self, file_path: Path) -> List[DatasetItem]:
        """从JSON文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持多种JSON结构
        if isinstance(data, list):
            raw_items = data
        elif isinstance(data, dict) and 'items' in data:
            raw_items = data['items']
        elif isinstance(data, dict) and 'data' in data:
            raw_items = data['data']
        else:
            raise ValueError("无法识别的JSON结构，需要包含'items'或'data'字段，或直接为数组")

        return [self._parse_item(item) for item in raw_items]

    def _load_jsonl(self, file_path: Path) -> List[DatasetItem]:
        """从JSONL文件加载"""
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    items.append(self._parse_item(item))
                except json.JSONDecodeError as e:
                    logger.warning(f"跳过无效行 {line_num}: {e}")

        return items

    def _load_csv(self, file_path: Path) -> List[DatasetItem]:
        """从CSV文件加载"""
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(self._parse_item(row))

        return items

    def _load_excel(self, file_path: Path) -> List[DatasetItem]:
        """从Excel文件加载"""
        df = pd.read_excel(file_path)
        items = []
        for _, row in df.iterrows():
            items.append(self._parse_item(row.to_dict()))

        return items

    def _parse_item(self, raw_item: Dict[str, Any]) -> DatasetItem:
        """解析原始数据项为DatasetItem"""
        # 灵活的字段映射
        question = raw_item.get('question') or raw_item.get('input') or raw_item.get('prompt') or ""
        context = raw_item.get('context') or raw_item.get('background') or raw_item.get('passage')
        ground_truth = (
            raw_item.get('ground_truth') or
            raw_item.get('answer') or
            raw_item.get('expected_output') or
            raw_item.get('reference')
        )

        # 处理tags
        tags = raw_item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        return DatasetItem(
            id=raw_item.get('id') or raw_item.get('item_id'),
            question=question,
            context=context,
            ground_truth=ground_truth,
            difficulty_level=raw_item.get('difficulty_level', 'medium'),
            category=raw_item.get('category', ''),
            tags=tags,
            metadata={k: v for k, v in raw_item.items()
                     if k not in ['id', 'question', 'context', 'ground_truth',
                                  'difficulty_level', 'category', 'tags']},
            created_at=datetime.now()
        )

    def save_dataset(
        self,
        dataset_name: str,
        items: List[DatasetItem],
        description: str = "",
        version: str = "1.0",
        source: str = ""
    ) -> DatasetMetadata:
        """
        保存数据集到数据库

        Args:
            dataset_name: 数据集名称
            items: 数据集项目列表
            description: 描述
            version: 版本号
            source: 数据来源

        Returns:
            DatasetMetadata: 数据集元数据
        """
        # 统计信息
        categories = list(set(item.category for item in items if item.category))
        difficulty_dist = {}
        for item in items:
            level = item.difficulty_level
            difficulty_dist[level] = difficulty_dist.get(level, 0) + 1

        # 创建元数据
        metadata = DatasetMetadata(
            name=dataset_name,
            description=description,
            version=version,
            total_items=len(items),
            categories=categories,
            difficulty_distribution=difficulty_dist,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=source,
            metadata={}
        )

        # 保存到数据库
        cursor = self.connection.cursor()

        # 插入或更新元数据
        cursor.execute("""
            INSERT OR REPLACE INTO datasets
            (name, description, version, total_items, categories,
             difficulty_distribution, source, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.name,
            metadata.description,
            metadata.version,
            metadata.total_items,
            json.dumps(metadata.categories),
            json.dumps(metadata.difficulty_distribution),
            metadata.source,
            metadata.created_at.isoformat(),
            metadata.updated_at.isoformat(),
            json.dumps(metadata.metadata)
        ))

        # 删除旧的数据项（如果存在）
        cursor.execute("DELETE FROM dataset_items WHERE dataset_name = ?", (dataset_name,))

        # 插入数据项
        for item in items:
            cursor.execute("""
                INSERT INTO dataset_items
                (dataset_name, item_id, question, context, ground_truth,
                 difficulty_level, category, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_name,
                item.id,
                item.question,
                item.context,
                item.ground_truth,
                item.difficulty_level,
                item.category,
                json.dumps(item.tags),
                json.dumps(item.metadata),
                item.created_at.isoformat()
            ))

        self.connection.commit()
        logger.info(f"数据集保存成功: {dataset_name}")

        return metadata

    def get_dataset(
        self,
        dataset_name: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DatasetItem]:
        """
        获取数据集

        Args:
            dataset_name: 数据集名称
            category: 过滤类别
            difficulty: 过滤难度
            limit: 限制返回数量

        Returns:
            List[DatasetItem]: 数据集项目列表
        """
        query = "SELECT * FROM dataset_items WHERE dataset_name = ?"
        params = [dataset_name]

        if category:
            query += " AND category = ?"
            params.append(category)

        if difficulty:
            query += " AND difficulty_level = ?"
            params.append(difficulty)

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        items = []
        for row in cursor.fetchall():
            items.append(DatasetItem(
                id=row['item_id'],
                question=row['question'],
                context=row['context'],
                ground_truth=row['ground_truth'],
                difficulty_level=row['difficulty_level'],
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else [],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        return items

    def list_datasets(self) -> List[DatasetMetadata]:
        """列出所有数据集"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM datasets")

        datasets = []
        for row in cursor.fetchall():
            datasets.append(DatasetMetadata(
                name=row['name'],
                description=row['description'],
                version=row['version'],
                total_items=row['total_items'],
                categories=json.loads(row['categories']) if row['categories'] else [],
                difficulty_distribution=json.loads(row['difficulty_distribution']) if row['difficulty_distribution'] else {},
                source=row['source'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))

        return datasets

    def delete_dataset(self, dataset_name: str):
        """删除数据集"""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM dataset_items WHERE dataset_name = ?", (dataset_name,))
        cursor.execute("DELETE FROM datasets WHERE name = ?", (dataset_name,))
        self.connection.commit()
        logger.info(f"数据集已删除: {dataset_name}")

    def get_dataset_stats(self, dataset_name: str) -> Dict[str, Any]:
        """获取数据集统计信息"""
        cursor = self.connection.cursor()

        # 基础统计
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT category) as num_categories,
                   AVG(LENGTH(question)) as avg_question_length,
                   AVG(LENGTH(ground_truth)) as avg_answer_length
            FROM dataset_items
            WHERE dataset_name = ?
        """, (dataset_name,))

        row = cursor.fetchone()

        # 难度分布
        cursor.execute("""
            SELECT difficulty_level, COUNT(*) as count
            FROM dataset_items
            WHERE dataset_name = ?
            GROUP BY difficulty_level
        """, (dataset_name,))

        difficulty_dist = {row['difficulty_level']: row['count']
                          for row in cursor.fetchall()}

        # 类别分布
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM dataset_items
            WHERE dataset_name = ? AND category != ''
            GROUP BY category
        """, (dataset_name,))

        category_dist = {row['category']: row['count']
                        for row in cursor.fetchall()}

        return {
            'total_items': row['total'],
            'num_categories': row['num_categories'],
            'avg_question_length': round(row['avg_question_length'], 2) if row['avg_question_length'] else 0,
            'avg_answer_length': round(row['avg_answer_length'], 2) if row['avg_answer_length'] else 0,
            'difficulty_distribution': difficulty_dist,
            'category_distribution': category_dist
        }

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
