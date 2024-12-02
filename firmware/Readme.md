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

#### **Logs You Will See:**
1. **Wi-Fi Connection Logs:**
   - Displays the connection progress to the specified Wi-Fi network.
   ```plaintext
   Connecting to Wi-Fi...
   Connected to the Wi-Fi network

### **2. MQTT Broker Connection Logs**

The logs provide detailed feedback on the connection status between the ESP8266 and the MQTT broker.

#### **Successful Connection**
- Indicates that the ESP8266 has successfully connected to the MQTT broker.
```plaintext
Connecting to MQTT broker...
Connected to MQTT broker
#### **Failed Connection**

- If the ESP8266 fails to connect, the log will display a failure message along with a specific return code.
- The return code helps diagnose the reason for the connection failure.

#### **Common Return Codes and Their Meanings**
- **`-1`**: Incorrect broker address or port.
- **`-2`**: Network connection failed (e.g., Wi-Fi issue).
- **`-3`**: Connection to the broker was lost.
- **`-4`**: Authentication failed (invalid username or password).
- **`-5`**: Client is not authorized to connect.

#### **Example Logs for Failed Connection**
```plaintext
Connecting to MQTT broker...
Failed with state -1
- **Indicates that the broker address or port is incorrect:**
  - This error occurs when the `mqttServer` or `mqttPort` values do not match the MQTT broker's actual address or port.
  - **Steps to Fix:**
    1. Verify the broker's IP address:
       - For a local broker (e.g., Mosquitto on Raspberry Pi), check the Raspberry Pi's IP address using `ifconfig` or `ip a` on the Pi.
       - Replace the `mqttServer` value in the code with the correct IP address.
    2. Confirm the MQTT broker's port:
       - The default port for MQTT is `1883`. Ensure the `mqttPort` in the code matches the broker's configuration.
       - If using a secure connection (MQTT over TLS), the default port is usually `8883`.
    3. Test the broker address and port:
       - Use an MQTT client like **MQTT Explorer** or the command-line tool `mosquitto_pub` to test connectivity to the broker:
         ```bash
         mosquitto_pub -h <broker_ip> -p <port> -t "test/topic" -m "hello"
         ```
       - Replace `<broker_ip>` and `<port>` with the broker's IP address and port.

  - Example Log for Incorrect Broker Address/Port:
    ```plaintext
    Connecting to MQTT broker...
    Failed with state -1
    ```
    
