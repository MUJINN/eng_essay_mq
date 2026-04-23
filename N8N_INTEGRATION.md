# n8n 模型集成说明

## 一、快速开始

### 1. 配置 n8n API 地址

编辑 `eng_essay_mq/grammar_mq_config.cfg`，在每个环境配置中添加 `n8n_api` 字段：

```json
{
  "online": {
    "mq_url_parameter": "...",
    "post_api": "...",
    "mq_queue": "...",
    "correct_essay_api": "...",
    "n8n_api": "https://n8n.your-domain.com/webhook/essay-correction"
  }
}
```

### 2. 使用 n8n 模型

在 MQ 消息中指定 `model` 为 `n8n`：

```json
{
  "subjectId": 9768863,
  "blockId": 23576240,
  "taskKey": "test-001",
  "task": "en-app",
  "model": "n8n",
  "grade": "高二",
  "totalScore": 15,
  "problem": "假定你是李华，写一封英文申请信...",
  "students": [
    {
      "uploadKey": "student-001",
      "post_text": "I'm Li Hua. I'm writing to apply..."
    }
  ]
}
```

## 二、n8n 服务端接口规范

### 输入格式

n8n 工作流需要接收以下 HTTP POST 请求：

```json
{
  "task": "en-app",
  "model": "n8n",
  "content": "I'm Li Hua. I'm writing to apply for the position...",
  "problem": "假定你是李华，写一封英文申请信...",
  "grade": "高二"
}
```

### 输出格式

n8n 工作流需要返回以下格式的 JSON：

```json
{
  "data": {
    "percentageScore": 85.5,
    "highlight": [
      ["excellent vocabulary here", [10, 35]]
    ],
    "error_set": [
      {
        "offset": 45,
        "length": 6,
        "message": "Spelling error: 'recieve' should be 'receive'"
      }
    ],
    "comment": "这是一篇结构清晰、表达准确的应用文...",
    "suggestion": "建议注意拼写和时态...",
    "improveArticle": "",
    "topicScore": 4,
    "contentScore": 4,
    "structureScore": 5,
    "languageScore": 4,
    "errorCorrection": [],
    "expression": []
  }
}
```

## 三、字段说明

### 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `percentageScore` | float | 百分制分数 (0-100) |
| `highlight` | array | 亮点表达 [["text", [start, end]]] |
| `error_set` | array | 语法错误 [{offset, length, message}] |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `comment` | string | 总评语 |
| `suggestion` | string | 改进建议 |
| `topicScore` | int | 主题分数 (0-5) |
| `contentScore` | int | 内容分数 (0-5) |
| `structureScore` | int | 结构分数 (0-5) |
| `languageScore` | int | 语言分数 (0-5) |

## 四、测试

运行测试脚本：

```bash
python test_n8n.py
```

## 五、代码改动说明

### 修改的文件

1. `eng_essay_mq/english_write.py`
   - 添加 `n8n_api` 参数到 `__init__`
   - 新增 `_correct_essay_by_n8n()` 方法
   - 在 `parser_one_essay()` 中添加 `model='n8n'` 分支

2. `eng_essay_mq/mq_client_grammar.py`
   - `read_configuration()` 返回 `n8n_api`
   - 更新整个调用链传递 `n8n_api` 参数

3. `eng_essay_mq/grammar_mq_config.cfg`
   - 添加 `n8n_api` 配置项

### 新增的文件

- `test_n8n.py` - n8n 模型测试脚本

## 六、故障排查

### 问题：n8n 接口调用失败

检查日志文件 `log/consumer_log.txt`，查看错误信息：

```
n8n API request failed after 3 retries
Exception in _correct_essay_by_n8n: ...
```

### 解决方法

1. 确认 n8n_api 配置正确
2. 确认 n8n 服务可以访问
3. 检查 n8n 工作流是否正常运行
4. 查看 n8n 日志

## 七、注意事项

1. **percentageScore 必须是 0-100 的浮点数**，不是 0-1
2. **highlight 格式是 `[text, [start, end]]`**，不是对象
3. **error_set 的 offset 和 length 是字符位置**，用于在原文中定位
4. 如果 n8n_api 未配置，会使用默认值（与 correct_essay_api 相同）

## 八、下一步

1. 配置实际的 n8n API 地址
2. 在 n8n 中创建英语作文批改工作流
3. 运行测试验证功能
4. 部署到生产环境
