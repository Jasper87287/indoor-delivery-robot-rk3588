# serial_sender.py

import serial
import threading
import time
import struct
from protocol import (
    pack_velocity_command, unpack_status_report,
    FRAME_HEADER, CMD_REPORT_STATUS
)

# 配置虚拟串口（Windows示例，Linux改成 /dev/pts/3）
PORT = 'COM10'
BAUDRATE = 115200


class RobotCommunicator:
    def __init__(self, port=PORT, baudrate=BAUDRATE):
        self.ser = serial.Serial(port, baudrate, timeout=0.1)
        self.latest_status = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # x,y,theta,vx,vy,omega
        self.running = True
        self.lock = threading.Lock()

        # 启动接收线程
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()
        print(f"[Linux 通信模块] 已打开 {port}")

    def _recv_loop(self):
        """后台接收状态帧"""
        buffer = bytearray()
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    buffer.extend(data)
                    # 状态帧长度固定为 28 字节
                    while len(buffer) >= 28:
                        if buffer[0] == FRAME_HEADER and buffer[2] == CMD_REPORT_STATUS:
                            try:
                                status = unpack_status_report(buffer[:28])
                                with self.lock:
                                    self.latest_status = status
                                # print(f"[Linux] 收到状态: {status[:3]}")  # 太多打印可注释
                                buffer = buffer[28:]
                            except ValueError:
                                buffer.pop(0)
                        else:
                            buffer.pop(0)
                else:
                    time.sleep(0.005)
            except Exception as e:
                print(f"[Linux] 接收线程异常: {e}")
                break

    def send_velocity(self, vx, vy, omega):
        """发送速度指令"""
        frame = pack_velocity_command(vx, vy, omega)
        self.ser.write(frame)
        print(f"[Linux] 发送速度: vx={vx:.3f}, vy={vy:.3f}, omega={omega:.3f}")

    def get_status(self):
        """获取最新状态（线程安全）"""
        with self.lock:
            return self.latest_status

    def close(self):
        self.running = False
        self.recv_thread.join(timeout=1)
        self.ser.close()


# 简单测试：连续发送几个速度指令，并打印收到的状态
if __name__ == '__main__':
    comm = RobotCommunicator()
    try:
        # 先发送前进指令 0.2 m/s
        comm.send_velocity(0.2, 0.0, 0.0)
        time.sleep(1)
        # 发送旋转指令
        comm.send_velocity(0.0, 0.0, 0.5)
        time.sleep(2)
        # 停止
        comm.send_velocity(0.0, 0.0, 0.0)
        time.sleep(0.5)

        # 打印最终状态
        x, y, theta, vx, vy, omega = comm.get_status()
        print(f"最终状态: 位置=({x:.3f}, {y:.3f}), 朝向={theta:.2f} rad")
    finally:
        comm.close()
