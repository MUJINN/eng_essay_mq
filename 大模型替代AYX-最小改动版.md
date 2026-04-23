# 大模型替代AYX - 最小改动版输出规范

## 📋 核心原则

**严格保持AYX模型的输出结构，不多不少，完全兼容现有系统**

---

## 一、输出结构（完全兼容AYX）

### 🔷 最终输出格式（系统返回给前端）

```json
{
  "subjectId": 123456,
  "blockId": 12345,
  "taskKey": "test-001",
  "model": "llm",
  "task": "en-app",

  "students": [
    {
      "uploadKey": "student-001",
      "score": 0.723,                    // 得分率（0-1之间的小数）
      "highlight": [                     // 亮点表达
        ["express sincere gratitude", [10, 35]],
        ["remarkable progress", [85, 103]]
      ],
      "error_set": [                     // 语法错误
        {
          "offset": 31,
          "length": 1,
          "message": "Use 'an' instead of 'a'",
          "rule": {
            "id": "ARTICLE_A_VS_AN",
            "category": "ERROR_GRAMMAR"
          }
        }
      ]
    }
  ]
}
```

---

## 二、大模型API输出格式

### 🔷 大模型应返回的格式

```json
{
  "data": {
    "percentageScore": 72.3,            // 百分比分数（0-100）
    "highlight": [                      // 亮点表达
      ["express sincere gratitude", [10, 35]],
      ["remarkable progress", [85, 103]]
    ],
    "error_set": [                      // 语法错误列表
      {
        "offset": 31,
        "length": 1,
        "message": "Use 'an' instead of 'a'",
        "rule": {
          "id": "ARTICLE_A_VS_AN",
          "category": "ERROR_GRAMMAR"
        }
      },
      {
        "offset": 85,
        "length": 9,
        "message": "Spelling error: 'recieving' should be 'receiving'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      }
    ]
  }
}
```

---

## 三、字段详细说明

### 🔷 输出字段（仅3个）

#### 3.1 score（真实得分）

```json
"score": 11.3
```

| 属性 | 说明 |
|------|------|
| **类型** | `float` |
| **范围** | 0-满分（如15分作文，范围0-15） |
| **说明** | **真实得分，不需要调整** |

**重要**：
- ✅ 大模型直接输出真实得分（如 11.3/15分）
- ✅ 后端**不需要**再做除以100的转换
- ✅ 前端**不需要**再做乘以totalScore的计算

#### 3.2 highlight（亮点表达）

```json
"highlight": [
  ["express sincere gratitude", [10, 35]],
  ["remarkable progress", [85, 103]]
]
```

| 属性 | 说明 |
|------|------|
| **类型** | `array` |
| **元素格式** | `[string, [int, int]]` |
| **说明** | 亮点文本 + 起始位置 + 结束位置 |

**格式说明**：
- `highlight[0]`: 亮点文本内容
- `highlight[1][0]`: 起始位置（字符索引，从0开始）
- `highlight[1][1]`: 结束位置（字符索引）

**示例**：
```
原文: I want to express my sincere gratitude for your help.
     ^^^^^^^^^^^^^^^^^^^^^^^^
     位置10-35

highlight: ["express my sincere gratitude", [10, 35]]
```

#### 3.3 error_set（语法错误集合）

```json
"error_set": [
  {
    "offset": 31,
    "length": 1,
    "message": "Use 'an' instead of 'a'",
    "rule": {
      "id": "ARTICLE_A_VS_AN",
      "category": "ERROR_GRAMMAR"
    }
  }
]
```

##### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| **offset** | `int` | ✅ | 错误起始位置（字符索引，从0开始） |
| **length** | `int` | ✅ | 错误字符数 |
| **message** | `string` | ✅ | 错误描述/修改建议 |
| **rule.id** | `string` | ✅ | 错误规则唯一标识 |
| **rule.category** | `string` | ✅ | 错误分类 |

##### rule.category 可选值

