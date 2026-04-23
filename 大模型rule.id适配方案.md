# 大模型替代自研模型后 rule.id 的适配方案

## 📋 问题

**Q**: 现在不用自研模型了,统一为大模型接口,`rule.id` 还有用吗?或者说怎么适配?

---

## 🔍 当前代码分析

### 1. 去重逻辑 (还在使用)

**位置**: `english_write.py:59-73`

```python
def remove_repeat(self, rule_set):
    repeat = set()
    removed_rule_set = []
    for item in rule_set:
        # ⚠️ 使用 offset + length + category 去重
        splice_str = "%s,%s,%s" % (
            item['offset'],
            item['length'],
            item['rule']['category']
        )
        repeat.add(splice_str)
```

**状态**: ✅ 函数保留,但**不再调用** (因为 `_parser_one_essay` 已经不使用了)

---

### 2. 合并规则逻辑 (还在使用)

**位置**: `english_write.py:16` 和测试代码

```python
from merge_rule_process import MergeRuleMethod, CallInterface

# 测试代码中使用
pprocess = MergeRuleMethod()
merge_rule = pprocess._process(error_rules_set, content)
```

**状态**: ⚠️ **只在测试代码中使用**,生产环境不调用

---

### 3. 大模型直接传递 (新逻辑)

**位置**: `english_write.py:619`

```python
every_student_info = {
    'uploadKey': uploadKey,
    'score': correction_result.get('score', 0),
    'highlight': correction_result.get('highlight', []),
    'error_set': correction_result.get('error_set', [])  # ⭐ 直接使用,不做处理
}
```

**状态**: ✅ **直接传递给前端,不做任何处理**

---

## 📊 rule.id 的作用变化

### 原来的自研模型 (GEC + AES)

```
GEC引擎 → 返回 error_set
  ↓
remove_repeat() 去重
  ↓
merge_rule_process 合并
  ↓
返回最终结果
```

**rule.id 的作用**:
- ❌ 去重时不使用
- ✅ 合并时区分来源 (GEC vs LT)
- ✅ 标识错误类型

---

### 现在的大模型

```
N8N大模型 → 返回 error_set
  ↓
直接传递给前端 (不做处理)
```

**rule.id 的作用**:
- ⚠️ **完全由大模型决定**
- ⚠️ 后端不处理
- ⚠️ 前端可能使用

---

## ✅ rule.id 在大模型模式下的作用

### 作用1: 前端显示错误类型

**前端可能根据 `rule.id` 显示不同的图标或样式**:

```javascript
// 前端可能的实现
if (rule.id === 'ARTICLE_A_VS_AN') {
    icon = '冠词错误图标'
} else if (rule.id === 'MORFOLOGIK_RULE_EN_US') {
    icon = '拼写错误图标'
}
```

**结论**: ✅ **有用!** 前端可能依赖 `rule.id`

---

### 作用2: 错误分类和统计

**前端可能根据 `rule.id` 做统计分析**:

```javascript
// 统计各种错误类型
const errorStats = {}
error_set.forEach(error => {
    const id = error.rule.id
    errorStats[id] = (errorStats[id] || 0) + 1
})

// 结果:
// {
//   'ARTICLE_A_VS_AN': 3,
//   'MORFOLOGIK_RULE_EN_US': 2,
//   'EN_A_VS_AN': 1
// }
```

**结论**: ✅ **有用!** 可以做错误统计

---

### 作用3: 后端不使用

**后端现在的逻辑**:

```python
# 不去重
# 不合并
# 直接传递
error_set = correction_result.get('error_set', [])
```

**结论**: ❌ **后端不使用 `rule.id`**

---

## 🎯 大模型 rule.id 的适配方案

### 方案1: 保持兼容 (推荐) ⭐

**让大模型返回类似原来的 `rule.id` 格式**

#### 原来的格式 (自研模型)

```json
{
  "rule": {
    "id": "ARTICLE_A_VS_AN",
    "category": "ERROR_GRAMMAR"
  }
}
```

#### 大模型应该返回

```json
{
  "rule": {
    "id": "ARTICLE_A_VS_AN",        // ⭐ 具体的错误规则ID
    "category": "ERROR_GRAMMAR"     // ⭐ 错误分类
  }
}
```

**优点**:
- ✅ 完全兼容前端
- ✅ 前端不需要修改
- ✅ 可以显示错误类型

**实现**:
- 大模型需要输出标准化的 `rule.id`
- 使用常见的错误规则ID (如 LanguageTool 的规则ID)

---

### 方案2: 使用固定值 (简单但不推荐)

**大模型返回固定的 `rule.id`**

```json
{
  "rule": {
    "id": "GRAMMAR_ERROR",         // ⭐ 固定值
    "category": "ERROR_GRAMMAR"
  }
}
```

**优点**:
- ✅ 简单,大模型容易实现
- ✅ `category` 已经包含错误分类

