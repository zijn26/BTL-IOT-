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
    setInputPin(2, true);   // Built-in LED (with pullup)
    setOutputPin(2, false); // Built-in LED
    setInputPin(4, true);    // Example input pin
    setOutputPin(5, false); // Example output pin
    setPWMChannel(18, 0, 1000); // Example PWM pin
    
    _initialized = true;
    Serial.println("✅ [GPIOManager] GPIO Manager initialized");
}

void GPIOManager::loop() {
    if (!_initialized) return;
    
    // Read sensor data every 5 seconds
    if (millis() - _lastDataSend > 5000) {
        readSensors();
        sendSensorData();
        _lastDataSend = millis();
    }
}

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
    
    ledcSetup(channel, frequency, 8); // 8-bit resolution
    ledcAttachPin(pin, channel);
    
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
    ledcWrite(_pinConfigs[pin].pwmChannel, dutyCycle);
}

void GPIOManager::addSensorData(const String& sensorName, float value) {
    if (_sensorData.length() > 0) _sensorData += ",";
    _sensorData += "\"" + sensorName + "\":" + String(value, 2);
}

void GPIOManager::addSensorData(const String& sensorName, int value) {
    if (_sensorData.length() > 0) _sensorData += ",";
    _sensorData += "\"" + sensorName + "\":" + String(value);
}

void GPIOManager::addSensorData(const String& sensorName, const String& value) {
    if (_sensorData.length() > 0) _sensorData += ",";
    _sensorData += "\"" + sensorName + "\":\"" + value + "\"";
}

void GPIOManager::processCommand(const String& command, const String& value) {
    Serial.printf("🎛️ [GPIOManager] Processing command: %s = %s\n", command.c_str(), value.c_str());
    
    if (command.startsWith("pin_")) {
        int pin = command.substring(4).toInt();
        
        if (command.endsWith("_digital")) {
            bool state = (value == "1" || value == "true" || value == "HIGH");
            writeDigital(pin, state);
            Serial.printf("📤 [GPIOManager] Pin %d set to %s\n", pin, state ? "HIGH" : "LOW");
        }
        else if (command.endsWith("_pwm")) {
            int dutyCycle = value.toInt();
            writePWM(pin, dutyCycle);
            Serial.printf("🌊 [GPIOManager] Pin %d PWM set to %d%%\n", pin, dutyCycle);
        }
        else if (command.endsWith("_analog")) {
            int analogValue = value.toInt();
            writeAnalog(pin, analogValue);
            Serial.printf("📊 [GPIOManager] Pin %d analog set to %d\n", pin, analogValue);
        }
    }
    else if (command == "led") {
        bool state = (value == "1" || value == "true" || value == "on");
        writeDigital(2, state); // Built-in LED
        Serial.printf("💡 [GPIOManager] LED %s\n", state ? "ON" : "OFF");
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

void GPIOManager::readSensors() {
    _sensorData = "{";
    
    // Read digital inputs
    addSensorData("pin_2_digital", readDigital(2));
    addSensorData("pin_4_digital", readDigital(4));
    
    // Read analog inputs
    addSensorData("pin_36_analog", readAnalog(36));
    addSensorData("pin_39_analog", readAnalog(39));
    
    // Add system info
    addSensorData("uptime", millis() / 1000);
    addSensorData("free_heap", ESP.getFreeHeap());
    addSensorData("temperature", temperatureRead());
    
    _sensorData += "}";
}

void GPIOManager::sendSensorData() {
    // This will be called from the MQTT thread
    Serial.printf("📊 [GPIOManager] Sensor data: %s\n", _sensorData.c_str());
}
