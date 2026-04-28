# rtthread_simulator.py
import serial
import threading
import time
import math
from protocol import (
    FRAME_HEADER, CMD_SET_VELOCITY, CMD_REPORT_STATUS,
    pack_status_report, unpack_velocity_command
)

# 配置虚拟串口（Windows示例，Linux改成 /dev/pts/2）
PORT = 'COM11'
BAUDRATE = 115200

class VirtualRobot:
    """模拟小车运动学（简单的差分模型，实际麦克纳姆轮更复杂，但这里只做模拟）"""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0  # 弧度
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0
        self.last_time = time.time()

    def set_velocity(self, vx, vy, omega):
        self.vx = vx
        self.vy = vy
        self.omega = omega
        print(f"[Robot] 收到速度指令: vx={vx:.3f}, vy={vy:.3f}, omega={omega:.3f}")

    def update_odometry(self):
        """根据当前速度更新位姿"""
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # 简化：世界坐标系下的速度直接积分
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.theta += self.omega * dt
        # 角度归一化到 [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

    def get_status(self):
        self.update_odometry()
        return (self.x, self.y, self.theta, self.vx, self.vy, self.omega)

def serial_read_thread(ser, robot):
    """串口接收线程：解析速度指令"""
    buffer = bytearray()
    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            buffer.extend(data)
            # 简单帧同步：寻找帧头 0xAA
            while len(buffer) >= 16:  # 最小速度指令帧长度
                if buffer[0] == FRAME_HEADER:
                    # 尝试解析
                    try:
                        vx, vy, omega = unpack_velocity_command(buffer[:16])
                        robot.set_velocity(vx, vy, omega)
                        # 解析成功，移除这16字节
                        buffer = buffer[16:]
                    except ValueError as e:
                        # 解析失败，可能是数据错位，丢弃第一个字节继续找帧头
                        print(f"[RT-Thread] 帧解析失败: {e}")
                        buffer.pop(0)
                else:
                    buffer.pop(0)
        else:
            time.sleep(0.001)  # 避免空转

def status_report_thread(ser, robot, interval=0.1):
    """定期回传状态线程"""
    while True:
        x, y, theta, vx, vy, omega = robot.get_status()
        frame = pack_status_report(x, y, theta, vx, vy, omega)
        ser.write(frame)
        print(f"[RT-Thread] 回传状态: x={x:.3f}, y={y:.3f}, theta={theta:.2f}")
        time.sleep(interval)

def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    print(f"[RT-Thread 模拟器] 已打开 {PORT}，等待指令...")
    robot = VirtualRobot()

    # 启动接收线程
    t_recv = threading.Thread(target=serial_read_thread, args=(ser, robot), daemon=True)
    t_recv.start()
    # 启动发送线程
    t_send = threading.Thread(target=status_report_thread, args=(ser, robot, 0.1), daemon=True)
    t_send.start()

    try:
        # 主线程阻塞，直到 Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n模拟器关闭")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
