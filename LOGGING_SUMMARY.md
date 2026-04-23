# Dify字段映射日志功能

## 概述

已成功添加MQ数据到Dify字段映射的日志输出功能，便于调试和监控数据传输过程。

## 修改的文件

### 1. `/eng_essay_mq/eng_essay_mq/utils/dify_client.py`

在 `correct_chinese_essay()` 方法中添加了字段映射日志：

```python
# 打印传入Dify的字段映射日志
logger.info("=" * 80)
logger.info("字段映射完成，准备传入Dify工作流的inputs字段:")
logger.info(json.dumps(inputs, ensure_ascii=False, indent=2))
logger.info("=" * 80)
```

**日志输出内容：**
- 完整的inputs字段（所有映射的参数字段）
- 格式化的JSON，便于阅读

### 2. `/eng_essay_mq/eng_essay_mq/english_write.py`

#### 2.1 修改 `_correct_essay_by_dify()` 方法签名

添加了额外参数：
```python
def _correct_essay_by_dify(self, grade, totalScore, content, task='cn', problem=None,
                            subject_id=None, block_id=None, task_key=None, student_key=None):
```

#### 2.2 在方法开始处添加字段映射日志

```python
# 打印即将传入Dify的字段映射信息
log_server.logging("=" * 80)
log_server.logging("MQ数据 → Dify 字段映射详情:")
log_server.logging(f"  grade: {grade}")
log_server.logging(f"  totalScore: {totalScore}")
log_server.logging(f"  content长度: {len(content)} 字符")
log_server.logging(f"  problem长度: {len(problem) if problem else 0} 字符")
log_server.logging("  其他参数: subject_id, block_id, task_key, student_key")
log_server.logging("=" * 80)
```

#### 2.3 修改调用dify客户端的地方

传递完整的参数：
```python
dify_result = correct_chinese_essay_with_dify(
    content=content,
    problem=problem,
    grade=grade,
    totalScore=totalScore,
    subject_id=subject_id,
    block_id=block_id,
    task_key=task_key,
    student_key=student_key
)
```

#### 2.4 修改 `parser_one_essay()` 方法

在调用 `_correct_essay_by_dify()` 时传递完整参数：
```python
correction_result = self._correct_essay_by_dify(
    grade, totalScore, post_text, task=task, problem=problem,
    subject_id=subjectId, block_id=blockId, task_key=taskKey, student_key=uploadKey
)
```

## 日志层级

日志输出分为三个层级：

### 1. english_write.py - MQ数据解析层
```
================================================================================
MQ数据 → Dify 字段映射详情:
  grade: 高三
  totalScore: 60
  content长度: 793 字符
  problem长度: 172 字符
  其他参数: subject_id, block_id, task_key, student_key
================================================================================
```

### 2. dify_client.py - 字段映射层
```
================================================================================
字段映射完成，准备传入Dify工作流的inputs字段:
{
  "student_answer": "...",
  "question_content": "...",
  "subject_chs": "语文",
  "question_type": "作文",
  "grade": "高三",
  "total_score": "60",
  "task_key": "9768863-23576240-1764578529021",
  "subject_id": "9768863",
  "block_id": "23576240",
  "student_key": "82881-112825-10-241"
}
================================================================================
```

### 3. dify_client.py - API调用层
```
Calling Dify workflow API: https://dify-wan.iyunxiao.com/v1/workflows/run
```

## 测试验证

### 测试脚本

1. **test_dify_logging.py** - 测试dify_client.py中的日志
2. **test_mq_to_dify.py** - 测试完整的字段映射流程

### 测试结果

✅ 所有字段成功映射并记录到日志
✅ 日志格式清晰，便于阅读
✅ 包含完整的字段信息，包括：
   - student_answer（学生作文）
   - question_content（题目要求）
   - subject_chs（固定值：语文）
   - question_type（固定值：作文）
   - grade（年级）
   - total_score（总分）
   - task_key（任务标识）
   - subject_id（学科ID）
   - block_id（题目块ID）
   - student_key（学生标识）

## 实际运行示例

运行 `python3 test_dify_logging.py` 的输出：

```
2025-12-01 22:17:55,055 - dify_client - INFO - ================================================================================
2025-12-01 22:17:55,055 - dify_client - INFO - 字段映射完成，准备传入Dify工作流的inputs字段:
2025-12-01 22:17:55,055 - dify_client - INFO - {
2025-12-01 22:17:55,055 - dify_client - INFO -   "student_answer": "语文作文题\n\n破除人生壁垒...",
2025-12-01 22:17:55,055 - dify_client - INFO -   "question_content": "作文：阅读下面的材料...",
2025-12-01 22:17:55,055 - dify_client - INFO -   ...
2025-12-01 22:17:55,055 - dify_client - INFO - }
2025-12-01 22:17:55,055 - dify_client - INFO - ================================================================================
```

## 总结

✅ 日志功能已成功添加
✅ 字段映射过程完全透明
✅ 便于调试和问题排查
✅ 不影响正常业务逻辑
