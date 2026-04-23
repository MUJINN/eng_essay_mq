#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
检查Python文件语法
"""

import py_compile
import sys

def check_file_syntax(filepath):
    """检查文件语法"""
    try:
        py_compile.compile(filepath, doraise=True)
        print("✓ {} - 语法正确".format(filepath))
        return True
    except py_compile.PyCompileError as e:
        print("✗ {} - 语法错误:".format(filepath))
        print(str(e))
        return False

if __name__ == '__main__':
    files_to_check = [
        '/home/wangdi5/eng_essay_mq/eng_essay_mq/english_write.py',
        '/home/wangdi5/eng_essay_mq/eng_essay_mq/mq_client_grammar.py',
        '/home/wangdi5/eng_essay_mq/eng_essay_mq/utils/dify_client.py'
    ]

    print("=" * 80)
    print("检查Python文件语法")
    print("=" * 80)

    all_ok = True
    for filepath in files_to_check:
        if not check_file_syntax(filepath):
            all_ok = False

    print("=" * 80)
    if all_ok:
        print("✓ 所有文件语法正确！")
    else:
        print("✗ 部分文件存在语法错误")
    print("=" * 80)

    sys.exit(0 if all_ok else 1)
