#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "PrecisionAgricola";
const char* password = "ag2025pass";

// MQTT Broker settings
const char* mqtt_broker = "192.168.4.1";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensor/readings";
const char* mqtt_client_id = "ESP32_SENSOR_001";

// Initialize WiFi and MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Function declarations
void connectToWiFi();
void connectToMQTT();
void sendExampleData();

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nESP32 MQTT Sensor Client Starting...");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Configure MQTT
  client.setServer(mqtt_broker, mqtt_port);
  
  // Connect to MQTT
  connectToMQTT();
}

void loop() {
  // Ensure MQTT connection is maintained
  if (!client.connected()) {
    connectToMQTT();
  }
  client.loop();
  
  // Send example data every 10 seconds
  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 10000) {
    sendExampleData();
    lastPublishTime = millis();
  }
}

void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  
  WiFi.begin(ssid, password);
  
  // Wait for connection with timeout
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttemptTime < 10000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nFailed to connect to WiFi. Restarting...");
    delay(1000);
    ESP.restart();
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void connectToMQTT() {
  int attempts = 0;
  
  while (!client.connected() && attempts < 5) {
    Serial.println("Connecting to MQTT broker...");
    
    if (client.connect(mqtt_client_id)) {
      Serial.println("Connected to MQTT broker");
    } else {
      attempts++;
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 2 seconds...");
      delay(2000);
    }
  }
  
  if (!client.connected()) {
    Serial.println("MQTT connection failed after multiple attempts. Restarting ESP32...");
    delay(1000);
    ESP.restart();
  }
}

void sendExampleData() {
  // Create JSON document for the payload
  StaticJsonDocument<256> doc;
  
  // Add device ID and timestamp
  doc["device_id"] = mqtt_client_id;
  doc["timestamp"] = millis() / 1000.0; // Simple timestamp
  
  // Create sensors object
  JsonObject sensors = doc.createNestedObject("sensors");
  
  // Add NH3 sensor data
  JsonObject nh3_sensor = sensors.createNestedObject("NH3");
  nh3_sensor["status"] = "active";
  nh3_sensor["reading"] = random(50, 100); // Random value for example
  
  // Add H2S sensor data
  JsonObject h2s_sensor = sensors.createNestedObject("H2S");
  h2s_sensor["status"] = "active";
  h2s_sensor["reading"] = random(10, 40); // Random value for example
  
  // Add pressure sensor data
  JsonObject pressure_sensor = sensors.createNestedObject("pressure");
  pressure_sensor["status"] = "active";
  pressure_sensor["reading"] = random(980, 1020); // Random value for example
  
  // Add aerator status
  JsonObject aerator_status = doc.createNestedObject("aerator_status");
  aerator_status["relay3"] = 0; // Example relay status (off)
  aerator_status["relay4"] = 1; // Example relay status (on)
  
  // Serialize the JSON document to a string
  String payload;
  serializeJson(doc, payload);
  
  // Print the payload for debugging
  Serial.println("Sending payload:");
  Serial.println(payload);
  
  // Publish the payload to the MQTT topic
  if (client.publish(mqtt_topic, payload.c_str())) {
    Serial.println("Payload sent successfully");
  } else {
    Serial.println("Failed to send payload");
  }
}