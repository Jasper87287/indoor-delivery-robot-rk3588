# 团队接口约定 (Interface Agreement)

本文档定义室内智能配送机器人项目中，各模块之间的软件接口，确保团队成员（张：电机控制，龙：路径规划，赵：通信与界面）能独立开发并正确对接。

---

## 一、系统架构与职责

```
┌─────────────────┐     串口/UART      ┌─────────────────┐
│   RK3588 Linux  │ ◄──────────────► │  RT-Thread 实时核 │
│   (大脑)         │   Protocol v1.0   │  (小脑)          │
├─────────────────┤                   ├─────────────────┤
│ 龙: 路径规划      │                   │ 张: 电机控制      │
│   调用 send()    │                   │   解析速度指令    │
│   读取 get()     │                   │   回传里程计      │
│ 赵: Flask 界面    │                   │                 │
│   通过 WebSocket │                   │                 │
│   调用 send()    │                   │                 │
└─────────────────┘                   └─────────────────┘
```

- **任务 C（赵文杰）** 负责：
  - Linux 侧串口通信模块 `serial_sender.py`
  - Flask Web 控制台（提供手动控制、状态显示）
  - 将 B 的规划结果转为速度指令发给串口
  - 从串口接收里程计数据提供给 B 和界面
- **任务 A（张明辉）** 负责：
  - RT-Thread 侧串口接收与发送，解析/组包协议
  - 电机 PID 控制，里程计推算
- **任务 B（龙俊荣）** 负责：
  - 路径规划算法，输出目标点或连续速度指令
  - 调用 C 提供的接口驱动底盘

---

## 二、Linux 侧 Python 接口（供 B 使用）

### 文件位置
`/linux/comm/serial_sender.py` （类 `RobotCommunicator`）

### 初始化

```python
from serial_sender import RobotCommunicator

# 板子上使用真实串口，如 /dev/ttyS0 或 /dev/rpmsg0
# 模拟测试时用 COM10（Windows）或 /dev/pts/2（Linux）
comm = RobotCommunicator(port='/dev/ttyS0', baudrate=115200)
```

### 发送速度指令

```python
def send_velocity(vx: float, vy: float, omega: float) -> None:
    """
    向底盘发送速度指令。

    参数:
        vx:   前进线速度 (m/s)，向前为正
        vy:   横向线速度 (m/s)，向左为正
        omega: 自转角速度 (rad/s)，逆时针为正
    """
```

**示例**：让小车以 0.2 m/s 前进的同时左转

```python
comm.send_velocity(0.2, 0.0, 0.5)
```

### 获取里程计状态

```python
def get_status() -> tuple:
    """
    获取最新里程计数据。

    返回:
        (x, y, theta, vx, vy, omega) 六元组
        x, y:     世界坐标系位移 (m)
        theta:    朝向角 (rad)，范围 (-π, π]
        vx, vy, omega: 当前速度 (m/s, m/s, rad/s)
    """
```

**示例**：B 同学的规划节点定时获取状态

```python
x, y, theta, vx, vy, omega = comm.get_status()
# 用这些数据进行闭环控制
```

### 急停

直接发送零速度即可：

```python
comm.send_velocity(0.0, 0.0, 0.0)
```

或使用协议中的急停指令（帧 `AA 00 03`），Linux 侧可扩展 `comm.emergency_stop()` 函数。

### 关闭通信

```python
comm.close()
```

---

## 三、RT-Thread 侧要求实现的接口（供 A 实现）

### 3.1 串口接收 & 速度指令解析

A 同学需要在 RT-Thread 端完成：

1. **串口初始化**：波特率 115200, 8N1
2. **接收中断**：逐字节接收，实现帧同步（找帧头 `0xAA`）
3. **解析速度指令**（指令类型 `0x01`）：
   - 校验通过后提取 `vx, vy, omega`（float 小端）
   - 将这三个值存入**全局共享变量**，供电机控制线程使用
4. **异常处理**：
   - 校验失败丢弃该帧
   - 超过 3 秒未收到 Linux 指令，自动将共享变量置零（安全停车）

### 3.2 里程计回传

A 同学需要定时（建议周期 **100ms**）回传状态帧（指令类型 `0x02`）：

- 从电机编码器或IMU获取当前位姿和速度
- 按协议组帧发送（28字节）
- 数据字段：`x, y, theta, vx, vy, omega`（均为 float 小端）

**参考回调函数原型**（伪代码）：

```c
void timer_callback(void) {
    struct odometry odom = get_odometry();
    uint8_t frame[28];
    pack_status_report(frame, odom.x, odom.y, odom.theta,
                       odom.vx, odom.vy, odom.omega);
    uart_send(fd, frame, 28);
}
```

### 3.3 电机控制接口

A 同学暴露给外部（C 同学的速度指令共享变量）的接口应为：

```c
void set_speed(float vx, float vy, float omega);  // 更新共享变量
void motor_control_thread();                       // PID 控制循环，读取共享变量
```

**注意**：麦克纳姆轮解算（将车体速度映射到四个轮速）由 A 同学在 `motor_control_thread` 中完成。

---

## 四、Web UI 与后端交互接口

Web 前端通过 HTTP + WebSocket 与 Flask 后端通信，供手动控制和监控使用。

### 4.1 静态页面

- URL: `http://<ip>:5000/`
- 功能：显示控制按钮、小车状态

### 4.2 获取状态 (HTTP GET)

- 路由: `/get_status`
- 返回 JSON:
  ```json
  {
    "x": 0.12,
    "y": -0.03,
    "theta": 1.57,
    "vx": 0.20,
    "vy": 0.00,
    "omega": 0.00
  }
  ```

### 4.3 发送速度 (WebSocket 事件)

- 事件名: `set_velocity`
- 前端发送数据:
  ```json
  { "vx": 0.2, "vy": 0.0, "omega": 0.0 }
  ```

### 4.4 急停 (WebSocket 事件)

- 事件名: `emergency_stop`
- 无需数据

---

## 五、引用文档

串口通信的详细帧格式、校验规则参见 `docs/communication_protocol.md`。任何修改必须同步更新该文档，并通知各成员。

---

## 六、附录：完整调用示例（B 同学的规划脚本片段）

```python
from serial_sender import RobotCommunicator
import time

comm = RobotCommunicator('/dev/ttyS0')

# 目标点导航示例
target_x, target_y = 1.0, 0.5
while True:
    x, y, theta, vx, vy, w = comm.get_status()
    # 简单比例控制（实际 B 会用更复杂的规划）
    err_x = target_x - x
    err_y = target_y - y
    if abs(err_x) < 0.05 and abs(err_y) < 0.05:
        comm.send_velocity(0, 0, 0)
        print("到达目标点")
        break
    # 计算速度（这里替代 B 的规划输出）
    vx_cmd = max(min(err_x * 0.5, 0.3), -0.3)
    vy_cmd = max(min(err_y * 0.5, 0.3), -0.3)
    comm.send_velocity(vx_cmd, vy_cmd, 0)
    time.sleep(0.1)
```

---

**文档版本**: v1.0  
**创建日期**: 2026-04-25  
**维护人**: 赵文杰（任务C）
```
