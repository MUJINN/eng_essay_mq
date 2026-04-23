#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试：验证传递给 Dify 的参数
"""

import json

def simulate_dify_call(**kwargs):
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
        'comment': '批改完成',
    }

def test_current_implementation():
    """测试当前代码实现的参数传递"""

    print("\n" + "="*60)
    print("🧪 测试场景：task='cn', model='ayx'")
    print("="*60)

    # 模拟输入数据
    subjectId = 9768863
    blockId = 23576240
    taskKey = "9768863-23576240-1764578529021"
    grade = "高三"
    totalScore = 60
    problem = "作文：阅读下面的材料，根据要求写作。"
    content = "测试作文内容"
    uploadKey = "test-upload-key-12345"

    print(f"\n📥 输入参数:")
    print(f"  subjectId: {subjectId}")
    print(f"  blockId: {blockId}")
    print(f"  taskKey: {taskKey}")
    print(f"  grade: {grade}")
    print(f"  totalScore: {totalScore}")
    print(f"  uploadKey: {uploadKey}")

    # 模拟当前代码（第486行）的调用
    print("\n" + "-"*60)
    print("❌ 当前实现（ english_write.py:486行 ）")
    print("-"*60)
    print("调用: _correct_essay_by_dify(")
    print("    grade,")
    print("    totalScore,")
    print("    post_text,")
    print("    task=task,")
    print("    problem=problem")
    print(")")
    print("\n🔍 实际传递给 Dify 的参数:")

    # 模拟方法内部调用（当前代码）
    result_current = simulate_dify_call(
        content=content,
        problem=problem,
        grade=grade,
        totalScore=totalScore,
        # ❌ 缺失的参数
        subject_id=None,
        block_id=None,
        task_key=None,
        student_key=None
    )

    # 模拟修复后的调用
    print("\n" + "-"*60)
    print("✅ 修复后实现")
    print("-"*60)
    print("调用: _correct_essay_by_dify(")
    print("    grade,")
    print("    totalScore,")
    print("    post_text,")
    print("    task=task,")
    print("    problem=problem,")
    print("    subjectId=subjectId,      # 添加")
    print("    blockId=blockId,          # 添加")
    print("    taskKey=taskKey,          # 添加")
    print("    uploadKey=uploadKey       # 添加")
    print(")")
    print("\n🔍 实际传递给 Dify 的参数:")

    result_fixed = simulate_dify_call(
        content=content,
        problem=problem,
        grade=grade,
        totalScore=totalScore,
        # ✅ 添加的参数
        subject_id=subjectId,
        block_id=blockId,
        task_key=taskKey,
        student_key=uploadKey
    )

    print("\n" + "="*60)
    print("📊 对比分析")
    print("="*60)
    print("\n❌ 当前实现缺失的字段:")
    print("  - subject_id (学科ID)")
    print("  - block_id (题目块ID)")
    print("  - task_key (任务键)")
    print("  - student_key (学生标识)")
    print("\n✅ 修复后完整字段:")
    print("  - content (作文内容)")
    print("  - problem (作文题目)")
    print("  - grade (年级)")
    print("  - totalScore (总分)")
    print("  - subject_id (学科ID)")
    print("  - block_id (题目块ID)")
    print("  - task_key (任务键)")
    print("  - student_key (学生标识)")

    print("\n" + "="*60)
    print("💡 总结")
    print("="*60)
    print("当前实现虽然方法签名支持这些参数，")
    print("但调用时没有传入，所以 Dify 收不到这些字段。")
    print("需要修改 parser_one_essay 方法的第486行，")
    print("添加这些参数。")
    print("="*60 + "\n")

if __name__ == '__main__':
    test_current_implementation()
