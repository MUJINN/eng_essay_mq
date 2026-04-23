#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试完整的MQ到Dify流程日志输出
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/wangdi5/eng_essay_mq/eng_essay_mq')

from english_write import EssayCorrection
from instance_log_server import log_server


def test_full_logging():
    """测试完整的MQ处理流程日志"""

    # 读取真实的MQ数据
    mq_file = '/home/wangdi5/eng_essay_mq/receive_mq_data.json'
    with open(mq_file, 'r', encoding='utf-8') as f:
        mq_data = json.load(f)

    print("\n" + "=" * 80)
    print("测试完整的MQ到Dify流程日志")
    print("=" * 80 + "\n")

    # 解析MQ数据（模拟mq_client_grammar.py中的逻辑）
    subjectId = mq_data.get('subjectId')
    blockId = mq_data.get('blockId')
    taskKey = mq_data.get('taskKey')
    grade = mq_data.get('grade')
    totalScore = mq_data.get('totalScore')
    model = mq_data.get('model', 'ayx')
    task = mq_data.get('task', 'cn')  # 使用cn表示中文
    problem = mq_data.get('problem', '')
    students = mq_data.get('students', [])

    print(f"MQ数据解析:")
    print(f"  subjectId: {subjectId}")
    print(f"  blockId: {blockId}")
    print(f"  taskKey: {taskKey}")
    print(f"  grade: {grade}")
    print(f"  totalScore: {totalScore}")
    print(f"  model: {model}")
    print(f"  task: {task}")
    print(f"  学生数量: {len(students)}")
    print()

    # 初始化批改服务
    ec = EssayCorrection(log_server)

    try:
        print("开始调用parser_one_essay...")
        print("-" * 80 + "\n")

        # 调用批改接口
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

        print("\n" + "=" * 80)
        print("✓ 批改完成！")
        print("=" * 80)
        print(f"返回结果包含 {len(result.get('students', []))} 个学生的批改结果")
        print()

        # 显示第一个学生的结果
        if result.get('students'):
            first_student = result['students'][0]
            print(f"第一个学生结果:")
            print(f"  uploadKey: {first_student.get('uploadKey')}")
            print(f"  分数: {first_student.get('score', 0)}")
            print(f"  评语长度: {len(first_student.get('comment', ''))} 字符")
            print(f"  维度分数: topic={first_student.get('topicScore')}, "
                  f"content={first_student.get('contentScore')}, "
                  f"structure={first_student.get('structureScore')}, "
                  f"language={first_student.get('languageScore')}")
            print()

        # 保存结果
        output_file = '/home/wangdi5/eng_essay_mq/full_logging_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"完整结果已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"\n✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 10 + "完整MQ到Dify流程日志测试" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    test_full_logging()

    print("\n" + "=" * 80)
    print("日志说明:")
    print("  1. 首先看到MQ数据解析日志")
    print("  2. 然后看到字段映射详情日志（来自english_write.py）")
    print("  3. 最后看到完整inputs字段日志（来自dify_client.py）")
    print("=" * 80 + "\n")
