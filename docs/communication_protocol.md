# 串口通信协议（Linux ↔ RT-Thread）

## 物理层
- 接口：UART 串口
- 波特率：115200
- 数据位：8
- 停止位：1
- 校验位：无

## 帧格式

| 偏移 | 长度 | 类型 | 说明 |
|:---|:---|:---|:---|
| 0 | 1 | uint8 | 帧头，固定 0xAA |
| 1 | 1 | uint8 | 数据区长度（不含帧头/长度/指令/校验） |
| 2 | 1 | uint8 | 指令类型 |
| 3~N | 变长 | — | 数据区 |
| N+1 | 1 | uint8 | 校验和（前 N+1 字节累加取低8位） |

---

## 指令 0x01：速度控制（Linux → RT-Thread）

数据区长度：12 字节

| 偏移 | 长度 | 类型 | 说明 |
|:---|:---|:---|:---|
| 0 | 4 | float32 小端 | Vx，线速度 m/s（向前为正） |
| 4 | 4 | float32 小端 | Vy，横向速度 m/s（向左为正） |
| 8 | 4 | float32 小端 | Omega，角速度 rad/s（逆时针为正） |

完整帧（16字节）：`AA 0C 01 [Vx] [Vy] [Omega] [校验]`

---

## 指令 0x02：状态回传（RT-Thread → Linux）

数据区长度：24 字节

| 偏移 | 长度 | 类型 | 说明 |
|:---|:---|:---|:---|
| 0 | 4 | float32 小端 | X 坐标（m） |
| 4 | 4 | float32 小端 | Y 坐标（m） |
| 8 | 4 | float32 小端 | Theta 朝向（rad，世界坐标系） |
| 12 | 4 | float32 小端 | 当前 Vx（m/s） |
| 16 | 4 | float32 小端 | 当前 Vy（m/s） |
| 20 | 4 | float32 小端 | 当前 Omega（rad/s） |

完整帧（28字节）：`AA 18 02 [X] [Y] [Theta] [Vx] [Vy] [Omega] [校验]`

---

## 0x03：急停（Linux → RT-Thread）

数据区长度：0 字节

完整帧（4字节）：`AA 00 03 [校验]`

---

## 校验和计算（Python 示例）

```python
def compute_checksum(data: bytes) -> int:
    return sum(data) & 0xFF
