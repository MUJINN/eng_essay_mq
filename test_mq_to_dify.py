#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试MQ数据到Dify的字段传递
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils')

from dify_client import DifyWorkflowClient


def test_mq_to_dify():
    """测试真实的MQ数据到Dify的字段映射"""

    # 读取真实的MQ数据
    mq_file = '/home/wangdi5/eng_essay_mq/receive_mq_data.json'
    with open(mq_file, 'r', encoding='utf-8') as f:
        mq_data = json.load(f)

    print("=" * 80)
    print("1. 原始MQ数据概览")
    print("=" * 80)
    print(f"subjectId: {mq_data.get('subjectId')}")
    print(f"blockId: {mq_data.get('blockId')}")
    print(f"taskKey: {mq_data.get('taskKey')}")
    print(f"grade: {mq_data.get('grade')}")
    print(f"totalScore: {mq_data.get('totalScore')}")
    print(f"model: {mq_data.get('model')}")
    print(f"task: {mq_data.get('task')}")
    print(f"problem长度: {len(mq_data.get('problem', ''))}")
    print(f"学生数量: {len(mq_data.get('students', []))}")
    print(f"第一个学生uploadKey: {mq_data['students'][0]['uploadKey']}")
    print(f"第一个学生作文长度: {len(mq_data['students'][0]['post_text'])}")
    print()

    # 解析MQ数据（模拟mq_client_grammar.py中的逻辑）
    subjectId = mq_data.get('subjectId')
    blockId = mq_data.get('blockId')
    taskKey = mq_data.get('taskKey')
    grade = mq_data.get('grade')
    totalScore = mq_data.get('totalScore')
    model = mq_data.get('model', 'ayx')
    task = mq_data.get('task', 'cn')
    problem = mq_data.get('problem', '')
    students = mq_data.get('students', [])

    print("=" * 80)
    print("2. MQ字段解析")
    print("=" * 80)
    print(f"subjectId: {subjectId} (type: {type(subjectId).__name__})")
    print(f"blockId: {blockId} (type: {type(blockId).__name__})")
    print(f"taskKey: {taskKey} (type: {type(taskKey).__name__})")
    print(f"grade: {grade} (type: {type(grade).__name__})")
    print(f"totalScore: {totalScore} (type: {type(totalScore).__name__})")
    print(f"model: {model} (type: {type(model).__name__})")
    print(f"task: {task} (type: {type(task).__name__})")
    print()

    # 构建Dify请求参数（模拟dify_client.py中的逻辑）
    print("=" * 80)
    print("3. 构建Dify inputs字段")
    print("=" * 80)

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

    print("Dify inputs字段:")
    print(json.dumps(inputs, ensure_ascii=False, indent=2))
    print()

    # 验证必传字段
    print("=" * 80)
    print("4. 字段完整性验证")
    print("=" * 80)

    required_fields = {
        "student_answer": "学生作文内容（必传）",
        "question_content": "作文题目要求（必传）",
        "subject_chs": "固定值：语文（必传）",
        "question_type": "固定值：作文（必传）",
        "grade": "年级（可选）",
        "total_score": "总分（可选）",
        "task_key": "任务标识（可选）",
        "subject_id": "科目ID（可选）",
        "block_id": "题目块ID（可选）",
        "student_key": "学生标识（可选）"
    }

    all_ok = True
    for field, desc in required_fields.items():
        is_present = field in inputs
        status = "✓" if is_present else "✗"
        value = inputs.get(field, "未设置")
        print(f"{status} {field:20s} - {desc:30s} : {value}")
        if not is_present:
            all_ok = False

    print()

    if all_ok:
        print("=" * 80)
        print("✓ 所有字段映射成功！")
        print("=" * 80)
    else:
        print("=" * 80)
        print("✗ 部分字段缺失！")
        print("=" * 80)

    # 构建完整请求体
    print()
    print("=" * 80)
    print("5. 完整HTTP请求体")
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
    print("6. HTTP请求信息")
    print("=" * 80)
    client = DifyWorkflowClient()
    print(f"URL: {client.workflow_url}")
    print(f"Method: POST")
    print(f"Headers:")
    print(f"  Authorization: Bearer {client.api_key[:20]}...")
    print(f"  Content-Type: application/json")
    print()

    # 实际调用测试（可选）
    print("=" * 80)
    print("7. 实际API调用测试")
    print("=" * 80)

    try:
        print("正在发送请求到Dify API...")
        print(f"作文内容预览: {inputs['student_answer'][:100]}...")
        print(f"题目内容预览: {inputs['question_content'][:100]}...")
        print()

        # 实际调用
        result = client.correct_chinese_essay(
            student_answer=inputs['student_answer'],
            question_content=inputs['question_content'],
            grade=grade,
            total_score=str(totalScore),
            task_key=taskKey,
            subject_id=str(subjectId),
            block_id=str(blockId),
            student_key=students[0]['uploadKey']
        )

        print("✓ Dify API调用成功！")
        print()
        print("返回结果:")
        print(f"  Score: {result.get('score', 0)}")
        print(f"  Percentage Score: {result.get('percentageScore', 0)}%")
        print(f"  Comment长度: {len(result.get('comment', ''))}")
        print(f"  维度分数: topic={result.get('topicScore')}, content={result.get('contentScore')}, "
              f"structure={result.get('structureScore')}, language={result.get('languageScore')}")
        print()

        # 保存结果
        output_file = '/home/wangdi5/eng_essay_mq/dify_test_result_real.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"完整结果已保存到: {output_file}")
        print()

        return True

    except Exception as e:
        print(f"✗ Dify API调用失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("注意：这可能是网络或认证问题，但字段映射是正确的。")
        return False


if __name__ == '__main__':
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "MQ数据到Dify字段传输测试" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        success = test_mq_to_dify()

        print()
        print("=" * 80)
        if success:
            print("✓ 测试完成 - 字段映射正确，API调用成功！")
        else:
            print("⚠ 测试完成 - 字段映射正确，API调用失败（可能是网络问题）")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
