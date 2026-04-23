# 大模型替换AYX - 输入参数精简版

## 🎯 目标
用大模型替换**自研AYX模型（GEC+AES）**，最小改动，完全兼容。

---

## 一、大模型API输入参数

### 🔷 核心参数（6个）

```json
{
  "task": "en-app",           // 任务类型：固定值
  "model": "llm",             // 模型标识：固定值
  "content": "I'm Li Hua...", // 学生作文内容
  "problem": "假定你是李华...", // 作文题目要求（可选）
  "grade": "高二",            // 年级
  "totalScore": 15            // 总分（必需）
}
```

### 🔷 参数说明

| 参数 | 类型 | 必需 | 示例 | 说明 |
|------|------|------|------|------|
| **task** | string | ✅ | `"en-app"` | 固定值，标识英语作文 |
| **model** | string | ✅ | `"llm"` | 固定值，标识大模型 |
| **content** | string | ✅ | `"I'm Li Hua..."` | 学生作文正文（纯文本，无换行符） |
| **grade** | string | ✅ | `"高二"` | 年级：初一~高三 |
| **totalScore** | int | ✅ | `15` | 总分（必需），大模型根据满分输出真实得分 |
| **problem** | string | ❌ | `"假定你是李华..."` | 作文题目（可选，建议提供） |

---

## 二、从系统到API的转换

### 🔷 数据流程

```
┌─────────────────────────────────────────┐
│  系统内部（english_write.py）            │
│                                         │
│  parser_one_essay() 调用：              │
│  - uploadKey = student['uploadKey']     │
│  - post_text = student['post_text']     │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  _correct_essay() 构建参数              │
│  [english_write.py:113]                 │
│                                         │
│  params = {                             │
│    'task': 'en-app',                    │
│    'model': 'llm',                      │
│    'content': post_text,  ← 学生作文    │
│    'problem': problem,    ← 作文题目    │
│    'grade': grade          ← 年级       │
│  }                                      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  POST到大模型API                         │
│  http://llm-api/correct_essay           │
└─────────────────────────────────────────┘
```

### 🔷 代码实现

