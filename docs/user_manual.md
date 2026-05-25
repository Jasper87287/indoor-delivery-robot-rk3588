# 用户手册

## 1. 简介

本手册适用于室内智能配送机器人，帮助用户完成从硬件连接、系统启动到运行配送任务的全过程。

### 1.1 系统组成

| 部件 | 说明 |
|------|------|
| 主控平台 | 瑞芯微 RK3588 开发板 |
| 机器人底盘 | 四轮麦克纳姆轮底盘（含编码电机） |
| 传感器 | 激光雷达、IMU、USB 摄像头 |
| 电源 | 12V 锂电池组 |

### 1.2 技术参数

| 参数 | 值 |
|------|-----|
| 尺寸 | 300×260×120 mm |
| 最大速度 | 0.5 m/s |
| 最大负载 | 2 kg |
| 续航时间 | 约 60 分钟 |
| 定位精度 | ±5 cm（目标） |

## 2. 硬件连接

### 2.1 串口调试连接

| USB 转 TTL 模块 | 小车拓展板（40Pin） |
|----------------|---------------------|
| TX | 引脚 11（RTT RX） |
| RX | 引脚 15（RTT TX） |
| GND | 引脚 9（GND） |

> 波特率：1500000，8N1

### 2.2 电源连接

- 电池 12V 输出接电机驱动板电源输入
- 驱动板 5V 输出接 RK3588 Type-C 供电口（或通过降压模块）

## 3. 软件启动流程

### 3.1 小车端启动

1. **SSH 登录 Linux**（电脑连接小车热点或同一路由器）：
   ```bash
   ssh rock@<小车IP>
密码：rock

启动 micro-ROS agent：

```
cd ~/Desktop/rock_ws/microros_ws
source install/setup.bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```
保持终端运行。

通过串口进入 RT-Thread（使用 MobaXterm，波特率 1500000）：

连接后按回车，出现 msh />

执行：

```
microros_chassis udp 10.10.10.31 8888
```
（等待 Connect successful!）

再执行：

```
chassis_car_app
```
（可选）启动假里程计（如果编码器未修复）：

```
python3 ~/robot_scripts/fake_odom.py
```
3.2 上位机启动（开发电脑）
安装依赖：

```
pip install flask flask-socketio eventlet
```
启动 Web 界面：

```
cd robot_web
python app.py
浏览器访问 http://localhost:5000
```

## 4. 操作说明
### 4.1 Web 界面功能
|控件	|功能|
|------|------|
|地图区域	|显示小车位置（蓝色圆点）|
|当前位置|	显示 x, y, θ|
|目标点输入框	|输入目标坐标（米）|
|导航按钮	|发送目标点，小车自动导航|
|急停按钮|	立即停止所有运动|

### 4.2 手动控制（SSH 终端）
# 前进 0.2 m/s
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.2}}" --once

# 停止
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0}}" --once
## 5. 常见问题
|问题|	解决方法|
|------|------|
|无法 SSH 登录|	检查小车 IP 是否正确，网络是否通畅|
|microros_chassis 连接失败|	尝试 IP 10.10.10.30 或 10.10.10.1；用 ifconfig 查看 vnet0 IP|
|小车不响应指令	|确认 chassis_car_app 已运行，agent 终端无报错|
|Web 界面无法连接 rosbridge	|检查小车 rosbridge 是否运行：ros2 run rosbridge_server rosbridge_websocket_launch.xml|

## 6. 维护
电池：每次使用后充满电存放

麦克纳姆轮：定期清理小轮中的杂物

激光雷达：用软布擦拭光学窗口

## 7. 获取帮助
竞赛 QQ 群：838028162

GitHub 仓库：https://github.com/Jasper87287/indoor-delivery-robot-rk3588

文档维护人：赵文杰
最后更新：2026年5月
