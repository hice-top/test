# Windows 一键部署构建器（需求与流程设计）

## 1. 项目目标
面向 **开发者→客户** 的交付场景，提供一个可视化构建器，将运行环境与业务程序打包成单个 `.exe`，客户双击后即可完成无人值守部署（必要时按冲突策略弹窗决策）。

---

## 2. 角色与核心价值

### 2.1 开发者端（构建器）
- 选择需要安装的基础环境：JDK、Tomcat、MySQL、SQL Server、Redis 等。
- 上传项目程序包：`app.jar`、`app.war`、`dist.zip`。
- 配置安装参数、前置检查、冲突处理策略、后置操作。
- 点击“立即构建”，生成可分发的 Windows 安装程序（`.exe`）。

### 2.2 客户端（部署程序）
- 运行 `.exe` 后自动完成环境安装与业务部署。
- 页面显示部署进度与日志（是否显示由高级选项控制）。
- 遇到“提示用户”策略时，弹窗让客户选择处理方式。
- 部署完成后给出成功/失败总结。

---

## 3. 端到端流程
1. 开发者在构建器中选择要部署的应用组件（JDK/Tomcat/数据库/缓存等）。
2. 上传业务程序包（`jar/war/dist.zip`），并配置 Web 服务器部署优先级（拖拽排序）。
3. 对每个应用配置安装包来源、安装路径、静默参数、前/后置动作。
4. 填写构建信息（项目名、版本、安装根目录、高级选项）。
5. 执行“立即构建”，触发打包脚本（例如 `npm run pack:win`）。
6. 生成并输出 `.exe` 到指定目录，交付给客户。
7. 客户运行 `.exe`，部署程序按配置执行安装、检查、冲突处理与业务分发。
8. 页面展示部署进度/日志，最终提示部署完成。

---

## 4. 功能模块拆分

## 4.1 开发者端（Builder UI）

### A. 应用选择
- 预置组件：JDK、Tomcat、MySQL、SQL Server、Redis、Nginx（可扩展）。
- 每个组件可独立启用/禁用与配置。

### B. 业务包上传
- 支持上传：`app.jar` / `app.war` / `dist.zip`。
- 对 `dist.zip` 提供“部署目标优先级”配置（拖拽列表）：
  - 例：Tomcat > Nginx。

### C. 应用配置（逐组件）
- 安装包路径（本地文件或制品库地址）。
- 安装目录。
- 静默安装参数。

### D. 安装前置操作
- Windows 功能配置（如 IIS/.NET 等可选）。
- 检查同名目录。
- 检查同版本程序。
- 检查同名 Windows 服务。

### E. 冲突处理策略
- 覆盖。
- 跳过。
- 备份后覆盖。
- 自动重命名旧目录。
- 自动重命名服务。
- 自动卸载旧版本。
- 提示用户选择。

### F. 安装后置操作
- 写入环境变量并追加到 `PATH`。
- 注册为 Windows 服务。
- 设置服务自动启动。
- 立即启动服务。

### G. 构建配置
- 项目名称。
- 部署安装包版本号。
- 项目安装根路径。
- 高级选项：
  - 生成安装日志。
  - 启用进度显示。
  - 智能自解压模式。

### H. 构建执行
- 一键构建。
- 调用打包脚本（如 Electron 打包命令）。
- 输出构建产物路径。

## 4.2 客户端（Installer UI + Engine）
- 启动后加载构建时生成的配置文件（manifest）。
- 按依赖顺序执行环境安装与项目部署。
- 实时展示执行步骤、进度、日志。
- 执行冲突策略；若策略为“提示用户”则进入交互选择。
- 输出最终报告（成功、失败、跳过、耗时）。

---

## 5. 部署规则（关键）

### 5.1 `war` 包部署
- 默认投放到 `tomcat/webapps`。

### 5.2 `dist.zip` 部署
1. 判断是否安装 Tomcat：若是，可部署到 `tomcat/webapps`（按系统约定目录）。
2. 判断是否安装 Nginx：若是，可部署到 Nginx 站点目录。
3. 若 Tomcat 与 Nginx 同时存在：
   - 严格按构建配置中的“优先级排序”选择目标。

---

## 6. 建议的配置清单（Manifest）结构

