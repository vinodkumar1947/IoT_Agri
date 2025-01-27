#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// DHT sensor configuration
#define DHTTYPE DHT11
const int DHTPin = 14; // GPIO14 for DHT11 data pin
DHT dht(DHTPin, DHTTYPE);

// Soil moisture sensor pin
const int SoilPin = 12; // GPIO12 for soil sensor

// Wi-Fi credentials
const char* ssid = "Saraswathi";
const char* password = "12345678";

// MQTT broker configuration
const char* mqttServer = "192.168.106.11"; // Raspberry Pi IP address
const int mqttPort = 1883;                 // MQTT broker port
const char* mqttUser = "neo";              // MQTT username
const char* mqttPassword = "123456";       // MQTT password
const char* mqttTopic = "sensor/data";     // MQTT topic to publish encrypted data

WiFiClient espClient;
PubSubClient client(espClient);

// RC4 Key-Scheduling Algorithm (KSA)
void rc4_init(unsigned char* s, unsigned char* key, int len) {
  int i, j = 0;
  unsigned char temp;
  for (i = 0; i < 256; i++) {
    s[i] = i;
  }
  for (i = 0; i < 256; i++) {
    j = (j + s[i] + key[i % len]) % 256;
    temp = s[i];
    s[i] = s[j];
    s[j] = temp;
  }
}

// RC4 Pseudo-Random Generation Algorithm (PRGA)
void rc4_crypt(unsigned char* s, unsigned char* data, int len) {
  int i = 0, j = 0, k, t;
  unsigned char temp;
  for (k = 0; k < len; k++) {
    i = (i + 1) % 256;
    j = (j + s[i]) % 256;
    temp = s[i];
    s[i] = s[j];
    s[j] = temp;
    t = (s[i] + s[j]) % 256;
    data[k] ^= s[t];
  }
}

// RC4 Encryption function
String rc4Encrypt(String data, String key) {

  unsigned char s[256];
  
  // Record the start time
  unsigned long startTime = millis();
  
  rc4_init(s, (unsigned char*)key.c_str(), key.length());
  Serial.print("\n");
  unsigned char dataBytes[data.length() + 1];
  Serial.print("\n");
  strcpy((char*)dataBytes, data.c_str());
  Serial.print("\n");
  rc4_crypt(s, dataBytes, data.length());
  Serial.print("\n");
  
  String encrypted = "";
  for (int i = 0; i < data.length(); i++) {
    if (dataBytes[i] < 16) {  // Add a leading zero for single-digit hex values
      encrypted += "0";
    }
    encrypted += String(dataBytes[i], HEX);  // Convert to HEX string
  }
  // Record the end time
  unsigned long endTime = millis();
  // Calculate elapsed time
  unsigned long encryptionTime = endTime - startTime;
  Serial.print("Encryption Time (ms): ");
  Serial.println(encryptionTime);

  return encrypted;
}

void setup() {
  Serial.begin(115200);
  pinMode(SoilPin, INPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to Wi-Fi...");
  }
  Serial.println("Connected to the Wi-Fi network");

  // Connect to MQTT broker
  client.setServer(mqttServer, mqttPort);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT broker...");
    if (client.connect("ESP8266Client", mqttUser, mqttPassword)) {
      Serial.println("Connected to MQTT broker");
    } else {
      Serial.print("Failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
  }

  // Initialize DHT sensor
  dht.begin();
}

void loop() {
  // Read sensor data
  int h = dht.readHumidity();
  int t = dht.readTemperature();
  int soil = digitalRead(SoilPin);

  // Handle sensor errors
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  // Combine sensor data into a single string
  String sensorData = String(h) + "," + String(t) + "," + String(soil);
  Serial.println("Raw Sensor Data: " + sensorData);

  // Encrypt the combined data using RC4
  String encryptionKey = "9951407307abcdef"; // RC4 encryption key
  String encryptedData = rc4Encrypt(sensorData, encryptionKey);
  Serial.println("Encrypted Data (HEX): " + encryptedData);

  // Publish encrypted data to MQTT topic
  if (client.publish(mqttTopic, encryptedData.c_str())) {
    Serial.println("Encrypted data published to MQTT topic");
  } else {
    Serial.println("Failed to publish data to MQTT topic");
  }

  // Ensure MQTT client stays connected
  client.loop();

  // Delay before sending the next message
  delay(3000);
}