**缺点**:
- ❌ 失去了错误类型的细节
- ❌ 前端无法区分具体错误
- ❌ 无法做详细的错误统计

---

### 方案3: 完全去除 id (不推荐)

**不返回 `rule.id`**

```json
{
  "rule": {
    "category": "ERROR_GRAMMAR"     // ⭐ 只返回category
  }
}
```

**优点**:
- ✅ 最简单

**缺点**:
- ❌ **不兼容!** 前端可能期望有 `id` 字段
- ❌ 失去了错误类型信息
- ❌ 可能导致前端报错

---

## 📋 推荐的 rule.id 格式

### 参考标准: LanguageTool

LanguageTool 是一个开源的语法检查工具,它的规则ID格式:

```
规则ID格式: {CATEGORY}_{SUBCATEGORY}_{SPECIFIC}

示例:
- ARTICLE_A_VS_AN          (冠词 a vs an)
- MORFOLOGIK_RULE_EN_US    (拼写错误)
- EN_CONTRACTION_SPELLING   (缩写拼写)
- SUBJECT_VERB_AGREEMENT    (主谓一致)
```

### 大模型应该返回的格式

```json
{
  "error_set": [
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
        "id": "MORFOLOGIK_RULE_EN_US",
        "category": "ERROR_SPELLING"
      }
    },
    {
      "offset": 120,
      "length": 3,
      "message": "Subject-verb agreement error",
      "rule": {
        "id": "SUBJECT_VERB_AGREEMENT",
        "category": "ERROR_GRAMMAR"
      }
    }
  ]
}
```

---

## 🔧 如何让大模型输出正确的 rule.id?

### 方案1: 在 Prompt 中指定

```
请批改英语作文,返回JSON格式:

{
  "error_set": [
    {
      "offset": 错误位置,
      "length": 错误长度,
      "message": "错误描述",
      "rule": {
        "id": "错误规则ID (使用以下标准值: ARTICLE_A_VS_AN, MORFOLOGIK_RULE_EN_US, SUBJECT_VERB_AGREEMENT, ...)",
        "category": "错误分类 (ERROR_SPELLING, ERROR_GRAMMAR, ERROR_TENSE, ...)"
      }
    }
  ]
}

错误规则ID标准值:
- 冠词错误: ARTICLE_A_VS_AN
- 拼写错误: MORFOLOGIK_RULE_EN_US
- 主谓一致: SUBJECT_VERB_AGREEMENT
- 时态错误: TENSE_CONSISTENCY
- 介词错误: PREPOSITION_USAGE
- 大小写错误: CAPITALIZATION
```

### 方案2: 后端映射 (推荐)

**大模型返回简化的 id,后端映射到标准格式**

```python
# 大模型返回
{
  "rule": {
    "id": "article_error",  # 简化描述
    "category": "ERROR_GRAMMAR"
  }
}

# 后端映射
rule_id_mapping = {
    "article_error": "ARTICLE_A_VS_AN",
    "spelling_error": "MORFOLOGIK_RULE_EN_US",
    "tense_error": "TENSE_CONSISTENCY",
    "subject_verb_agreement": "SUBJECT_VERB_AGREEMENT",
    # ...
}

# 转换
standard_id = rule_id_mapping.get(
    llm_rule_id,
    llm_rule_id.upper()  # 如果没有映射,直接转大写
)
```

---

## ✅ 总结

### rule.id 在大模型模式下的状态

| 场景 | rule.id 是否有用 | 说明 |
|------|----------------|------|
| **后端去重** | ❌ 不使用 | 后端不做任何处理 |
| **后端合并** | ❌ 不使用 | 后端不做任何处理 |
| **前端显示** | ✅ **有用!** | 可能用于显示错误类型 |
| **错误统计** | ✅ **有用!** | 可以统计各类错误 |
| **用户体验** | ✅ **有用!** | 提供更详细的反馈 |

### 推荐方案

**让大模型返回标准的 `rule.id` 格式**:

```json
{
  "rule": {
    "id": "ARTICLE_A_VS_AN",
    "category": "ERROR_GRAMMAR"
  }
}
```

**原因**:
1. ✅ 兼容前端 (前端不需要修改)
2. ✅ 提供更好的用户体验
3. ✅ 可以做详细的错误统计
4. ✅ 保持数据格式一致性

### 实现建议

**在 N8N 工作流的 Prompt 中指定**:

```
返回的 error_set 中,每个错误必须包含:
- offset: 错误位置
- length: 错误长度
- message: 错误描述
- rule.id: 使用标准错误规则ID (如 ARTICLE_A_VS_AN, MORFOLOGIK_RULE_EN_US 等)
- rule.category: 错误分类 (ERROR_SPELLING, ERROR_GRAMMAR, ERROR_TENSE 等)
```

---

**结论**: `rule.id` 在大模型模式下**仍然有用**,主要是给前端使用。建议让大模型返回标准格式的 `rule.id`,以保持兼容性和提供更好的用户体验! 👍
