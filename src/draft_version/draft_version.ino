#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_BMP3XX.h>
#include <esp_task_wdt.h>

// Define pin assignments
#define RELAY_LOAD_1 12  // Relay for load 1
#define RELAY_LOAD_2 27  // Relay for load 2
#define RELAY_SENSOR_1 13  // Relay for energizing sensor 1
#define RELAY_SENSOR_2 14  // Relay for energizing sensor 2
#define NH3_SENSOR_PIN 36  // Analog pin for NH3 sensor
#define H2S_SENSOR_PIN 39  // Analog pin for H2S sensor

// WiFi credentials
const char* ssid = "PrecisionAgricola";
const char* password = "ag2025pass";

// MQTT Broker settings
const char* mqtt_broker = "192.168.4.1";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensor/readings";
const char* mqtt_client_id = "ESP32_SENSOR_001";

// Timing constants
const unsigned long SENSOR_READ_INTERVAL = 30000;  // Read sensors every 30 seconds
const unsigned long RELAY_CYCLE_INTERVAL = 3600000;  // Cycle relays every hour (3600000 ms)
const unsigned long WDT_TIMEOUT = 30;  // Watchdog timeout in seconds

// Relay monitoring
const int MAX_RELAY_CYCLES_PER_DAY = 24;  // Maximum times relays should cycle per day
int relayCycleCount[4] = {0, 0, 0, 0};  // Counter for each relay
unsigned long lastRelayCycleTime = 0;  // Last time relays were cycled
unsigned long lastDailyCycleReset = 0;  // Last time the cycle counter was reset

// Sensor calibration values
const float NH3_CALIBRATION_FACTOR = 0.1;  // Example calibration factor
const float H2S_CALIBRATION_FACTOR = 0.05;  // Example calibration factor
const float ANALOG_REFERENCE = 3.3;  // ADC reference voltage

// Initialize objects
WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_BMP3XX bmp;

// Function declarations
void connectToWiFi();
void connectToMQTT();
void initSensors();
void initRelays();
void setupWatchdog();
void controlRelays();
void readSensors();
void sendSensorData(float nh3, float h2s, float pressure, float temperature);
void checkRelayCycles();

// Sensor values
float nh3_value = 0;
float h2s_value = 0;
float pressure_value = 0;
float temperature_value = 0;

// Relay states
bool relay_states[4] = {false, false, false, false};

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nESP32 Precision Agriculture Sensor System Starting...");
  
  // Initialize relays
  initRelays();
  
  // Initialize sensors
  initSensors();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Configure MQTT
  client.setServer(mqtt_broker, mqtt_port);
  
  // Connect to MQTT
  connectToMQTT();
  
  // Setup watchdog
  setupWatchdog();
  
  // Initialize timing variables
  lastRelayCycleTime = millis();
  lastDailyCycleReset = millis();
  
  Serial.println("Setup completed successfully");
}

void loop() {
  // Reset watchdog timer to prevent reset
  esp_task_wdt_reset();
  
  // Ensure MQTT connection is maintained
  if (!client.connected()) {
    connectToMQTT();
  }
  client.loop();
  
  // Control relays based on timing
  static unsigned long lastRelayControlTime = 0;
  if (millis() - lastRelayControlTime > RELAY_CYCLE_INTERVAL) {
    controlRelays();
    lastRelayControlTime = millis();
  }
  
  // Read sensors and send data periodically
  static unsigned long lastSensorReadTime = 0;
  if (millis() - lastSensorReadTime > SENSOR_READ_INTERVAL) {
    readSensors();
    sendSensorData(nh3_value, h2s_value, pressure_value, temperature_value);
    lastSensorReadTime = millis();
  }
  
  // Check if we need to reset daily relay cycle counter (once per day)
  if (millis() - lastDailyCycleReset > 86400000) { // 24 hours in milliseconds
    for (int i = 0; i < 4; i++) {
      relayCycleCount[i] = 0;
    }
    lastDailyCycleReset = millis();
    Serial.println("Daily relay cycle counters reset");
  }
  
  // Check for excessive relay cycling
  checkRelayCycles();
  
  // Small delay to prevent CPU hogging
  delay(100);
}

