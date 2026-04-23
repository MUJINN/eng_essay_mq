#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试：验证传递给 Dify 的字段
"""

import json
from unittest.mock import patch, MagicMock

# 模拟 dify_client 中的 correct_chinese_essay_with_dify 函数
def mock_correct_chinese_essay_with_dify(**kwargs):
    """模拟 Dify 客户端，记录接收到的参数"""
    print("\n" + "="*60)
    print("📡 传递给 Dify 的参数:")
    print("="*60)
    for key, value in kwargs.items():
        print(f"  {key}: {value}")
    print("="*60)

    # 返回模拟的批改结果
    return {
        'score': 48,
        'totalScore': 48,
        'percentageScore': 80.0,
        'topicScore': 4,
        'contentScore': 4,
        'structureScore': 4,
        'languageScore': 4,
        'comment': '批改完成',
        'suggestion': '',
        'errorCorrection': [],
        'expression': [],
        'improveArticle': '',
        'raw_response': {}
    }

# 应用 mock
import eng_essay_mq.utils.dify_client as dify_client
dify_client.correct_chinese_essay_with_dify = mock_correct_chinese_essay_with_dify

# 导入测试模块
from eng_essay_mq.english_write import EssayCorrection
from eng_essay_mq.instance_log_server import log_server

def test_dify_params():
    """测试传递给 Dify 的参数"""

    # 创建批改器实例
    ec = EssayCorrection(log_server)

    # 测试数据
    subjectId = 9768863
    blockId = 23576240
    taskKey = "9768863-23576240-1764578529021"
    grade = "高三"
    totalScore = 60
    model = 'ayx'
    task = 'cn'
    problem = "作文：阅读下面的材料，根据要求写作。"

    students = [
        {
            "uploadKey": "test-upload-key-12345",
            "post_text": "测试作文内容"
        }
    ]

    print("\n" + "="*60)
    print("🧪 测试场景：task='cn', model='ayx'")
    print("="*60)
    print(f"subjectId: {subjectId}")
    print(f"blockId: {blockId}")
    print(f"taskKey: {taskKey}")
    print(f"grade: {grade}")
    print(f"totalScore: {totalScore}")
    print(f"model: {model}")
    print(f"task: {task}")
    print(f"uploadKey: {students[0]['uploadKey']}")

    # 调用批改方法
    print("\n📝 调用 parser_one_essay...")
    result = ec.parser_one_essay(
        subjectId=subjectId,
        blockId=blockId,
        taskKey=taskKey,
        grade=grade,
        totalScore=totalScore,
        students=students,
        model=model,
        task=task,
        problem=problem
    )

    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

    # 分析结果
    print("\n📊 字段传递情况分析:")
    print("-" * 60)

    # 检查 Dify 是否收到了完整参数
    # 注意：由于我们 mock 了函数，实际参数会打印出来

if __name__ == '__main__':
    test_dify_params()
