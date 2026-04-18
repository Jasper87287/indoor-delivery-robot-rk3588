# 系统架构说明

## 1. 整体架构概述

本系统采用 **RT-Thread 虚拟化混合部署** 方案，在单颗瑞芯微 RK3588 芯片上同时运行 Linux 和 RT-Thread 两个操作系统：

- **Linux 侧**（大脑）：负责计算密集型的 AI 任务，包括 SLAM 建图、路径规划、目标检测等
- **RT-Thread 侧**（小脑）：负责高实时性控制任务，包括电机 PID 控制、麦克纳姆轮运动解算、传感器数据采集

两侧通过串口（UART）进行通信，实现决策与执行的协同工作。

## 2. 系统架构图

```mermaid
flowchart TB
    subgraph RK3588[RK3588 开发板]
        subgraph Linux[Linux 侧 - 大脑]
            L1[SLAM 建图]
            L2[路径规划 A*/RRT]
            L3[目标识别 二维码/视觉]
            L4[串口通信 主端]
        end
        subgraph RTThread[RT-Thread 侧 - 小脑]
            R1[电机 PID 控制]
            R2[麦克纳姆轮运动解算]
            R3[IMU/编码器数据采集]
            R4[串口通信 从端]
        end
    end
    
    subgraph Hardware[硬件外设]
        H1[直流电机×4]
        H2[霍尔编码器×4]
        H3[IMU MPU6050]
        H4[激光雷达]
        H5[深度相机]
    end

    L4 <-->|自定义串口协议| R4
    L1 --> L2 --> L3
    L3 --> L4
    R4 --> R1 --> R2
    R2 --> H1
    H2 --> R3
    R3 --> R4
    H4 --> L1
    H5 --> L3

    subgraph UI[上位机]
        Web[Web 界面 / Qt]
    end

    Web <--> L4
