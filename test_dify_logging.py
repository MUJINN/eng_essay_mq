#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试Dify字段映射日志输出
"""

import json
import sys
import os
import logging

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 添加项目路径
sys.path.insert(0, '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils')

from dify_client import DifyWorkflowClient


def test_dify_logging():
    """测试Dify字段映射日志输出"""

    # 读取真实的MQ数据
    mq_file = '/home/wangdi5/eng_essay_mq/receive_mq_data.json'
    with open(mq_file, 'r', encoding='utf-8') as f:
        mq_data = json.load(f)

    print("\n" + "=" * 80)
    print("测试Dify字段映射日志输出")
    print("=" * 80 + "\n")

    # 解析MQ数据
    subjectId = mq_data.get('subjectId')
    blockId = mq_data.get('blockId')
    taskKey = mq_data.get('taskKey')
    grade = mq_data.get('grade')
    totalScore = mq_data.get('totalScore')
    problem = mq_data.get('problem', '')
    students = mq_data.get('students', [])

    # 获取第一个学生的数据
    student = students[0]
    uploadKey = student['uploadKey']
    post_text = student['post_text']

    # 初始化Dify客户端
    client = DifyWorkflowClient()

    print(f"准备调用Dify API...")
    print(f"学生作文长度: {len(post_text)} 字符")
    print(f"题目长度: {len(problem)} 字符\n")

    try:
        # 调用Dify API（这将触发日志输出）
        result = client.correct_chinese_essay(
            student_answer=post_text,
            question_content=problem,
            grade=grade,
            total_score=str(totalScore),
            task_key=taskKey,
            subject_id=str(subjectId),
            block_id=str(blockId),
            student_key=uploadKey
        )

        print("\n" + "=" * 80)
        print("✓ Dify API调用成功！")
        print("=" * 80)
        print(f"返回分数: {result.get('score', 0)}")
        print(f"评语长度: {len(result.get('comment', ''))} 字符")
        print()

        return True

    except Exception as e:
        print(f"\n✗ Dify API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "Dify字段映射日志测试" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")

    test_dify_logging()

    print("\n注意：上面的日志显示了字段映射的完整过程")
    print("=" * 80 + "\n")
