import os
import json
from flask import Flask, render_template_string, request, Response
import requests

app = Flask(__name__)

# ================= 环境变量导入 =================
# 从系统环境变量读取 API Key 和模型
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# 默认使用 z-ai/glm-5.2，如遇 404 可在终端修改环境变量为 "meta/llama-3.1-8b-instruct"
MODEL_NAME = os.getenv("NVIDIA_MODEL_NAME", "z-ai/glm-5.2")
# ===============================================

if not NVIDIA_API_KEY:
    print("\n" + "="*20)
    print("⚠️  警告: 未检测到环境变量 NVIDIA_API_KEY！")
    print("请在终端运行: export NVIDIA_API_KEY=\"您的密钥\" 后再启动此服务。")
    print("="*20 + "\n")

# 针对 Kindle 墨水屏和旧版 WebKit 优化的极简交互页面（无刷新，纯原生 AJAX）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kindle AI Realtime Chat</title>
    <!-- 引入服务端本地/备用 marked.js（确保旧版 Kindle 支持 ES5） -->
    <script type="text/javascript" src="/marked.min.js"></script>
    <style>
        body {
            font-family: Georgia, serif;
            background-color: #ffffff;
            color: #000000;
            margin: 10px;
            padding: 0;
            font-size: 16px;
            line-height: 1.4;
        }
        .container {
            max-width: 100%;
        }
        h1 {
            font-size: 20px;
            border-bottom: 2px solid #000000;
            padding-bottom: 5px;
            margin-top: 0;
        }
        .chat-box {
            padding: 8px;
            margin-bottom: 15px;
            background-color: #ffffff;
            min-height: 150px;
        }
        .message {
            margin-bottom: 12px;
            border-bottom: 1px dashed #cccccc;
            padding-bottom: 8px;
        }
        .role-user {
            font-weight: bold;
        }
        .role-assistant {
            margin-left: 5px;
        }
        
        /* ================= 针对水墨屏适配的 Markdown 样式 ================= */
        .role-assistant h1, .role-assistant h2, .role-assistant h3, 
        .role-assistant h4, .role-assistant h5, .role-assistant h6 {
            margin: 10px 0 5px 0;
            font-size: 1.1em;
            font-weight: bold;
            border-bottom: 1px solid #000000;
            padding-bottom: 2px;
        }
        .role-assistant p {
            margin: 6px 0;
        }
        .role-assistant ul, .role-assistant ol {
            margin: 5px 0;
            padding-left: 20px;
        }
        .role-assistant li {
            margin-bottom: 3px;
        }
        .role-assistant code {
            font-family: "Courier New", Courier, monospace;
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 1px 4px;
            font-size: 14px;
        }
        .role-assistant pre {
            background-color: #ffffff;
            border: 1px solid #000000;
            padding: 8px;
            margin: 10px 0;
            overflow-x: auto;
            white-space: pre-wrap; /* 强制换行，防止在墨水屏上出现横向滚动条 */
            word-wrap: break-word;
        }
        .role-assistant pre code {
            background-color: transparent;
            border: none;
            padding: 0;
            font-size: 14px;
            display: block;
        }
        .role-assistant blockquote {
            border-left: 3px solid #000000;
            margin: 8px 0 8px 10px;
            padding-left: 10px;
            color: #333333;
            font-style: italic;
        }
        .role-assistant table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        .role-assistant th, .role-assistant td {
            border: 1px solid #000000;
            padding: 5px;
            text-align: left;
            font-size: 14px;
        }
        .role-assistant th {
            background-color: #f0f0f0; /* 轻微灰色背景，高对比度 */
        }
        .role-assistant strong {
            font-weight: bold;
        }
        .role-assistant em {
            font-style: italic;
        }
        .role-assistant a {
            color: #000000;
            text-decoration: underline;
        }
        .role-assistant img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 5px 0;
        }
        /* ================================================================= */

        .input-area textarea {
            width: 100%;
            height: 80px;
            font-size: 16px;
            border: 2px solid #000000;
            padding: 5px;
            box-sizing: border-box;
        }
        .btn {
            display: block;
            width: 100%;
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #000000;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 8px;
            cursor: pointer;
            box-sizing: border-box;
        }
        .btn-clear {
            background-color: #ffffff;
            color: #000000;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Kindle Realtime Chat</h1>
        
        <!-- 消息承载区 -->
        <div class="chat-box" id="chat-box">
            <p id="empty-hint" style="color: #666666; font-style: italic;">暂无对话，开始输入吧...</p>
        </div>
        
        <!-- 拦截表单默认提交，改用 JS 手动处理 -->
        <form class="input-area" id="chat-form" onsubmit="sendMessage(); return false;">
            <textarea id="user_input" placeholder="输入您的问题。按【回车键】发送，按【Shift+回车】换行..." required></textarea>
            <button type="submit" class="btn" id="send-btn">发 送</button>
        </form>
        
        <button type="button" class="btn btn-clear" onclick="clearChat()">清空对话</button>
        
        <!-- 底部定位辅助锚点 -->
        <div id="bottom" style="height: 20px;"></div>
    </div>

    <!-- 高兼容性 ES5 脚本（确保旧款 Kindle Webkit 不报错） -->
    <script type="text/javascript">
        // 存储本地对话历史 (格式同 OpenAI: {role, content})
        var chatHistory = [];

        // 添加消息到页面的公用函数
        function appendMessage(role, initialContent) {
            var chatBox = document.getElementById('chat-box');
            
            // 首次发送时隐藏“暂无对话”提示
            var hint = document.getElementById('empty-hint');
            if (hint) {
                hint.parentNode.removeChild(hint);
            }

            var msgDiv = document.createElement('div');
            msgDiv.className = 'message';
            
            var roleSpan = document.createElement('span');
            roleSpan.className = 'role-user';
            roleSpan.innerHTML = (role === 'user' ? '【我】' : '【AI】');
            msgDiv.appendChild(roleSpan);
            
            var contentDiv = document.createElement('div');
            contentDiv.className = 'role-assistant';
            
            // 如果存在 marked，则尝试使用其渲染初始消息（如用户发送的内容）
            if (window.marked) {
                contentDiv.innerHTML = window.marked(initialContent);
            } else {
                contentDiv.innerHTML = initialContent;
            }
            msgDiv.appendChild(contentDiv);
            
            chatBox.appendChild(msgDiv);
            
            return contentDiv; // 返回此 DIV 的引用以便后续更新流数据
        }

        // 发送消息核心逻辑
        function sendMessage() {
            var input = document.getElementById('user_input');
            var sendBtn = document.getElementById('send-btn');
            var text = input.value.trim();
            if (!text) return;
            
            // 禁用输入和发送按钮，防止重复提交
            input.disabled = true;
            sendBtn.disabled = true;
            input.value = '';

            // 1. 将用户提问追加至历史记录并上屏
            chatHistory.push({ role: 'user', content: text });
            appendMessage('user', text);
            
            // 2. 预备 AI 的消息容器
            var aiContentDiv = appendMessage('assistant', '思考中...');
            
            // 3. 建立传统的 XMLHttpRequest (兼容旧设备的最稳妥流式读取方案)
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/chat', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            xhr.onreadystatechange = function() {
                // readyState 3 代表正在接收响应体（分块到达），readyState 4 代表请求结束
                if (xhr.readyState === 3 || xhr.readyState === 4) {
                    try {
                        var responseText = xhr.responseText;
                        if (responseText) {
                            // 使用 marked 解析累计流文本并实时更新，避免拆分标记出现语法截断
                            if (window.marked) {
                                aiContentDiv.innerHTML = window.marked(responseText);
                            } else {
                                aiContentDiv.innerHTML = responseText;
                            }
                        }
                    } catch (e) {
                        // 在极少数极老旧浏览器中，readyState 3 时访问 responseText 会报错
                        // 此时捕获异常，静默等待 readyState 4 完成
                    }
                }
                
                // 请求完全结束
                if (xhr.readyState === 4) {
                    input.disabled = false;
                    sendBtn.disabled = false;
                    
                    if (xhr.status === 200) {
                        // 将 AI 最终的完整回答保存至前端历史记录中
                        chatHistory.push({ role: 'assistant', content: xhr.responseText });
                    } else {
                        aiContentDiv.innerHTML = '【出错了】无法获取响应：' + xhr.responseText;
                    }
                }
            };
            
            // 将包含上下文的历史记录发送给后端
            xhr.send(JSON.stringify({ history: chatHistory }));
        }

        // 清空对话
        function clearChat() {
            chatHistory = [];
            document.getElementById('chat-box').innerHTML = '<p id="empty-hint" style="color: #666666; font-style: italic;">暂无对话，开始输入吧...</p>';
            window.scrollTo(0, 0);
        }

        // 回车发送，Shift+回车换行的逻辑
        var textarea = document.getElementById('user_input');
        if (textarea) {
            textarea.addEventListener('keydown', function(event) {
                var isEnter = (event.key === 'Enter' || event.keyCode === 13);
                if (isEnter && !event.shiftKey) {
                    event.preventDefault(); // 阻止 textarea 默认的换行
                    sendMessage();
                }
            });
        }
    </script>
