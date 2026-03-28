# dws aiapp 命令参考

> 完整的 `dws aiapp` 命令参数说明，供 AI Agent 按需加载。

## 命令概览

| 命令 | 用途 |
|------|------|
| `dws aiapp create` | 新建 AI 应用 |
| `dws aiapp modify` | 修改已有 AI 应用 |
| `dws aiapp query` | 查询任务状态 |

---

## dws aiapp create

新建 AI 应用（品牌官网）。

### 语法

```bash
dws aiapp create \
  --prompt <用户描述> \
  --skills <技能ID列表> \
  --format json \
  [--attachments <附件信息>]
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|:---:|------|
| `--prompt` | ✅ | 用户对应用的描述，自然语言 |
| `--skills` | ✅ | 技能 ID，多个用逗号分隔。品牌官网必须包含 `skill_88a1554dd1e04d4c` |
| `--format json` | ✅ | 输出格式，必须为 json |
| `--attachments` | ❌ | 附件信息 (仅 create 支持，见下方详细说明) |

### 附件参数格式

`--attachments` 参数值为 JSON 数组，每个对象必须包含以下 4 个字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `name` | string | ✅ | 文件名，如 `"logo.png"` |
| `type` | string | ✅ | MIME 类型，如 `image/png`, `image/jpeg`, `application/pdf` |
| `url` | string | ✅ | 文件访问 URL，必须是可公开访问的地址 |
| `size` | number | ✅ | 文件大小 (字节) |

**正确示例:**

```bash
# 单个附件 (Logo)
--attachments '[{"name":"logo.png","type":"image/png","url":"https://example.com/logo.png","size":102400}]'

# 多个附件 (Logo + VI文档)
--attachments '[{"name":"logo.png","type":"image/png","url":"https://...","size":102400},{"name":"vi-guide.pdf","type":"application/pdf","url":"https://...","size":2048000}]'

# 多个附件 (Logo + VI文档 + 产品图 + Banner)
--attachments '[{"name":"logo.png","type":"image/png","url":"https://...","size":102400},{"name":"VI手册.pdf","type":"application/pdf","url":"https://...","size":2048000},{"name":"产品图.jpg","type":"image/jpeg","url":"https://...","size":512000},{"name":"banner.png","type":"image/png","url":"https://...","size":819200}]'
```

**支持的文件类型:**

| 类型 | MIME 类型 | 说明 |
|------|----------|------|
| PNG 图片 | `image/png` | Logo、图标、透明背景图 |
| JPEG 图片 | `image/jpeg` | 产品图、Banner、照片 |
| PDF 文档 | `application/pdf` | VI手册、品牌规范文档 |
| Word 文档 | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 品牌说明文档 |

**错误示例:**

```bash
# [错误] 缺少必填字段 (缺少 type 和 size)
--attachments '[{"name":"logo.png","url":"https://..."}]'

# [错误] 不是 JSON 数组格式
--attachments "logo.png"
```

### 返回值

```json
{
  "success": true,
  "result": {
    "status": "queued",
    "taskId": "019ced49-cefe-7531-9511-58bfcd4ec655",
    "taskUrl": "/open-api/ai-app/tasks/019ced49-cefe-7531-9511-58bfcd4ec655",
    "threadId": "fab89a91-35d6-44d7-9d59-927dea5e4396",
    "threadViewUrl": "https://ai-app.dingtalk.com/chat?threadId=fab89a91-35d6-44d7-9d59-927dea5e4396"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `threadId` | string | 会话标识，用于后续 modify |
| `taskId` | string | 任务标识，用于 query 查询状态 |
| `threadViewUrl` | string | 应用创建过程链接，拿到后必须第一时间展示给用户 |
| `status` | string | 任务状态: `queued`, `running`, `succeeded`, `failed` |

Agent 必须优先从 `result.threadViewUrl` 提取应用创建过程链接，并在普通回复正文中展示；不要只把它留在工具输出里。`threadId`、`taskId` 是内部字段，不要主动展示给用户。

### 示例

```bash
# 基础创建
dws aiapp create \
  --prompt "帮我创建一个简约现代风格的科技公司官网" \
  --skills skill_88a1554dd1e04d4c \
  --format json

# 带 Logo 创建
dws aiapp create \
  --prompt "根据这个Logo创建企业官网" \
  --skills skill_88a1554dd1e04d4c \
  --format json \
  --attachments '[{"name":"logo.png","type":"image/png","url":"https://...","size":102400}]'

# 组合视觉设计技能
dws aiapp create \
  --prompt "创建美观的企业官网" \
  --skills official_b3f7380095ef4e31,skill_88a1554dd1e04d4c \
  --format json
```

---

## dws aiapp modify

修改已有 AI 应用。

> **注意**: modify 命令**不支持**附件参数，如需更换素材请重新 create。

### 语法

```bash
dws aiapp modify \
  --thread-id <threadId> \
  --prompt <修改要求> \
  --skills <技能ID列表> \
  --format json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|:---:|------|
| `--thread-id` | ✅ | 会话标识，从 create 返回中获取 |
| `--prompt` | ✅ | 修改要求，自然语言 |
| `--skills` | ✅ | 技能 ID，必须包含 `skill_88a1554dd1e04d4c` |
| `--format json` | ✅ | 输出格式，必须为 json |

### 返回值

```json
{
  "success": true,
  "data": {
    "threadId": "thread_abc123",
    "taskId": "task_new456",
    "status": "running"
  }
}
```

### 示例

```bash
dws aiapp modify \
  --thread-id thread_abc123 \
  --prompt "优化一下首页的Banner布局" \
  --skills skill_88a1554dd1e04d4c \
  --format json
```

---

## dws aiapp query

查询任务执行状态。

### 语法

```bash
dws aiapp query \
  --task-id <taskId> \
  --format json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|:---:|------|
| `--task-id` | ✅ | 任务标识，从 create/modify 返回中获取 |
| `--format json` | ✅ | 输出格式，必须为 json |

> **注意**: query 命令**不需要** `--skills` 参数

### 返回值

```json
{
  "success": true,
  "result": {
    "taskId": "019ced40-abb4-77e3-b204-ad332eaa87d6",
    "status": "succeeded",
    "threadId": "ff7d37ba-28bb-4819-a6ea-4fe86966f7db",
    "updatedAt": "2026-03-15T00:54:00.528021+08:00",
    "rawThreadStatus": "idle",
    "rawRunStatus": "success",
    "result": {
      "threadId": "ff7d37ba-28bb-4819-a6ea-4fe86966f7db",
      "threadTitle": "西溪湿地极简旅游首页设计",
      "appPreviewUrl": "https://49jh7cecep.ai-app.pub"
    }
  }
}
```

轮询脚本必须优先从 `result.status` 读取任务状态，并从 `result.result.appPreviewUrl` 读取最终预览地址。
当 `status = succeeded` 时，`result.result.threadTitle` 应作为最终展示给用户的应用名称。

### 示例

```bash
dws aiapp query \
  --task-id task_xyz789 \
  --format json
```

---

## 上下文传递链

```
create → 返回 threadId, taskId
   ↓
modify (使用 threadId) → 返回新 taskId
   ↓
query (使用 taskId) → 返回执行结果
```

| 操作 | 提取字段 | 传递给 |
|------|---------|--------|
| `create` | `threadId` | `modify --thread-id` |
| `create` | `taskId` | `query --task-id` |
| `modify` | `taskId` | `query --task-id` |
