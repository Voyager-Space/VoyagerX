import graphviz
import os

def render_hardware():
    dot = graphviz.Digraph('Hardware', comment='VoyagerX Hardware Architecture', format='png')
    dot.attr(rankdir='TB', dpi='300', bgcolor='white')
    
    # Styles
    dot.attr('node', shape='box', style='filled', fontname='Arial')
    
    # --- FLIGHT COMPUTER ---
    with dot.subgraph(name='cluster_0') as c:
        c.attr(label='🚀 FLIGHT COMPUTER (AVIONICS)', style='rounded', color='blue', bgcolor='#f0f8ff')
        
        c.node('BAT', 'LiPo Battery\n(7.4V, 500mAh)', fillcolor='#ffcc99')
        c.node('BUCK', 'LM2596 Buck Converter\n(7.4V -> 5.0V)', fillcolor='#ffcc99')
        c.node('ESP_FC', 'ESP32 Dev Kit V1\n(Flight Computer)', fillcolor='#6699ff', fontcolor='white')
        c.node('RADIO_FC', 'NRF24L01+ PA/LNA\n(Transmitter)', fillcolor='#ff99ff')
        
        c.node('MPU', 'MPU9250\n(9-Axis IMU)', fillcolor='#99ff99')
        c.node('BMP', 'BMP280\n(Altimeter)', fillcolor='#99ff99')
        c.node('GPS', 'Ublox Neo-M8N\n(GNSS)', fillcolor='#99ff99')
        
        # Power Connections
        c.edge('BAT', 'BUCK', label='High Current')
        c.edge('BUCK', 'ESP_FC', label='5V Main')
        c.edge('BUCK', 'RADIO_FC', label='5V Clean')
        
        # Data Connections
        c.edge('ESP_FC', 'MPU', label='I2C (SDA/SCL)')
        c.edge('ESP_FC', 'BMP', label='I2C (SDA/SCL)')
        c.edge('ESP_FC', 'GPS', label='UART (TX/RX)')
        c.edge('ESP_FC', 'RADIO_FC', label='SPI (VSPI)')

    # --- GROUND STATION ---
    with dot.subgraph(name='cluster_1') as c:
        c.attr(label='💻 GROUND STATION', style='rounded', color='black', bgcolor='#eeeeee')
        
        c.node('RADIO_GS', 'NRF24L01+ PA/LNA\n(Receiver)', fillcolor='#ff99ff')
        c.node('ESP_GS', 'ESP32 Dev Kit V1\n(Receiver Node)', fillcolor='#6699ff', fontcolor='white')
        c.node('LAPTOP', 'Mission Control Laptop\n(VoyagerX Dashboard)', fillcolor='#cccccc')
        
        c.edge('RADIO_GS', 'ESP_GS', label='SPI')
        c.edge('ESP_GS', 'LAPTOP', label='USB Serial\n(115200 Baud)')

    # Wireless Link
    dot.edge('RADIO_FC', 'RADIO_GS', label='2.4GHz RF Link\n(250kbps Binary Packets)', style='dashed', color='red', penwidth='2.0')

    output_path = dot.render(filename='voyager_hardware', cleanup=True)
    print(f"✅ Hardware Diagram saved to: {output_path}")

def render_firmware():
    dot = graphviz.Digraph('Firmware', comment='VoyagerX Firmware Logic', format='png')
    dot.attr(rankdir='TB', dpi='300')
    dot.attr('node', shape='rect', style='rounded,filled', fillcolor='white', fontname='Arial')

    # Start
    dot.node('START', 'System Boot', shape='oval', fillcolor='#eeeeee')
    dot.node('INIT', 'Hardware Initialization\n(I2C, SPI, UART)')
    dot.node('CALIB', 'Gyro Calibration\n(Hold Still 5s)', fillcolor='#fffacd')
    
    # Fork
    dot.node('FORK', 'FreeRTOS Task Fork', shape='diamond', fillcolor='#ffcc00')

    # Core 0
    with dot.subgraph(name='cluster_core0') as c:
        c.attr(label='CORE 0: The Navigator (GPS)', color='green', bgcolor='#eaffea')
        c.node('C0_LOOP', 'Read Serial Buffer')
        c.node('PARSE', 'Parse NMEA Sentence')
        c.node('LOCK0', '🔒 Lock Mutex')
        c.node('UPDATE', 'Update Shared Coordinates')
        c.node('UNLOCK0', '🔓 Unlock Mutex')
        
        c.edge('C0_LOOP', 'PARSE', label='Data Available')
        c.edge('PARSE', 'LOCK0', label='Valid Fix')
        c.edge('LOCK0', 'UPDATE')
        c.edge('UPDATE', 'UNLOCK0')
        c.edge('UNLOCK0', 'C0_LOOP')

    # Core 1
    with dot.subgraph(name='cluster_core1') as c:
        c.attr(label='CORE 1: The Pilot (Flight Loop)', color='blue', bgcolor='#e6f2ff')
        c.node('C1_LOOP', 'Loop Start (50Hz)')
        c.node('READ_SENSORS', 'Read MPU9250 & BMP280')
        c.node('FUSION', 'Madgwick Filter Calculation')
        c.node('LOCK1', '🔒 Lock Mutex')
        c.node('GET_GPS', 'Read Shared Coordinates')
        c.node('UNLOCK1', '🔓 Unlock Mutex')
        c.node('PACK', 'Pack Binary Struct')
        c.node('SEND', 'Radio Transmit')
        
        c.edge('C1_LOOP', 'READ_SENSORS')
        c.edge('READ_SENSORS', 'FUSION')
        c.edge('FUSION', 'LOCK1')
        c.edge('LOCK1', 'GET_GPS')
        c.edge('GET_GPS', 'UNLOCK1')
        c.edge('UNLOCK1', 'PACK')
        c.edge('PACK', 'SEND')
        c.edge('SEND', 'C1_LOOP')

    # Wiring
    dot.edge('START', 'INIT')
    dot.edge('INIT', 'CALIB')
    dot.edge('CALIB', 'FORK')
    dot.edge('FORK', 'C0_LOOP')
    dot.edge('FORK', 'C1_LOOP')

    output_path = dot.render(filename='voyager_firmware', cleanup=True)
    print(f"✅ Firmware Diagram saved to: {output_path}")

if __name__ == '__main__':
    try:
        render_hardware()
        render_firmware()
        print("\n🎉 All diagrams generated successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Did you install Graphviz? Run: sudo apt install graphviz")