```json
{
  "ERROR_SPELLING": "拼写错误",
  "ERROR_GRAMMAR": "语法错误",
  "ERROR_VERB": "动词错误",
  "ERROR_NOUN": "名词错误",
  "ERROR_ARTICLE": "冠词错误",
  "ERROR_PREPOSITION": "介词错误",
  "ERROR_CONJUNCTION": "连词错误",
  "ERROR_TENSE": "时态错误",
  "ERROR_CAPITALIZATION": "大小写错误",
  "ERROR_PUNCTUATION": "标点错误",
  "COLLOCATIONS": "搭配错误"
}
```

##### message 格式建议

```
简洁明了的错误提示，20-100字

✅ "Use 'an' instead of 'a'"
✅ "Spelling error: 'recieving' should be 'receiving'"
✅ "Missing subject after 'Because'"
✅ "Should use present tense instead of past tense"

❌ "Error"（太简短）
❌ "There is an error in your sentence"（不够具体）
```

---

## 四、与AYX模型字段对比

### 🔷 完整对比表

| 字段 | AYX模型 | 大模型（目标） | 说明 |
|------|---------|--------------|------|
| **score** | ✅ 0-1小数 | ✅ 真实得分（如11.3/15分） | 不需要转换 |
| **highlight** | ✅ `[text, [start, end]]` | ✅ 相同格式 | 完全兼容 |
| **error_set** | ✅ 详见说明 | ✅ 相同结构 | 完全兼容 |

**结论**：大模型**直接输出真实得分**，不需要percentageScore转换

---

## 五、数据转换流程

### 🔷 完整流程图

```
┌─────────────────────────────────────────┐
│  大模型API                              │
│  输出：percentageScore + highlight +    │
│        error_set                        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  数据转换层（后端）                      │
│  1. percentageScore → score（除以100）  │
│  2. highlight 直接使用                  │
│  3. error_set 直接使用                  │
│  4. 其他字段填充为默认值                │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  最终输出（与AYX完全一致）              │
└─────────────────────────────────────────┘
```

### 🔷 转换代码示例

```python
def convert_llm_to_ayx_format(llm_result, uploadKey, totalScore):
    """
    将大模型输出转换为AYX格式

    Args:
        llm_result: 大模型返回的JSON数据
        uploadKey: 学生ID
        totalScore: 总分（不使用，仅用于兼容）

    Returns:
        与AYX格式完全一致的学生信息字典
    """
    data = llm_result.get('data', {})

    # 提取大模型输出
    score = data.get('score', 0)           # 真实得分，如11.3
    highlight = data.get('highlight', [])
    error_set = data.get('error_set', [])

    # 大模型已输出真实得分，无需转换
    # 但为了兼容AYX格式，仍转换为0-1的比例
    score_ratio = score / totalScore if totalScore > 0 else 0

    # 转换为AYX格式
    student_info = {
        'uploadKey': uploadKey,
        'score': score_ratio,              # 0-1之间（前端可能会再转换）
        'highlight': highlight,
        'error_set': error_set
    }

    return student_info
```

**注意**：虽然大模型输出真实得分，但为了兼容现有系统，仍转换为0-1的比例。前端显示时可能会再乘以totalScore。

---

## 六、完整示例

### 🔷 输入：学生作文

```json
{
  "grade": "高二",
  "totalScore": 15,
  "post_text": "I'm Li Hua. I notice that some students eat snacks at mealtimes instead of having meals. Now I'd like to call on you to form a healthy eating habit. For us students, eating healthy food is of great importane because we need enough nutrients to keep our body functoning well. Having meals regulary is a good way to keep fit and prevent deceases. By eating snack, we may get sick easily. Let's change our way of living."
}
```

### 🔷 大模型输出

