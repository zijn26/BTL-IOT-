// ESP32_MultiThread_IoT.ino
#include "wifiStation.h"
#include "settings.h"
#include "mqtt.h"
#include "gpioManager.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

// ======= Global References =======
WiFiStation* wifi;
MQTTProtocol* mqtt;
GPIOManager* gpio;

// ======= FreeRTOS Objects =======
QueueHandle_t sensorDataQueue;
QueueHandle_t commandQueue;
SemaphoreHandle_t mqttMutex;

// ======= Data Structures =======
struct SensorData {
    String sensorName;
    String value;
    unsigned long timestamp;
};

struct CommandData {
    String command;
    String value;
    unsigned long timestamp;
};

// ======= Task Handles =======
TaskHandle_t wifiTaskHandle = NULL;
TaskHandle_t mqttTaskHandle = NULL;
TaskHandle_t gpioTaskHandle = NULL;
TaskHandle_t sensorTaskHandle = NULL;

// ======= Task Functions =======
void wifiTask(void* parameter);
void mqttTask(void* parameter);
void gpioTask(void* parameter);
void sensorTask(void* parameter);

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
    mqtt->updateConfig("192.168.1.100", 1883, "esp32", "password");
    mqtt->begin();
    mqtt->setCallback(mqttCallback);
    
    // Initialize GPIO
    gpio->begin();
    
    // Create FreeRTOS objects
    sensorDataQueue = xQueueCreate(10, sizeof(SensorData));
    commandQueue = xQueueCreate(10, sizeof(CommandData));
    mqttMutex = xSemaphoreCreateMutex();
    
    if (sensorDataQueue == NULL || commandQueue == NULL || mqttMutex == NULL) {
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
        sensorTask,         // Task function
        "SensorTask",       // Task name
        4096,               // Stack size
        NULL,               // Parameters
        1,                  // Priority
        &sensorTaskHandle,  // Task handle
        1                   // Core 1
    );
    
    Serial.println("✅ All tasks created successfully!");
    Serial.printf("📊 Free heap after setup: %d bytes\n", ESP.getFreeHeap());
    
    // Subscribe to MQTT topics
    if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
        mqtt->subscribe("device/commands");
        mqtt->subscribe("device/gpio");
        mqtt->subscribe("device/led");
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
            SensorData sensorData;
            if (xQueueReceive(sensorDataQueue, &sensorData, 0) == pdTRUE) {
                if (xSemaphoreTake(mqttMutex, pdMS_TO_TICKS(100))) {
                    String topic = "sensors/" + sensorData.sensorName;
                    mqtt->publish(topic.c_str(), sensorData.value);
                    Serial.printf("📤 [MQTTTask] Published: %s = %s\n", 
                                  topic.c_str(), sensorData.value.c_str());
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
        gpio->loop();
        
        // Process command queue
        CommandData commandData;
        if (xQueueReceive(commandQueue, &commandData, 0) == pdTRUE) {
            gpio->processCommand(commandData.command, commandData.value);
        }
        
        vTaskDelay(pdMS_TO_TICKS(100)); // 100ms
    }
}

// ======= Sensor Task (Core 1) =======
void sensorTask(void* parameter) {
    Serial.println("🌡️ [SensorTask] Started on Core 1");
    
    while (true) {
        // Read sensors and send data
        SensorData sensorData;
        
        // Read digital pins
        sensorData.sensorName = "pin_2";
        sensorData.value = String(gpio->readDigital(2));
        sensorData.timestamp = millis();
        xQueueSend(sensorDataQueue, &sensorData, pdMS_TO_TICKS(10));
        
        sensorData.sensorName = "pin_4";
        sensorData.value = String(gpio->readDigital(4));
        sensorData.timestamp = millis();
        xQueueSend(sensorDataQueue, &sensorData, pdMS_TO_TICKS(10));
        
        // Read analog pins
        sensorData.sensorName = "pin_36_analog";
        sensorData.value = String(gpio->readAnalog(36));
        sensorData.timestamp = millis();
        xQueueSend(sensorDataQueue, &sensorData, pdMS_TO_TICKS(10));
        
        // System info
        sensorData.sensorName = "system_uptime";
        sensorData.value = String(millis() / 1000);
        sensorData.timestamp = millis();
        xQueueSend(sensorDataQueue, &sensorData, pdMS_TO_TICKS(10));
        
        sensorData.sensorName = "system_free_heap";
        sensorData.value = String(ESP.getFreeHeap());
        sensorData.timestamp = millis();
        xQueueSend(sensorDataQueue, &sensorData, pdMS_TO_TICKS(10));
        
        vTaskDelay(pdMS_TO_TICKS(5000)); // 5 seconds
    }
}

// ======= MQTT Callback =======
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String message = "";
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    Serial.printf("📨 [MQTT] Received: %s = %s\n", topic, message.c_str());
    
    // Process different topics
    String topicStr = String(topic);
    
    if (topicStr == "device/commands") {
        // Parse JSON command
        CommandData commandData;
        commandData.command = "system_command";
        commandData.value = message;
        commandData.timestamp = millis();
        xQueueSend(commandQueue, &commandData, pdMS_TO_TICKS(10));
    }
    else if (topicStr == "device/gpio") {
        // Parse GPIO command
        CommandData commandData;
        commandData.command = "gpio_command";
        commandData.value = message;
        commandData.timestamp = millis();
        xQueueSend(commandQueue, &commandData, pdMS_TO_TICKS(10));
    }
    else if (topicStr == "device/led") {
        // LED control
        CommandData commandData;
        commandData.command = "led";
        commandData.value = message;
        commandData.timestamp = millis();
        xQueueSend(commandQueue, &commandData, pdMS_TO_TICKS(10));
    }
}
