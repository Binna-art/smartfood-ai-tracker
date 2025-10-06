import bluetooth

def send_robot_message(message):
    try:
        bd_addr = "00:21:13:01:23:45"  # replace with your Pico's MAC address
        port = 1
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((bd_addr, port))
        sock.send(message)
        sock.close()
    except Exception as e:
        print("Bluetooth error:", e)