```json
{
  "data": {
    "percentageScore": 68.5,
    "highlight": [
      ["call on you to form", [55, 75]],
      ["of great importance", [105, 123]],
      ["keep fit and prevent", [175, 193]]
    ],
    "error_set": [
      {
        "offset": 8,
        "length": 6,
        "message": "Spelling error: 'notioce' should be 'notice'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      },
      {
        "offset": 115,
        "length": 8,
        "message": "Spelling error: 'importane' should be 'importance'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      },
      {
        "offset": 160,
        "length": 8,
        "message": "Spelling error: 'functoning' should be 'functioning'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      },
      {
        "offset": 195,
        "length": 7,
        "message": "Spelling error: 'regulary' should be 'regularly'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      },
      {
        "offset": 230,
        "length": 8,
        "message": "Spelling error: 'deceases' should be 'diseases'",
        "rule": {
          "id": "SPELLING_ERROR",
          "category": "ERROR_SPELLING"
        }
      }
    ]
  }
}
```

### 🔷 转换后最终输出（与AYX一致）

```json
{
  "subjectId": 123456,
  "blockId": 12345,
  "taskKey": "test-001",
  "model": "llm",
  "task": "en-app",

  "students": [
    {
      "uploadKey": "student-001",
      "score": 0.685,                    // 68.5 / 100
      "highlight": [
        ["call on you to form", [55, 75]],
        ["of great importance", [105, 123]],
        ["keep fit and prevent", [175, 193]]
      ],
      "error_set": [
        {
          "offset": 8,
          "length": 6,
          "message": "Spelling error: 'notioce' should be 'notice'",
          "rule": {
            "id": "SPELLING_ERROR",
            "category": "ERROR_SPELLING"
          }
        }
        // ... 其他错误
      ],

      // 保持与AYX一致的默认值
      "comment": "",
      "suggestion": [],
      "improveArticle": "",
      "topicScore": 0,
      "contentScore": 0,
      "structureScore": 0,
      "languageScore": 0,
      "errorCorrection": [],
      "expression": []
    }
  ]
}
```

---

## 七、Prompt模板（大模型）

### 🔷 System Prompt

```markdown
你是一位专业的英语作文批改专家。你的任务是批改学生的英语作文并返回标准的JSON格式数据。

**输出要求**：
1. 给出0-100的分数（percentageScore）
2. 提取3-5个亮点表达（highlight），包含文本和准确位置
3. 检出所有语法错误（error_set），包含位置和修改建议

**输出格式**：严格遵循JSON Schema，不要输出任何额外内容。
```

### 🔷 User Prompt

```markdown
请批改以下英语作文：

【学生作文】
{post_text}

【年级】
{grade}

【满分】
{totalScore}分

请按照以下JSON格式输出：
```json
{
  "data": {
    "percentageScore": 分数（0-100）,
    "highlight": [
      ["亮点文本", [起始位置, 结束位置]],
      ...
    ],
    "error_set": [
      {
        "offset": 错误起始位置,
        "length": 错误长度,
        "message": "错误描述",
        "rule": {
          "id": "错误规则ID",
          "category": "错误分类"
        }
      },
      ...
    ]
  }
}
```
```

---

## 八、技术实现要点

### 🔷 offset 和 length 计算示例

**原文**：
```
I'm recieving your letter. I hav a good news.
```

**错误1：recieving**
```
offset: 5
length: 9
解释：
  - 从第5个字符开始（'r'）
  - 错误单词有9个字符
  - post_text[5:14] = "recieving"
```

**错误2：hav**
```
offset: 27
length: 3
解释：
  - 从第27个字符开始（'h'）
  - 错误单词有3个字符
  - post_text[27:30] = "hav"
```

### 🔷 highlight 位置计算示例

**原文**：
```
I want to express my sincere gratitude for your help.
```

**亮点：express my sincere gratitude**
```
起始位置：从'I want to '之后开始
  "I want to " = 10个字符
  offset = 10

结束位置：到'for'之前
  "I want to express my sincere gratitude" = 35个字符
  end = 35

highlight: ["express my sincere gratitude", [10, 35]]
```

### 🔷 错误分类选择指南