void initRelays() {
  // Initialize relay pins as outputs
  pinMode(RELAY_LOAD_1, OUTPUT);
  pinMode(RELAY_LOAD_2, OUTPUT);
  pinMode(RELAY_SENSOR_1, OUTPUT);
  pinMode(RELAY_SENSOR_2, OUTPUT);
  
  // Set initial state (relays OFF)
  digitalWrite(RELAY_LOAD_1, LOW);
  digitalWrite(RELAY_LOAD_2, LOW);
  digitalWrite(RELAY_SENSOR_1, LOW);
  digitalWrite(RELAY_SENSOR_2, LOW);
  
  Serial.println("Relays initialized");
}

// Fix for initSensors() function - Pin mode issue
void initSensors() {
  // Initialize I2C for BMP3901 sensor
  Wire.begin();
  if (!bmp.begin_I2C()) {
    Serial.println("Could not find a valid BMP3XX sensor, check wiring!");
    // Continue anyway as we might still have the analog sensors
  } else {
    // Set up BMP sensor with correct constant names
    bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_8X);
    bmp.setPressureOversampling(BMP3_OVERSAMPLING_4X);
    bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
    Serial.println("BMP3XX pressure sensor initialized");
  }
  
  // Fixed pinMode calls
  pinMode((uint8_t)NH3_SENSOR_PIN, INPUT);
  pinMode((uint8_t)H2S_SENSOR_PIN, INPUT);
  
  Serial.println("Analog sensors initialized");
}


void setupWatchdog() {
  // Initialize ESP32 watchdog timer using the newer API
  Serial.println("Initializing watchdog timer...");
  
  // For ESP32 Arduino core 3.x and above (newer API)
  esp_task_wdt_config_t wdtConfig;
  wdtConfig.timeout_ms = WDT_TIMEOUT * 1000; // Convert seconds to milliseconds
  wdtConfig.idle_core_mask = 0;              // No idle core
  wdtConfig.trigger_panic = true;            // Trigger a panic when timeout
  
  esp_task_wdt_init(&wdtConfig);
  esp_task_wdt_add(NULL); // Add current thread to WDT watch
  
  Serial.println("Watchdog timer initialized");
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

void controlRelays() {
  // This function implements the relay control logic
  // For this example, we'll simply toggle the relays based on timing
  
  // Toggle relay_load_1 and relay_load_2 (pins 12, 27)
  relay_states[0] = !relay_states[0];
  digitalWrite(RELAY_LOAD_1, relay_states[0] ? HIGH : LOW);
  relayCycleCount[0]++;
  
  relay_states[1] = !relay_states[1];
  digitalWrite(RELAY_LOAD_2, relay_states[1] ? HIGH : LOW);
  relayCycleCount[1]++;
  
  Serial.print("Load relays toggled. States: ");
  Serial.print(relay_states[0]);
  Serial.print(", ");
  Serial.println(relay_states[1]);
  
  // For sensor relays, we'll turn them on for sensor reading and off afterward
  // Turn on sensor relays before reading
  relay_states[2] = true;
  digitalWrite(RELAY_SENSOR_1, HIGH);
  relayCycleCount[2]++;
  
  relay_states[3] = true;
  digitalWrite(RELAY_SENSOR_2, HIGH);
  relayCycleCount[3]++;
  
  Serial.println("Sensor relays activated for readings");
  
  // Allow sensors to stabilize
  delay(2000);
  
  // Read sensors while they're powered
  readSensors();
  
  // Turn off sensor relays to save power
  relay_states[2] = false;
  digitalWrite(RELAY_SENSOR_1, LOW);
  
  relay_states[3] = false;
  digitalWrite(RELAY_SENSOR_2, LOW);
  
  Serial.println("Sensor relays deactivated after readings");
  
  // Send the data after reading
  sendSensorData(nh3_value, h2s_value, pressure_value, temperature_value);
}

void readSensors() {
  // Read NH3 sensor (analog pin 36)
  int nh3_raw = analogRead(NH3_SENSOR_PIN);
  nh3_value = (nh3_raw / 4095.0) * ANALOG_REFERENCE * NH3_CALIBRATION_FACTOR;
  
  // Read H2S sensor (analog pin 39)
  int h2s_raw = analogRead(H2S_SENSOR_PIN);
  h2s_value = (h2s_raw / 4095.0) * ANALOG_REFERENCE * H2S_CALIBRATION_FACTOR;
  
  // Read pressure sensor (BMP3901 via I2C)
  if (bmp.performReading()) {
    pressure_value = bmp.pressure / 100.0; // Convert Pa to hPa
    temperature_value = bmp.temperature;
  } else {
    Serial.println("Failed to read BMP sensor");
    pressure_value = 0;
    temperature_value = 0;
  }
  
  // Print sensor values for debugging
  Serial.println("Sensor Readings:");
  Serial.print("  NH3: ");
  Serial.print(nh3_value);
  Serial.println(" ppm");
  
  Serial.print("  H2S: ");
  Serial.print(h2s_value);
  Serial.println(" ppm");
  
  Serial.print("  Pressure: ");
  Serial.print(pressure_value);
  Serial.println(" hPa");
  
  Serial.print("  Temperature: ");
  Serial.print(temperature_value);
  Serial.println(" °C");
}

void sendSensorData(float nh3, float h2s, float pressure, float temperature) {
  // Create JSON document for the payload
  StaticJsonDocument<512> doc;
  
  // Add device ID and timestamp
  doc["device_id"] = mqtt_client_id;
  doc["timestamp"] = millis() / 1000.0; // Simple timestamp
  
  // Create sensors object
  JsonObject sensors = doc.createNestedObject("sensors");
  
  // Add NH3 sensor data
  JsonObject nh3_sensor = sensors.createNestedObject("NH3");
  nh3_sensor["status"] = (nh3 > 0) ? "active" : "error";
  nh3_sensor["reading"] = nh3;
  
  // Add H2S sensor data
  JsonObject h2s_sensor = sensors.createNestedObject("H2S");
  h2s_sensor["status"] = (h2s > 0) ? "active" : "error";
  h2s_sensor["reading"] = h2s;
  
  // Add pressure sensor data
  JsonObject pressure_sensor = sensors.createNestedObject("pressure");
  pressure_sensor["status"] = (pressure > 0) ? "active" : "error";
  pressure_sensor["reading"] = pressure;
  
  // Add temperature data
  JsonObject temp_sensor = sensors.createNestedObject("temperature");
  temp_sensor["status"] = (temperature > -50) ? "active" : "error"; // Sanity check
  temp_sensor["reading"] = temperature;
  
  // Add aerator status (relay states)
  JsonObject aerator_status = doc.createNestedObject("aerator_status");
  aerator_status["relay3"] = relay_states[0] ? 1 : 0; // Map to relay3 in expected format
  aerator_status["relay4"] = relay_states[1] ? 1 : 0; // Map to relay4 in expected format
  
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
    
    // Try to reconnect and send again
    if (!client.connected()) {
      connectToMQTT();
      if (client.publish(mqtt_topic, payload.c_str())) {
        Serial.println("Payload sent after reconnection");
      } else {
        Serial.println("Failed to send payload even after reconnection");
      }
    }
  }
}

