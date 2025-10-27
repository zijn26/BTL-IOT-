#ifndef WIFI_STATION_H
#define WIFI_STATION_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include "settings.h"

class WiFiStation {
public:
    // ======= Singleton Accessor =======
    static WiFiStation& getInstance() {
        static WiFiStation instance;
        return instance;
    }

    // ======= Public API =======
    void begin();
    void loop();
    void waitForConnection();  // Chặn code cho đến khi WiFi kết nối thành công
    
    // Kiểm tra trạng thái WiFi
    bool isConnected();
    bool isConfigMode();
    String getSSID();
    String getIP();
    
    // Cấu hình WiFi từ code
    void setWiFiConfig(const String& ssid, const String& password);
    
    // Bắt đầu chế độ cấu hình (Access Point)
    void startConfigMode();
    
    // Dừng chế độ cấu hình
    void stopConfigMode();

    // Cấm copy & gán
    WiFiStation(const WiFiStation&) = delete;
    WiFiStation& operator=(const WiFiStation&) = delete;

private:
    // ======= Private constructor =======
    WiFiStation();

    // ======= Private members =======
    WebServer _server;
    DNSServer _dnsServer;
    
    String _configSSID;
    String _configPassword;
    String _apSSID;
    String _apPassword;
    
    bool _isConfigMode;
    bool _isConnected;
    unsigned long _lastCheck;
    
    // ======= Private methods =======
    void loadWiFiConfig();
    void saveWiFiConfig();
    void connectToWiFi();
    bool connectToWiFiWithRetry(int maxRetries);
    void handleRoot();
    void handleConfig();
    void handleScan();
    void handleStatus();
    void handleReset();
    void startAP();
    void stopAP();
    String generateHTML();
    String generateScanResults();
};

#endif
