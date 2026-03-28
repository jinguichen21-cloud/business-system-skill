# 轮询查询应用状态

执行 `create` 或 `modify` 后，必须在当前活跃窗口持续跟踪任务进度，直到任务成功或失败为止。

## 轮询策略

- 默认查询间隔：**30 秒**
- 默认用户可见进度间隔：**300 秒**
- 最长跟踪时长：**60 分钟**
- 任务处于 `queued` 或 `running` 时，持续轮询，**不要**只查 1-2 次就停止
- 创建命令返回后，先把 `threadViewUrl` 和当前状态告诉用户；其中 `threadViewUrl` 最重要，必须优先展示
- `threadId`、`taskId` 只用于 agent 内部后续调用，不要主动展示给用户
- 如果创建返回中没有 `threadViewUrl`，立刻执行一次 `query` 补取，再向用户同步
- 轮询过程需要在当前会话中同步给用户；脚本每个 300 秒进度点都要输出一次心跳，agent 看到后要明确告诉用户"任务还在创建中，请耐心等待"
- 轮询是当前会话内的前台循环，不是 automation / reminder / cron / 后台调度
- 必须使用 skill 包里的 `scripts/poll_aiapp_status.py`
- 必须用 `uv run python <绝对脚本路径>` 执行，不要直接在错误目录下跑 `./scripts/...`
- 在执行脚本前，先解析 skill 根目录，拼出 `scripts/poll_aiapp_status.py` 的绝对路径
- 不要发明 `verbose` 等不存在的查询参数
- 当 `status = succeeded` 时，停止轮询，输出最终结果（包含 threadId、应用访问链接等）
- 当 `status = failed` 时，停止轮询，向用户报告失败信息

## 轮询流程

```bash
# 1. 创建后获取 taskId
dws aiapp create --prompt "<用户描述>" --skills skill_88a1554dd1e04d4c --format json
# → 记录返回的 taskId、threadId、threadViewUrl

# 2. 如果 create 返回中没有 threadViewUrl，立刻补查一次
dws aiapp query --task-id <taskId> --format json

# 3. 定位 skill 根目录，拼出绝对脚本路径，再启动长轮询脚本
TASK_ID="<taskId>" THREAD_ID="<threadId>" THREAD_VIEW_URL="<threadViewUrl>" \
uv run python "<skill_root>/scripts/poll_aiapp_status.py"
```

## Agent 执行要求

1. `create` 或 `modify` 返回后，第一条回复先给用户 `threadViewUrl` 和当前状态，不要只说"已开始创建"。
2. 连续查询时不要靠模型自己记住"稍后再查"，必须启动 `scripts/poll_aiapp_status.py`，让进程实际持续运行。
3. 统一使用 `uv run python <绝对脚本路径>`，不要引用 `./scripts/...` 这类相对路径。
4. 脚本每 30 秒内部查询一次；每经过一个 300 秒进度点且任务仍是 `queued`/`running`，agent 在当前会话发送一句简短更新，例如：`任务还在创建中，请耐心等待。`
5. 最长跟踪 60 分钟；60 分钟后若仍未完成，告诉用户任务仍在运行，并附上 `threadViewUrl` 供用户继续查看。
6. 当脚本输出 `task_succeeded` 时，向用户汇总 `threadTitle`（作为应用名称）、`threadViewUrl`、`appPreviewUrl`。
7. 当脚本输出 `task_failed` 时，向用户展示失败信息，并询问是否需要重试。
8. 如果脚本启动失败，先检查 skill 根目录是否解析正确，再检查绝对脚本路径是否存在。

## 结束条件

| 条件 | 处理 |
|------|------|
| `status = succeeded` | 停止轮询，展示 threadTitle、threadViewUrl、appPreviewUrl 给用户 |
| `status = failed` | 停止轮询，展示错误信息 |
| 已跟踪 60 分钟仍未结束 | 停止自动跟踪，展示 threadViewUrl，并告诉用户任务仍在后台继续 |

## 最终结果输出格式

任务完成后，向用户汇总展示以下信息：

| 字段 | 说明 |
|------|------|
| 任务状态 | succeeded / failed |
| 应用名称 | `threadTitle` |
| 应用访问链接 | `appPreviewUrl`（成功后可用） |
| 会话链接 | `threadViewUrl`（可随时查看进度页） |
