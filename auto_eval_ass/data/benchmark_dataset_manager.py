"""
基准数据集管理模块

负责基准数据集的导入、存储和查询
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .models import (
    BenchmarkDataset,
    BenchmarkQuestion,
    EvaluationType,
    JSONEncoder
)

logger = logging.getLogger(__name__)


class BenchmarkDatasetManager:
    """
    基准数据集管理类

    提供基准数据集的导入、存储和查询功能
    支持不同类型的评测任务(LLM/RAG/Agent)
    """

    def __init__(self, database):
        """
        初始化基准数据集管理器

        Args:
            database: EvaluationDatabase实例
        """
        self.db = database

    async def import_from_json(
        self,
        json_path: Union[str, Path],
        dataset_name: str,
        evaluation_type: EvaluationType = EvaluationType.GENERAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        从JSON文件导入基准数据集

        Args:
            json_path: JSON文件路径
            dataset_name: 数据集名称
            evaluation_type: 评估类型 (llm/rag/agent/general)
            metadata: 额外的元数据

        Returns:
            数据集ID或None
        """
        try:
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 创建数据集记录
            dataset = BenchmarkDataset(
                name=dataset_name,
                title=data.get('title', ''),
                description=data.get('description', ''),
                evaluation_type=evaluation_type,
                chapter_info=data.get('chapter_info'),
                total_questions=len(data.get('questions', [])),
                metadata=metadata or {}
            )

            # 保存数据集
            dataset_id = await self.db.save_benchmark_dataset(dataset)

            if not dataset_id:
                logger.error("保存数据集失败")
                return None

            logger.info(f"数据集已创建: {dataset_name} (ID: {dataset_id})")

            # 导入问题
            questions = data.get('questions', [])
            imported_count = 0

            for q_data in questions:
                question = BenchmarkQuestion(
                    dataset_id=dataset_id,
                    question_number=q_data.get('id', 0),
                    category=q_data.get('category', []),
                    chapter_info=q_data.get('chapter_info'),
                    question=q_data.get('question', ''),
                    answer=q_data.get('answer', ''),
                    key_words=q_data.get('key_words', []),
                    has_calculation=q_data.get('has_calculation', False),
                    difficulty_level=self._infer_difficulty(q_data),
                    metadata={}
                )

                success = await self.db.save_benchmark_question(question)
                if success:
                    imported_count += 1

            logger.info(f"成功导入 {imported_count}/{len(questions)} 个问题")

            return dataset_id

        except Exception as e:
            logger.error(f"导入JSON文件失败: {e}")
            return None

    def _infer_difficulty(self, question_data: Dict[str, Any]) -> str:
        """
        推断问题难度

        Args:
            question_data: 问题数据

        Returns:
            难度等级: easy/medium/hard
        """
        # 根据不同特征推断难度
        has_calc = question_data.get('has_calculation', False)
        category_count = len(question_data.get('category', []))

        # 简单规则：有计算或多个分类标签的认为更难
        if has_calc and category_count > 2:
            return "hard"
        elif has_calc or category_count > 1:
            return "medium"
        else:
            return "easy"

    async def get_dataset(self, dataset_id: int) -> Optional[BenchmarkDataset]:
        """获取数据集信息"""
        return await self.db.get_benchmark_dataset(dataset_id)

    async def get_dataset_by_name(self, name: str) -> Optional[BenchmarkDataset]:
        """根据名称获取数据集"""
        return await self.db.get_benchmark_dataset_by_name(name)

    async def list_datasets(
        self,
        evaluation_type: Optional[EvaluationType] = None
    ) -> List[BenchmarkDataset]:
        """列出所有数据集"""
        return await self.db.list_benchmark_datasets(evaluation_type)

    async def get_questions(
        self,
        dataset_id: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        has_calculation: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BenchmarkQuestion]:
        """获取数据集中的问题"""
        return await self.db.get_benchmark_questions(
            dataset_id=dataset_id,
            category=category,
            difficulty=difficulty,
            has_calculation=has_calculation,
            limit=limit,
            offset=offset
        )

    async def get_question_by_number(
        self,
        dataset_id: int,
        question_number: int
    ) -> Optional[BenchmarkQuestion]:
        """根据题号获取问题"""
        return await self.db.get_benchmark_question_by_number(
            dataset_id,
            question_number
        )

    async def get_dataset_statistics(
        self,
        dataset_id: int
    ) -> Dict[str, Any]:
        """获取数据集统计信息"""
        return await self.db.get_benchmark_dataset_statistics(dataset_id)

    async def delete_dataset(self, dataset_id: int) -> bool:
        """删除数据集及其所有问题"""
        return await self.db.delete_benchmark_dataset(dataset_id)

    async def export_to_json(
        self,
        dataset_id: int,
        output_path: Union[str, Path]
    ) -> bool:
        """导出数据集为JSON文件"""
        try:
            dataset = await self.get_dataset(dataset_id)
            if not dataset:
                logger.error(f"数据集不存在: {dataset_id}")
                return False

            questions = await self.get_questions(dataset_id)

            export_data = {
                'title': dataset.title,
                'description': dataset.description,
                'chapter_info': dataset.chapter_info,
                'evaluation_type': dataset.evaluation_type.value,
                'total_questions': dataset.total_questions,
                'questions': [
                    {
                        'id': q.question_number,
                        'category': q.category,
                        'chapter_info': q.chapter_info,
                        'question': q.question,
                        'answer': q.answer,
                        'key_words': q.key_words,
                        'has_calculation': q.has_calculation,
                        'difficulty_level': q.difficulty_level
                    }
                    for q in questions
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, cls=JSONEncoder)

            logger.info(f"数据集已导出到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出数据集失败: {e}")
            return False

    async def search_questions(
        self,
        dataset_id: int,
        keyword: str,
        search_in_answer: bool = False
    ) -> List[BenchmarkQuestion]:
        """在数据集中搜索问题"""
        return await self.db.search_benchmark_questions(
            dataset_id=dataset_id,
            keyword=keyword,
            search_in_answer=search_in_answer
        )
