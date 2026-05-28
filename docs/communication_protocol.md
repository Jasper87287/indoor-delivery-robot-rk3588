# 通信协议（Linux ↔ RT-Thread）

## 物理层
- 方式：Micro-ROS over UDP
- Linux IP：192.168.1.1（热点模式）
- 端口：8888
- 传输层：UDP 数据包

## 应用层话题

### /cmd_vel（Linux → RT-Thread）
- 消息类型：geometry_msgs/msg/Twist
- 频率：由路径规划节点决定（通常 10~50 Hz）
- 字段：
  - linear.x：前进速度 (m/s)
  - linear.y：横向速度 (m/s)
  - angular.z：旋转速度 (rad/s)

### /odom（RT-Thread → Linux）
- 消息类型：nav_msgs/msg/Odometry
- 频率：100 Hz
- 字段：
  - pose.pose.position.x/y：世界坐标 (m)
  - pose.pose.orientation：朝向（四元数）
  - twist.twist.linear.x/y：当前速度 (m/s)
  - twist.twist.angular.z：当前角速度 (rad/s)
