#include "wifiStation.h"
#include "settings.h"
#include "mqtt.h"
#include "gpioManager.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include "DHT.h"
#define CLIENT_ID "066420c45a4e819437bbfbea63b83739"
// ======= Global References =======
WiFiStation* wifi;
MQTTProtocol* mqtt;
GPIOManager* gpio;
#define DHTPIN 5
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
// ======= FreeRTOS Objects =======
QueueHandle_t deviceDataQueue;
QueueHandle_t commandQueue;
SemaphoreHandle_t mqttMutex;

// ======= Data Structures =======
struct DeviceData {
    int pin;
    int VirtualPin;
    String value;
    unsigned long timestamp;
};

struct CommandData {
    int VirtualPin;
    String Message;
    unsigned long timestamp;
};

// ======= Task Handles =======
TaskHandle_t wifiTaskHandle = NULL;
TaskHandle_t mqttTaskHandle = NULL;
TaskHandle_t gpioTaskHandle = NULL;
TaskHandle_t readTaskHandle = NULL;

// ======= Task Functions =======
void wifiTask(void* parameter);
void mqttTask(void* parameter);
void gpioTask(void* parameter);
void ReadDataTask(void* parameter);

// ======= MQTT Callback =======
void mqttCallback(char* topic, byte* payload, unsigned int length);

// ======= Setup Function =======
void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("🚀 Starting ESP32 Multi-Thread IoT Device...");
    Serial.printf("📊 Free heap at start: %d bytes\n", ESP.getFreeHeap());
    
    // Initialize NVS
    Settings::initializeNVS();
    
    // Get singleton references
    wifi = &WiFiStation::getInstance();
    mqtt = &MQTTProtocol::getInstance();
    gpio = &GPIOManager::getInstance();
    
    // Initialize WiFi (blocking until connected)
    wifi->begin();
    
    // Initialize MQTT
    mqtt->updateConfig("10.1.1.20", 1883, CLIENT_ID);
    mqtt->begin();
    mqtt->setCallback(mqttCallback);
    
    // Initialize GPIO
    gpio->begin();
    gpio->setOutputPin(4, true);
    gpio->saveGPIOConfig(); // luu cau hinh GPIO vao NVS
    dht.begin(); // chan 5 lam cam bien nhiet do 

    // Create FreeRTOS objects
    deviceDataQueue = xQueueCreate(10, sizeof(DeviceData));
    commandQueue = xQueueCreate(10, sizeof(CommandData));
    mqttMutex = xSemaphoreCreateMutex();
    
    if (deviceDataQueue == NULL || commandQueue == NULL || mqttMutex == NULL) {
        Serial.println("❌ Failed to create FreeRTOS objects!");
        return;
    }
    
    // Create tasks
    xTaskCreatePinnedToCore(
        wifiTask,           // Task function
        "WiFiTask",         // Task name
        4096,               // Stack size
        NULL,               // Parameters
        2,                  // Priority
        &wifiTaskHandle,    // Task handle
        0                   // Core 0
    );
    
    xTaskCreatePinnedToCore(
        mqttTask,           // Task function
        "MQTTTask",         // Task name
        4096,               // Stack size
        NULL,               // Parameters
        3,                  // Priority
        &mqttTaskHandle,    // Task handle
        1                   // Core 1
    );
    
    xTaskCreatePinnedToCore(
        gpioTask,           // Task function
        "GPIOTask",         // Task name
        4096,               // Stack size
        NULL,               // Parameters
        2,                  // Priority
        &gpioTaskHandle,    // Task handle
        0                   // Core 0
    );
    
    xTaskCreatePinnedToCore(
        ReadDataTask,         // Task function
        "SensorTask",       // Task name
        4096,               // Stack size
        NULL,               // Parameters
        1,                  // Priority
        &readTaskHandle,  // Task handle
        1                   // Core 1
    );
    
    Serial.println("✅ All tasks created successfully!");
    Serial.printf("📊 Free heap after setup: %d bytes\n", ESP.getFreeHeap());
    
    // Subscribe to MQTT topics
    //111111
    if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
        mqtt->subscribe((String("CT/") + CLIENT_ID + "/4").c_str());//// lay cai dat tu web
        mqtt->subscribe((String("SS/") + CLIENT_ID + "/5").c_str());//// lay cai dat tu web
        // mqtt->subscribe("device/gpio");
        // mqtt->subscribe("device/led");
        xSemaphoreGive(mqttMutex);
    }
    
    Serial.println("🎉 Setup completed successfully!");
}

// ======= Loop Function =======
void loop() {
    // Main loop is now handled by FreeRTOS tasks
    // This loop can be used for monitoring or low-priority tasks
    vTaskDelay(pdMS_TO_TICKS(10000)); // 10 seconds
    
    Serial.printf("📊 System Status - Free heap: %d bytes, Uptime: %d seconds\n", 
                  ESP.getFreeHeap(), millis() / 1000);
}

