#include "gpioManager.h"

GPIOManager::GPIOManager() : _initialized(false), _lastDataSend(0) {
    // Initialize pin configurations
    for (int i = 0; i < 40; i++) {
        _pinConfigs[i].pin = i;
        _pinConfigs[i].mode = -1;
        _pinConfigs[i].pwmChannel = -1;
        _pinConfigs[i].frequency = 1000;
        _pinConfigs[i].isConfigured = false;
    }
}

void GPIOManager::begin() {
    Serial.println("🔌 [GPIOManager] Initializing GPIO Manager...");
    
    // Load GPIO configuration from NVS
    loadGPIOConfig();
    
    // Configure default pins
    // setOutputPin(2, false); // Built-in LED
    
    _initialized = true;
    Serial.println("✅ [GPIOManager] GPIO Manager initialized");
}

// void GPIOManager::loop() {
//     if (!_initialized) return;
    
//     // Read sensor data every 5 seconds
//     if (millis() - _lastDataSend > 5000) {
//         // readSensors();
//         // sendSensorData();
//         // _lastDataSend = millis();
//     }
// }

void GPIOManager::setInputPin(int pin, bool pullup) {
    if (pin < 0 || pin >= 40) return;
    
    pinMode(pin, pullup ? INPUT_PULLUP : INPUT);
    _pinConfigs[pin].mode = pullup ? INPUT_PULLUP : INPUT;
    _pinConfigs[pin].isConfigured = true;
    
    Serial.printf("📥 [GPIOManager] Pin %d configured as INPUT%s\n", 
                  pin, pullup ? "_PULLUP" : "");
}

void GPIOManager::setOutputPin(int pin, bool initialValue) {
    if (pin < 0 || pin >= 40) return;
    
    pinMode(pin, OUTPUT);
    digitalWrite(pin, initialValue);
    _pinConfigs[pin].mode = OUTPUT;
    _pinConfigs[pin].isConfigured = true;
    
    Serial.printf("📤 [GPIOManager] Pin %d configured as OUTPUT (initial: %s)\n", 
                  pin, initialValue ? "HIGH" : "LOW");
}

void GPIOManager::setPWMChannel(int pin, int channel, int frequency) {
    if (pin < 0 || pin >= 40 || channel < 0 || channel > 15) return;
    
    // ESP32 core 3.x uses ledcAttach with parameters: pin, freq, resolution
    ledcAttach(pin, frequency, 8); // 8-bit resolution
    
    _pinConfigs[pin].mode = OUTPUT;
    _pinConfigs[pin].pwmChannel = channel;
    _pinConfigs[pin].frequency = frequency;
    _pinConfigs[pin].isConfigured = true;
    
    Serial.printf("🌊 [GPIOManager] Pin %d configured as PWM (channel: %d, freq: %d Hz)\n", 
                  pin, channel, frequency);
}

bool GPIOManager::readDigital(int pin) {
    if (pin < 0 || pin >= 40 || !_pinConfigs[pin].isConfigured) return false;
    return digitalRead(pin);
}

void GPIOManager::writeDigital(int pin, bool value) {
    if (pin < 0 || pin >= 40 || !_pinConfigs[pin].isConfigured) return;
    digitalWrite(pin, value);
}

int GPIOManager::readAnalog(int pin) {
    if (pin < 0 || pin >= 40) return 0;
    return analogRead(pin);
}

void GPIOManager::writeAnalog(int pin, int value) {
    if (pin < 0 || pin >= 40) return;
    analogWrite(pin, value);
}

void GPIOManager::writePWM(int pin, int dutyCycle) {
    if (pin < 0 || pin >= 40 || !_pinConfigs[pin].isConfigured) return;
    if (_pinConfigs[pin].pwmChannel < 0) return;
    
    dutyCycle = constrain(dutyCycle, 0, 255);
    // ESP32 core 3.x uses pin instead of channel
    ledcWrite(pin, dutyCycle);
}

// void GPIOManager::addSensorData(const String& sensorName, float value) {
//     if (_sensorData.length() > 0) _sensorData += ",";
//     _sensorData += "\"" + sensorName + "\":" + String(value, 2);
// }

