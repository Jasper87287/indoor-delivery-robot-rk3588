# protocol.py
import struct

FRAME_HEADER = 0xAA
CMD_SET_VELOCITY = 0x01  # 速度控制指令
CMD_REPORT_STATUS = 0x02  # 状态回传指令（里程计）


def compute_checksum(data: bytes) -> int:
    """计算累加和校验（低8位）"""
    return sum(data) & 0xFF


def pack_velocity_command(vx: float, vy: float, omega: float) -> bytes:
    """
    打包速度指令帧
    格式: [HEADER(1)][LEN(1)][CMD(1)][vx(4)][vy(4)][omega(4)][CHECKSUM(1)]
    总长度: 1+1+1+12+1 = 16 字节
    """
    payload = struct.pack('<fff', vx, vy, omega)  # 小端浮点数
    length = len(payload)  # 12
    header_and_cmd = bytes([FRAME_HEADER, length, CMD_SET_VELOCITY])
    data = header_and_cmd + payload
    checksum = compute_checksum(data)
    return data + bytes([checksum])


def unpack_velocity_command(frame: bytes) -> tuple:
    """
    解包速度指令，返回 (vx, vy, omega)
    如果校验失败或格式错误，抛出异常
    """
    if len(frame) < 16:
        raise ValueError("帧长度不足")
    if frame[0] != FRAME_HEADER:
        raise ValueError("帧头错误")
    length = frame[1]
    if length != 12:
        raise ValueError("数据长度错误")
    if frame[2] != CMD_SET_VELOCITY:
        raise ValueError("指令类型错误")

    data = frame[:15]  # 去除校验字节的部分
    received_checksum = frame[15]
    if compute_checksum(data) != received_checksum:
        raise ValueError("校验和错误")

    payload = frame[3:15]
    vx, vy, omega = struct.unpack('<fff', payload)
    return vx, vy, omega


def pack_status_report(x: float, y: float, theta: float,
                       vx: float, vy: float, omega: float) -> bytes:
    """
    打包状态回传帧（里程计 + 当前速度）
    格式: [HEADER(1)][LEN(1)][CMD(1)][x(4)][y(4)][theta(4)][vx(4)][vy(4)][omega(4)][CHECKSUM(1)]
    数据区长度: 6*4 = 24 字节
    """
    payload = struct.pack('<ffffff', x, y, theta, vx, vy, omega)
    length = len(payload)  # 24
    header_and_cmd = bytes([FRAME_HEADER, length, CMD_REPORT_STATUS])
    data = header_and_cmd + payload
    checksum = compute_checksum(data)
    return data + bytes([checksum])


def unpack_status_report(frame: bytes) -> tuple:
    """解包状态帧，返回 (x, y, theta, vx, vy, omega)"""
    if len(frame) < 28:
        raise ValueError("帧长度不足")
    if frame[0] != FRAME_HEADER:
        raise ValueError("帧头错误")
    if frame[1] != 24:
        raise ValueError("数据长度错误")
    if frame[2] != CMD_REPORT_STATUS:
        raise ValueError("指令类型错误")

    data = frame[:27]
    received_checksum = frame[27]
    if compute_checksum(data) != received_checksum:
        raise ValueError("校验和错误")

    payload = frame[3:27]
    x, y, theta, vx, vy, omega = struct.unpack('<ffffff', payload)
    return x, y, theta, vx, vy, omega
