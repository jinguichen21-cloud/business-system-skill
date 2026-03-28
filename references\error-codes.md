# 错误码及处理方式

> 常见错误场景的诊断和解决方案。

## 错误分类

| 类别 | 错误码范围 | 说明 |
|------|-----------|------|
| 参数错误 | 400-499 | 命令参数不正确 |
| 权限错误 | 401, 403 | 认证或授权失败 |
| 执行错误 | 500-599 | 服务端处理失败 |
| 超时错误 | timeout | 任务执行超时 |

---

## 常见错误及处理

### E001: 缺少必填参数

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "MISSING_PARAMETER",
    "message": "Missing required parameter: --skills"
  }
}
```

**原因**: 命令缺少必填参数

**处理方式**:
1. 检查命令是否包含所有必填参数
2. create/modify 必须包含: `--prompt`, `--skills`, `--format json`
3. modify 还必须包含: `--thread-id`
4. query 必须包含: `--task-id`, `--format json`

---

### E002: threadId 无效

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_THREAD_ID",
    "message": "Thread not found: thread_xxx"
  }
}
```

**原因**: 提供的 threadId 不存在或已过期

**处理方式**:
1. 确认 threadId 是从之前 create 返回中提取的
2. 不要编造 threadId
3. 如果 threadId 过期，询问用户是否重新 create

---

### E003: taskId 无效

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TASK_ID",
    "message": "Task not found: task_xxx"
  }
}
```

**原因**: 提供的 taskId 不存在

**处理方式**:
1. 确认 taskId 是从 create/modify 返回中提取的
2. 不要编造 taskId

---

### E004: 权限不足

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You don't have permission to perform this action"
  }
}
```

**原因**: 用户未登录或权限不足

**处理方式**:
1. 提示用户检查登录状态
2. 执行 `dws auth login` 重新登录
3. 确认用户有该技能的使用权限

---

### E005: 任务执行失败

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "TASK_FAILED",
    "message": "Task execution failed: ..."
  }
}
```

**原因**: AI 应用生成过程中出错

**处理方式**:
1. 向用户展示完整错误信息
2. 询问用户是否需要调整 prompt 后重试
3. 不要自行猜测替代方案

---

### E006: 请求超时

**错误信息**:
```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "Request timed out"
  }
}
```

**原因**: 任务执行时间过长

**处理方式**:
1. 使用 `dws aiapp query --task-id <taskId>` 查询任务状态
2. 如果任务仍在执行，等待后再次查询
3. 如果任务已失败，告知用户并询问是否重试

---

## 调试技巧

### 1. 检查命令格式

```bash
# 正确格式
dws aiapp create --prompt "..." --skills skill_88a1554dd1e04d4c --format json

# 常见错误: 忘记 --format json
dws aiapp create --prompt "..." --skills skill_88a1554dd1e04d4c  # ❌
```

### 2. 验证返回值

```bash
# 检查返回是否包含预期字段
{
  "success": true,
  "data": {
    "threadId": "...",  # 用于 modify
    "taskId": "..."     # 用于 query
  }
}
```

### 3. 状态轮询

```bash
# 任务可能需要一些时间，建议轮询状态
while status == "running":
    sleep(5)
    query --task-id <taskId>
```

---

## 错误处理原则

1. **展示给用户**: 遇到错误时，将错误信息展示给用户，不要自行猜测
2. **不要重试危险操作**: 删除、覆盖等操作失败后，需用户确认再重试
3. **保留上下文**: 保存 threadId 和 taskId，便于后续排查
4. **询问而非猜测**: 不确定用户意图时，询问而非自行决定
