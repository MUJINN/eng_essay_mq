#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
简化的Dify字段传递测试
"""

import json
import sys
import os

# 添加路径
sys.path.insert(0, '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils')


def test_dify_inputs():
    """测试Dify inputs字段构建"""

    # 模拟从MQ消息中解析出的数据
    subjectId = "test_subject_001"
    blockId = "test_block_001"
    taskKey = "test_task_001"
    grade = "高二"
    totalScore = 60
    uploadKey = "student_001"
    content = "学生作文内容..."
    problem = "作文题目要求..."

    print("=" * 80)
    print("输入参数:")
    print("=" * 80)
    print(f"subjectId: {subjectId}")
    print(f"blockId: {blockId}")
    print(f"taskKey: {taskKey}")
    print(f"grade: {grade}")
    print(f"totalScore: {totalScore}")
    print(f"uploadKey: {uploadKey}")
    print(f"content: {content[:30]}...")
    print(f"problem: {problem}")
    print()

    # 构建inputs（模拟dify_client.py的逻辑）
    inputs = {
        "student_answer": content,
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
    if uploadKey:
        inputs["student_key"] = uploadKey

    print("=" * 80)
    print("生成的inputs字段:")
    print("=" * 80)
    print(json.dumps(inputs, ensure_ascii=False, indent=2))
    print()

    # 构建完整请求体
    request_data = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": "mq_client_{}".format(taskKey or 'default')
    }

    print("=" * 80)
    print("完整请求体:")
    print("=" * 80)
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    print()

    # 验证字段
    print("=" * 80)
    print("字段验证:")
    print("=" * 80)

    expected_fields = {
        "student_answer": content,
        "question_content": problem,
        "subject_chs": "语文",
        "question_type": "作文",
        "grade": grade,
        "total_score": str(totalScore),
        "task_key": taskKey,
        "subject_id": subjectId,
        "block_id": blockId,
        "student_key": uploadKey
    }

    all_pass = True
    for field, expected_value in expected_fields.items():
        actual_value = inputs.get(field)
        status = "✓" if actual_value == expected_value else "✗"
        if actual_value != expected_value:
            all_pass = False
            print(f"{status} {field:20s} - 期望: {expected_value}, 实际: {actual_value}")
        else:
            print(f"{status} {field:20s} - {actual_value}")

    print()
    print("=" * 80)
    if all_pass:
        print("✓ 所有字段传递正确！")
    else:
        print("✗ 部分字段传递有误！")
    print("=" * 80)

    return all_pass


def test_dify_client_import():
    """测试是否能正确导入Dify客户端"""
    try:
        from dify_client import DifyWorkflowClient, correct_chinese_essay_with_dify
        print("=" * 80)
        print("✓ Dify客户端模块导入成功")
        print("=" * 80)

        client = DifyWorkflowClient()
        print(f"\n客户端配置:")
        print(f"  base_url: {client.base_url}")
        print(f"  api_key: {client.api_key[:20]}...")
        print(f"  workflow_url: {client.workflow_url}")
        return True
    except Exception as e:
        print("=" * 80)
        print(f"✗ Dify客户端模块导入失败: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    print("=" * 80)
    print("Dify字段传递测试")
    print("=" * 80)
    print()

    # 测试1: 导入模块
    import_ok = test_dify_client_import()
    print()

    # 测试2: 字段构建
    if import_ok:
        fields_ok = test_dify_inputs()
    else:
        print("由于导入失败，跳过字段构建测试")

    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