**文件**：`english_write.py`
**函数**：`_correct_essay()`
**位置**：[110-139行](english_write.py#L110)

```python
def _correct_essay(self, grade, totalScore, content, model='ayx', task='en', problem=None):
    log_server.logging("enter _correct_essay")

    # 构建请求参数
    params = {
        'task': task,
        'model': model,
        'content': content,
        "problem": problem,
        "grade": grade
    }

    # 调用大模型API（带重试，最多3次）
    for i in range(3):
        response = post_request(self.correct_essay_api, json=params)
        if response is not None:
            break
        else:
            time.sleep(0.1)

    # 解析返回结果
    response_data = response.json()
    correct_result = response_data.get('data', None)

    return correct_result
```

---

## 三、实际示例

### 🔷 示例1：申请信（15分）

#### 输入：学生作文
```
题目：假定你是李华，写一封申请信

Dear Sir or Madam,

I am writing to apply for the position of library volunteer.
I am interested in reading and I have read many books.
I am a responsible student and I can help others find books.
I hope you can give me this chance.

Thank you for considering my application.

Yours faithfully,
Li Hua
```

#### 传给大模型
```json
{
  "task": "en-app",
  "model": "llm",
  "content": "Dear Sir or Madam,I am writing to apply...",
  "problem": "假定你是李华，写一封申请信",
  "grade": "高二",
  "totalScore": 15
}
```

**注意**：content中的换行符已被去除

---

### 🔷 示例2：议论文（25分）

#### 输入：学生作文
```
题目：请讨论是否应该禁止学生带手机进校园

In my opinion, students should not be allowed to bring mobile phones to school. There are several reasons for this. First, mobile phones can distract students from their studies. Many students spend too much time playing games or chatting on their phones during class. Second, using mobile phones in class can disturb the teacher and other students. Third, some students may use mobile phones to cheat in exams.

Therefore, I believe schools should prohibit students from bringing mobile phones to campus.
```

#### 传给大模型
```json
{
  "task": "en-app",
  "model": "llm",
  "content": "In my opinion, students should not be allowed to bring mobile phones to school. There are several reasons for this. First, mobile phones can distract students from their studies. Many students spend too much time playing games or chatting on their phones during class. Second, using mobile phones in class can disturb the teacher and other students. Third, some students may use mobile phones to cheat in exams.Therefore, I believe schools should prohibit students from bringing mobile phones to campus.",
  "problem": "请讨论是否应该禁止学生带手机进校园",
  "grade": "高一"
}
```

---

### 🔷 示例3：无题目的自由作文（20分）

#### 输入：学生作文
```
My Favorite Season

My favorite season is spring. In spring, the weather becomes warm and everything comes back to life. Trees turn green and flowers start to bloom. I love spring because I can fly kites and go hiking with my friends. Spring gives me hope and energy. I always feel happy in this beautiful season.
```

#### 传给大模型
```json
{
  "task": "en-app",
  "model": "llm",
  "content": "My Favorite SeasonMy favorite season is spring. In spring, the weather becomes warm and everything comes back to life. Trees turn green and flowers start to bloom. I love spring because I can fly kites and go hiking with my friends. Spring gives me hope and energy. I always feel happy in this beautiful season.",
  "problem": "",
  "grade": "初三"
}
```

---

## 四、关键处理细节

### 🔷 1. content 预处理

**去除换行符**（[english_write.py:573](english_write.py#L573)）：
```python
if '\n' in post_text:
    post_text = re.sub("\n", "", post_text)
```

**示例**：
```
输入：
"Dear Sir,\n\nI am writing to apply..."

输出：
"Dear Sir,I am writing to apply..."
```

### 🔷 2. grade 可选值

```json
{
  "初一": "Junior 1",
  "初二": "Junior 2",
  "初三": "Junior 3",
  "高一": "Senior 1",
  "高二": "Senior 2",
  "高三": "Senior 3"
}
```

### 🔷 3. problem 字段

- **有题目**：提供完整题目内容
- **无题目**：传空字符串 `""`

**为什么建议提供？**
- ✅ 帮助判断是否切题
- ✅ 评估内容完整性
- ✅ 提供更准确的建议

**为什么totalScore必需？**
- ✅ 大模型需要知道满分是多少（15分、25分等）
- ✅ 大模型直接输出真实得分（如11.3/15分）
- ✅ 不需要后端做分数转换

---

## 五、API接口规范

### 🔷 完整请求

```http
POST /correct_essay HTTP/1.1
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "task": "en-app",
  "model": "llm",
  "content": "I'm Li Hua. I am writing to apply...",
  "problem": "假定你是李华，写一封申请信",
  "grade": "高二"
}
```

### 🔷 成功响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "percentageScore": 75.5,
    "highlight": [["express sincere gratitude", [10, 35]]],
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
  }
}
```

---

## 六、配置说明

### 🔷 API地址配置

**文件**：`grammar_mq_config.cfg`

```json
{
  "online": {
    "correct_essay_api": "http://your-llm-api/correct_essay"
  }
}
```

**代码中读取**（[english_write.py:44](english_write.py#L44)）：
```python
self.correct_essay_api = "http://your-llm-api/correct_essay"
```

---

## 七、快速参考

### 📊 参数速查

| 参数 | 必需 | 类型 | 示例 |
|------|------|------|------|
| task | ✅ | string | `"en-app"` |
| model | ✅ | string | `"llm"` |
| content | ✅ | string | `"I'm Li Hua..."` |
| grade | ✅ | string | `"高二"` |
| problem | ❌ | string | `"假定你是李华..."` |

### ✅ 检查清单

部署前确认：
- [ ] API端点可访问
- [ ] content已去除换行符
- [ ] grade在可选列表中（初一~高三）
- [ ] task固定为"en-app"
- [ ] model固定为"llm"
- [ ] problem有值（即使为空字符串）
- [ ] 配置了重试机制（最多3次）

---

## 八、与AYX模型对比

### 🔷 AYX模型的输入

```python
# GEC引擎输入
{"post_content": "I'm Li Hua..."}

# AES引擎输入
{"post_content": "I'm Li Hua...", "grade": "高二"}
```

### 🔷 大模型的输入

```json
{
  "task": "en-app",
  "model": "llm",
  "content": "I'm Li Hua...",
  "grade": "高二",
  "problem": "假定你是李华..."
}
```

### 🔷 对比总结

| 对比项 | AYX（GEC+AES） | 大模型 |
|--------|---------------|--------|
| **输入字段** | 2个（post_content, grade） | 5个 |
| **任务类型** | 固定（英语作文） | 显式传递task |
| **题目信息** | ❌ 无 | ✅ 有problem |
| **引擎数量** | 2个（GEC+AES） | 1个（大模型） |
| **调用次数** | 2次 | 1次 |

---

**文档版本**: v1.0（精简版）
**生成时间**: 2026-02-06
**适用范围**: 大模型替换自研AYX模型
