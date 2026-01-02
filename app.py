import threading, serial, time, json, csv, io, math
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response


SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

app = Flask(__name__)

SYSTEM_MODE = "IDLE" 
telemetry = { 
    "ax":0.0, "ay":0.0, "az":0.0, 
    "pitch":0.0, "roll":0.0, "yaw":0.0, 
    "height":0.0, "lat":12.9716, "long":77.5946, 
    "status":"STANDBY" 
}
flight_log = []

sim_state = {
    "lat": 12.9716, "long": 77.5946, "alt": 0.0,
    "vx": 0.0, "vy": 0.0, "vz": 0.0
}
sim_inputs = { "ax":0.0, "ay":0.0, "az":0.0, "pitch":0.0, "roll":0.0, "yaw":0.0 }


def serial_worker():
    global telemetry, flight_log
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ VoyagerX Hardware Connected on {SERIAL_PORT}")
        telemetry["status"] = "LIVE FEED ACTIVE"
        
        while SYSTEM_MODE == "LIVE":
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    parts = line.split(',')
                    if len(parts) >= 9:
                        data = {
                            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                            "ax": float(parts[0]), "ay": float(parts[1]), "az": float(parts[2]),
                            "pitch": float(parts[3]), "roll": float(parts[4]), "yaw": float(parts[5]),
                            "height": float(parts[6]), "lat": float(parts[7]), "long": float(parts[8])
                        }
                        telemetry.update(data)
                        telemetry["status"] = "LIVE FEED ACTIVE"
                        flight_log.append(data)
                except: pass
            time.sleep(0.005)
    except:
        telemetry["status"] = "HARDWARE DISCONNECTED"
        print("❌ Serial Connection Failed")


def simulation_worker():
    global telemetry, flight_log, sim_state
    print("🎮 VoyagerX Physics Engine Started")
    telemetry["status"] = "SIMULATION ACTIVE"
    
    last_time = time.time()
    
    while SYSTEM_MODE == "SIMULATION":
        now = time.time()
        dt = now - last_time
        last_time = now
        if dt > 0.1: dt = 0.05 
        sim_state["vx"] += sim_inputs['ax'] * 9.8 * dt
        sim_state["vy"] += sim_inputs['ay'] * 9.8 * dt
        sim_state["vz"] += sim_inputs['az'] * 9.8 * dt
    
        sim_state["vx"] *= 0.99
        sim_state["vy"] *= 0.99
        if sim_inputs['az'] <= 0 and sim_state["alt"] > 0:
             sim_state["vz"] -= 9.8 * dt 
        
       
        sim_state["alt"] += sim_state["vz"] * dt
        if sim_state["alt"] < 0: 
            sim_state["alt"] = 0
            sim_state["vz"] = 0
            sim_state["vx"] = 0
            sim_state["vy"] = 0

        sim_state["lat"] += (sim_state["vy"] * dt) / 111000.0
        sim_state["long"] += (sim_state["vx"] * dt) / (111000.0 * math.cos(math.radians(sim_state["lat"])))

        data = {
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "ax": sim_inputs['ax'], "ay": sim_inputs['ay'], "az": sim_inputs['az'],
            "pitch": sim_inputs['pitch'], "roll": sim_inputs['roll'], "yaw": sim_inputs['yaw'],
            "height": sim_state["alt"], 
            "lat": sim_state["lat"], "long": sim_state["long"]
        }
        telemetry.update(data)
        telemetry["status"] = "SIMULATION ACTIVE"
        flight_log.append(data)
        
        time.sleep(0.05) 

@app.route('/')
def landing(): return render_template('landing.html')
@app.route('/visualizer')
def visualizer(): return render_template('visualizer.html')
@app.route('/analytics')
def analytics(): return render_template('analytics.html')

@app.route('/api/start/<mode>')
def start_system(mode):
    global SYSTEM_MODE, flight_log, sim_state
    SYSTEM_MODE = mode.upper()
    flight_log = []
    

    sim_state = {"lat": 12.9716, "long": 77.5946, "alt": 0.0, "vx": 0, "vy": 0, "vz": 0}
    
    if SYSTEM_MODE == "LIVE": 
        threading.Thread(target=serial_worker, daemon=True).start()
    elif SYSTEM_MODE == "SIMULATION": 
        threading.Thread(target=simulation_worker, daemon=True).start()
        
    return jsonify({"status": "STARTED"})

@app.route('/api/data')
def get_data(): return jsonify(telemetry)

@app.route('/api/control', methods=['POST'])
def update_control():
    sim_inputs.update(request.json)
    return jsonify({"status": "OK"})

@app.route('/api/export_csv')
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Lat', 'Long', 'AX', 'AY', 'AZ', 'Height', 'Yaw', 'Roll', 'Pitch'])
    for row in flight_log:
        writer.writerow([row.get('time'), row['lat'], row['long'], row['ax'], row['ay'], row['az'], row['height'], row['yaw'], row['roll'], row['pitch']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=voyager_log.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)