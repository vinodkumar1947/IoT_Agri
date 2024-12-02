# Hardware Connections

| Component           | Pin                  |
|---------------------|----------------------|
| DHT11 Sensor (Data) | GPIO14 (D5 on NodeMCU) |
| Soil Moisture Sensor| GPIO12 (D6 on NodeMCU) |


# Notes and Explanation for the ESP8266 MQTT Sensor Node Code

This code is designed to read sensor data from a **DHT11** (temperature and humidity sensor) and a soil moisture sensor, encrypt the data using the **RC4 algorithm**, and publish the encrypted data to an **MQTT broker**. Here’s a comprehensive guide, including what to do, what not to do, and troubleshooting tips.

---

## **What This Code Does**
1. **Connects to a Wi-Fi Network:**
   - Uses provided SSID and password to establish Wi-Fi connectivity.

2. **Reads Sensor Data:**
   - DHT11: Reads temperature and humidity.
   - Soil Moisture Sensor: Reads soil moisture state (binary: 1/0).

3. **Encrypts Data:**
   - Combines sensor data into a CSV string (e.g., `"45,23,1"`) and encrypts it using **RC4 encryption** with a predefined key.

4. **Publishes Encrypted Data to MQTT:**
   - Sends the encrypted data to the specified **MQTT topic** (`sensor/data`).

5. **Maintains MQTT Connection:**
   - Keeps the MQTT client connected to the broker to handle continuous publishing.

---

## **What To Do**

### **1. Hardware Setup**
- **ESP8266 NodeMCU:**
  - Ensure it's powered via USB or an external 3.3V power source.
- **DHT11 Sensor:**
  - Connect the **data pin** to **GPIO14** (D5 on NodeMCU).
  - Provide 3.3V power and GND connections.
- **Soil Moisture Sensor:**
  - Connect the **signal pin** to **GPIO12** (D6 on NodeMCU).
  - Provide 3.3V power and GND connections.

### **2. Configure MQTT Broker**
- Install an MQTT broker (e.g., **Mosquitto**) on a Raspberry Pi or any local server.
- Update the `mqttServer`, `mqttPort`, `mqttUser`, and `mqttPassword` variables in the code to match your broker setup.
  ```cpp
  const char* mqttServer = "192.168.106.11";
  const int mqttPort = 1883;
  const char* mqttUser = "neo";
  const char* mqttPassword = "123456";
  
### **3. Choose a Strong Encryption Key**
- Replace the RC4 encryption key with a stronger, more secure key.
    ```cpp
    String encryptionKey = "your_secure_key_here";
### **4. Monitor Serial Logs**
- Open the **Arduino Serial Monitor** to observe the program's output.
- Set the baud rate to `115200` to ensure correct data display.


# Logs You Will See

### **1. Wi-Fi Connection Logs**
- Displays the connection progress to the specified Wi-Fi network.
```plaintext
Connecting to Wi-Fi...
Connected to the Wi-Fi network
```

### **2. MQTT Broker Connection Logs**
- Shows the connection status to the MQTT broker.
```plaintext
Connecting to MQTT broker...
Connected to MQTT broker
```
- If connection fails, it provides the failure state:
```plaintext
Failed with state -2
```

### **3. Sensor Data Logs**
- Logs raw sensor readings from the DHT11 and soil moisture sensor.
```plaintext
Raw Sensor Data: 45,23,1
```

### **4. Encryption Logs**
- Shows the encrypted data in HEX format after processing the sensor data.
```plaintext
Encrypted Data (HEX): 4f2e7b1d6a8c9d02b3
```

### **5. MQTT Publishing Logs**
- Indicates whether the data was successfully published to the MQTT broker.
```plaintext
Encrypted data published to MQTT topic
```
- If publishing fails:
```plaintext
Failed to publish data to MQTT topic
```

---

### **How to Use Serial Monitor**
- Open the **Arduino IDE** and select `Tools > Serial Monitor` (or press `Ctrl+Shift+M`).
- Verify the baud rate is set to `115200`.
- Use the logs to troubleshoot issues such as:
  - Wi-Fi connection problems.
  - MQTT broker connectivity.
  - Sensor data validity.
  - Encryption process results.
