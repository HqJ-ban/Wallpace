# Wallpace — Codex 会话启动指令模板

## 📋 每次新会话的「第一句话」

把这个整段粘贴给任何新 Codex 会话，它就会立刻进入开发状态：

---

```
我想继续开发 D:\my_project\Desktop_wallpaper 下的 Wallpace 项目（一个用 Python + PySide6 编写的 Windows 桌面壁纸自动切换工具）。

请先按以下顺序读取项目文件来建立上下文：
1. README.md — 了解项目概况和功能清单
2. .codex/context.md — 当前开发进度和待办清单（核心参考）
3. docs/api-design.md — 所有核心类的接口定义（实现模块前必读）
4. docs/implementation-plan.md — 完整开发计划和时间线
5. docs/architecture.md — 系统架构和模块职责

阅读完成后，请告诉我：
- 项目当前进展到哪一步了
- 下一步建议做什么
- 是否有任何需要我确认的设计决策
```

---

## 🔗 文档速查表（Codex 会自动读取这些文件）

| 在 Codex 中引用 | 对应本地路径 | 用途 |
|----------------|-------------|------|
| `context.md` | `.codex/context.md` | **会话上下文（最重要）** |
| `api-design.md` | `docs/api-design.md` | API 接口定义 |
| `implementation-plan.md` | `docs/implementation-plan.md` | 开发计划 |
| `architecture.md` | `docs/architecture.md` | 架构图与模块职责 |
| `dev-standards.md` | `docs/dev-standards.md` | 编码规范 |

---

## 💡 使用技巧

**开始开发时：** 粘贴上面的引导语 + `"先从 Phase 1.5 开始"`

**继续上次工作：** 粘贴引导语 + `"读 dev-log 最新的记录，从最后未完成的任务接着做"`

**修复 bug：** 粘贴引导语 + `"帮我调试 [具体错误信息]"`

**实现新功能：** 粘贴引导语 + `"我想新增 [功能描述]，先设计方案再写代码"`
