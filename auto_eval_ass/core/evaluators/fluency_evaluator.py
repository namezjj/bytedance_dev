"""
流畅性评估器

评估模型回答的语言流畅性、可读性和表达自然度
"""

import re
import math
from typing import Tuple, Dict, Any, List
from collections import Counter

from .base_evaluator import BaseEvaluator

class FluencyEvaluator(BaseEvaluator):
    """
    流畅性评估器

    评估模型回答的语言表达是否流畅、自然，是否符合语言习惯
    """

    def get_dimension_name(self) -> str:
        return "流畅性"

    def get_dimension_description(self) -> str:
        return "评估回答的语言流畅度、表达自然度和文本可读性"

    def _get_evaluation_prompt(self) -> str:
        return """作为一个专业的语言流畅性评估员，请评估以下AI模型回答的流畅性。

评估维度：{dimension_name}
维度描述：{dimension_description}

问题：{question}

{context}

{conversation_history}

模型回答：
{model_response}

请从以下几个方面进行评估：
1. 语言流畅度：语句是否通顺流畅
2. 表达自然度：是否符合自然语言表达习惯
3. 语法正确性：语法是否正确无误
4. 可读性：文本是否易于理解和阅读

评估标准：
- 0.0-0.2：语言极不流畅，存在严重语法错误
- 0.2-0.4：语言不够流畅，存在较多语法问题
- 0.4-0.6：语言基本流畅但有些表达不自然
- 0.6-0.8：语言较流畅，表达自然，偶有小问题
- 0.8-1.0：语言非常流畅自然，表达清晰易懂

请按以下格式回复：
分数：[0-1之间的分数]
评估：[详细的评估说明，分析流畅性的具体表现]

示例回复：
分数：0.88
评估：回答语言流畅自然，语句通顺，表达清晰易懂，没有明显的语法错误。

请开始评估："""

    def _parse_evaluation_result(self, llm_response: str) -> Tuple[float, str]:
        """
        解析LLM的流畅性评估结果

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
            print(f"解析流畅性评估结果失败: {e}")
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
        positive_keywords = ['流畅', '自然', '通顺', '清晰', '易读', '表达']
        # 负面关键词
        negative_keywords = ['不流畅', '生硬', '拗口', '语法', '错误', '难懂']

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

    def calculate_readability_score(self, text: str) -> float:
        """
        计算文本可读性分数

        Args:
            text: 输入文本

        Returns:
            可读性分数 (0-1)
        """
        if not text:
            return 0.0

        # 分句
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # 计算基础指标
        total_chars = len(text)
        total_words = len(text.split())
        total_sentences = len(sentences)

        # 平均句长
        avg_sentence_length = total_chars / total_sentences

        # 平均词长
        avg_word_length = total_chars / total_words if total_words > 0 else 0

        # 句长变化性（标准差）
        sentence_lengths = [len(s) for s in sentences]
        if len(sentence_lengths) > 1:
            mean_length = sum(sentence_lengths) / len(sentence_lengths)
            length_variance = sum((l - mean_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            length_std = math.sqrt(length_variance)
        else:
            length_std = 0

        # 可读性评分（简化版本）
        readability_score = 1.0

        # 句长适中性（理想句长在20-50字符之间）
        if 15 <= avg_sentence_length <= 60:
            readability_score *= 1.0
        elif 10 <= avg_sentence_length <= 80:
            readability_score *= 0.8
        else:
            readability_score *= 0.6

        # 句长多样性（适度的多样性有利于可读性）
        if 5 <= length_std <= 25:
            readability_score *= 1.0
        elif length_std > 0:
            readability_score *= 0.9

        # 词长适中性（中文通常2-3字符为词）
        if 1.5 <= avg_word_length <= 3.5:
            readability_score *= 1.0
        else:
            readability_score *= 0.8

        return max(0.0, min(1.0, readability_score))

    def detect_grammar_issues(self, text: str) -> Dict[str, int]:
        """
        检测语法问题

        Args:
            text: 输入文本

        Returns:
            语法问题统计字典
        """
        issues = {
            'repetition': 0,
            'incomplete_sentences': 0,
            'punctuation_errors': 0,
            'unusual_phrases': 0
        }

        # 检测重复词汇
        words = text.split()
        if len(words) > 0:
            word_count = Counter(words)
            for word, count in word_count.items():
                if count > len(words) * 0.1 and len(word) > 1:  # 超过10%的重复
                    issues['repetition'] += 1

        # 检测不完整句子（非常短的句子）
        sentences = re.split(r'[。！？]', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 0 and len(sentence) < 5:
                issues['incomplete_sentences'] += 1

        # 检测标点符号问题
        # 连续标点
        if re.search(r'[。，！？；]{2,}', text):
            issues['punctuation_errors'] += 1

        # 句首无空格后的标点
        if re.search(r'[a-zA-Z][。，！？；]', text):
            issues['punctuation_errors'] += 1

        # 检测不寻常的短语（可以扩展）
        unusual_patterns = [
            r'的的',  # 重复助词
            r'了了',  # 重复助词
            r'是的是的',  # 重复确认
        ]
        for pattern in unusual_patterns:
            if re.search(pattern, text):
                issues['unusual_phrases'] += 1

        return issues

    def calculate_coherence_score(self, text: str) -> float:
        """
        计算文本连贯性分数

        Args:
            text: 输入文本

        Returns:
            连贯性分数 (0-1)
        """
        if not text:
            return 0.0

        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 2:
            return 0.8  # 单句给较高分数

        coherence_score = 0.0

        # 计算句间词汇重叠度
        total_overlap = 0
        for i in range(len(sentences) - 1):
            words1 = set(sentences[i].split())
            words2 = set(sentences[i + 1].split())

            if words1 and words2:
                overlap = len(words1 & words2) / len(words1 | words2)
                total_overlap += overlap

        avg_overlap = total_overlap / (len(sentences) - 1)

        # 适度的词汇重叠表示连贯
        if 0.1 <= avg_overlap <= 0.4:
            coherence_score += 0.5
        elif 0.05 <= avg_overlap <= 0.6:
            coherence_score += 0.3
        else:
            coherence_score += 0.1

        # 检查连接词使用
        connectors = ['但是', '因此', '所以', '而且', '另外', '首先', '其次', '最后', '总之']
        connector_count = sum(1 for conn in connectors if conn in text)

        if 1 <= connector_count <= len(sentences) * 0.3:
            coherence_score += 0.3
        elif connector_count > 0:
            coherence_score += 0.2

        # 检查主题一致性（简化版本）
        all_words = ' '.join(sentences).split()
        if all_words:
            word_freq = Counter(all_words)
            # 高频词汇比例
            high_freq_ratio = sum(1 for count in word_freq.values()
                                if count > 1) / len(word_freq)
            coherence_score += high_freq_ratio * 0.2

        return min(1.0, coherence_score)

    def calculate_naturalness_score(self, text: str) -> float:
        """
        计算表达自然度分数

        Args:
            text: 输入文本

        Returns:
            自然度分数 (0-1)
        """
        if not text:
            return 0.0

        naturalness_score = 1.0

        # 检测过于正式或生硬的表达
        formal_patterns = [
            r'综上所述',
            r'由此可见',
            r'因此可见',
            r'基于上述',
            r'鉴于以上'
        ]

        formal_count = sum(1 for pattern in formal_patterns if re.search(pattern, text))
        if formal_count > len(text.split()) * 0.05:  # 超过5%的过于正式表达
            naturalness_score -= 0.2

        # 检测重复句式
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) > 2:
            # 检查句首重复
            sentence_starts = [s[:5] for s in sentences]
            start_count = Counter(sentence_starts)
            repeated_starts = sum(1 for count in start_count.values() if count > 1)

            if repeated_starts > len(sentences) * 0.3:
                naturalness_score -= 0.15

        # 检测长度变化（自然的文本应该有长度变化）
        sentence_lengths = [len(s) for s in sentences]
        if len(sentence_lengths) > 1:
            unique_lengths = len(set(sentence_lengths))
            length_diversity = unique_lengths / len(sentence_lengths)

            if length_diversity < 0.3:  # 长度过于单一
                naturalness_score -= 0.1

        return max(0.0, naturalness_score)

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        获取流畅性评估的具体标准

        Returns:
            评估标准字典
        """
        criteria = super().get_evaluation_criteria()
        criteria.update({
            'specific_criteria': {
                'language_fluency': '语言流畅度',
                'expression_naturalness': '表达自然度',
                'grammar_correctness': '语法正确性',
                'text_readability': '文本可读性',
                'coherence': '内容连贯性'
            },
            'scoring_guidelines': {
                '0.0-0.2': '语言极不流畅，存在严重语法错误',
                '0.2-0.4': '语言不够流畅，存在较多语法问题',
                '0.4-0.6': '语言基本流畅但有些表达不自然',
                '0.6-0.8': '语言较流畅，表达自然，偶有小问题',
                '0.8-1.0': '语言非常流畅自然，表达清晰易懂'
            },
            'evaluation_focus': [
                '语句是否通顺流畅',
                '语法是否正确无误',
                '表达是否符合语言习惯',
                '文本是否易于阅读理解',
                '段落和句子结构是否合理'
            ],
            'common_issues': {
                'repetition': '词汇或句式重复',
                'incomplete_sentences': '句子不完整',
                'punctuation_errors': '标点符号错误',
                'unnatural_phrases': '表达不自然',
                'poor_coherence': '内容缺乏连贯性'
            }
        })
        return criteria

    def comprehensive_fluency_analysis(self, text: str) -> Dict[str, float]:
        """
        综合流畅性分析

        Args:
            text: 输入文本

        Returns:
            各方面流畅性评分字典
        """
        analysis = {}

        # 基础评分
        analysis['readability'] = self.calculate_readability_score(text)
        analysis['coherence'] = self.calculate_coherence_score(text)
        analysis['naturalness'] = self.calculate_naturalness_score(text)

        # 语法问题检测
        issues = self.detect_grammar_issues(text)
        total_issues = sum(issues.values())

        # 语法质量评分（问题越少分数越高）
        if total_issues == 0:
            analysis['grammar_quality'] = 1.0
        elif total_issues <= 2:
            analysis['grammar_quality'] = 0.8
        elif total_issues <= 5:
            analysis['grammar_quality'] = 0.6
        elif total_issues <= 10:
            analysis['grammar_quality'] = 0.4
        else:
            analysis['grammar_quality'] = 0.2

        # 综合流畅性分数
        weights = {
            'readability': 0.3,
            'coherence': 0.3,
            'naturalness': 0.25,
            'grammar_quality': 0.15
        }

        analysis['overall_fluency'] = sum(
            analysis[metric] * weight
            for metric, weight in weights.items()
        )

        return analysis