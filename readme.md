# AI CLI Kit (`aik`)

上游仓库：[goodnightzsj/codex-session-cloner](https://github.com/goodnightzsj/codex-session-cloner.git)

`ai-cli-kit` 是一个本地 AI CLI 工具箱。打包了两个子工具，共享同一套底层（原子写入 / 跨进程锁 / TUI 渲染 / Windows VT / UTF-8 launcher）：

| 子工具 | 用途 | 兼容入口 |
|---|---|---|
| **Codex Session Toolkit** | 浏览 / 迁移 / 导入导出 / 修复 Codex 会话 | `cst` / `codex-session-toolkit` |
| **CC Clean (Claude Code)** | 安全清理 Claude 本地标识 / 遥测 / 历史，自动备份 | `cc-clean` |

![界面预览](./assets/12345.png)

## 快速开始

### 一键安装（macOS / Linux）

```bash
chmod +x install.sh aik cc-clean codex-session-toolkit codex-session-toolkit.command
./install.sh
./aik             # 进入交互菜单，选 Codex 或 CC Clean
```

### 一键安装（Windows）

双击 `install.bat`，再双击 `aik.cmd`。或：

```powershell
.\install.ps1
.\aik.cmd
```

### 进 TUI 后

无参运行 `./aik` → 用 ↑↓ 选 **Codex Session Toolkit** 或 **CC Clean** → Enter 进入对应工具的菜单。

也可以跳过菜单直接进子工具：

```bash
./codex-session-toolkit            # Codex 子工具的 TUI
./cc-clean                         # CC Clean 的 TUI
```

## 常用命令

### Codex（会话管理）

```bash
./aik codex list                       # 列出本机 Codex 会话
./aik codex export <session_id>        # 导出单个会话为 Bundle
./aik codex export-desktop-all         # 批量导出 Desktop 会话
./aik codex import <session_id>        # 导入 Bundle
./aik codex clone-provider             # 切换 provider 后克隆
./aik codex repair-desktop             # 修复 Desktop 可见性 / 索引
./aik codex --help                     # 完整子命令清单
```

兼容写法：把 `./aik codex` 换成 `./codex-session-toolkit` 即可，参数完全一致。

### CC Clean（Claude 本地清理）

```bash
./aik claude plan                              # 预览默认安全清理计划
./aik claude clean --preset safe --yes         # 执行安全清理（自动备份）
./aik claude clean --preset full --yes         # 完整重置（含会话数据，慎用）
./aik claude remap-history --run-claude --yes  # 重新生成新 ID 并回写历史
./aik claude --help
```

兼容写法：`./aik claude` 等价于 `./cc-clean`。

**安全机制**：所有删除默认走 `~/.claude-clean-backups/<时间戳>/` 备份目录，可随时恢复。`--no-backup` 显式关闭备份；`--dry-run` 只预览不动磁盘。

## 源码模式（开发 / 不安装直接跑）

仓库自带 launcher，git 工作树下不需要 `pip install`：

```bash
./aik --help
./codex-session-toolkit --help
./cc-clean --help
```

或用 `python -m`：

```bash
python -m ai_cli_kit              # 顶层菜单
python -m ai_cli_kit.codex        # Codex 子工具
python -m ai_cli_kit.claude       # Claude 子工具
```

## 制作发布包

```bash
./release.sh
# 输出 dist/releases/ai-cli-kit-<version>.tar.gz / .zip
```

对方解压后跑 `./install.sh`（macOS / Linux）或 `install.bat`（Windows）即可。

## 工程命令

```bash
make help          # 看所有 target
make bootstrap     # 等价 ./install.sh
make test          # 跑全部单测（需 PYTHONPATH=src）
make check         # compile + test + launcher smoke
make release       # 等价 ./release.sh
```

---

<div align="center">

**学 AI，上 L 站**

[![LINUX DO](https://img.shields.io/badge/LINUX%20DO-社区-gray?style=flat-square)](https://linux.do/)

本项目在 [LINUX DO](https://linux.do/) 社区发布与交流。

</div>

## 许可证

MIT License
