"""
完整性评估器

评估模型回答的完整性和信息覆盖度
"""

import re
from typing import Tuple, Dict, Any, List
from collections import Counter

from .base_evaluator import BaseEvaluator

class CompletenessEvaluator(BaseEvaluator):
    """
    完整性评估器

    评估模型回答是否完整覆盖了问题的各个方面，是否遗漏重要信息
    """

    def get_dimension_name(self) -> str:
        return "完整性"

    def get_dimension_description(self) -> str:
        return "评估回答的信息完整性、覆盖度和充分性"

    def _get_evaluation_prompt(self) -> str:
        return """作为一个专业的信息完整性评估员，请评估以下AI模型回答的完整性。

评估维度：{dimension_name}
维度描述：{dimension_description}

问题：{question}

{context}

{conversation_history}

{ground_truth}

模型回答：
{model_response}

请从以下几个方面进行评估：
1. 信息覆盖度：是否覆盖了问题的关键方面
2. 细节充分性：是否提供了足够的细节和解释
3. 逻辑完整性：回答的逻辑是否完整
4. 遗漏检测：是否遗漏了重要信息

评估标准：
- 0.0-0.2：回答严重不完整，遗漏大量关键信息
- 0.2-0.4：回答不够完整，遗漏较多重要信息
- 0.4-0.6：回答基本完整但缺乏一些细节
- 0.6-0.8：回答较完整，覆盖了主要信息
- 0.8-1.0：回答非常完整，全面覆盖了所有重要信息

请按以下格式回复：
分数：[0-1之间的分数]
评估：[详细的评估说明，分析完整性的具体表现]

示例回复：
分数：0.85
评估：回答全面覆盖了问题的各个方面，提供了充分的细节和解释，没有遗漏重要信息。

请开始评估："""

    def _parse_evaluation_result(self, llm_response: str) -> Tuple[float, str]:
        """
        解析LLM的完整性评估结果

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
                score_match = re.search(r'Score[：:]\s*([0-9]*\.?[0-9]+)', llm_response)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    score = self._heuristic_score_extraction(llm_response)

            # 提取评估内容
            evaluation_match = re.search(r'评估[：:]\s*(.+)', llm_response, re.DOTALL)
            if evaluation_match:
                feedback = evaluation_match.group(1).strip()
            else:
                evaluation_match = re.search(r'Evaluation[：:]\s*(.+)', llm_response, re.DOTALL)
                if evaluation_match:
                    feedback = evaluation_match.group(1).strip()
                else:
                    feedback = llm_response.strip()

            return score, feedback

        except Exception as e:
            print(f"解析完整性评估结果失败: {e}")
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
        positive_keywords = ['完整', '全面', '充分', '详细', '覆盖', '充分']
        # 负面关键词
        negative_keywords = ['不完整', '遗漏', '缺失', '不够', '缺乏', '简单']

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

    def extract_question_aspects(self, question: str) -> List[str]:
        """
        提取问题的各个方面

        Args:
            question: 问题文本

        Returns:
            问题方面列表
        """
        # 识别问题中的关键词汇和方面
        aspects = []

        # 使用标点符号分割复杂问题
        sentences = re.split(r'[，。！？；]', question)

        # 提取每个句子的核心概念
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 简单的方面提取：识别疑问词和关键名词
                if any(qw in sentence for qw in ['什么', '如何', '为什么', '哪个', '怎样']):
                    aspects.append(sentence)
                elif len(sentence) > 5:  # 较长的句子可能包含重要方面
                    aspects.append(sentence)

        # 识别列表型问题
        if '和' in question or '以及' in question or '与' in question:
            parts = re.split(r'[和以及与]', question)
            for part in parts:
                part = part.strip()
                if len(part) > 3:
                    aspects.append(part)

        return aspects

    def calculate_aspect_coverage(self, question: str, answer: str) -> float:
        """
        计算问题方面在回答中的覆盖度

        Args:
            question: 问题
            answer: 回答

        Returns:
            方面覆盖度分数 (0-1)
        """
        question_aspects = self.extract_question_aspects(question)
        if not question_aspects:
            return 0.8  # 如果无法提取方面，给较高的默认分数

        covered_aspects = 0
        answer_lower = answer.lower()

        for aspect in question_aspects:
            aspect_lower = aspect.lower()
            # 检查回答中是否包含方面的关键词
            aspect_keywords = self._extract_aspect_keywords(aspect)
            keyword_matches = sum(1 for kw in aspect_keywords if kw in answer_lower)

            # 如果匹配的关键词超过一定比例，认为覆盖了该方面
            if keyword_matches >= max(1, len(aspect_keywords) * 0.3):
                covered_aspects += 1

        coverage = covered_aspects / len(question_aspects)
        return coverage

    def _extract_aspect_keywords(self, aspect: str) -> List[str]:
        """
        提取方面的关键词

        Args:
            aspect: 方面文本

        Returns:
            关键词列表
        """
        # 简单的关键词提取：去除停用词，提取主要词汇
        import jieba

        # 简单停用词列表
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '什么', '如何', '为什么'}

        words = []
        for word in jieba.cut(aspect):
            if len(word) > 1 and word not in stop_words:
                words.append(word.lower())

        return words

    def calculate_information_density(self, answer: str) -> float:
        """
        计算回答的信息密度

        Args:
            answer: 回答文本

        Returns:
            信息密度分数 (0-1)
        """
        if not answer:
            return 0.0

        # 计算独特词汇比例
        words = answer.split()
        unique_words = set(words)

        if not words:
            return 0.0

        unique_ratio = len(unique_words) / len(words)

        # 计算平均句长
        sentences = re.split(r'[。！？]', answer)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        # 综合评分：独特词汇比例 + 句长适中性
        density_score = unique_ratio * 0.6

        # 句长适中性（理想句长在15-25词之间）
        if 10 <= avg_sentence_length <= 30:
            density_score += 0.4
        elif 5 <= avg_sentence_length <= 40:
            density_score += 0.2
        else:
            density_score += 0.0

        return min(1.0, density_score)

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        获取完整性评估的具体标准

        Returns:
            评估标准字典
        """
        criteria = super().get_evaluation_criteria()
        criteria.update({
            'specific_criteria': {
                'information_coverage': '信息覆盖全面性',
                'detail_sufficiency': '细节充分程度',
                'logical_completeness': '逻辑完整性',
                'missing_detection': '遗漏信息检测',
                'aspect_completeness': '问题方面覆盖度'
            },
            'scoring_guidelines': {
                '0.0-0.2': '严重不完整，遗漏大量关键信息',
                '0.2-0.4': '不够完整，遗漏较多重要信息',
                '0.4-0.6': '基本完整但缺乏一些细节',
                '0.6-0.8': '较完整，覆盖了主要信息',
                '0.8-1.0': '非常完整，全面覆盖了所有重要信息'
            },
            'evaluation_focus': [
                '是否回答了问题的所有部分',
                '是否提供了充分的细节和解释',
                '信息是否丰富且有价值',
                '逻辑链条是否完整',
                '是否遗漏了用户期望的重要信息'
            ],
            'question_type_completeness': {
                'factual': '需要提供准确的事实和数据',
                'procedural': '需要提供完整的步骤和方法',
                'comparative': '需要比较所有相关方面',
                'evaluative': '需要提供全面的评价和建议'
            }
        })
        return criteria

    def analyze_completeness_by_type(self, question: str, answer: str, question_type: str) -> Dict[str, float]:
        """
        根据问题类型分析完整性

        Args:
            question: 问题
            answer: 回答
            question_type: 问题类型

        Returns:
            各类型完整性评分字典
        """
        completeness_scores = {}

        # 基础完整性评分
        aspect_coverage = self.calculate_aspect_coverage(question, answer)
        information_density = self.calculate_information_density(answer)

        completeness_scores['aspect_coverage'] = aspect_coverage
        completeness_scores['information_density'] = information_density

        # 根据问题类型进行特定评分
        if question_type == 'procedural':
            # 操作性问题需要步骤清晰
            step_keywords = ['首先', '然后', '接着', '最后', '第一步', '第二步']
            step_count = sum(1 for kw in step_keywords if kw in answer)
            completeness_scores['step_clarity'] = min(1.0, step_count / 3)

        elif question_type == 'factual':
            # 事实性问题需要具体数据
            number_pattern = re.findall(r'\d+', answer)
            completeness_scores['data_provision'] = min(1.0, len(number_pattern) / 2)

        elif question_type == 'comparative':
            # 比较性问题需要对比多个方面
            comparison_words = ['对比', '比较', '相同', '不同', '区别', '优势']
            comparison_count = sum(1 for cw in comparison_words if cw in answer)
            completeness_scores['comparison_depth'] = min(1.0, comparison_count / 2)

        elif question_type == 'evaluative':
            # 评价性问题需要观点和建议
            opinion_words = ['认为', '建议', '推荐', '优点', '缺点', '评价']
            opinion_count = sum(1 for ow in opinion_words if ow in answer)
            completeness_scores['opinion_provision'] = min(1.0, opinion_count / 2)

        return completeness_scores