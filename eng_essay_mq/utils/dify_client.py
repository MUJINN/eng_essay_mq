#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Dify工作流客户端 - 用于语文作文批改
从utils/dify.py中提取的核心请求方法
"""

import json
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DifyWorkflowClient:
    """Dify工作流客户端，用于调用语文作文批改服务"""

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        初始化Dify客户端

        Args:
            base_url: Dify服务基础URL，默认为 https://dify-wan.iyunxiao.com
            api_key: API密钥，默认为 app-bWAHsOUjHReTr9IsD9YBAu72
        """
        self.base_url = base_url or "https://dify-wan.iyunxiao.com"
        self.api_key = api_key or "app-bWAHsOUjHReTr9IsD9YBAu72"
        self.workflow_url = "{}/v1/workflows/run".format(self.base_url)

    def correct_chinese_essay(self,
                             student_answer: str,
                             question_content: str,
                             grade: str = None,
                             total_score: str = None,
                             task_key: str = None,
                             subject_id: str = None,
                             block_id: str = None,
                             student_key: str = None,
                             **kwargs) -> Dict[str, Any]:
        """
        调用Dify工作流批改语文作文

        Args:
            student_answer: 学生作文内容
            question_content: 作文题目要求
            grade: 年级（如：高二）
            total_score: 总分（如：60）
            task_key: 任务标识
            subject_id: 科目ID
            block_id: 题目块ID
            student_key: 学生标识
            **kwargs: 其他可选参数

        Returns:
            批改结果字典，包含：
            - score: 得分
            - percentageScore: 得分率
            - comments: 批改评语
            - highlights: 优秀句子高亮
            - errors: 错误标记
        """
        # 构建请求参数
        inputs = {
            "student_answer": student_answer,
            "question_content": question_content,
            "subject_chs": "语文",  # 固定为语文
            "question_type": "作文",  # 固定为作文类型
        }

        # 添加可选参数
        if grade:
            inputs["grade"] = grade
        if total_score:
            inputs["total_score"] = str(total_score)
        if task_key:
            inputs["task_key"] = task_key
        if subject_id:
            inputs["subject_id"] = str(subject_id)
        if block_id:
            inputs["block_id"] = str(block_id)
        if student_key:
            inputs["student_key"] = student_key

        # 添加其他额外参数
        for key, value in kwargs.items():
            if value is not None:
                inputs[key] = str(value) if not isinstance(value, str) else value

        # 构建完整请求体
        request_data = {
            "inputs": inputs,
            "response_mode": "blocking",  # 使用阻塞模式获取完整结果
            "user": "mq_client_{}".format(task_key or 'default')
        }

        # 请求头
        headers = {
            "Authorization": "Bearer {}".format(self.api_key),
            "Content-Type": "application/json"
        }

        try:
            logger.info("Calling Dify workflow API: {}".format(self.workflow_url))
            logger.debug("Request data: {}".format(json.dumps(request_data, ensure_ascii=False)))

            # 发送请求
            response = requests.post(
                self.workflow_url,
                headers=headers,
                json=request_data,
                timeout=120  # 2分钟超时
            )

            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 提取批改结果
            correction_result = self._parse_dify_response(result, int(total_score))

            return correction_result

        except requests.exceptions.RequestException as e:
            logger.error("Failed to call Dify API: {}".format(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in Dify client: {}".format(e))
            raise

    def _parse_dify_response(self, response: Dict[str, Any], total_score: int) -> Dict[str, Any]:
        """
        解析Dify工作流返回的响应，对齐电信模型的字段格式

        Args:
            response: Dify API返回的原始响应

        Returns:
            标准化的批改结果，与电信模型格式对齐
        """
        try:
            # 从响应中提取输出数据
            if 'data' in response and 'outputs' in response['data']:
                outputs = response['data']['outputs']
            elif 'outputs' in response:
                outputs = response['outputs']
            elif 'result' in response:
                # 如果result是字符串，尝试解析为JSON
                if isinstance(response['result'], str):
                    try:
                        outputs = json.loads(response['result'])
                    except json.JSONDecodeError:
                        outputs = {"result": response['result']}
                else:
                    outputs = response['result']
            else:
                outputs = response

            # 提取基础分数（满分60分）
            score = float(outputs.get("score", 0)) if outputs.get("score") else 0

            # 计算百分比分数
            saved_total_score = total_score
            if total_score <= 0:
                saved_total_score = 60

            percentageScore = (score / saved_total_score) * 100 if score > 0 else 0

            # 处理维度分数，转换为5分制
            dimension_scores = self._convert_dimension_scores(outputs.get("score_dimension", []), saved_total_score)

            # 构建标准化结果（对齐电信模型格式）
            correction_result = {
                # 基础分数字段
                "score": score,
                "percentageScore": percentageScore,
                "totalScore": score,  # 保持与电信模型一致

                # 维度分数（5分制）
                "topicScore": dimension_scores.get("主题契合", 0),      # 主题契合
                "contentScore": dimension_scores.get("内容与情感", 0),   # 内容与情感
                "structureScore": dimension_scores.get("结构严谨", 0),   # 结构严谨
                "languageScore": dimension_scores.get("表达规范", 0),    # 表达规范

                # 评语和建议
                "comment": outputs.get("reason", ""),  # reason字段对应comment
                "suggestion": outputs.get("suggestion", ""),

                # 其他字段
                "errorCorrection": outputs.get("errorCorrection", []),
                "expression": outputs.get("expression", []),
                "improveArticle": outputs.get("improveArticle", ""),

                # 保留原始维度信息和响应
                "score_dimension": outputs.get("score_dimension", []),
                "raw_response": outputs
            }

            return correction_result

        except Exception as e:
            logger.error("Failed to parse Dify response: {}".format(e))
            logger.debug("Raw response: {}".format(response))
            # 返回最基本的结果（对齐电信模型格式）
            return {
                "score": 0,
                "percentageScore": 0,
                "totalScore": 0,
                "topicScore": 0,
                "contentScore": 0,
                "structureScore": 0,
                "languageScore": 0,
                "comment": "批改服务解析失败",
                "suggestion": "",
                "errorCorrection": [],
                "expression": [],
                "improveArticle": "",
                "raw_response": response
            }

    def _convert_dimension_scores(self, score_dimensions: list, total_score : int) -> Dict[str, int]:
        """
        将维度分数转换为5分制

        Args:
            score_dimensions: 维度分数列表

        Returns:
            转换后的5分制分数字典
        """
        # # 各维度的总分映射
        # dimension_max_scores = {
        #     "主题契合": 15,
        #     "内容与情感": 20,
        #     "结构严谨": 15,
        #     "表达规范": 10
        # }

        # 各维度的总分映射（服务端返回4分制）
        dimension_max_scores = {
            "主题契合": 4,
            "内容与情感": 4,
            "结构严谨": 4,
            "表达规范": 4
        }

        converted_scores = {}

        try:
            for dimension in score_dimensions:
                if isinstance(dimension, dict):
                    name = dimension.get("dimension_name", "")
                    score = float(dimension.get("dimension_score", 0))

                    if name in dimension_max_scores:
                        max_score = dimension_max_scores[name]
                        # 转换为5分制并四舍五入取整
                        five_point_score = round((score / max_score) * 5)
                        # 确保分数在0-5之间
                        five_point_score = max(0, min(5, five_point_score))
                        converted_scores[name] = five_point_score

                        logger.debug("维度 '{}': {}/{} -> 5分制: {}".format(name, score, max_score, five_point_score))

        except Exception as e:
            logger.error("Error converting dimension scores: {}".format(e))

        # 确保所有维度都有值（默认为0）
        for dim_name in dimension_max_scores.keys():
            if dim_name not in converted_scores:
                converted_scores[dim_name] = 0

        return converted_scores


# 创建一个默认实例供直接调用
default_client = DifyWorkflowClient()


def correct_chinese_essay_with_dify(content: str, problem: str, grade: str = None,
                                   totalScore: int = 60, **kwargs) -> Dict[str, Any]:
    """
    便捷函数：使用Dify工作流批改语文作文

    Args:
        content: 学生作文内容
        problem: 作文题目要求
        grade: 年级
        totalScore: 总分
        **kwargs: 其他参数

    Returns:
        批改结果字典
    """
    return default_client.correct_chinese_essay(
        student_answer=content,
        question_content=problem,
        grade=grade,
        total_score=str(totalScore),
        **kwargs
    )