</body>
</html>
"""

# 预加载/下载 ES5 版本的 marked.js 依赖，保障局域网无外网环境正常工作
def download_marked_js():
    local_path = "marked.min.js"
    if not os.path.exists(local_path):
        try:
            print("正在尝试预下载 ES5 兼容的 marked.min.js...")
            url = "https://cdn.jsdelivr.net/npm/marked@0.8.0/marked.min.js"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                print("成功保存 marked.min.js 到本地。")
        except Exception as e:
            print(f"预下载 marked.min.js 失败（可能处于离线局域网环境）: {e}")

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

# 静态资源请求接口，提供本地缓存或轻量降级 Markdown 编译
@app.route("/marked.min.js")
def get_marked():
    local_path = "marked.min.js"
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="application/javascript")
    else:
        # 兜底降级方案：若局域网离线且无本地文件，输出一个极简版的纯 ES5 正则 Markdown 编译器
        # 覆盖基础的标题、加粗、斜体、引用、单行/多行代码解析，不引入任何 ES6 特性
        fallback_js = """
        window.marked = function(text) {
            if (!text) return "";
            var escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            escaped = escaped.replace(/\\*\\*(.*?)\\*\\*/g, "<strong>$1</strong>");
            escaped = escaped.replace(/\\*(.*?)\\*/g, "<em>$1</em>");
            var lines = escaped.split('\\n');
            var inCode = false;
            var result = [];
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (line.indexOf('```') === 0) {
                    if (inCode) {
                        result.push('</code></pre>');
                        inCode = false;
                    } else {
                        result.push('<pre><code>');
                        inCode = true;
                    }
                } else {
                    if (inCode) {
                        result.push(line);
                    } else {
                        if (line.indexOf('### ') === 0) {
                            result.push('<h3>' + line.substring(4) + '</h3>');
                        } else if (line.indexOf('## ') === 0) {
                            result.push('<h2>' + line.substring(3) + '</h2>');
                        } else if (line.indexOf('# ') === 0) {
                            result.push('<h1>' + line.substring(2) + '</h1>');
                        } else if (line.indexOf('> ') === 0) {
                            result.push('<blockquote>' + line.substring(2) + '</blockquote>');
                        } else {
                            result.push(line.replace(/`(.*?)`/g, "<code>$1</code>") + '<br>');
                        }
                    }
                }
            }
            return result.join('\\n');
        };
        """
        return Response(fallback_js, mimetype="application/javascript")

@app.route("/chat", methods=["POST"])
def chat():
    # 接收来自前端 JS 的全量历史对话
    data = request.json or {}
    history = data.get("history", [])
    
    if not NVIDIA_API_KEY:
        return "错误: 树莓派服务端未检测到 NVIDIA_API_KEY。请在终端执行 'export NVIDIA_API_KEY=...' 后重启服务。", 500
        
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": history,
        "temperature": 1,
        "max_tokens": 16384,
        "stream": True # 启用英伟达 API 端流式传输
    }
    
    # 使用生成器将数据一块块实时吐给前端
    def generate():
        try:
            # stream=True 允许分块读取响应
            response = requests.post(NVIDIA_BASE_URL, json=payload, headers=headers, timeout=60, stream=True)
            if response.status_code != 200:
                err_api_msg = f"API Error: {response.status_code} - {response.text}"
                yield err_api_msg.encode('utf-8')
                return
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data:"):
                        data_content = decoded_line[5:].strip()
                        if data_content == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_content)
                            delta = chunk_json["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"].encode('utf-8')
                        except Exception:
                            pass
        except Exception as e:
            err_conn_msg = f"Connection Error: {str(e)}"
            yield err_conn_msg.encode('utf-8')
            
    return Response(generate(), mimetype="text/plain")

if __name__ == "__main__":
    download_marked_js()  # 启动时执行一次 marked.js 本地化下载
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)