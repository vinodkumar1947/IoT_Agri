from cloudevents.http import CloudEvent
import functions_framework
from google.events.cloud import firestore
import logging
import os
import binascii


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    )

# RC4 Decryption Functions
def rc4_init(key):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    return s

def rc4_crypt(s, data):
    i = 0
    j = 0
    out = []
    for byte in data:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        t = (s[i] + s[j]) % 256
        out.append(byte ^ s[t])
    return bytes(out)

def rc4_decrypt(encrypted_hex, key):
    try:
        s = rc4_init(key.encode())
        encrypted_data = binascii.unhexlify(encrypted_hex)
        decrypted_data = rc4_crypt(s, encrypted_data)
        return decrypted_data.decode()
    except (binascii.Error, UnicodeDecodeError) as e:
        logging.error(f"Decryption failed: {e}")
        return None

@functions_framework.cloud_event
def hello_firestore(cloud_event: CloudEvent) -> None:
    try:
        """Triggers by a change to a Firestore document.
        Args:
            cloud_event: cloud event with information on the firestore event trigger
        """
        firestore_payload = firestore.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)

        logging.info(f"Function triggered by change to: {cloud_event['source']}")

        # Extract Firestore fields
        doc_fields = firestore_payload.value.fields

        # Check if 'temperature' and 'humidity' fields exist
        if 'temperature' in doc_fields and 'humidity' in doc_fields and 'soil_moisture' in doc_fields:
            encrypted_temperature = doc_fields['temperature'].string_value
            encrypted_humidity = doc_fields['humidity'].string_value
            encrypted_soil_moisture = doc_fields['soil_moisture'].string_value

            # Get the decryption key securely
            decryption_key = os.getenv("DECRYPTION_KEY", "9951407307abcdef")

            # Decrypt the fields
            decrypted_temperature = rc4_decrypt(encrypted_temperature, decryption_key)
            decrypted_humidity = rc4_decrypt(encrypted_humidity, decryption_key)
            decrypted_soil_moisture = rc4_decrypt(encrypted_soil_moisture, decryption_key)

            if decrypted_temperature and decrypted_humidity and decrypted_soil_moisture:
                logging.info(f"Decrypted Temperature: {decrypted_temperature}")
                logging.info(f"Decrypted Humidity: {decrypted_humidity}")
                logging.info(f"Decrypted Soil_Moisture: {decrypted_soil_moisture}")
               
                logging.info("Decrypted data Done!.")

            else:
                logging.warning("Decryption failed for one or more fields.")
        else:
            logging.warning("No encrypted data found in the Firestore document.")
    except Exception as e:
        logging.error(f"Error processing Firestore event: {e}")