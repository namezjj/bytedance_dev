"""
相关性评估器

评估模型回答与问题的相关性和切题程度
"""

import re
import math
from typing import Tuple, Dict, Any, List
from collections import Counter

from .base_evaluator import BaseEvaluator

class RelevanceEvaluator(BaseEvaluator):
    """
    相关性评估器

    评估模型回答是否直接回答了用户问题，是否切题，是否包含无关信息
    """

    def get_dimension_name(self) -> str:
        return "相关性"

    def get_dimension_description(self) -> str:
        return "评估回答与问题的相关性、切题程度和信息聚焦度"

    def _get_evaluation_prompt(self) -> str:
        return """作为一个专业的问答质量评估员，请评估以下AI模型回答的相关性。

评估维度：{dimension_name}
维度描述：{dimension_description}

问题：{question}

{context}

{conversation_history}

模型回答：
{model_response}

请从以下几个方面进行评估：
1. 直接相关性：回答是否直接针对问题
2. 切题程度：回答是否偏离主题
3. 信息聚焦：是否包含大量无关信息
4. 问题覆盖：是否完整覆盖了问题的各个方面

评估标准：
- 0.0-0.2：回答完全无关或严重偏离主题
- 0.2-0.4：回答部分相关但包含大量无关内容
- 0.4-0.6：回答基本相关但不够聚焦
- 0.6-0.8：回答相关且切题，偶有少量无关信息
- 0.8-1.0：回答高度相关，完全切题且聚焦

请按以下格式回复：
分数：[0-1之间的分数]
评估：[详细的评估说明，分析相关性的具体表现]

示例回复：
分数：0.90
评估：回答直接针对了用户的问题，全面覆盖了问题的各个方面，没有包含无关信息。

请开始评估："""

    def _parse_evaluation_result(self, llm_response: str) -> Tuple[float, str]:
        """
        解析LLM的相关性评估结果

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
                # 尝试英文格式
                score_match = re.search(r'Score[：:]\s*([0-9]*\.?[0-9]+)', llm_response)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    # 启发式分数提取
                    score = self._heuristic_score_extraction(llm_response)

            # 提取评估内容
            evaluation_match = re.search(r'评估[：:]\s*(.+)', llm_response, re.DOTALL)
            if evaluation_match:
                feedback = evaluation_match.group(1).strip()
            else:
                # 尝试英文格式
                evaluation_match = re.search(r'Evaluation[：:]\s*(.+)', llm_response, re.DOTALL)
                if evaluation_match:
                    feedback = evaluation_match.group(1).strip()
                else:
                    feedback = llm_response.strip()

            return score, feedback

        except Exception as e:
            print(f"解析相关性评估结果失败: {e}")
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
        positive_keywords = ['相关', '切题', '直接', '针对', '覆盖', '聚焦']
        # 负面关键词
        negative_keywords = ['无关', '偏离', '不相关', '跑题', '离题', '无关信息']

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

    def calculate_text_relevance(self, question: str, answer: str) -> float:
        """
        计算问题和回答的文本相关性

        Args:
            question: 问题
            answer: 回答

        Returns:
            相关性分数 (0-1)
        """
        # 提取关键词
        question_words = self._extract_keywords(question)
        answer_words = self._extract_keywords(answer)

        if not question_words:
            return 0.5

        # 计算TF-IDF权重
        question_tfidf = self._calculate_tfidf(question_words)
        answer_tfidf = self._calculate_tfidf(answer_words)

        # 计算余弦相似度
        return self._cosine_similarity(question_tfidf, answer_tfidf)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 简单的关键词提取：去除停用词，提取名词和动词
        import jieba
        import jieba.posseg as pseg

        # 简单停用词列表
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

        words = []
        for word, flag in pseg.cut(text):
            # 只保留名词、动词、形容词
            if flag.startswith(('n', 'v', 'a')) and len(word) > 1 and word not in stop_words:
                words.append(word.lower())

        return words

    def _calculate_tfidf(self, words: List[str]) -> Dict[str, float]:
        """
        计算TF-IDF权重

        Args:
            words: 词列表

        Returns:
            TF-IDF字典
        """
        if not words:
            return {}

        # 计算词频
        tf = Counter(words)
        total_words = len(words)

        # 计算TF-IDF（简化版本，使用词频作为权重）
        tfidf = {}
        for word, count in tf.items():
            tfidf[word] = count / total_words

        return tfidf

    def _cosine_similarity(self, dict1: Dict[str, float], dict2: Dict[str, float]) -> float:
        """
        计算余弦相似度

        Args:
            dict1: 字典1
            dict2: 字典2

        Returns:
            余弦相似度
        """
        # 获取所有词汇
        all_words = set(dict1.keys()) | set(dict2.keys())

        if not all_words:
            return 0.0

        # 计算向量
        vec1 = [dict1.get(word, 0.0) for word in all_words]
        vec2 = [dict2.get(word, 0.0) for word in all_words]

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def analyze_question_type(self, question: str) -> str:
        """
        分析问题类型

        Args:
            question: 问题

        Returns:
            问题类型
        """
        question_lower = question.lower()

        # 事实性问题
        if any(word in question_lower for word in ['什么', '是什么', '谁是', '哪里', '何时', '为什么', '如何']):
            return 'factual'

        # 操作性问题
        if any(word in question_lower for word in ['怎么', '如何', '怎样', '步骤', '方法']):
            return 'procedural'

        # 比较性问题
        if any(word in question_lower for word in ['比较', '对比', '区别', '差异', '哪个更好']):
            return 'comparative'

        # 评价性问题
        if any(word in question_lower for word in ['评价', '看法', '意见', '建议', '推荐']):
            return 'evaluative'

        # 默认类型
        return 'general'

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        获取相关性评估的具体标准

        Returns:
            评估标准字典
        """
        criteria = super().get_evaluation_criteria()
        criteria.update({
            'specific_criteria': {
                'direct_relevance': '直接针对问题的程度',
                'topic_coherence': '主题一致性',
                'information_focus': '信息聚焦度',
                'question_coverage': '问题覆盖完整性',
                'irrelevance_detection': '无关信息的检测'
            },
            'scoring_guidelines': {
                '0.0-0.2': '完全无关或严重偏离主题',
                '0.2-0.4': '部分相关但包含大量无关内容',
                '0.4-0.6': '基本相关但不够聚焦',
                '0.6-0.8': '相关且切题，偶有少量无关信息',
                '0.8-1.0': '高度相关，完全切题且聚焦'
            },
            'evaluation_focus': [
                '回答是否直接针对问题核心',
                '是否包含过多无关信息',
                '是否完整覆盖问题的各个方面',
                '信息组织是否合理',
                '是否针对问题类型进行相应回答'
            ],
            'question_types': {
                'factual': '事实性问题 - 期待准确的答案',
                'procedural': '操作性问题 - 期待步骤说明',
                'comparative': '比较性问题 - 期待对比分析',
                'evaluative': '评价性问题 - 期待观点和建议',
                'general': '一般性问题 - 期待综合回答'
            }
        })
        return criteria

    def calculate_relevance_penalty(self, answer: str, question_type: str) -> float:
        """
        根据问题类型计算相关性惩罚

        Args:
            answer: 回答
            question_type: 问题类型

        Returns:
            惩罚分数 (0-1, 1表示无惩罚)
        """
        # 检查回答是否包含与问题类型匹配的内容
        answer_lower = answer.lower()

        type_keywords = {
            'factual': ['事实', '数据', '具体', '准确', '实际上'],
            'procedural': ['步骤', '首先', '然后', '方法', '操作', '流程'],
            'comparative': ['比较', '对比', '区别', '相同', '不同', '优势'],
            'evaluative': ['认为', '建议', '推荐', '优点', '缺点', '评价'],
            'general': ['总的来说', '总的来说', '基本上', '通常']
        }

        relevant_keywords = type_keywords.get(question_type, [])
        keyword_count = sum(1 for keyword in relevant_keywords if keyword in answer_lower)

        # 根据关键词匹配程度给分
        if keyword_count >= 3:
            return 1.0  # 高度相关
        elif keyword_count >= 2:
            return 0.8  # 较相关
        elif keyword_count >= 1:
            return 0.6  # 部分相关
        else:
            return 0.4  # 相关性较低