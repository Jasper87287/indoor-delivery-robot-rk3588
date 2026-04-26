# ui/flask_app.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import sys
import os

# 关键修改：加两层父目录，因为 serial_sender.py 在 /linux/ 下
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serial_sender import RobotCommunicator

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化通信模块（暂时连虚拟串口 COM10）
comm = RobotCommunicator(port='COM10')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    x, y, theta, vx, vy, omega = comm.get_status()
    return jsonify({
        'x': round(x, 3),
        'y': round(y, 3),
        'theta': round(theta, 2),
        'vx': round(vx, 3),
        'vy': round(vy, 3),
        'omega': round(omega, 3)
    })

@socketio.on('set_velocity')
def handle_velocity(data):
    vx = float(data.get('vx', 0))
    vy = float(data.get('vy', 0))
    omega = float(data.get('omega', 0))
    comm.send_velocity(vx, vy, omega)

@socketio.on('emergency_stop')
def handle_stop():
    comm.send_velocity(0.0, 0.0, 0.0)
    print("[UI] 急停！")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
