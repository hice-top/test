# 部署引擎执行设计（可落地）

## 1) 总体执行阶段
1. 读取并校验 `manifest.json`（建议按 `manifest.schema.json`）。
2. 提升管理员权限（若 `execution.requireAdmin=true`）。
3. 进行全局前置检测：
   - 权限、磁盘可用空间、系统版本。
   - 已存在服务与端口探测。
4. 安装组件（按依赖顺序，例如 JDK -> DB/缓存 -> Web 服务器）。
5. 分发业务包（jar/war/dist.zip）。
6. 服务健康检查（端口连通性、进程存活）。
7. 输出结果报告（成功、失败、跳过、耗时、建议动作）。

## 2) 组件安装算法（伪代码）
```text
for component in components where enabled=true:
  run preChecks
  if conflict found:
    action = resolveByPolicy(conflictPolicy)
    if action == abort:
      mark failed and stop if stopOnFailure
  execute silent installer
  run postActions
  mark component done
```

## 3) 冲突策略行为建议
- `overwrite`：删除目标目录/服务后重装。
- `skip`：记录为跳过并继续下一个组件。
- `backup_then_overwrite`：备份旧目录到 `*_bak_timestamp` 再覆盖。
- `rename_old_folder`：旧目录自动更名，保留历史版本。
- `rename_service`：旧服务追加后缀后再注册新服务。
- `uninstall_old`：调用卸载器后继续安装。
- `ask_user`：弹窗二次确认并记录用户选择。

## 4) 业务包部署规则
- `war`：优先部署到 `tomcat/webapps`。
- `jar`：复制到 `<installRoot>/app`，并可自动注册为 Windows 服务。
- `dist.zip`：
  1. 若仅有 Tomcat，投放到 `tomcat/webapps` 或静态目录。
  2. 若仅有 Nginx，投放到 Nginx 站点目录。
  3. 若两者并存，按 `artifacts.webTargetPriority` 首项决定目标。

## 5) 日志与进度
- `advanced.enableLogs=true`：输出结构化日志（jsonl + 文本摘要）。
- `advanced.showProgress=true`：UI 显示阶段进度与当前步骤。
- 每个步骤记录：`startAt`、`endAt`、`status`、`errorCode`、`errorMessage`。

## 6) 失败恢复
- 若 `execution.allowResume=true`：保存 `state.json`（已完成步骤）。
- 重试时跳过成功步骤，仅从失败点继续。
- 若 `rollbackOnFailure=true`：按备份索引反向执行回滚。
