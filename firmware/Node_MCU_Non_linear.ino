#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTTYPE DHT11
const int DHTPin = 02;         // use 2 instead of 02 (octal) for clarity
const int SoilPin = 12;
#define SBOX_SIZE 256

DHT dht(DHTPin, DHTTYPE);

// Wi-Fi credentials
const char* ssid = "saraswathi";
const char* password = "12345678";

// MQTT configuration
const char* mqttServer = "192.168.79.11";
const int mqttPort = 1883;
const char* mqttUser = "neo";
const char* mqttPassword = "123456";
const char* mqttTopic = "sensor/data";

WiFiClient espClient;
PubSubClient client(espClient);

// Key preprocessing to 32 bytes
void preprocessKey(String inputKey, unsigned char* outKey, int& keyLen) {
  const int desiredLen = 32;
  keyLen = desiredLen;
  for (int i = 0; i < desiredLen; i++) {
    byte val = 0;
    for (int j = 0; j < inputKey.length(); j++) {
      val ^= (inputKey[j] + i * 17 + j * 31);
      val = (val << 1) | (val >> 7);
    }
    outKey[i] = val;
  }
}

// Enhanced KSA using a 256-element S-box with an 8-bit type
void enhancedKSA(unsigned char* S, unsigned char* key, int keyLen, int a = 3, int b = 7) {
  for (int i = 0; i < SBOX_SIZE; i++) {
    S[i] = i;
  }
  int j = 0;
  for (int i = 0; i < SBOX_SIZE; i++) {
    int k = key[i % keyLen];
    int f = (k * k + a * k + b) % SBOX_SIZE;
    j = (j + S[i] + f) % SBOX_SIZE;
    std::swap(S[i], S[j]);
  }
}

void enhancedPRGA(unsigned char* S, unsigned char* data, int len) {
  int i = 0, j = 0;
  Serial.print("Keystream: ");
  for (int k = 0; k < len; k++) {
    i = (i + 1) % SBOX_SIZE;
    j = (j + S[i]) % SBOX_SIZE;
    std::swap(S[i], S[j]);
    int t = (S[i] + S[j]) % SBOX_SIZE;
    byte ks = S[t];
    Serial.print(ks, HEX);
    Serial.print(" ");
    data[k] ^= ks;
  }
  Serial.println();
}

// Enhanced RC4 Encryption returning encrypted binary
void rc4EncryptEnhanced(const char* data, const String& key, unsigned char* encryptedOut, size_t& dataLen) {
  unsigned char S[SBOX_SIZE]; // 256 bytes S-box
  unsigned char hashedKey[32];
  int keyLen = 0;

  // Measure memory before encryption
  uint32_t memBefore = ESP.getFreeHeap();

  // Preprocess the key
  preprocessKey(key, hashedKey, keyLen);
  Serial.print("Hashed Key: ");
	for (int i = 0; i < keyLen; i++) {
	  Serial.print(hashedKey[i], HEX);
	  Serial.print(" ");
	}
	Serial.println();
	
  enhancedKSA(S, hashedKey, keyLen);

  // Determine the data length from the C string
  dataLen = strlen(data);

  // Copy input into the output buffer
  memcpy(encryptedOut, data, dataLen);

  // Perform encryption
  unsigned long startTime = micros();
  enhancedPRGA(S, encryptedOut, dataLen);
  unsigned long endTime = micros();

  // Measure memory usage
  uint32_t memAfter = ESP.getFreeHeap();
  uint32_t memUsed = (memBefore > memAfter) ? (memBefore - memAfter) : 0;

  // Debug output
  Serial.print("Encryption Time (us): ");
  Serial.println(endTime - startTime);
  Serial.print("Estimated Memory Used (bytes): ");
  Serial.println(memUsed);
}

void setup() {
  Serial.begin(115200);
  pinMode(SoilPin, INPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to Wi-Fi...");
  }
  Serial.println("Wi-Fi connected");

  client.setServer(mqttServer, mqttPort);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT broker...");
    if (client.connect("ESP8266Client", mqttUser, mqttPassword)) {
      Serial.println("Connected to MQTT broker");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }

  Serial.print("Total Free Heap (bytes): ");
  Serial.println(ESP.getFreeHeap());

  dht.begin();
}

void loop() {
  if (!client.connected()) {
    Serial.println("MQTT disconnected. Reconnecting...");
    while (!client.connected()) {
      if (client.connect("ESP8266Client", mqttUser, mqttPassword)) {
        Serial.println("Reconnected to MQTT broker");
      } else {
        Serial.print("Retry failed, rc=");
        Serial.println(client.state());
        delay(2000);
      }
    }
  }

  client.loop();

  int h = dht.readHumidity();
  int t = dht.readTemperature();
  int soil = digitalRead(SoilPin);

  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  char sensorData[32];
  snprintf(sensorData, sizeof(sensorData), "%d,%d,%d", h, t, soil);

  String encryptionKey = "9951407307abcdef";
  unsigned char encryptedData[64];  // maximum expected size
  size_t encryptedLen;
  
  Serial.print("Plaintext sensorData: ");
	Serial.println(sensorData);
	
  rc4EncryptEnhanced(sensorData, encryptionKey, encryptedData, encryptedLen);
  
  Serial.print("Encrypted payload length: ");
  Serial.println(encryptedLen);

  bool success = client.publish(mqttTopic, encryptedData, encryptedLen);
  if (success) {
    Serial.println("Published to MQTT");
  } else {
    Serial.println("MQTT publish failed - check broker, auth, or connection.");
  }

  delay(3000);
}