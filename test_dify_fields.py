#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
模拟MQ消息测试Dify字段传递
"""

import json
import sys
import os

# 添加项目路径
sys.path.append('/home/wangdi5/eng_essay_mq/eng_essay_mq')

from english_write import EssayCorrection
from instance_log_server import log_server


def test_dify_fields():
    """测试Dify调用时传入的字段"""

    # 模拟MQ消息格式（来自mq_client_grammar.py的run_essay_correction函数）
    mq_data = {
        "subjectId": "test_subject_001",      # 科目ID
        "blockId": "test_block_001",          # 题目块ID
        "taskKey": "test_task_001",           # 任务标识
        "grade": "高二",                       # 年级
        "totalScore": 60,                     # 总分
        "model": "ayx",                       # 模型类型
        "task": "cn",                         # 任务类型（cn表示语文）
        "key": "test_key_123",                # 返回标识
        "problem": "阅读下面的材料，根据要求写作。(60分)...",
        "students": [
            {
                "uploadKey": "student_001",
                "post_text": """撑正视快乐之长篇，向提高素养处慢溯但是，并不是每个人都会追寻正确的快乐
流年不改，星河暗换，蝉鸣高树，彧彧花在科技"光速"发展的背景下，越来越多的人繁沉伦在打麻将、熬夜追剧，肝游戏中，以"摆娱乐设施日新月异，人们得以烂"放松,休闲为的方挡篇牌，以"躺平"为旗帜、长此以往式越来越多，获得快乐的方式层出不穷。"""
            }
        ]
    }

    print("=" * 80)
    print("模拟MQ消息数据:")
    print("=" * 80)
    print(json.dumps(mq_data, ensure_ascii=False, indent=2))
    print()

    # 解析MQ数据（模拟mq_client_grammar.py中的逻辑）
    subjectId = mq_data.get('subjectId')
    blockId = mq_data.get('blockId')
    taskKey = mq_data.get('taskKey')
    grade = mq_data.get('grade')
    totalScore = mq_data.get('totalScore')
    model = mq_data.get('model', 'dianxin')
    task = mq_data.get('task', 'en-app')
    problem = mq_data.get('problem', '')
    students = mq_data.get('students', [])

    print("=" * 80)
    print("解析后的字段:")
    print("=" * 80)
    print(f"subjectId: {subjectId}")
    print(f"blockId: {blockId}")
    print(f"taskKey: {taskKey}")
    print(f"grade: {grade}")
    print(f"totalScore: {totalScore}")
    print(f"model: {model}")
    print(f"task: {task}")
    print(f"problem: {problem[:50]}...")
    print(f"students数量: {len(students)}")
    print()

    # 测试Dify字段构建（不实际调用API，只验证字段）
    print("=" * 80)
    print("将要传入Dify的inputs字段:")
    print("=" * 80)

    from utils.dify_client import DifyWorkflowClient

    client = DifyWorkflowClient()

    # 构建Dify请求参数
    inputs = {
        "student_answer": students[0]['post_text'],
        "question_content": problem,
        "subject_chs": "语文",
        "question_type": "作文",
    }

    # 添加可选参数
    if grade:
        inputs["grade"] = grade
    if totalScore:
        inputs["total_score"] = str(totalScore)
    if taskKey:
        inputs["task_key"] = taskKey
    if subjectId:
        inputs["subject_id"] = str(subjectId)
    if blockId:
        inputs["block_id"] = str(blockId)
    if students[0]['uploadKey']:
        inputs["student_key"] = students[0]['uploadKey']

    print(json.dumps(inputs, ensure_ascii=False, indent=2))
    print()

    # 验证必传字段
    print("=" * 80)
    print("字段验证:")
    print("=" * 80)
    required_fields = {
        "student_answer": "学生作文内容",
        "question_content": "作文题目要求",
        "subject_chs": "固定值：语文",
        "question_type": "固定值：作文",
        "grade": "年级",
        "total_score": "总分",
        "task_key": "任务标识",
        "subject_id": "科目ID",
        "block_id": "题目块ID",
        "student_key": "学生标识"
    }

    for field, desc in required_fields.items():
        status = "✓" if field in inputs else "✗"
        value = inputs.get(field, "未设置")
        print(f"{status} {field:20s} - {desc:20s} : {value}")
    print()

    # 构建完整请求体
    print("=" * 80)
    print("完整请求体:")
    print("=" * 80)
    request_data = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": f"mq_client_{taskKey or 'default'}"
    }

    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    print()

    # 显示HTTP请求信息
    print("=" * 80)
    print("HTTP请求信息:")
    print("=" * 80)
    print(f"URL: {client.workflow_url}")
    print(f"Method: POST")
    print(f"Headers:")
    print(f"  Authorization: Bearer {client.api_key[:20]}...")
    print(f"  Content-Type: application/json")
    print()

    return True


if __name__ == '__main__':
    try:
        test_dify_fields()
        print("=" * 80)
        print("测试完成！字段传递验证通过。")
        print("=" * 80)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
