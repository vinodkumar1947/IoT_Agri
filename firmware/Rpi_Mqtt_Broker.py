import paho.mqtt.client as mqtt
import binascii
import logging
import requests
from datetime import datetime, timezone
from google.oauth2 import service_account
import google.auth.transport.requests
import time # Import the time module for measuring elapsed time

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
    encrypted_data = binascii.unhexlify(data_hex)
    start_time = time.time()  # Record the start time
    s = rc4_init(key.encode())  # Initialize RC4 with the key
    decrypted_data = rc4_crypt(s, encrypted_data)
    decryption_time = time.time() - start_time  # Calculate elapsed time
    logging.info(f"Decryption Time: {decryption_time:.6f} seconds")  # Print decryption time
    return decrypted_data.decode()  # Convert decrypted bytes to string

# RC4 Encrypt Function
def rc4_encrypt(data, key):
    start_time = time.time()  # Record the start time
    s = rc4_init(key.encode())  # Initialize RC4 with the key
    data_bytes = data.encode()  # Convert string to bytes
    encrypted_data = rc4_crypt(s, data_bytes)  # Encrypt data
    encryption_time = time.time() - start_time  # Calculate elapsed time
    logging.info(f"Encryption Time: {encryption_time:.6f} seconds")  # Print encryption time
    return binascii.hexlify(encrypted_data).decode()  # Return HEX string

# Fetch Access Token for Firestore
def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/datastore"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

# Send Data to Firestore
def send_to_firestore(humidity, temperature, soil_moisture):
    access_token = get_access_token()  # Fetch a new access token dynamically
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    timestamp = datetime.now(timezone.utc).isoformat()

    # Encryption key
    #encryption_key = "newencryptionkey123"
    encryption_key= "9951407307abcdef"

    # Encrypt individual sensor values
    encrypted_humidity = rc4_encrypt(humidity, encryption_key)
    encrypted_temperature = rc4_encrypt(temperature, encryption_key)
    encrypted_soil_moisture = rc4_encrypt(soil_moisture, encryption_key)

    data = {
        "fields": {
            "humidity": {"stringValue": encrypted_humidity},
            "temperature": {"stringValue": encrypted_temperature},
            "soil_moisture": {"stringValue": encrypted_soil_moisture},
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

        # RC4 decryption key
        decryption_key = "9951407307abcdef"

        # Decrypt the message
        decrypted_message = rc4_decrypt(encrypted_message, decryption_key)
        logging.info(f"Decrypted Data: {decrypted_message}")

        # Parse decrypted data to extract individual sensor readings
        humidity, temperature, soil_moisture = decrypted_message.split(",")
        logging.info(f"Humidity: {humidity}, Temperature: {temperature}, Soil Moisture: {soil_moisture}")

        # Send individual sensor values to Firestore
        send_to_firestore(humidity, temperature, soil_moisture)
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