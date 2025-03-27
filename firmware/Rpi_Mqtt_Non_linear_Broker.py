import binascii
import logging
import requests
from datetime import datetime, timezone
from google.oauth2 import service_account
import google.auth.transport.requests
import paho.mqtt.client as mqtt

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MQTT Broker Configuration
BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
MQTT_TOPIC = "sensor/data"
MQTT_USER = "neo"
MQTT_PASSWORD = "123456"

# Firestore URL and Service Account
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/iotagri-3f696/databases/(default)/documents/rc4_non_linear_test"
SERVICE_ACCOUNT_FILE = "iotagri-3f696-632b6aee8946.json"

###############################################################################
#                       Enhanced RC4-Style Encryption                         #
###############################################################################

a = 3
b = 7
SBOX_SIZE = 256

def custom_key_preprocess(key_str, desired_len=32):
    out = []
    for i in range(desired_len):
        val = 0
        for j in range(len(key_str)):
            tmp = (ord(key_str[j]) + i * 17 + j * 31) & 0xFF
            val ^= tmp
            val = ((val << 1) & 0xFF) | (val >> 7)
        out.append(val)
    return out

def enhanced_ksa(key):
    S = list(range(SBOX_SIZE))
    j = 0
    for i in range(SBOX_SIZE):
        k = key[i % len(key)]
        f = (k * k + a * k + b) % SBOX_SIZE
        j = (j + S[i] + f) % SBOX_SIZE
        S[i], S[j] = S[j], S[i]
    return S

def enhanced_rc4_crypt(data_bytes, key_str):
    key = custom_key_preprocess(key_str)
    S = enhanced_ksa(key)
    i = j = 0
    output = []
    for byte in data_bytes:
        i = (i + 1) % SBOX_SIZE
        j = (j + S[i]) % SBOX_SIZE
        S[i], S[j] = S[j], S[i]
        t = (S[i] + S[j]) % SBOX_SIZE
        k_t = S[t]
        output.append(byte ^ k_t)
    return bytes(output)

###############################################################################
#                     Firestore Communication Functions                       #
###############################################################################

def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/datastore"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

def send_to_firestore(encrypted_data):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    timestamp = datetime.now(timezone.utc).isoformat()

    data = {
        "fields": {
            "encrypted_data": {"stringValue": binascii.hexlify(encrypted_data).decode()},
            "timestamp": {"stringValue": timestamp}
        }
    }

    try:
        response = requests.post(FIRESTORE_URL, headers=headers, json=data)
        response.raise_for_status()
        logging.info(f"Encrypted Data sent to Firestore: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send encrypted data to Firestore: {e}")

###############################################################################
#                          MQTT Callback Functions                            #
###############################################################################

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        encrypted_bytes = msg.payload  # Use raw binary data
        logging.info(f"Received Encrypted Payload (HEX): {binascii.hexlify(encrypted_bytes).decode()}")
        send_to_firestore(encrypted_bytes)
    except Exception as e:
        logging.error(f"Error processing MQTT message: {e}")

###############################################################################
#                                   Main                                      #
###############################################################################

def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_ADDRESS, BROKER_PORT)
    client.loop_forever()

if __name__ == "__main__":
    main()