// ======= WiFi Task (Core 0) =======
void wifiTask(void* parameter) {
    Serial.println("📡 [WiFiTask] Started on Core 0");
    
    while (true) {
        wifi->loop();
        
        // Check WiFi status
        if (!wifi->isConnected()) {
            Serial.println("⚠️ [WiFiTask] WiFi disconnected!");
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000)); // 1 second
    }
}

// ======= MQTT Task (Core 1) =======
void mqttTask(void* parameter) {
    Serial.println("📨 [MQTTTask] Started on Core 1");
    
    while (true) {
        if (wifi->isConnected()) {
            if (xSemaphoreTake(mqttMutex, pdMS_TO_TICKS(100))) {
                mqtt->loop();
                xSemaphoreGive(mqttMutex);
            }
            
            // Process sensor data queue
            DeviceData deviceData;
            if (xQueueReceive(deviceDataQueue, &deviceData, 0) == pdTRUE) {
                if (xSemaphoreTake(mqttMutex, pdMS_TO_TICKS(100))) {
                    String topic = String("SS/") + CLIENT_ID + "/";
                    topic = topic + String(deviceData.VirtualPin);

                    mqtt->publish(topic.c_str(), deviceData.value , false );
                    Serial.printf("📤 [MQTTTask] Published: %s = %s\n", 
                                  topic.c_str(), deviceData.value.c_str());
                    xSemaphoreGive(mqttMutex);
                }
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(100)); // 100ms
    }
}

// ======= GPIO Task (Core 0) =======
void gpioTask(void* parameter) {
    Serial.println("🔌 [GPIOTask] Started on Core 0");
    
    while (true) {
        // gpio->loop();
        
        // Process command queue
        CommandData commandData;
        if (xQueueReceive(commandQueue, &commandData, 0) == pdTRUE) {
            if(commandData.Message.substring(0 , 2) == "ER") {
                Serial.printf("📤 [ERROR] SERVER ERROR: %s ", 
                    commandData.Message.c_str());
                continue;
            }
            gpio->processCommand(commandData.VirtualPin, commandData.Message , 1);
        }
        
        vTaskDelay(pdMS_TO_TICKS(100)); // 100ms
    }
}

// ======= Sensor Task (Core 1) =======
void ReadDataTask(void* parameter) {
    Serial.println("🌡️ [SensorTask] Started on Core 1");
    float t ;
    float h ;
    while (true) {
         h = dht.readHumidity();
         t = dht.readTemperature();
        //222222
        // Read sensors and send data
        DeviceData deviceData;
        
        // Read digital pins
        deviceData.pin = 5;
        deviceData.VirtualPin = 5;
        deviceData.value = String(t);
        deviceData.timestamp = millis();
        xQueueSend(deviceDataQueue, &deviceData, pdMS_TO_TICKS(10));
        
        // sensorData.sensorName = "pin_4";
        // sensorData.value = String(gpio->readDigital(4));
        // sensorData.timestamp = millis();
        // xQueueSend(deviceDataQueue, &deviceData, pdMS_TO_TICKS(10));
        
        // // Read analog pins
        // sensorData.sensorName = "pin_36_analog";
        // sensorData.value = String(gpio->readAnalog(36));
        // sensorData.timestamp = millis();
        // xQueueSend(deviceDataQueue, &deviceData, pdMS_TO_TICKS(10));
        
        // // System info
        // sensorData.sensorName = "system_uptime";
        // sensorData.value = String(millis() / 1000);
        // sensorData.timestamp = millis();
        // xQueueSend(deviceDataQueue, &deviceData, pdMS_TO_TICKS(10));
        
        // sensorData.sensorName = "system_free_heap";
        // sensorData.value = String(ESP.getFreeHeap());
        // sensorData.timestamp = millis();
        // xQueueSend(deviceDataQueue, &deviceData, pdMS_TO_TICKS(10));
        
        vTaskDelay(pdMS_TO_TICKS(8000)); // 5 seconds
    }
}

// ======= MQTT Callback =======
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String message = "";
    for (int i = 0; i < length; i++) {
        message = message + String((char)payload[i]);
    }
    
    Serial.printf("📨 [MQTT] Received: %s = %s\n", topic, message.c_str());
    
    // Process different topics
    String topicStr = String(topic);
    String type = topicStr.substring(0, topicStr.indexOf("/"));
    String clientId = topicStr.substring(topicStr.indexOf("/") + 1, topicStr.lastIndexOf("/"));
    String virtualPin = topicStr.substring(topicStr.lastIndexOf("/") + 1);

    // giai nen message dangj json 
    if (type == "CT") {
        // Parse JSON command
        CommandData commandData;
        commandData.VirtualPin = virtualPin.toInt();
        commandData.Message =  String(message);
        commandData.timestamp = millis();
        xQueueSend(commandQueue, &commandData, pdMS_TO_TICKS(10));
    } else if (type == "SS") {
        // Parse JSON command
        CommandData commandData;
        commandData.VirtualPin = virtualPin.toInt();
        commandData.Message = "ER "+String(message);
        commandData.timestamp = millis();
        xQueueSend(commandQueue, &commandData, pdMS_TO_TICKS(10));
    }
}