```json
{
  "project": {
    "name": "demo-project",
    "version": "1.0.0",
    "installRoot": "D:/apps/demo"
  },
  "advanced": {
    "enableLogs": true,
    "showProgress": true,
    "smartExtract": true
  },
  "components": [
    {
      "name": "jdk",
      "enabled": true,
      "installer": "packages/jdk.exe",
      "installPath": "D:/env/jdk17",
      "silentArgs": "/s",
      "preChecks": ["folderConflict", "sameVersion", "serviceConflict"],
      "conflictPolicy": "backup_then_overwrite",
      "postActions": ["setEnv", "appendPath"]
    }
  ],
  "artifacts": {
    "jar": "upload/app.jar",
    "war": "upload/app.war",
    "frontendZip": "upload/dist.zip",
    "webTargetPriority": ["tomcat", "nginx"]
  }
}
```

---

## 7. 执行引擎建议顺序
1. 初始化与配置校验。
2. 前置检测（权限、磁盘空间、系统版本、端口占用）。
3. 逐组件执行：前置检查 → 冲突处理 → 静默安装 → 后置动作。
4. 部署业务程序包（jar/war/dist.zip）。
5. 服务注册与启动验证。
6. 生成总结报告并提示完成。

---

## 8. 异常与回滚建议
- 组件安装失败时：记录失败点并停止后续依赖步骤。
- 若开启“备份后覆盖”：保留备份索引，支持一键回滚。
- 若某服务启动失败：自动抓取最近日志并引导排障。
- 用户中断安装：保存断点状态，支持重试。

---

## 9. 打包与交付建议
- 构建器技术栈：Electron + 前端配置页面 + 本地部署引擎。
- 打包命令：`npm run pack:win`（可扩展 CI 命令）。
- 交付物：
  - `ProjectInstaller.exe`
  - `manifest.json`
  - 安装包资源目录（可内嵌或随包分发）

---

## 10. 验收标准（MVP）
- 可选择至少 3 类环境组件并成功安装。
- 可上传并部署 `war` 与 `dist.zip`。
- 同时存在 Tomcat+Nginx 时，`dist.zip` 能按优先级准确部署。
- 冲突策略“提示用户”可触发并生效。
- 安装过程可显示进度与日志。
- 最终有明确完成提示与结果报告。

---

## 11. 本仓库交付物（当前阶段）
- `manifest.schema.json`：安装配置的 JSON Schema，供构建器导出与安装器加载时校验。
- `examples/manifest.sample.json`：可直接用于联调的示例配置。
- `docs/engine-workflow.md`：部署引擎执行顺序、冲突策略、失败恢复设计。
- `tools/validate_manifest.py`：无第三方依赖的基础校验脚本。

### 快速验证
```bash
python3 tools/validate_manifest.py examples/manifest.sample.json
```

---

## 12. 完整可运行版本（本仓库）
当前仓库已经提供一个 **可直接运行的原型版本**（命令行模式），包含：
- 初始化 manifest 模板
- 校验 manifest
- 按 manifest 执行部署流程（模拟安装与分发）
- 输出安装日志、断点状态、部署报告

### 12.1 运行环境
- Python 3.9+
- 无第三方依赖

### 12.2 快速开始
```bash
# 1) 生成 manifest（可编辑）
python3 -m app.main init --output runtime/manifest.json

# 2) 校验 manifest
python3 -m app.main validate runtime/manifest.json

# 3) 执行安装流程
python3 -m app.main install runtime/manifest.json --runtime-dir runtime
```

### 12.3 输出内容
安装后可在 `runtime/` 下看到：
- `logs/install.log`：执行日志
- `state.json`：断点状态（可配合 `--resume` 继续）
- `report.json`：结果报告（步骤状态、时间、失败信息）
- `sandbox_install/`：模拟部署产物目录

### 12.4 继续开发为 GUI/EXE
当前版本为 CLI 可运行内核。若要形成最终 Windows GUI 一键安装器，可在此基础上新增：
1. Electron 配置界面（Builder UI）
2. 将 `app.main install` 作为安装引擎调用
3. 增加真实安装器执行器（MSI/EXE 静默参数）
4. 使用 `npm run pack:win` 输出最终 `.exe`

---

## 13. Windows GUI 一键安装器（最终形态）
本仓库现已包含 GUI 版本入口：

```bash
python3 -m app.gui
```

GUI 支持：
- Manifest 初始化（从示例模板生成）
- Manifest 编辑/保存
- Manifest 校验
- 执行安装流程（含日志、报告查看、`--resume` 续跑）

### 13.1 在 Windows 打包为 EXE
推荐 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_win_exe.ps1
```

打包完成后输出：
- `dist/WindowsOneClickInstaller.exe`

### 13.2 交付给客户的最小清单
- `WindowsOneClickInstaller.exe`
- `manifest.json`（可内置或外置）
- 组件安装包目录（jdk/tomcat/mysql/sqlserver/redis/nginx 等）
- 业务包（`app.jar`/`app.war`/`dist.zip`）
