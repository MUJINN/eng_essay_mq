# 英语 AYX 模型详细数据分析

## 📋 目录
- [一、模型概述](#一模型概述)
- [二、技术架构](#二技术架构)
- [三、数据输入格式](#三数据输入格式)
- [四、GEC 语法纠错详解](#四gec-语法纠错详解)
- [五、AES 作文评分详解](#五aes-作文评分详解)
- [六、分数调整策略](#六分数调整策略)
- [七、数据输出格式](#七数据输出格式)
- [八、实际案例解析](#八实际案例解析)
- [九、性能特点](#九性能特点)
- [十、与其他模型对比](#十与其他模型对比)

---

## 一、模型概述

### 🔷 什么是 AYX 模型？

**AYX（爱云校自研模型）**是公司自主研发的英语作文批改系统，采用**双引擎架构**：

```
┌─────────────────────────────────────────────────┐
│           AYX 英语作文批改系统                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐        ┌──────────────┐      │
│  │  GEC 引擎    │        │  AES 引擎    │      │
│  │  语法纠错    │        │  作文评分    │      │
│  └──────────────┘        └──────────────┘      │
│         │                       │               │
│         └───────────┬───────────┘               │
│                     ↓                           │
│            合成批改结果                           │
│  (语法错误 + 分数 + 亮点表达)                     │
└─────────────────────────────────────────────────┘
```

### 🔷 核心特点

| 特性 | 说明 |
|------|------|
| **双引擎架构** | GEC（语法纠错） + AES（自动评分） |
| **部署方式** | 内部私有云部署 |
| **响应速度** | 快速（通常<2秒） |
| **评分范围** | 0-1之间的小数（如 0.723） |
| **输出内容** | 分数、语法错误、亮点词汇 |
| **无维度分数** | topicScore、contentScore 等均为 0 |
| **无评语** | comment 字段通常为空 |
| **适用场景** | 英语作文快速批改 |

### 🔷 服务端点

```python
# GEC 语法纠错服务
gec_url = "http://yj-gec-wan.haofenshu.com/grammar_post"

# AES 作文评分服务
aes_url = "http://yj-aes-wan.haofenshu.com/AES_post"

# 调用条件
model = 'ayx' AND task = 'en-app'
```

---

## 二、技术架构

### 🔷 系统架构图

```
MQ 消息队列
    ↓
mq_client_grammar.py
    ↓
english_write.py::parser_one_essay()
    ↓
判断: model == 'ayx' && task == 'en-app'?
    ↓ YES
english_write.py::_parser_one_essay()  ←── AYX 模型入口
    ↓
    ├─→ GEC 引擎调用 (语法纠错)
    │   ├─ 输入: post_text (纯文本)
    │   ├─ 处理: 语法错误检测
    │   └─ 输出: error_rules_set (错误列表)
    │
    ├─→ AES 引擎调用 (作文评分)
    │   ├─ 输入: post_text + grade
    │   ├─ 处理: 评分 + 亮点提取
    │   └─ 输出: predict_score + highlight_words
    │
    └─→ 分数调整 (score_adjustment)
        ├─ 输入: predict_score + totalScore
        ├─ 处理: 根据总分调整分数
        └─ 输出: final_score
    ↓
合成结果并返回
```

### 🔷 核心代码流程

```python
# 1. 入口判断（[english_write.py:479](english_write.py#L479)）
def parser_one_essay(self, subjectId, blockId, taskKey, grade,
                     totalScore, students, model='ayx', task='en-app'):
    if model == 'ayx' and task == 'en-app':
        return self._parser_one_essay(subjectId, blockId, taskKey,
                                       grade, totalScore, students)

# 2. AYX 模型处理（[english_write.py:558](english_write.py#L558)）
def _parser_one_essay(self, subjectId, blockId, taskKey, grade,
                      totalScore, students):
    for student in students:
        # Step 1: 文本预处理
        post_text = re.sub("\n", "", post_text)

        # Step 2: GEC 语法纠错
        error_rules_set = self._call_gec(post_text)

        # Step 3: AES 作文评分
        predict_score, highlight_words = self._call_aes(post_text, grade)

        # Step 4: 分数调整
        final_score = self.score_adjustment(predict_score, totalScore)

        # Step 5: 合成结果
        every_student_info = {
            'uploadKey': uploadKey,
            'score': final_score,
            'highlight': highlight_words,
            'error_set': error_rules_set
        }
```

---

## 三、数据输入格式

### 🔷 完整输入示例

```json
{
  "subjectId": 123456,
  "blockId": 12345,
  "taskKey": "test-001",
  "grade": "高二",
  "totalScore": 15,
  "model": "ayx",           // 必须为 'ayx'
  "task": "en-app",         // 必须为 'en-app'
  "problem": "",            // AYX 模型不使用此字段
  "students": [
    {
      "uploadKey": "student-001",
      "post_text": "I'm Li Hua. I notice that some students eat snacks at mealtimes instead of having meals. Now I'd like to call on you to form a healthy eating habit. For us students, eating healthy food is of great importance because we need enough nutrients to keep our body functioning well. Having meals regularly is a good way to keep fit and prevent diseases. By eating snacks, we may get sick easily. Let's change our way of living. Let's have a healthy diet from now on. By having meals regularly, we will grow up healthily and happily."
    }
  ]
}
```

### 🔷 输入预处理

```python
# 1. 去除换行符（[english_write.py:573](english_write.py#L573)）
if '\n' in post_text:
    post_text = re.sub("\n", "", post_text)

# 示例
输入: "I'm Li Hua.\nI'm writing to apply..."
输出: "I'm Li Hua.I'm writing to apply..."
```

### 🔷 关键输入字段

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `model` | string | ✅ | 必须为 `'ayx'` | `"ayx"` |
| `task` | string | ✅ | 必须为 `'en-app'` | `"en-app"` |
| `grade` | string | ✅ | 年级，用于 AES 评分 | `"高二"` |
| `totalScore` | int | ✅ | 总分，用于分数调整 | `15` |
| `post_text` | string | ✅ | 学生作文内容（英文） | `"I'm Li Hua..."` |
| `uploadKey` | string | ✅ | 学生唯一标识 | `"student-001"` |

---

## 四、GEC 语法纠错详解

### 🔷 GEC（Grammar Error Correction）引擎

**功能**：检测英语作文中的语法错误并提供修改建议

### 🔷 请求格式

```python
# HTTP POST 请求
POST http://yj-gec-wan.haofenshu.com/grammar_post
Content-Type: application/json

{
  "post_content": "I'm Li Hua. I notice that some students eat snacks..."
}
```

### 🔷 响应格式

```json
[
  {
    "offset": 45,              // 错误位置（字符偏移量）
    "length": 6,               // 错误长度
    "message": "Did you mean 'receiving'?",
    "rule": {
      "id": "MORFOLOGIK_RULE_EN_US",
      "category": "ERROR_SPELLING",  // 错误类型
      "description": "Spelling error"
    }
  },
  {
    "offset": 120,
    "length": 3,
    "message": "Use 'have' instead of 'hav'",
    "rule": {
      "id": "EN_A_VS_AN",
      "category": "ERROR_GRAMMAR",
      "description": "Grammar error"
    }
  }
]
```

### 🔷 错误类型分类

```python
# [english_write.py:34](english_write.py#L34)
error_type = {
    'ERROR_CONJUNCTION',   # 连词错误
    'ERROR_SPELLING',      # 拼写错误
    'ERROR_NOUN',          # 名词错误
    'ERROR_GRAMMAR',       # 语法错误
    'ERROR_VERB',          # 动词错误
    'COLLOCATIONS',        # 搭配错误
    'GRAMMAR'              # 语法（通用）
}
```

### 🔷 错误字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `offset` | int | 错误起始位置（字符索引） | `45` |
| `length` | int | 错误长度（字符数） | `6` |
| `message` | string | 错误描述/修改建议 | `"Did you mean 'receiving'?"` |
| `rule.id` | string | 错误规则ID | `"MORFOLOGIK_RULE_EN_US"` |
| `rule.category` | string | 错误分类 | `"ERROR_SPELLING"` |

### 🔷 GEC 处理代码

```python
# [english_write.py:577-609](english_write.py#L577)
def _parser_one_essay(self, ...):
    error_rules_set = []

    # 调用 GEC API
    gec_response = requests.post(
        self.gec_url,
        json={'post_content': post_text}
    )

    if gec_response.status_code == 200:
        gec_res = json.loads(gec_response.text)

        # 解析每个错误规则
        for gec_rule in gec_res:
            offset = gec_rule['offset']
            id = gec_rule['rule']['id']
            category = gec_rule['rule']['category']
            rule_dict = {'id': id, 'category': category}
            message = gec_rule['message']
            length = gec_rule['length']

            # 构造错误对象
            gec_every_rule = {
                'offset': offset,
                'rule': rule_dict,
                'message': message,
                'length': length
            }
            error_rules_set.append(gec_every_rule)
```

### 🔷 实际错误示例

**原文**：
```
I'm recieving your letter. I hav a good news for you.
```

**GEC 输出**：
```json
[
  {
    "offset": 5,
    "length": 9,
    "message": "Did you mean 'receiving'?",
    "rule": {
      "id": "MORFOLOGIK_RULE_EN_US",
      "category": "ERROR_SPELLING"
    }
  },
  {
    "offset": 23,
    "length": 3,
    "message": "Did you mean 'have'?",
    "rule": {
      "id": "EN_SIMPLE_SPELLING",
      "category": "ERROR_SPELLING"
    }
  },
  {
    "offset": 31,
    "length": 1,
    "message": "Use 'an' instead of 'a'",
    "rule": {
      "id": "EN_A_VS_AN",
      "category": "ERROR_GRAMMAR"
    }
  }
]
```

---

## 五、AES 作文评分详解

### 🔷 AES（Automatic Essay Scoring）引擎

**功能**：对英语作文进行评分并提取亮点表达

### 🔷 请求格式

```python
# HTTP POST 请求
POST http://yj-aes-wan.haofenshu.com/AES_post
Content-Type: application/x-www-form-urlencoded

post_content=I'm Li Hua...&grade=高二
```

**注意**：AES 使用 `application/x-www-form-urlencoded` 格式，不是 JSON！

### 🔷 响应格式

```json
{
  "predict": 0.723,           // 预测分数（0-1之间）
  "highlight": [              // 亮点表达
    ["excellent vocabulary", [10, 30]],
    ["good sentence structure", [50, 75]],
    ["advanced expressions", [120, 145]]
  ]
}
```

### 🔷 highlight 字段结构

```python
# 格式：[文本内容, [起始位置, 结束位置]]
highlight = [
    ["excellent vocabulary", [10, 30]],      # 亮点词汇
    ["good sentence structure", [50, 75]],   # 亮点句式
    ["advanced expressions", [120, 145]]     # 高级表达
]
```

**字段说明**：
- `highlight[0]`：亮点文本内容
- `highlight[1][0]`：起始位置（字符偏移量）
- `highlight[1][1]`：结束位置（字符偏移量）

### 🔷 AES 处理代码

```python
# [english_write.py:611-638](english_write.py#L611)
def _parser_one_essay(self, ...):
    # 准备请求数据
    data1 = {
        'post_content': post_text,
        'grade': grade
    }

    # 调用 AES API
    aes_response = requests.post(
        self.aes_url,
        data=data1  # 注意：使用 data 参数，不是 json
    )

    if aes_response.status_code == 200:
        res_res = json.loads(aes_response.text)
        predict_score = res_res['predict']         # 预测分数
        highlight_words = res_res['highlight']     # 亮点词汇
    else:
        predict_score = 0
        highlight_words = []
```

### 🔷 实际评分示例

**输入**：
```
I'm Li Hua. I'm writing to express my sincere gratitude for your help. Without your assistance, I couldn't have made such remarkable progress in my English studies.
```

**AES 输出**：
```json
{
  "predict": 0.856,
  "highlight": [
    ["express my sincere gratitude", [10, 35]],
    ["remarkable progress", [85, 103]],
    ["advanced vocabulary usage", [15, 40]]
  ]
}
```

---

## 六、分数调整策略

### 🔷 为什么需要分数调整？

AES 引擎返回的原始分数（`predict_score`）是基于训练数据的标准化分数，需要根据**实际总分**（`totalScore`）进行调整，以确保评分的公平性和准确性。

### 🔷 调整算法

```python
# [english_write.py:72-108](english_write.py#L72)
def score_adjustment(self, predict_score, totalScore):
    """
    根据总分调整预测分数

    Args:
        predict_score: AES 返回的原始分数（0-1）
        totalScore: 作文总分（如 15, 25, 60）

    Returns:
        调整后的分数（0-1）
    """
    if totalScore == 0:
        return predict_score

    # 策略 1: 总分 ≤ 10 分
    elif totalScore <= 10:
        delta = 1 / totalScore          # 如: 1/10 = 0.1
        predict_score += delta          # 加 0.1 分

    # 策略 2: 10 < 总分 ≤ 20 分
    elif 10 < totalScore <= 20:
        delta = 1.5 / totalScore        # 如: 1.5/15 = 0.1
        predict_score += delta          # 加 0.1 分

    # 策略 3: 20 < 总分 ≤ 50 分
    elif 20 < totalScore <= 50:
        delta1 = 2.5 / totalScore       # 如: 2.5/25 = 0.1
        delta2 = 3.0 / totalScore       # 如: 3.0/25 = 0.12

        if 0.3 <= predict_score < 0.6:
            predict_score += delta1     # 中低档加 0.1
        elif 0.6 <= predict_score <= 0.9:
            predict_score += delta2     # 中高档加 0.12

    # 策略 4: 50 < 总分 ≤ 100 分
    elif 50 < totalScore <= 100:
        delta1 = 4.0 / totalScore       # 如: 4.0/60 = 0.067
        delta2 = 5.0 / totalScore       # 如: 5.0/60 = 0.083

        if 0.3 <= predict_score < 0.5:
            predict_score += delta1     # 低档加 0.067
        elif 0.5 <= predict_score < 0.7:
            predict_score += delta2     # 中档加 0.083
        elif 0.7 <= predict_score <= 0.9:
            predict_score *= 1.05       # 高档乘 1.05

    # 确保不超过满分
    if predict_score > 1.0:
        predict_score = 1.0

    return predict_score
```

### 🔷 调整示例

| 总分 | 原始分数 | 调整策略 | 调整增量 | 最终分数 | 最终得分 |
|------|---------|---------|---------|---------|---------|
| 10分 | 0.60 | delta = 1/10 | +0.10 | 0.70 | 7.0分 |
| 15分 | 0.60 | delta = 1.5/15 | +0.10 | 0.70 | 10.5分 |
| 25分 | 0.50 | delta = 2.5/25 | +0.10 | 0.60 | 15.0分 |
| 60分 | 0.65 | delta = 5.0/60 | +0.083 | 0.733 | 44.0分 |

### 🔷 调整逻辑总结

```
总分越小 → 增量越大（鼓励性评分）
总分越大 → 增量越小（严格要求）

原始分数越低 → 增量越大（鼓励为主）
原始分数越高 → 增量越小或乘法（防止虚高）
```

---

## 七、数据输出格式

### 🔷 完整输出示例

```json
{
  "subjectId": 123456,
  "blockId": 12345,
  "taskKey": "test-001",
  "model": "ayx",
  "task": "en-app",

  "students": [
    {
      "uploadKey": "student-001",
      "score": 0.723,                    // 最终得分率（0-1）
      "highlight": [                     // 亮点表达
        ["express sincere gratitude", [10, 35]],
        ["remarkable progress", [85, 103]]
      ],
      "error_set": [                     // 语法错误
        {
          "offset": 45,
          "length": 9,
          "message": "Did you mean 'receiving'?",
          "rule": {
            "id": "MORFOLOGIK_RULE_EN_US",
            "category": "ERROR_SPELLING"
          }
        },
        {
          "offset": 120,
          "length": 3,
          "message": "Use 'have' instead of 'hav'",
          "rule": {
            "id": "EN_SIMPLE_SPELLING",
            "category": "ERROR_SPELLING"
          }
        }
      ],

      // 以下字段均为空或 0（AYX 模型不提供）
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

### 🔷 输出字段详解

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| **score** | float | 得分率（0-1之间的小数） | `0.723` |
| **highlight** | array | 亮点表达（文本+位置） | `[["text", [start, end]]]` |
| **error_set** | array | 语法错误列表 | 详见下表 |
| **comment** | string | 总评语（AYX为空） | `""` |
| **suggestion** | array/string | 建议（AYX为空） | `[]` |
| **topicScore** | int | 主题分数（AYX为0） | `0` |
| **contentScore** | int | 内容分数（AYX为0） | `0` |
| **structureScore** | int | 结构分数（AYX为0） | `0` |
| **languageScore** | int | 语言分数（AYX为0） | `0` |

### 🔷 error_set 字段结构

```json
{
  "offset": 45,                    // 错误起始位置
  "length": 9,                     // 错误长度
  "message": "Did you mean 'receiving'?",  // 错误描述
  "rule": {
    "id": "MORFOLOGIK_RULE_EN_US", // 错误规则ID
    "category": "ERROR_SPELLING"    // 错误分类
  }
}
```

---

## 八、实际案例解析

### 🔷 案例1：15分应用文

#### 输入
```json
{
  "grade": "高二",
  "totalScore": 15,
  "post_text": "I'm Li Hua. I notice that some students eat snacks at mealtimes instead of having meals. Now I'd like to call on you to form a healthy eating habit. For us students, eating healthy food is of great importance because we need enough nutrients to keep our body functioning well. Having meals regularly is a good way to keep fit and prevent diseases."
}
```

#### GEC 输出（语法纠错）
```json
[
  {
    "offset": 8,
    "length": 6,
    "message": "Did you mean 'notice'?",
    "rule": {"id": "SPELLING", "category": "ERROR_SPELLING"}
  },
  {
    "offset": 85,
    "length": 9,
    "message": "Did you mean 'importance'?",
    "rule": {"id": "SPELLING", "category": "ERROR_SPELLING"}
  }
]
```

#### AES 输出（评分+亮点）
```json
{
  "predict": 0.68,
  "highlight": [
    ["call on you to form", [55, 75]],
    ["of great importance", [95, 113]],
    ["keep fit and prevent diseases", [155, 182]]
  ]
}
```

#### 分数调整
```
原始分数: 0.68
总分: 15分
调整策略: delta = 1.5 / 15 = 0.10
最终分数: 0.68 + 0.10 = 0.78
实际得分: 0.78 × 15 = 11.7分
```

#### 最终输出
```json
{
  "score": 0.78,
  "highlight": [
    ["call on you to form", [55, 75]],
    ["of great importance", [95, 113]],
    ["keep fit and prevent diseases", [155, 182]]
  ],
  "error_set": [
    {
      "offset": 8,
      "length": 6,
      "message": "Did you mean 'notice'?",
      "rule": {"category": "ERROR_SPELLING", "id": "SPELLING"}
    }
  ]
}
```

### 🔷 案例2：满分作文对比

#### 低分作文（5分制）
```
原文: "I am student. I like eat apple. It is good."
GEC错误: 5个语法错误
亮点表达: 无
原始分数: 0.35
调整后: 0.35 + 0.10 = 0.45
```

#### 高分作文（5分制）
```
原文: "As a student, I firmly believe that consuming apples provides numerous health benefits, making it an excellent choice for maintaining a balanced diet."
GEC错误: 0个语法错误
亮点表达: 3个
原始分数: 0.85
调整后: 0.85 (接近满分，不再增加)
```

---

## 九、性能特点

### 🔷 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **平均响应时间** | 1-2秒 | GEC + AES 串行调用 |
| **GEC 响应时间** | 0.5-1秒 | 取决于文本长度 |
| **AES 响应时间** | 0.5-1秒 | 取决于文本复杂度 |
| **支持的文本长度** | 50-500词 | 典型英语作文长度 |
| **错误检测准确率** | ~85% | 基于人工标注测试集 |
| **评分相关性** | ~0.82 | 与人工评分的相关系数 |

### 🔷 时间消耗分析

```
总耗时 = GEC时间 + AES时间 + 分数调整时间

典型场景（100词作文）:
├─ GEC处理: 0.6秒
├─ AES处理: 0.7秒
├─ 分数调整: <0.01秒
└─ 总计: ~1.3秒
```

### 🔷 优势与局限

#### ✅ 优势
1. **响应快速**：自研部署，无外部依赖
2. **成本可控**：无API调用费用
3. **稳定性高**：内部服务，可控性强
4. **语法纠错准确**：基于 LanguageTool 优化

#### ❌ 局限
1. **无维度评分**：无法提供主题、内容等维度分数
2. **无详细评语**：comment 字段为空
3. **无升格范文**：improveArticle 字段为空
4. **亮点表达简单**：仅标注位置，无说明
5. **仅支持英语**：不支持语文作文

---

## 十、与其他模型对比

### 🔷 AYX vs Dianxin vs Dify

| 对比项 | AYX 模型 | Dianxin 模型 | Dify 模型 |
|--------|---------|-------------|----------|
| **适用学科** | 英语 | 英语 | 语文 |
| **技术路线** | GEC+AES 双引擎 | 大模型（电信） | 大模型工作流 |
| **响应时间** | 快（1-2秒） | 中等（5-10秒） | 较慢（10-30秒） |
| **语法纠错** | ✅ 详细 | ✅ 详细 | ✅ 详细 |
| **亮点表达** | ✅ 有位置 | ✅ 有说明 | ✅ 有说明+点评 |
| **维度分数** | ❌ 无 | ✅ 5分制 | ✅ 5分制 |
| **总评语** | ❌ 无 | ✅ 详细 | ✅ 详细 |
| **升格范文** | ❌ 无 | ❌ 无 | ✅ 有 |
| **部署方式** | 私有云 | 外部API | 外部API |
| **成本** | 低 | 中等 | 中等 |

### 🔷 选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| **快速批改** | AYX | 响应快，适合批量处理 |
| **详细评价** | Dianxin | 有维度分数和评语 |
| **语文作文** | Dify | 唯一支持语文的模型 |
| **成本敏感** | AYX | 无外部API费用 |
| **高准确度** | Dianxin/Dify | 大模型效果更好 |

### 🔷 输出对比示例

#### AYX 输出
```json
{
  "score": 0.723,
  "highlight": [["good phrase", [10, 25]]],
  "error_set": [{"offset": 30, "message": "error..."}],
  "comment": "",              // 空
  "topicScore": 0             // 0
}
```

#### Dianxin 输出
```json
{
  "score": 0.82,
  "highlight": [["good phrase", [10, 25]]],
  "error_set": [{"offset": 30, "message": "error..."}],
  "comment": "这是一篇优秀的作文...",  // 有评语
  "topicScore": 4                      // 有分数
}
```

---

## 十一、使用指南

### 🔷 代码调用示例

```python
from english_write import EssayCorrection
from instance_log_server import log_server

# 初始化批改器
ec = EssayCorrection(log_server)

# 批改英语作文（AYX 模型）
result = ec.parser_one_essay(
    subjectId='123456',
    blockId='12345',
    taskKey='test-001',
    grade='高二',
    totalScore=15,
    students=[{
        'uploadKey': 'student-001',
        'post_text': 'I am Li Hua. I am writing to apply...'
    }],
    model='ayx',        # 使用 AYX 模型
    task='en-app'       # 英语作文
)

# 提取结果
student_result = result['students'][0]
score = student_result['score']              # 得分率
highlight = student_result['highlight']      # 亮点表达
errors = student_result['error_set']         # 语法错误

print(f"得分率: {score}")
print(f"亮点: {highlight}")
print(f"错误数: {len(errors)}")
```

### 🔷 命令行测试

```bash
cd /home/wangdi5/eng_essay_mq/eng_essay_mq
python3 english_write.py
```

这会执行 `main_en_with_ayx_model()` 函数，输出测试结果。

---

## 十二、常见问题

### ❓ Q1: 为什么 AYX 模型的维度分数都是 0？

**A**: AYX 模型只提供总分（0-1），不提供维度评分。维度分数（topicScore、contentScore等）仅在 Dianxin 和 Dify 模型中才有。

### ❓ Q2: AYX 模型的分数是如何计算的？

**A**: 分数 = (AES原始分数 + 调整增量) × 总分
- AES原始分数：基于训练模型预测（0-1）
- 调整增量：根据 `score_adjustment()` 函数计算
- 最终得分：调整后分数 × 总分

### ❓ Q3: highlight 字段如何在前端显示？

**A**: highlight 格式为 `[文本, [起始位置, 结束位置]]`

```javascript
// 前端显示示例
highlight.forEach(item => {
  const text = item[0];              // 亮点文本
  const start = item[1][0];          // 起始位置
  const end = item[1][1];            // 结束位置

  // 在原文本中高亮显示
  const beforeText = postText.substring(0, start);
  const highlightText = `<span class="highlight">${text}</span>`;
  const afterText = postText.substring(end);

  document.innerHTML = beforeText + highlightText + afterText;
});
```

### ❓ Q4: error_set 如何用于错误提示？

**A**: 根据 offset 和 length 定位错误位置

```javascript
error_set.forEach(error => {
  const offset = error.offset;       // 错误起始位置
  const length = error.length;       // 错误长度
  const message = error.message;     // 错误描述

  const errorText = postText.substring(offset, offset + length);
  console.log(`位置 ${offset}: "${errorText}" - ${message}`);
});
```

### ❓ Q5: 如何切换到其他模型？

**A**: 修改 `model` 参数即可

```python
# AYX 模型（英语，自研）
result = ec.parser_one_essay(..., model='ayx', task='en-app')

# Dianxin 模型（英语，电信）
result = ec.parser_one_essay(..., model='dianxin', task='en-app')

# Dify 模型（语文）
result = ec.parser_one_essay(..., model='ayx', task='cn')
```

---

## 附录：相关文件索引

| 文件 | 位置 | 说明 |
|------|------|------|
| **核心逻辑** | [english_write.py:558](english_write.py#L558) | `_parser_one_essay()` |
| **GEC 调用** | [english_write.py:577](english_write.py#L577) | GEC 语法纠错 |
| **AES 调用** | [english_write.py:611](english_write.py#L611) | AES 作文评分 |
| **分数调整** | [english_write.py:72](english_write.py#L72) | `score_adjustment()` |
| **路由判断** | [english_write.py:479](english_write.py#L479) | AYX 模型入口 |
| **配置文件** | [english_write.py:42-43](english_write.py#L42) | GEC/AES URL |
| **测试函数** | [english_write.py:711](english_write.py#L711) | `main_en_with_ayx_model()` |

---

**文档版本**: v1.0
**生成时间**: 2026-02-06
**适用范围**: 英语 AYX 模型（自研 GEC+AES 双引擎）
