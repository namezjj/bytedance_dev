"""
准确性评估器

评估模型回答的事实准确性和正确性
"""

import re
import json
from typing import Tuple, Dict, Any, List

from .base_evaluator import BaseEvaluator

class AccuracyEvaluator(BaseEvaluator):
    """
    准确性评估器

    评估模型回答是否包含事实错误、错误信息或误导性内容
    """

    def get_dimension_name(self) -> str:
        return "准确性"

    def get_dimension_description(self) -> str:
        return "评估回答的事实准确性、信息正确性和可靠性"

    def _get_evaluation_prompt(self) -> str:
        return """作为一个专业的事实核查员，请评估以下AI模型回答的准确性。

评估维度：{dimension_name}
维度描述：{dimension_description}

问题：{question}

{context}

{conversation_history}

{ground_truth}

模型回答：
{model_response}

请从以下几个方面进行评估：
1. 事实准确性：回答中陈述的事实是否正确
2. 信息一致性：回答内部是否自相矛盾
3. 来源可靠性：如果引用信息，是否可靠
4. 错误识别：是否存在明显的事实错误

评估标准：
- 0.0-0.2：回答包含严重事实错误，完全不可信
- 0.2-0.4：回答有较多错误信息，可信度低
- 0.4-0.6：回答基本正确但有一些小错误
- 0.6-0.8：回答基本准确，偶有细微错误
- 0.8-1.0：回答高度准确，无明显事实错误

请按以下格式回复：
分数：[0-1之间的分数]
评估：[详细的评估说明，指出具体的问题和优点]

示例回复：
分数：0.85
评估：回答中的所有事实陈述都是准确的，包括...但是...方面可以进一步改进。

请开始评估："""

    def _parse_evaluation_result(self, llm_response: str) -> Tuple[float, str]:
        """
        解析LLM的准确性评估结果

        Args:
            llm_response: LLM的原始响应

        Returns:
            (分数, 详细反馈) 的元组
        """
        try:
            # 提取分数
            score_match = re.search(r'分数[：:]\s*([0-9]*\.?[0-9]+)', llm_response)
            if score_match:
                score = float(score_match.group(1))
            else:
                # 尝试其他格式
                score_match = re.search(r'Score[：:]\s*([0-9]*\.?[0-9]+)', llm_response)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    # 如果找不到分数，根据内容进行启发式评估
                    score = self._heuristic_score_extraction(llm_response)

            # 提取评估内容
            evaluation_match = re.search(r'评估[：:]\s*(.+)', llm_response, re.DOTALL)
            if evaluation_match:
                feedback = evaluation_match.group(1).strip()
            else:
                # 尝试其他格式的评估内容
                evaluation_match = re.search(r'Evaluation[：:]\s*(.+)', llm_response, re.DOTALL)
                if evaluation_match:
                    feedback = evaluation_match.group(1).strip()
                else:
                    feedback = llm_response.strip()

            return score, feedback

        except Exception as e:
            print(f"解析准确性评估结果失败: {e}")
            return 0.5, llm_response

    def _heuristic_score_extraction(self, response: str) -> float:
        """
        启发式分数提取

        Args:
            response: LLM响应

        Returns:
            提取的分数
        """
        response_lower = response.lower()

        # 正面关键词
        positive_keywords = ['准确', '正确', '准确无误', '事实正确', '无误', '可靠']
        # 负面关键词
        negative_keywords = ['错误', '不准确', '错误信息', '事实错误', '误导', '矛盾']

        positive_count = sum(1 for keyword in positive_keywords if keyword in response_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in response_lower)

        # 基于关键词计算分数
        if negative_count > positive_count + 1:
            return 0.3
        elif positive_count > negative_count + 1:
            return 0.8
        elif positive_count > 0:
            return 0.6
        elif negative_count > 0:
            return 0.4
        else:
            return 0.5

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        获取准确性评估的具体标准

        Returns:
            评估标准字典
        """
        criteria = super().get_evaluation_criteria()
        criteria.update({
            'specific_criteria': {
                'factual_correctness': '事实陈述的正确性',
                'consistency': '信息内部一致性',
                'source_reliability': '信息来源的可靠性',
                'error_identification': '错误信息的识别',
                'misleading_content': '误导性内容的检测'
            },
            'scoring_guidelines': {
                '0.0-0.2': '包含严重事实错误，完全不可信',
                '0.2-0.4': '有较多错误信息，可信度低',
                '0.4-0.6': '基本正确但有小错误',
                '0.6-0.8': '基本准确，偶有细微错误',
                '0.8-1.0': '高度准确，无明显事实错误'
            },
            'evaluation_focus': [
                '关键事实的准确性',
                '数据和统计信息的正确性',
                '时间、地点、人物等具体信息的准确性',
                '专业术语和概念的正确使用',
                '逻辑推理的合理性'
            ]
        })
        return criteria

    def validate_input_for_accuracy(self, question: str, answer: str, ground_truth: str = None) -> bool:
        """
        验证准确性评估的输入

        Args:
            question: 问题
            answer: 回答
            ground_truth: 参考答案（可选）

        Returns:
            是否有效
        """
        if not question or not question.strip():
            return False

        if not answer or not answer.strip():
            return False

        # 检查回答是否包含实质内容
        if len(answer.strip()) < 10:
            return False

        return True

    def extract_factual_claims(self, text: str) -> List[str]:
        """
        提取文本中的事实性声明

        Args:
            text: 输入文本

        Returns:
            事实声明列表
        """
        # 简单的事实声明提取模式
        factual_patterns = [
            r'\d{4}年',  # 年份
            r'\d+%',     # 百分比
            r'\d+\s*[万千百十]',  # 数量
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:说|表示|指出|宣布)',  # 人物引述
            r'据.*报道',  # 媒体报道
            r'(?:是|为)\s*[^，。！？]+',  # 定义性陈述
        ]

        claims = []
        for pattern in factual_patterns:
            matches = re.findall(pattern, text)
            claims.extend(matches)

        return list(set(claims))  # 去重

    def calculate_fact_check_score(self, answer: str, ground_truth: str = None) -> float:
        """
        基于参考答案计算事实核查分数

        Args:
            answer: 模型回答
            ground_truth: 参考答案

        Returns:
            事实核查分数
        """
        if not ground_truth:
            return 0.5  # 没有参考答案时给中等分数

        answer_claims = self.extract_factual_claims(answer)
        truth_claims = self.extract_factual_claims(ground_truth)

        if not answer_claims:
            return 0.7  # 回答中没有事实声明，给较高分数

        # 计算重叠度
        overlap = len(set(answer_claims) & set(truth_claims))
        total_claims = len(set(answer_claims) | set(truth_claims))

        return overlap / total_claims if total_claims > 0 else 0.5