import time
import json
import socket
import sys
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# --- CONFIGURATION ---
# Your Endpoint (Paris Region)
AWS_ENDPOINT = "a303ehanbggla2-ats.iot.eu-west-3.amazonaws.com"
CLIENT_ID = "FireDetectionPi"
TOPIC = "home/fire_alert"

# Socket Config (Must match the port your PC sends to)
HOST_IP = '0.0.0.0' # Listens on all interfaces
PORT = 65432        # Default port (Change if your PC script uses a different one)

# Certificate Files
ROOT_CA = "root-CA.pem"
CERT_FILE = "certificate.pem.crt"
KEY_FILE = "private.pem.key"

# --- AWS CONNECTION SETUP ---
print("[System] Initializing AWS IoT Client...")

mqtt_client = AWSIoTMQTTClient(CLIENT_ID)
mqtt_client.configureEndpoint(AWS_ENDPOINT, 8883)
mqtt_client.configureCredentials(ROOT_CA, KEY_FILE, CERT_FILE)

# Connection Settings (Optimized for stability)
mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
mqtt_client.configureOfflinePublishQueueing(-1) 
mqtt_client.configureDrainingFrequency(2) 
mqtt_client.configureConnectDisconnectTimeout(10)
mqtt_client.configureMQTTOperationTimeout(5)

# Connect
try:
    mqtt_client.connect()
    print(f"[AWS] Connected to {AWS_ENDPOINT}!")
except Exception as e:
    print(f"[Error] Could not connect to AWS: {e}")
    sys.exit(1)

# --- HELPER FUNCTION ---
def send_alert_to_cloud():
    payload = {
        "device_id": "Pi_Camera_01",
        "alert_type": "FIRE",
        "timestamp": time.time(),
        "status": "CRITICAL"
    }
    # Publish to AWS
    mqtt_client.publish(TOPIC, json.dumps(payload), 1)
    print(f"[AWS] Payload Sent: {payload}")

# --- MAIN LISTENER LOOP ---
# This acts as a server waiting for the PC to say "on"
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server_socket.bind((HOST_IP, PORT))
    server_socket.listen(1)
    print(f"[Socket] Listening for PC signals on port {PORT}...")

    while True:
        conn, addr = server_socket.accept()
        data = conn.recv(1024).decode().strip()
        
        if data == "on":
            print("[Alert] FIRE DETECTED signal received from PC!")
            # 1. (Optional) Turn on physical buzzer here
            # GPIO.output(BUZZER_PIN, GPIO.HIGH)
            
            # 2. Send Data to AWS
            send_alert_to_cloud()
            
        elif data == "off":
            print("[Info] Reset signal received.")
            # GPIO.output(BUZZER_PIN, GPIO.LOW)

        conn.close()

except KeyboardInterrupt:
    print("\n[System] Stopping...")
    mqtt_client.disconnect()
    server_socket.close()