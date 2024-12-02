import paho.mqtt.client as mqtt
import binascii
import logging
import requests
from datetime import datetime, timezone
from google.oauth2 import service_account
import google.auth.transport.requests

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MQTT Broker Configuration
BROKER_ADDRESS = "localhost"  # Use "localhost" for local broker on RPi
BROKER_PORT = 1883
MQTT_TOPIC = "sensor/data"  # Topic to subscribe to
MQTT_USER = "neo"
MQTT_PASSWORD = "123456"

# Firestore URL for your collection
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/iotagri-3f696/databases/(default)/documents/apple"
SERVICE_ACCOUNT_FILE = "iotagri-3f696-632b6aee8946.json"  # Path to your service account JSON file

# RC4 Key-Scheduling Algorithm (KSA)
def rc4_init(key):
    s = list(range(256))  # State array
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    return s

# RC4 Pseudo-Random Generation Algorithm (PRGA)
def rc4_crypt(s, data):
    i = 0
    j = 0
    out = []
    for char in data:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        t = (s[i] + s[j]) % 256
        out.append(char ^ s[t])
    return bytes(out)

# RC4 Decrypt Function
def rc4_decrypt(data_hex, key):
    # Convert hexadecimal string to bytes
    encrypted_data = binascii.unhexlify(data_hex)
    s = rc4_init(key.encode())  # Initialize RC4 with the key
    decrypted_data = rc4_crypt(s, encrypted_data)
    return decrypted_data.decode()  # Convert decrypted bytes to string

# RC4 Encrypt Function
def rc4_encrypt(data, key):
    s = rc4_init(key.encode())  # Initialize RC4 with the key
    data_bytes = data.encode()  # Convert string to bytes
    encrypted_data = rc4_crypt(s, data_bytes)  # Encrypt data
    return binascii.hexlify(encrypted_data).decode()  # Return HEX string

# Fetch Access Token for Firestore
def get_access_token():
    """Generate an access token for Firestore using a service account."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/datastore"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

# Send Data to Firestore
def send_to_firestore(encrypted_data):
    access_token = get_access_token()  # Fetch a new access token dynamically
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    timestamp = datetime.now(timezone.utc).isoformat()

    data = {
        "fields": {
            "encrypted_data": {"stringValue": encrypted_data},
            "timestamp": {"stringValue": timestamp}
        }
    }

    try:
        response = requests.post(FIRESTORE_URL, headers=headers, json=data)
        response.raise_for_status()
        logging.info(f"Data sent to Firestore: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to Firestore: {e}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        # Decode the incoming MQTT message
        encrypted_message = msg.payload.decode()
        logging.info(f"Encrypted Message (HEX): {encrypted_message}")

        # Validate that the message has an even number of characters
        if len(encrypted_message) % 2 != 0:
            logging.error("Received an invalid HEX string: Odd-length string")
            return

        # RC4 decryption key (must match the ESP8266 key)
        decryption_key = "9951407307abcdef"

        # Decrypt the message
        decrypted_message = rc4_decrypt(encrypted_message, decryption_key)
        logging.info(f"Decrypted Data: {decrypted_message}")

        # Parse decrypted data to extract individual sensor readings
        humidity, temperature, soil_moisture = decrypted_message.split(",")
        logging.info(f"Humidity: {humidity}, Temperature: {temperature}, Soil Moisture: {soil_moisture}")

        # Combine and re-encrypt the data
        combined_data = f"{humidity},{temperature},{soil_moisture}"
        encryption_key = "newencryptionkey123"  # New key for re-encryption
        re_encrypted_data = rc4_encrypt(combined_data, encryption_key)
        logging.info(f"Re-encrypted Data (HEX): {re_encrypted_data}")

        # Send re-encrypted data to Firestore
        send_to_firestore(re_encrypted_data)
    except Exception as e:
        logging.error(f"Error processing MQTT message: {e}")

# Main Program
def main():
    # Initialize MQTT client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to MQTT broker
    client.connect(BROKER_ADDRESS, BROKER_PORT)

    # Start MQTT loop
    client.loop_forever()

if __name__ == "__main__":
    main()