#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
测试 n8n 模型集成
"""

import json
from eng_essay_mq.english_write import EssayCorrection
from eng_essay_mq.instance_log_server import log_server

def test_n8n_model():
    """测试 n8n 模型"""
    ec = EssayCorrection(log_server, n8n_api="https://yj-llm-wan.yunxiao.com/correct_essay")

    subjectId = 'test-n8n-001'
    blockId = 'test-block-001'
    taskKey = 'test-key-001'
    grade = '高二'
    totalScore = 15
    students = [{
        "uploadKey": "test-student-001",
        "post_text": "I'm Li Hua. I'm writing to apply for the position of host in the English-reading Salon. "
                   "I believe I am qualified for this position. First, I have good command of English. "
                   "Second, I have experience in hosting activities. I would appreciate it if you could consider my application."
    }]

    model = 'n8n'
    task = 'en-app'
    problem = "假定你是李华，得知研学机构 Global Camp 正在招募市图书馆暑期" \
              "英语阅读沙龙（English-reading Salon）活动的主持人，请写一封英文申请信"

    print("=" * 80)
    print("测试 n8n 模型")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Task: {task}")
    print(f"Grade: {grade}")
    print(f"Total Score: {totalScore}")
    print(f"Student Count: {len(students)}")
    print("-" * 80)

    try:
        result = ec.parser_one_essay(
            subjectId, blockId, taskKey, grade, totalScore,
            students, model, task, problem
        )

        print("\n批改结果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 验证结果结构
        assert 'subjectId' in result
        assert 'blockId' in result
        assert 'taskKey' in result
        assert 'students' in result
        assert len(result['students']) == 1

        student_result = result['students'][0]
        print("\n学生批改结果字段：")
        print(f"  - uploadKey: {student_result.get('uploadKey')}")
        print(f"  - score: {student_result.get('score')}")
        print(f"  - highlight: {len(student_result.get('highlight', []))} 条")
        print(f"  - error_set: {len(student_result.get('error_set', []))} 条")
        print(f"  - comment: {student_result.get('comment', '')[:50]}...")
        print(f"  - topicScore: {student_result.get('topicScore')}")
        print(f"  - contentScore: {student_result.get('contentScore')}")
        print(f"  - structureScore: {student_result.get('structureScore')}")
        print(f"  - languageScore: {student_result.get('languageScore')}")

        print("\n✅ 测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_n8n_model()
