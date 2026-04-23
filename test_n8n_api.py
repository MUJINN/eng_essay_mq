#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大模型API接口
"""
import requests
import json

# API地址
api_url = "https://n8n.iyunxiao.com/webhook/ai_group/english/easy_essay"

# 测试数据
test_data = {
    "task": "en-app",
    "model": "llm",
    "content": "He walked in front of the desk, angrily looked the books, which caused all the things. He held them, throat them here and there. Then Jack sit down, lay on the chair with no force. Neither moving or getting mad, Jack just stay at there. Jack was thinking, why I must study these subjects that I hate? Why mother always told me what to do? At the moment, his mother knocked the door, but Jack pretended didn't hear. He shaked his head and stared at these books. At the time, Jack looked a note, and heard his mother say, What do you want to eat? Don't hurt yourself, dear\nHe looked at the note, which it has writen come on, I believe you can make better",
    "problem": "第二节（满分25分）阅读下面材料，根据其内容和所给段落开头语续写两段，使之构成一篇完整的短文。",
    "grade": "高二"
}

print("=" * 80)
print("测试大模型API接口")
print("=" * 80)
print(f"\nAPI地址: {api_url}")
print(f"\n请求数据:")
print(json.dumps(test_data, ensure_ascii=False, indent=2))
print("\n" + "=" * 80)

try:
    # 发送POST请求
    print("\n正在发送请求...")
    response = requests.post(
        api_url,
        json=test_data,
        headers={"Content-Type": "application/json"},
        timeout=120  # 2分钟超时
    )

    print(f"\n响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print("\n" + "=" * 80)
    print("\n响应内容:")

    # 尝试解析JSON响应
    try:
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 保存到文件
        output_file = "/home/wangdi5/eng_essay_mq/n8n_api_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n\n响应已保存到: {output_file}")

        # 分析返回的数据结构
        print("\n" + "=" * 80)
        print("\n数据结构分析:")
        print("-" * 80)

        if 'data' in result:
            data = result['data']
            print(f"✓ 包含 'data' 字段")

            # 检查percentageScore
            if 'percentageScore' in data:
                print(f"✓ percentageScore: {data['percentageScore']}")
            else:
                print("✗ 缺少 'percentageScore' 字段")

            # 检查highlight
            if 'highlight' in data:
                print(f"✓ highlight: {len(data['highlight'])} 条")
                for i, item in enumerate(data['highlight'][:3], 1):
                    print(f"  {i}. {item}")
            else:
                print("✗ 缺少 'highlight' 字段")

            # 检查error_set
            if 'error_set' in data:
                print(f"✓ error_set: {len(data['error_set'])} 条")
                for i, item in enumerate(data['error_set'][:3], 1):
                    print(f"  {i}. offset={item.get('offset')}, length={item.get('length')}, message={item.get('message')[:50]}...")
            else:
                print("✗ 缺少 'error_set' 字段")

        else:
            print("✗ 响应中不包含 'data' 字段")
            print(f"实际包含的键: {list(result.keys())}")

    except json.JSONDecodeError as e:
        print(f"⚠ 响应不是有效的JSON格式")
        print(f"错误: {e}")
        print(f"\n原始响应文本:")
        print(response.text)

except requests.exceptions.Timeout:
    print("\n❌ 请求超时（超过120秒）")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ 连接错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"\n❌ 请求失败: {e}")
except Exception as e:
    print(f"\n❌ 未知错误: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
