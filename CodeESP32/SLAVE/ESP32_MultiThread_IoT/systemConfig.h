#ifndef SYSTEM_CONFIG_H
#define SYSTEM_CONFIG_H

// ======= System Configuration =======
#define SYSTEM_VERSION "1.0.0"
#define DEVICE_NAME "ESP32_IoT_Slave"

// ======= Task Configuration =======
#define WIFI_TASK_STACK_SIZE 4096
#define MQTT_TASK_STACK_SIZE 4096
#define GPIO_TASK_STACK_SIZE 4096
#define SENSOR_TASK_STACK_SIZE 4096

#define WIFI_TASK_PRIORITY 2
#define MQTT_TASK_PRIORITY 3
#define GPIO_TASK_PRIORITY 2
#define SENSOR_TASK_PRIORITY 1

// ======= Core Assignment =======
#define WIFI_TASK_CORE 0
#define MQTT_TASK_CORE 1
#define GPIO_TASK_CORE 0
#define SENSOR_TASK_CORE 1

// ======= Timing Configuration =======
#define WIFI_CHECK_INTERVAL 1000    // 1 second
#define MQTT_LOOP_INTERVAL 100       // 100ms
#define GPIO_LOOP_INTERVAL 100       // 100ms
#define SENSOR_READ_INTERVAL 5000    // 5 seconds
#define STATUS_REPORT_INTERVAL 10000 // 10 seconds

// ======= Queue Configuration =======
#define SENSOR_QUEUE_SIZE 10
#define COMMAND_QUEUE_SIZE 10

// ======= GPIO Configuration =======
#define BUILTIN_LED_PIN 2
#define DEFAULT_INPUT_PIN 4
#define DEFAULT_OUTPUT_PIN 5
#define DEFAULT_PWM_PIN 18
#define DEFAULT_PWM_CHANNEL 0
#define DEFAULT_PWM_FREQUENCY 1000

// ======= MQTT Configuration =======
#define MQTT_TOPIC_COMMANDS "device/commands"
#define MQTT_TOPIC_GPIO "device/gpio"
#define MQTT_TOPIC_LED "device/led"
#define MQTT_TOPIC_STATUS "device/status"
#define MQTT_TOPIC_SENSORS_PREFIX "sensors/"

// ======= WiFi Configuration =======
#define WIFI_RETRY_COUNT 6
#define WIFI_CONNECT_TIMEOUT 10000
#define WIFI_RETRY_DELAY 2000

// ======= Debug Configuration =======
#define DEBUG_SERIAL_BAUD 115200
#define DEBUG_ENABLED true

// ======= Memory Configuration =======
#define MIN_FREE_HEAP_WARNING 10000  // Warning if free heap < 10KB

#endif
