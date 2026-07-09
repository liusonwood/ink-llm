# Kindle LLM Chat

> 在 Kindle 墨水屏上流畅使用 AI 大模型实时聊天

专为 **Kindle 电子墨水屏浏览器** 设计的轻量级 AI 聊天应用。部署在树莓派上，通过局域网访问，让你在护眼的墨水屏上也能享受流式 AI 对话体验。

---

## 为什么为 Kindle 设计？

Kindle 内置浏览器基于老旧 WebKit 内核，仅支持 ES5 语法，无法运行任何现代前端框架。市面上的 AI 聊天界面在 Kindle 上要么完全打不开，要么布局错乱、刷新闪烁严重。

本项目针对 Kindle 水墨屏做了全链路适配：

| 适配点 | 方案 |
|--------|------|
| **浏览器兼容** | 纯 ES5 JavaScript，使用 `XMLHttpRequest` 替代 `fetch`/`Promise` |
| **水墨屏显示** | 纯黑白高对比度 CSS，无渐变色、无动画、无半透明 |
| **减少闪烁** | 禁用所有 CSS transition/animation，避免墨水屏刷新残影 |
| **本地离线** | `marked.js` 预下载到本地，不依赖外部 CDN |
| **单文件部署** | HTML 模板内嵌在 Python 文件中，一个文件启动全栈 |

---

## 特性

- **SSE 流式输出** — AI 回复逐字呈现，无需等待完整响应
- **多模型支持** — 基于 NVIDIA API，可选 GLM、Mistral、Llama 等模型
- **Markdown 渲染** — 支持代码块、表格、引用、列表等富文本格式（水墨屏优化样式）
- **全量上下文** — 对话历史完整保留，AI 应答更连贯
- **极简部署** — 单文件 Flask 应用，树莓派即可运行
- **键位优化** — 回车发送，Shift+回车换行，适配 Kindle 软键盘

---

## 快速开始

### 环境要求

- Python 3.7+
- 树莓派（或其他 Linux 主机）
- NVIDIA API Key（[免费申请](https://build.nvidia.com/explore/discover)）

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/liusonwood/kindle-llm-chat.git
cd kindle-llm-chat

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install flask requests

# 4. 设置 API Key
export NVIDIA_API_KEY="nvapi-你的密钥"

# 5. 可选：指定模型（默认为 z-ai/glm-5.2）
export NVIDIA_MODEL_NAME="mistralai/mistral-small-4-119b-2603"
```

### 启动

```bash
python app.py
```

服务默认运行在 `http://0.0.0.0:5000`。

在 Kindle 浏览器地址栏输入 `http://树莓派IP:5000` 即可访问。

### 后台运行（生产环境）

```bash
nohup ./start.sh > output.log 2>&1 &
```

停止服务：

```bash
pkill -f app.py
```

---

## 项目结构

```
kindle-llm-chat/
├── app.py           # Flask 主程序（含内嵌 HTML/CSS/JS）
├── marked.min.js    # Markdown 解析库（ES5 兼容版 v0.8.0）
├── start.sh         # 启动脚本
├── README.md
└── LICENSE
```

---

## 支持模型

通过 `NVIDIA_MODEL_NAME` 环境变量切换，可选模型包括：

- `z-ai/glm-5.2`（默认，中文优秀）
- `mistralai/mistral-small-4-119b-2603`
- `meta/llama-3.1-8b-instruct`
- `qwen/qwen-2.5-7b-instruct`
- `deepseek-ai/deepseek-r1`

更多模型见 [NVIDIA API 目录](https://build.nvidia.com/explore/discover)。

---

## 关于墨水屏

Kindle 墨水屏的优势在于无蓝光、类纸阅读体验，但 Web 页面设计需遵循以下原则：

1. 纯黑白配色，避免灰色在 E-Ink 上辨识度低
2. 禁止动画和过渡效果，减少屏幕刷新
3. 加大字体和对比度，补偿墨水屏响应速度
4. 避免横向滚动条，E-Ink 拖拽体验较差

本项目全部遵循上述原则，你在代码中看到的每一行 CSS 都经过 Kindle 实机测试。

---

## License

MIT © 2026 [liusonwood](https://github.com/liusonwood)