void checkRelayCycles() {
  // Check if any relay has exceeded the maximum number of cycles per day
  bool excessiveCycling = false;
  for (int i = 0; i < 4; i++) {
    if (relayCycleCount[i] > MAX_RELAY_CYCLES_PER_DAY) {
      Serial.print("WARNING: Relay ");
      Serial.print(i);
      Serial.print(" has cycled ");
      Serial.print(relayCycleCount[i]);
      Serial.println(" times, which exceeds the maximum allowed");
      excessiveCycling = true;
    }
  }
  
  // If any relay is cycling too much, we can take corrective action
  if (excessiveCycling) {
    // Create and send an alert message
    StaticJsonDocument<256> doc;
    doc["device_id"] = mqtt_client_id;
    doc["alert_type"] = "excessive_relay_cycling";
    doc["timestamp"] = millis() / 1000.0;
    
    JsonObject cycleData = doc.createNestedObject("cycle_counts");
    for (int i = 0; i < 4; i++) {
      String relayKey = "relay";
      relayKey += (i + 1);
      cycleData[relayKey] = relayCycleCount[i];
    }
    
    String payload;
    serializeJson(doc, payload);
    
    // Send to a different topic for alerts
    if (client.publish("sensor/alerts", payload.c_str())) {
      Serial.println("Alert sent successfully");
    }
    
    // We could also take corrective action here, such as disabling the relays
    // For now, we'll just log the issue
  }
}