// void GPIOManager::addSensorData(const String& sensorName, int value) {
//     if (_sensorData.length() > 0) _sensorData += ",";
//     _sensorData += "\"" + sensorName + "\":" + String(value);
// }

// void GPIOManager::addSensorData(const String& sensorName, const String& value) {
//     if (_sensorData.length() > 0) _sensorData += ",";
//     _sensorData += "\"" + sensorName + "\":\"" + value + "\"";
// }

void GPIOManager::processCommand(const int virtualPin, const String& message , bool isDigital) {
    Serial.printf("🎛️ [GPIOManager] Processing command: %d = %s\n", virtualPin, message.c_str());
    if (isDigital) {
        bool state = false;
        if(message == "true" || message == "HIGH" ) state = true;
            else if(message == "false" || message == "LOW") state = false;
                else state = (message.toInt() >=1 )? true : false;
        
        writeDigital(virtualPin, state);
        Serial.printf("📤 [GPIOManager] Pin %d set to %s\n", virtualPin, state ? "HIGH" : "LOW");
    }
    else if (!isDigital) {
        float value = message.toFloat();
        writeAnalog(virtualPin, (int)value);   
        Serial.printf("📊 [GPIOManager] Pin %d analog set to %f\n", virtualPin, value);
    }
}

String GPIOManager::getStatus() const {
    String status = "{";
    status += "\"initialized\":" + String(_initialized ? "true" : "false") + ",";
    status += "\"configured_pins\":[";
    
    bool first = true;
    for (int i = 0; i < 40; i++) {
        if (_pinConfigs[i].isConfigured) {
            if (!first) status += ",";
            status += "{";
            status += "\"pin\":" + String(i) + ",";
            status += "\"mode\":" + String(_pinConfigs[i].mode) + ",";
            status += "\"pwm_channel\":" + String(_pinConfigs[i].pwmChannel) + ",";
            status += "\"frequency\":" + String(_pinConfigs[i].frequency);
            status += "}";
            first = false;
        }
    }
    
    status += "]}";
    return status;
}

void GPIOManager::loadGPIOConfig() {
    Settings gpioSettings("gpio", true);
    
    // Load pin configurations
    for (int i = 0; i < 40; i++) {
        String pinKey = "pin_" + String(i);
        int mode = gpioSettings.getInt(pinKey + "_mode", -1);
        
        if (mode != -1) {
            _pinConfigs[i].mode = mode;
            _pinConfigs[i].pwmChannel = gpioSettings.getInt(pinKey + "_pwm", -1);
            _pinConfigs[i].frequency = gpioSettings.getInt(pinKey + "_freq", 1000);
            _pinConfigs[i].isConfigured = true;
        }
    }
    
    Serial.println("📖 [GPIOManager] GPIO configuration loaded from NVS");
}

void GPIOManager::saveGPIOConfig() {
    Settings gpioSettings("gpio", true);
    
    // Save pin configurations
    for (int i = 0; i < 40; i++) {
        if (_pinConfigs[i].isConfigured) {
            String pinKey = "pin_" + String(i);
            gpioSettings.setInt(pinKey + "_mode", _pinConfigs[i].mode);
            gpioSettings.setInt(pinKey + "_pwm", _pinConfigs[i].pwmChannel);
            gpioSettings.setInt(pinKey + "_freq", _pinConfigs[i].frequency);
        }
    }
    
    Serial.println("💾 [GPIOManager] GPIO configuration saved to NVS");
}

// void GPIOManager::readSensors() {
//     _sensorData = "{";
    
//     // Read digital inputs
//     addSensorData("pin_2_digital", readDigital(2));
//     addSensorData("pin_4_digital", readDigital(4));
    
//     // Read analog inputs
//     addSensorData("pin_36_analog", readAnalog(36));
//     addSensorData("pin_39_analog", readAnalog(39));
    
//     // Add system info
//     addSensorData("uptime", millis() / 1000);
//     addSensorData("free_heap", ESP.getFreeHeap());
//     addSensorData("temperature", temperatureRead());
    
//     _sensorData += "}";
// }

// void GPIOManager::sendSensorData() {
//     // This will be called from the MQTT thread
//     Serial.printf("📊 [GPIOManager] Sensor data: %s\n", _sensorData.c_str());
// }
