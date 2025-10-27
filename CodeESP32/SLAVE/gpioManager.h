#ifndef GPIO_MANAGER_H
#define GPIO_MANAGER_H

#include <Arduino.h>
#include "settings.h"

class GPIOManager {
public:
    // ======= Singleton Accessor =======
    static GPIOManager& getInstance() {
        static GPIOManager instance;
        return instance;
    }

    // ======= Public API =======
    void begin();
    void loop();
    
    // GPIO Configuration
    void setInputPin(int pin, bool pullup = true);
    void setOutputPin(int pin, bool initialValue = false);
    void setPWMChannel(int pin, int channel, int frequency = 1000);
    
    // GPIO Operations
    bool readDigital(int pin);
    void writeDigital(int pin, bool value);
    int readAnalog(int pin);
    void writeAnalog(int pin, int value);
    void writePWM(int pin, int dutyCycle);
    
    // Data Management
    void addSensorData(const String& sensorName, float value);
    void addSensorData(const String& sensorName, int value);
    void addSensorData(const String& sensorName, const String& value);
    
    // Command Processing
    void processCommand(const String& command, const String& value);
    
    // Status
    bool isInitialized() const { return _initialized; }
    String getStatus() const;

    // Cấm copy & gán
    GPIOManager(const GPIOManager&) = delete;
    GPIOManager& operator=(const GPIOManager&) = delete;

private:
    // ======= Private constructor =======
    GPIOManager();

    // ======= Private members =======
    bool _initialized;
    String _sensorData;
    unsigned long _lastDataSend;
    
    // GPIO Configuration
    struct PinConfig {
        int pin;
        int mode;        // INPUT, OUTPUT, INPUT_PULLUP
        int pwmChannel;  // -1 if not PWM
        int frequency;   // PWM frequency
        bool isConfigured;
    };
    
    PinConfig _pinConfigs[40]; // ESP32 has 40 GPIO pins
    
    // ======= Private methods =======
    void loadGPIOConfig();
    void saveGPIOConfig();
    void sendSensorData();
    void parseCommand(const String& command);
};

#endif
