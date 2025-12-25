"""
Web-based UI for client (使用Flask + 浏览器)
"""
from flask import Flask, render_template_string, request, jsonify, send_file
import threading
import webbrowser
import qrcode
from io import BytesIO
import base64


# HTML模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>币安事件合约群控交易系统 - 登录</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 400px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #5568d3;
        }
        .error {
            color: red;
            margin-top: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>币安事件合约群控交易系统</h1>
        <form id="loginForm">
            <div class="form-group">
                <label>用户名:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label>密码:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">登录</button>
            <div id="error" class="error"></div>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = '/main';
                } else {
                    errorDiv.textContent = data.message || '登录失败';
                }
            } catch (error) {
                errorDiv.textContent = '登录失败: ' + error.message;
            }
        });
    </script>
</body>
</html>
"""

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>币安事件合约群控交易系统 - 主界面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .controls {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .log-area {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        button:hover { opacity: 0.8; }
        input[type="number"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            width: 100px;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            margin-left: 10px;
        }
        .status.online { background: #28a745; color: white; }
        .status.offline { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>币安事件合约群控交易系统</h1>
        <p>用户: <span id="username">{{ username }}</span></p>
        <p>币安状态: <span id="binanceStatus" class="status offline">未登录</span></p>
    </div>
    
    <div class="controls">
        <h3>控制面板</h3>
        <div>
            <label>下单金额: </label>
            <input type="number" id="orderAmount" value="5" min="5" max="200" step="1">
            <button class="btn-primary" onclick="setOrderAmount()">设置金额</button>
        </div>
        <div style="margin-top: 10px;">
            <button class="btn-success" id="startBtn" onclick="startOrder()">开始自动下单</button>
            <button class="btn-danger" id="stopBtn" onclick="stopOrder()" disabled>停止自动下单</button>
            <button class="btn-secondary" onclick="logout()">退出登录</button>
        </div>
    </div>
    
    <div class="controls">
        <h3>日志</h3>
        <div id="logArea" class="log-area"></div>
    </div>
    
    <script>
        let orderRunning = false;
        
        function setOrderAmount() {
            const amount = document.getElementById('orderAmount').value;
            fetch('/api/set_order_amount', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount: parseFloat(amount)})
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    addLog('下单金额已设置为: ' + amount);
                }
            });
        }
        
        function startOrder() {
            fetch('/api/start_order', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        orderRunning = true;
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('stopBtn').disabled = false;
                        addLog('自动下单已启动');
                    }
                });
        }
        
        function stopOrder() {
            fetch('/api/stop_order', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        orderRunning = false;
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('stopBtn').disabled = true;
                        addLog('自动下单已停止');
                    }
                });
        }
        
        function logout() {
            fetch('/api/logout', {method: 'POST'})
                .then(() => window.location.href = '/');
        }
        
        function addLog(message) {
            const logArea = document.getElementById('logArea');
            const time = new Date().toLocaleTimeString();
            logArea.innerHTML += `[${time}] ${message}<br>`;
            logArea.scrollTop = logArea.scrollHeight;
        }
        
        // 定期拉取日志
        setInterval(() => {
            fetch('/api/get_logs')
                .then(r => r.json())
                .then(data => {
                    if (data.logs) {
                        data.logs.forEach(log => addLog(log));
                    }
                });
        }, 1000);
    </script>
</body>
</html>
"""


class WebUI:
    """Web-based UI"""
    
    def __init__(self, client_app):
        self.client_app = client_app
        self.app = Flask(__name__)
        self.logs = []
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        @self.app.route('/')
        def login():
            return render_template_string(LOGIN_TEMPLATE)
        
        @self.app.route('/main')
        def main():
            return render_template_string(MAIN_TEMPLATE, username="User")
        
        @self.app.route('/api/login', methods=['POST'])
        def api_login():
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            # TODO: 调用实际的登录逻辑
            # result = self.client_app.auth_service.login(username, password)
            # if result.get('code') == 200:
            #     return jsonify({'success': True})
            # else:
            #     return jsonify({'success': False, 'message': result.get('message')})
            
            # 临时：总是返回成功
            self.add_log(f"登录尝试: {username}")
            return jsonify({'success': True})
        
        @self.app.route('/api/set_order_amount', methods=['POST'])
        def api_set_order_amount():
            data = request.json
            amount = data.get('amount')
            # TODO: 调用实际的设置金额逻辑
            self.add_log(f"设置下单金额: {amount}")
            return jsonify({'success': True})
        
        @self.app.route('/api/start_order', methods=['POST'])
        def api_start_order():
            # TODO: 调用实际的开始下单逻辑
            self.add_log("开始自动下单")
            return jsonify({'success': True})
        
        @self.app.route('/api/stop_order', methods=['POST'])
        def api_stop_order():
            # TODO: 调用实际的停止下单逻辑
            self.add_log("停止自动下单")
            return jsonify({'success': True})
        
        @self.app.route('/api/logout', methods=['POST'])
        def api_logout():
            # TODO: 调用实际的退出登录逻辑
            return jsonify({'success': True})
        
        @self.app.route('/api/get_logs')
        def api_get_logs():
            logs = self.logs.copy()
            self.logs.clear()
            return jsonify({'logs': logs})
    
    def add_log(self, message):
        """添加日志"""
        self.logs.append(message)
        if len(self.logs) > 100:
            self.logs.pop(0)
    
    def run(self, host='127.0.0.1', port=5000):
        """运行Web服务器"""
        url = f'http://{host}:{port}'
        print(f"启动Web界面: {url}")
        
        # 在新线程中打开浏览器
        def open_browser():
            import time
            time.sleep(1)
            webbrowser.open(url)
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        # 运行Flask应用
        self.app.run(host=host, port=port, debug=False, use_reloader=False)

