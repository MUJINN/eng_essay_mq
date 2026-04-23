#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
实际调用Dify API测试
"""

import json
import sys
import os

# 添加路径
sys.path.insert(0, '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils')

from dify_client import DifyWorkflowClient, correct_chinese_essay_with_dify


def test_real_dify_call():
    """实际调用Dify API测试"""

    # 测试数据
    content = """撑正视快乐之长篇，向提高素养处慢溯。但是，并不是每个人都会追寻正确的快乐。

流年不改，星河暗换，蝉鸣高树，彧彧花在科技"光速"发展的背景下，越来越多的人沉浸在打麻将、熬夜追剧，肝游戏中，以"摆烂"放松为方式，以"躺平"为旗帜。长此以往，不仅他们的身体先跨掉，更可怕的是已然失去了奋进之心，彻底沦为自暴自弃者，终会被沦遗弃在虚拟的幻境中。这就是他们所谓的快乐。

追求快乐，需正视其本质。正如刘禹锡在《陋室铭》中所言："谈笑有鸿儒，往来无白丁，可以调素琴，阅金经。"虽身居陋室，但他的快乐却得以满足。弹琴、读书，朴素中渗透着典雅，实在令人向往。由此可见，快乐的本质不在于方式而在于人的心境与抱负，就像胡安焉，即使是在宿舍楼的杂物间内，即使是在微弱的灯光下，他仍可沉浸在阅读的汪洋中，品味着知识所带给他的滋润。"""

    problem = """阅读下面的材料，根据要求写作。(60分)

胡安焉在北京送快递时，每晚下班后，都会关掉手机，独自在宿舍楼的杂物间待两个小时。没有同事间吆喝的牌局，也没有手游网剧的干扰，他就着昏暗的灯光，读完了《尤利西斯》《没有个性的人》《审判》等大部头的著作。多年后，胡安焉成为一位畅销书作家，而当初寝室里消遣的同事，依然在快递站点起早贪黑地工作。

当今时代，获得快乐的方式层出不穷，但追求怎样的快乐，拉开了人与人之间的差距。

要求:综合材料内容及含意，选好角度，确定立意，明确文体，自拟标题，不要套作不得抄袭，不得泄露个人信息:不少于800字"""

    # 初始化客户端
    client = DifyWorkflowClient()

    print("=" * 80)
    print("实际调用Dify API测试")
    print("=" * 80)
    print()

    # 显示请求信息
    print("请求信息:")
    print("-" * 80)
    print(f"URL: {client.workflow_url}")
    print(f"Grade: 高二")
    print(f"Total Score: 60")
    print(f"Content Length: {len(content)} 字符")
    print(f"Problem Length: {len(problem)} 字符")
    print()

    try:
        print("正在发送请求到Dify API...")
        print("-" * 80)

        # 实际调用API
        result = correct_chinese_essay_with_dify(
            content=content,
            problem=problem,
            grade="高二",
            totalScore=60,
            subject_id="test_001",
            block_id="test_block_001",
            task_key="test_task_001",
            student_key="student_001",
            key="test_key_123"
        )

        print()
        print("=" * 80)
        print("✓ Dify API调用成功！")
        print("=" * 80)
        print()

        # 显示返回结果
        print("返回结果概览:")
        print("-" * 80)
        print(f"Score: {result.get('score', 0)}")
        print(f"Total Score: {result.get('totalScore', 0)}")
        print(f"Percentage Score: {result.get('percentageScore', 0)}")
        print(f"Topic Score: {result.get('topicScore', 0)}")
        print(f"Content Score: {result.get('contentScore', 0)}")
        print(f"Structure Score: {result.get('structureScore', 0)}")
        print(f"Language Score: {result.get('languageScore', 0)}")
        print()
        print(f"Comment Length: {len(result.get('comment', ''))} 字符")
        print(f"Suggestion Length: {len(result.get('suggestion', ''))} 字符")
        print(f"Error Corrections Count: {len(result.get('errorCorrection', []))}")
        print(f"Expressions Count: {len(result.get('expression', []))}")
        print()

        # 显示部分评语
        comment = result.get('comment', '')
        if comment:
            print("评语预览:")
            print("-" * 80)
            print(comment[:200] + "..." if len(comment) > 200 else comment)
            print()

        # 保存完整结果到文件
        output_file = '/home/wangdi5/eng_essay_mq/dify_test_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"完整结果已保存到: {output_file}")
        print()

        # 验证字段
        print("字段验证:")
        print("-" * 80)

        expected_fields = ['score', 'totalScore', 'percentageScore', 'topicScore',
                         'contentScore', 'structureScore', 'languageScore', 'comment']

        all_present = True
        for field in expected_fields:
            has_field = field in result
            status = "✓" if has_field else "✗"
            value = result.get(field, 'N/A')
            print(f"{status} {field:20s}: {value}")
            if not has_field:
                all_present = False

        print()
        print("=" * 80)
        if all_present:
            print("✓ 所有必要字段都已返回！")
        else:
            print("✗ 部分必要字段缺失！")
        print("=" * 80)

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print(f"✗ Dify API调用失败: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_real_dify_call()
