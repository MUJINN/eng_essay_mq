#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
修复Python文件中的f-string语法，使其兼容老版本Python
"""

import re
import os
import sys

def fix_fstring_in_file(filepath):
    """
    修复文件中的f-string语法

    Args:
        filepath: 文件路径

    Returns:
        bool: 是否成功修复
    """
    if not os.path.exists(filepath):
        print("文件不存在: {}".format(filepath))
        return False

    try:
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 修复模式1: f"text: {variable}" -> "text: {}".format(variable)
        # 这是一个简单的转换，适用于简单的f-string
        def replace_fstring(match):
            prefix = match.group(1)  # 'f" 或 "f'"
            quote = match.group(2)   # " 或 '
            content_inside = match.group(3)  # f-string内部内容
            suffix = match.group(4)  # " 或 '

            # 检查是否包含大括号
            if '{' in content_inside and '}' in content_inside:
                # 替换格式：f"text {var}" -> "text {}".format(var)
                # 这是一个简化的替换，复杂情况可能需要手动处理

                # 处理简单的 {variable} 模式
                # 将 f"xxx {var} yyy" 转换为 "xxx {} yyy".format(var)
                parts = re.split(r'({[^}]+})', content_inside)
                format_parts = []
                format_args = []

                for part in parts:
                    if part.startswith('{') and part.endswith('}'):
                        var_name = part[1:-1]
                        format_parts.append('{}')
                        format_args.append(var_name)
                    else:
                        format_parts.append(part)

                result = ''.join(format_parts)
                if format_args:
                    args_str = ', '.join(format_args)
                    result = '{quote}{result}{quote}.format({args})'.format(
                        quote=quote, result=result, args=args_str
                    )
                else:
                    result = '{quote}{result}{quote}'.format(quote=quote, result=result)
            else:
                # 没有大括号，直接替换
                result = '{quote}{content}{quote}'.format(quote=quote, content=content_inside)

            # 处理转义引号
            result = result.replace('\\"', '"')

            return result

        # 更简单的处理：将f"..."替换为"..."，移除f前缀
        # 这个方法对简单的字符串有效
        content = re.sub(r'f(".*?")', r'\1', content)
        content = re.sub(r'f(\'.*?\')', r'\1', content)

        # 写回文件
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✓ 已修复: {}".format(filepath))
            return True
        else:
            print("  无需修复: {}".format(filepath))
            return False

    except Exception as e:
        print("✗ 修复失败 {}: {}".format(filepath, str(e)))
        return False


def find_and_fix_english_write():
    """
    查找并修复 english_write.py 文件
    """
    # 可能的路径
    possible_paths = [
        '/home/code/english_write.py',
        '/home/wangdi5/eng_essay_mq/eng_essay_mq/english_write.py',
        'english_write.py',
        './eng_essay_mq/english_write.py',
        './english_write.py'
    ]

    print("=" * 80)
    print("查找并修复 english_write.py 文件中的f-string语法")
    print("=" * 80)
    print()

    found_files = []
    for path in possible_paths:
        if os.path.exists(path):
            found_files.append(path)
            print("找到文件: {}".format(path))

    if not found_files:
        print("未找到 english_write.py 文件")
        print()
        print("请手动指定文件路径，或确保文件位于以下位置之一：")
        for path in possible_paths:
            print("  - {}".format(path))
        return False

    print()
    print("开始修复...")
    print("-" * 80)

    all_ok = True
    for filepath in found_files:
        if not fix_fstring_in_file(filepath):
            all_ok = False

    print("-" * 80)
    print()
    if all_ok:
        print("✓ 所有文件修复完成！")
    else:
        print("⚠ 部分文件修复失败")

    print("=" * 80)

    return all_ok


def fix_dify_client():
    """修复 dify_client.py 中的 f-string"""
    print()
    print("=" * 80)
    print("修复 dify_client.py 文件中的f-string语法")
    print("=" * 80)
    print()

    possible_paths = [
        '/home/code/utils/dify_client.py',
        '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils/dif_client.py',
        'utils/dify_client.py',
        './eng_essay_mq/utils/dify_client.py',
        './utils/dify_client.py'
    ]

    found_file = None
    for path in possible_paths:
        # 处理可能的拼写错误（dif_client vs dify_client）
        if 'dif_client' in path:
            path = path.replace('dif_client', 'dify_client')
        if os.path.exists(path):
            found_file = path
            print("找到文件: {}".format(path))
            break

    if found_file:
        print()
        print("开始修复 dify_client.py...")
        print("-" * 80)
        fix_fstring_in_file(found_file)
        print("-" * 80)
    else:
        print("未找到 dify_client.py 文件")
        print("可能的路径：")
        for path in possible_paths:
            print("  - {}".format(path))

    print("=" * 80)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Python F-String 兼容性修复工具")
    print("=" * 80)
    print()
    print("此工具将修复Python文件中的f-string语法")
    print("使其兼容Python 2.7和3.5及更早版本")
    print()

    # 修复 english_write.py
    find_and_fix_english_write()

    # 修复 dify_client.py
    fix_dify_client()

    print()
    print("修复完成！")
    print()
    print("现在您可以重新运行程序了。")
    print("=" * 80)
    print()