| 错误类型 | category | id示例 |
|---------|---------|--------|
| 拼写错误 | ERROR_SPELLING | SPELLING_ERROR |
| 冠词错误（a/an） | ERROR_GRAMMAR | ARTICLE_A_VS_AN |
| 时态错误 | ERROR_TENSE | TENSE_CONSISTENCY |
| 主谓一致 | ERROR_GRAMMAR | SUBJECT_VERB_AGREEMENT |
| 介词错误 | ERROR_PREPOSITION | PREPOSITION_ERROR |
| 大小写 | ERROR_CAPITALIZATION | CAPITALIZATION |
| 标点符号 | ERROR_PUNCTUATION | PUNCTUATION_ERROR |

---

## 九、质量要求

### 🔷 评分准确性

| 指标 | 要求 |
|------|------|
| **总分准确率** | 与人工评分相关系数 ≥ 0.80 |
| **百分比分数** | 0-100，保留1位小数 |

### 🔷 语法错误检测

| 指标 | 要求 |
|------|------|
| **召回率** | ≥ 0.80（检出80%以上的错误） |
| **精确率** | ≥ 0.85（检出的错误85%以上是正确的） |
| **位置准确性** | offset误差 ≤ 2字符 |

### 🔷 亮点表达提取

| 指标 | 要求 |
|------|------|
| **数量** | 3-5个 |
| **位置准确性** | offset误差 ≤ 2字符 |
| **质量** | 确实是优秀表达（词汇、句式、搭配等） |

---

## 十、兼容性检查清单

### ✅ 部署前检查

- [ ] 大模型输出包含 `percentageScore` 字段（0-100）
- [ ] 大模型输出包含 `highlight` 字段（数组格式）
- [ ] 大模型输出包含 `error_set` 字段（数组格式）
- [ ] `highlight` 格式为 `[text, [start, end]]`
- [ ] `error_set` 包含 offset, length, message, rule
- [ ] 后端转换后 `score` 为 0-1 之间的小数
- [ ] 其他字段填充为默认值（0或空）
- [ ] 前端能正常渲染（无需修改代码）

### ✅ 测试用例

```python
# 测试用例1：正常输出
{
  "percentageScore": 75.5,
  "highlight": [["good", [0, 4]]],
  "error_set": []
}
# 预期：score = 0.755

# 测试用例2：无亮点
{
  "percentageScore": 60.0,
  "highlight": [],
  "error_set": [...]
}
# 预期：score = 0.600, highlight = []

# 测试用例3：无错误
{
  "percentageScore": 85.0,
  "highlight": [...],
  "error_set": []
}
# 预期：score = 0.850, error_set = []
```

---

## 十一、API接口规范

### 🔷 请求格式

```http
POST /api/llm_correct HTTP/1.1
Content-Type: application/json

{
  "task": "en-app",
  "model": "llm",
  "content": "I'm Li Hua...",
  "grade": "高二",
  "totalScore": 15
}
```

### 🔷 响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "percentageScore": 75.5,
    "highlight": [["text", [0, 4]]],
    "error_set": [...]
  }
}
```

### 🔷 错误响应

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "批改服务异常",
  "message": "详细错误信息"
}
```

---

## 附录：快速参考

### 📊 核心字段速查

| 字段 | 类型 | 示例 | 说明 |
|------|------|------|------|
| **percentageScore** | float | 75.5 | 百分比分数（0-100） |
| **highlight** | array | `[["text", [0, 4]]]` | 亮点表达 |
| **error_set[].offset** | int | 10 | 错误起始位置 |
| **error_set[].length** | int | 3 | 错误长度 |
| **error_set[].message** | string | "Use 'an'" | 错误描述 |
| **error_set[].rule.id** | string | "ARTICLE_A_VS_AN" | 规则ID |
| **error_set[].rule.category** | string | "ERROR_GRAMMAR" | 错误分类 |

### 🔄 数据转换

```python
# 大模型输出 → 系统输出
score = percentageScore / 100.0

# 示例
percentageScore = 75.5
score = 75.5 / 100 = 0.755
```

---

**文档版本**: v2.0（最小改动版）
**生成时间**: 2026-02-06
**适用范围**: 大模型替代AYX英语作文批改
**兼容性**: 完全兼容现有AYX系统
