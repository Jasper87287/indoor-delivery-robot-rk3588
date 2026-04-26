# UI 可视化界面（赵文杰）

## 目录结构

```
ui/
├── README.md              # 本文件
├── flask_app.py           # Flask 后端主程序
├── templates/
│   └── index.html         # Web 控制台页面（含 Canvas 轨迹绘制）
└── static/                # 静态资源（可选，当前 JS/CSS 内嵌于 HTML）
```

## 功能

- **手动控制**：通过按钮发送前进/后退/左移/右移/旋转/斜向等速度指令
- **急停**：一键发送零速度，紧急停止
- **实时状态显示**：里程计数据（X、Y、θ、Vx、Vy、ω）以 5 Hz 刷新
- **轨迹可视化**：Canvas 画布实时绘制小车位置、朝向和运动轨迹（绿色线条）
- **WebSocket 通信**：前端通过 Socket.IO 与 Flask 后端交互，后端连接串口发送指令至底盘

## 依赖

- Python 3.8+
- Flask
- Flask-SocketIO
- pyserial

安装命令：

```bash
pip install flask flask-socketio pyserial
```

## 快速启动

### 1. 确保通信模块就绪

`linux/comm/serial_sender.py` 与模拟器（`rtthread_simulator.py` 在项目根目录）需在同一硬件或虚拟串口环境中。

模拟器启动方式（Windows 需先创建虚拟串口对 COM10/COM11）:

```bash
python rtthread_simulator.py
```

### 2. 启动 Flask 服务

在 `ui` 目录下运行：

```bash
cd ui
python flask_app.py
```

服务默认运行在 `http://0.0.0.0:5000`。

### 3. 打开控制台

浏览器访问 `http://localhost:5000` 即可看到控制界面。

> 局域网内其他设备可通过 `http://<本机IP>:5000` 访问，如 `http://10.5.63.132:5000`。

## 界面说明

- **左侧 Canvas**：网格地图，红色圆点代表小车，黑色线段指示车头朝向，绿色轨迹记录历史路径。
- **中间按钮**：方向控制与急停。
- **右侧状态栏**：实时更新当前位置与速度数值。

## 配置说明

如需更改串口号或波特率，可在 `flask_app.py` 中修改 `RobotCommunicator` 的初始化参数：

```python
comm = RobotCommunicator(port='COM10', baudrate=115200)   # 本地模拟
# comm = RobotCommunicator(port='/dev/ttyS0', baudrate=115200)  # 真实板卡
```

Canvas 的缩放比例可在 `index.html` 中调整 `scale` 变量（默认为 100 像素/米）。

## 注意事项

- Flask 以 `debug=False, use_reloader=False` 运行，避免串口被多进程重复打开。
- 真实部署时请关闭开发服务器，改用生产级 WSGI 服务器（如 gunicorn）。
```
