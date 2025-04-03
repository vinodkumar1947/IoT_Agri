from cloudevents.http import CloudEvent
import functions_framework
from google.events.cloud import datastore
from google.protobuf import json_format
from google.cloud import firestore as gcf_firestore
import logging
import os, binascii, time

logging.basicConfig(level=logging.INFO)
SBOX_SIZE = 256

def preprocess_key(input_key: str) -> bytes:
    desired_len = 32
    out_key = bytearray(desired_len)
    for i in range(desired_len):
        val = 0
        for j in range(len(input_key)):
            val ^= (ord(input_key[j]) + i * 17 + j * 31) & 0xFF
            val = ((val << 1) | (val >> 7)) & 0xFF  # important!
        out_key[i] = val
    return bytes(out_key)

def enhanced_ksa(key: bytes, a=3, b=7) -> bytearray:
    S = bytearray(range(SBOX_SIZE))
    j = 0
    for i in range(SBOX_SIZE):
        k = key[i % len(key)]
        f = (k * k + a * k + b) % SBOX_SIZE
        j = (j + S[i] + f) % SBOX_SIZE
        S[i], S[j] = S[j], S[i]
    return S

def enhanced_prga(S: bytearray, data: bytearray) -> bytes:
    i = j = 0
    out = bytearray(len(data))
    for k in range(len(data)):
        i = (i + 1) % SBOX_SIZE
        j = (j + S[i]) % SBOX_SIZE
        S[i], S[j] = S[j], S[i]
        t = (S[i] + S[j]) % SBOX_SIZE
        out[k] = data[k] ^ S[t]
    return bytes(out)

def rc4_decrypt_enhanced(encrypted_hex: str, key: str):
    try:
        encrypted_data = binascii.unhexlify(encrypted_hex)
        hashed_key = preprocess_key(key)
        S = enhanced_ksa(hashed_key)

        start_time = time.time()
        decrypted = enhanced_prga(S, bytearray(encrypted_data))
        end_time = time.time()

        decryption_time_us = int((end_time - start_time) * 1_000_000)
        # Return string only if clean ASCII
        try:
            decoded = decrypted.decode("ascii")  # this will now work!
            return decoded, decryption_time_us
        except Exception:
            # fallback
            return binascii.hexlify(decrypted).decode(), decryption_time_us
    except Exception as e:
        logging.error(f"RC4 decryption failed: {e}")
        return None, 0

@functions_framework.cloud_event
def hello_firestore(cloud_event: CloudEvent) -> None:
    try:
        print("=============Event Triggered===========")
        # Parse protobuf data from CloudEvent
        event_proto = datastore.EntityEventData()
        event_proto._pb.ParseFromString(cloud_event.data)
        print(event_proto.value.entity)
        entity = event_proto.value.entity
        properties = entity.properties
        doc_segments = entity.key.path
        last_segment = doc_segments[-1]
        doc_name = f"rc4_non_linear_test/{last_segment.name}"
        logging.info(f"Processing document: {doc_name}")

        # Inside the function after reading properties
        if "decrypted_data" in properties:
            logging.info("Decrypted data already exists. Skipping to avoid loop.")
            return
        
        if "encrypted_data" not in properties:
            logging.warning("No 'encrypted_data' found.")
            return

        encrypted_hex = properties["encrypted_data"].string_value
        print("Encrypted Hex:")
        print(encrypted_hex)
        timestamp = properties["timestamp"].string_value
        print("Timestamp:")
        print(timestamp)
        key = os.getenv("DECRYPTION_KEY", "9951407307abcdef")

        decrypted_text, time_us = rc4_decrypt_enhanced(encrypted_hex, key)
        
        if decrypted_text:
            # Update the document in Firestore
            firestore_client = gcf_firestore.Client()
            doc_ref = firestore_client.document(doc_name)
            doc_ref.update({
                "decrypted_data": decrypted_text,
                "decryption_time_us": time_us
            })
            logging.info(f"✅ Decrypted: {decrypted_text} in {time_us} µs")
        else:
            logging.warning("Decryption failed.")
    except Exception as e:
        logging.error(f"🔥 Function error: {e}")