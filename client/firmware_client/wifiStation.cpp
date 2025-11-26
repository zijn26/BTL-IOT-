#include "wifiStation.h"

WiFiStation::WiFiStation() 
    : _server(80), _dnsServer(), _isConfigMode(false), _isConnected(false), _lastCheck(0) {
    _apSSID = "ESP32_Config_" + String(random(1000, 9999));
    _apPassword = "";  // Không cần mật khẩu
}

void WiFiStation::begin() {
    Serial.println("🚀 [WiFiStation] Starting WiFi Station...");
    
    // Load cấu hình WiFi từ NVS
    loadWiFiConfig();
    
    // Kiểm tra xem có cấu hình WiFi đã lưu trước không
    if (_configSSID.length() > 0) {
        Serial.printf("📖 [WiFiStation] Found saved WiFi config: %s\n", _configSSID.c_str());
        Serial.println("🔄 [WiFiStation] Attempting to connect with retry mechanism...");
        
        // Thử kết nối WiFi với cơ chế retry 6 lần
        bool connected = connectToWiFiWithRetry(6);
        
        if (connected) {
            Serial.println("✅ [WiFiStation] WiFi connected successfully!");
            return; // Kết nối thành công, tiếp tục code
        } else {
            Serial.println("❌ [WiFiStation] Failed to connect after 6 attempts");
            Serial.println("📡 [WiFiStation] Starting config mode...");
            startConfigMode();
            waitForConnection();
        }
    } else {
        Serial.println("📡 [WiFiStation] No WiFi config found in NVS");
        Serial.println("📡 [WiFiStation] Starting config mode...");
        startConfigMode();
        waitForConnection();
    }
}

void WiFiStation::loop() {
    if (_isConfigMode) {
        _dnsServer.processNextRequest();
        _server.handleClient();
    } else {
        // Kiểm tra kết nối WiFi định kỳ
        if (millis() - _lastCheck > 30000) { // Mỗi 30 giây
            _lastCheck = millis();
            if (WiFi.status() != WL_CONNECTED) {
                Serial.println("⚠️ [WiFiStation] WiFi disconnected, attempting reconnect...");
                connectToWiFi();
            }
        }
    }
}

void WiFiStation::waitForConnection() {
    Serial.println("⏳ [WiFiStation] Waiting for WiFi connection...");
    Serial.println("📱 [WiFiStation] Please connect to WiFi and configure if needed");
    
    while (!isConnected()) {
        // Xử lý web server trong config mode
        if (_isConfigMode) {
            _dnsServer.processNextRequest();
            _server.handleClient();
        }
        
        // Kiểm tra kết nối WiFi
        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("✅ [WiFiStation] WiFi connected successfully!");
            Serial.printf("📡 [WiFiStation] SSID: %s\n", WiFi.SSID().c_str());
            Serial.printf("🌐 [WiFiStation] IP: %s\n", WiFi.localIP().toString().c_str());
            _isConnected = true;
            break;
        }
        
        delay(100);
    }
}

bool WiFiStation::isConnected() {
    _isConnected = (WiFi.status() == WL_CONNECTED);
    return _isConnected;
}

bool WiFiStation::isConfigMode() {
    return _isConfigMode;
}

String WiFiStation::getSSID() {
    return WiFi.SSID();
}

String WiFiStation::getIP() {
    return WiFi.localIP().toString();
}

void WiFiStation::setWiFiConfig(const String& ssid, const String& password) {
    _configSSID = ssid;
    _configPassword = password;
    saveWiFiConfig();
}

void WiFiStation::startConfigMode() {
    Serial.println("📡 [WiFiStation] Starting Access Point mode...");
    
    // Tạo Access Point không cần mật khẩu
    WiFi.mode(WIFI_AP);
    WiFi.softAP(_apSSID.c_str(), _apPassword.c_str());
    
    // Cấu hình DNS server để redirect tất cả traffic về ESP32
    _dnsServer.start(53, "*", WiFi.softAPIP());
    
    // Cấu hình web server
    _server.on("/", [this]() { handleRoot(); });
    _server.on("/config", HTTP_POST, [this]() { handleConfig(); });
    _server.on("/scan", HTTP_GET, [this]() { handleScan(); });
    _server.on("/status", HTTP_GET, [this]() { handleStatus(); });
    _server.on("/reset", HTTP_POST, [this]() { handleReset(); });
    _server.onNotFound([this]() { handleRoot(); });
    
    _server.begin();
    _isConfigMode = true;
    
    Serial.printf("✅ [WiFiStation] Access Point started: %s (No Password)\n", _apSSID.c_str());
    Serial.printf("📱 [WiFiStation] Connect to WiFi: %s\n", _apSSID.c_str());
    Serial.printf("🌐 [WiFiStation] Open browser: http://192.168.4.1\n");
}

void WiFiStation::stopConfigMode() {
    Serial.println("🛑 [WiFiStation] Stopping config mode...");
    
    _server.stop();
    _dnsServer.stop();
    WiFi.softAPdisconnect(true);
    WiFi.mode(WIFI_STA);
    
    _isConfigMode = false;
}

void WiFiStation::loadWiFiConfig() {
    Settings wifiSettings("wifi", true);
    
    _configSSID = wifiSettings.getString("ssid", "");
    _configPassword = wifiSettings.getString("password", "");
    
    Serial.printf("📖 [WiFiStation] Loaded config: SSID=%s\n", _configSSID.c_str());
}

void WiFiStation::saveWiFiConfig() {
    Settings wifiSettings("wifi", true);
    
    wifiSettings.setString("ssid", _configSSID);
    wifiSettings.setString("password", _configPassword);
    
    Serial.printf("💾 [WiFiStation] Saved config: SSID=%s\n", _configSSID.c_str());
}

void WiFiStation::connectToWiFi() {
    Serial.printf("🔗 [WiFiStation] Connecting to %s...\n", _configSSID.c_str());
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(_configSSID.c_str(), _configPassword.c_str());
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ [WiFiStation] WiFi connected!");
        Serial.printf("📡 [WiFiStation] SSID: %s\n", WiFi.SSID().c_str());
        Serial.printf("🌐 [WiFiStation] IP: %s\n", WiFi.localIP().toString().c_str());
        _isConnected = true;
    } else {
        Serial.println("\n❌ [WiFiStation] WiFi connection failed!");
        _isConnected = false;
    }
}

bool WiFiStation::connectToWiFiWithRetry(int maxRetries) {
    Serial.printf("🔄 [WiFiStation] Attempting to connect to %s (max %d retries)\n", _configSSID.c_str(), maxRetries);
    
    for (int attempt = 1; attempt <= maxRetries; attempt++) {
        Serial.printf("🔗 [WiFiStation] Attempt %d/%d: Connecting to %s...\n", attempt, maxRetries, _configSSID.c_str());
        
        WiFi.mode(WIFI_STA);
        WiFi.begin(_configSSID.c_str(), _configPassword.c_str());
        
        // Chờ kết nối trong 10 giây
        unsigned long startTime = millis();
        while (WiFi.status() != WL_CONNECTED && (millis() - startTime) < 10000) {
            delay(100);
        }
        
        if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("✅ [WiFiStation] WiFi connected on attempt %d!\n", attempt);
            Serial.printf("📡 [WiFiStation] SSID: %s\n", WiFi.SSID().c_str());
            Serial.printf("🌐 [WiFiStation] IP: %s\n", WiFi.localIP().toString().c_str());
            _isConnected = true;
            return true;
        } else {
            Serial.printf("❌ [WiFiStation] Attempt %d failed (Status: %d)\n", attempt, WiFi.status());
            if (attempt < maxRetries) {
                Serial.printf("⏳ [WiFiStation] Waiting 2 seconds before retry...\n");
                delay(2000);
            }
        }
    }
    
    Serial.printf("❌ [WiFiStation] All %d attempts failed!\n", maxRetries);
    _isConnected = false;
    return false;
}

void WiFiStation::handleRoot() {
    String html = generateHTML();
    _server.send(200, "text/html", html);
}

void WiFiStation::handleConfig() {
    if (_server.hasArg("ssid") && _server.hasArg("password")) {
        String ssid = _server.arg("ssid");
        String password = _server.arg("password");
        
        Serial.printf("🔧 [WiFiStation] Received config: SSID=%s\n", ssid.c_str());
        
        // Lưu cấu hình
        setWiFiConfig(ssid, password);
        
        // Gửi response
        _server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Config saved! Attempting to connect...\"}");
        
        // Dừng config mode và thử kết nối với retry
        delay(1000);
        stopConfigMode();
        
        Serial.println("🔄 [WiFiStation] Configuration saved, attempting connection with retry...");
        bool connected = connectToWiFiWithRetry(6);
        
        if (connected) {
            Serial.println("✅ [WiFiStation] WiFi connected successfully!");
            _isConnected = true;
        } else {
            Serial.println("❌ [WiFiStation] Failed to connect, returning to config mode...");
            startConfigMode();
        }
    } else {
        _server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing SSID or password\"}");
    }
}

void WiFiStation::handleScan() {
    Serial.println("🔍 [WiFiStation] Scanning for WiFi networks...");
    
    int n = WiFi.scanNetworks();
    String result = generateScanResults();
    
    _server.send(200, "application/json", result);
}

void WiFiStation::handleStatus() {
    String status = "{";
    status += "\"connected\":" + String(isConnected() ? "true" : "false") + ",";
    status += "\"ssid\":\"" + getSSID() + "\",";
    status += "\"ip\":\"" + getIP() + "\",";
    status += "\"configMode\":" + String(_isConfigMode ? "true" : "false");
    status += "}";
    
    _server.send(200, "application/json", status);
}

void WiFiStation::handleReset() {
    Serial.println("🔄 [WiFiStation] Resetting WiFi configuration...");
    
    // Xóa cấu hình WiFi
    Settings wifiSettings("wifi", true);
    wifiSettings.eraseAll();
    
    _server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"WiFi config reset! Device will restart...\"}");
    
    delay(2000);
    ESP.restart();
}

String WiFiStation::generateHTML() {
    String html = R"HTML(
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 WiFi Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
        button:hover { background-color: #45a049; }
        .scan-btn { background-color: #2196F3; margin-bottom: 10px; }
        .scan-btn:hover { background-color: #1976D2; }
        .reset-btn { background-color: #f44336; margin-top: 10px; }
        .reset-btn:hover { background-color: #d32f2f; }
        .status { margin-top: 20px; padding: 10px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .networks { margin-top: 10px; }
        .network-item { padding: 8px; margin: 5px 0; background-color: #f8f9fa; border-radius: 3px; cursor: pointer; }
        .network-item:hover { background-color: #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 ESP32 WiFi Configuration</h1>
        
        <div class="form-group">
            <label for="ssid">WiFi Network (SSID):</label>
            <input type="text" id="ssid" name="ssid" placeholder="Enter WiFi network name">
        </div>
        
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" placeholder="Enter WiFi password">
        </div>
        
        <button class="scan-btn" onclick="scanNetworks()">🔍 Scan for Networks</button>
        <div id="networks" class="networks"></div>
        
        <button onclick="saveConfig()">💾 Save Configuration</button>
        <button class="reset-btn" onclick="resetConfig()">🔄 Reset Configuration</button>
        
        <div id="status"></div>
    </div>

    <script>
        function scanNetworks() {
            document.getElementById('networks').innerHTML = 'Scanning...';
            fetch('/scan')
                .then(response => response.json())
                .then(data => {
                    let html = '<h3>Available Networks:</h3>';
                    data.networks.forEach(network => {
                        html += `<div class="network-item" onclick="selectNetwork('${network.ssid}')">
                            <strong>${network.ssid}</strong> (${network.rssi} dBm, ${network.encryption})
                        </div>`;
                    });
                    document.getElementById('networks').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('networks').innerHTML = 'Error scanning networks';
                });
        }
        
        function selectNetwork(ssid) {
            document.getElementById('ssid').value = ssid;
        }
        
        function saveConfig() {
            const ssid = document.getElementById('ssid').value;
            const password = document.getElementById('password').value;
            
            if (!ssid) {
                showStatus('Please enter WiFi network name', 'error');
                return;
            }
            
            showStatus('Saving configuration...', 'success');
            
            fetch('/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `ssid=${encodeURIComponent(ssid)}&password=${encodeURIComponent(password)}`
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.message, data.status === 'success' ? 'success' : 'error');
                if (data.status === 'success') {
                    setTimeout(() => {
                        showStatus('Device is restarting... Please wait and reconnect to your WiFi network.', 'success');
                    }, 2000);
                }
            })
            .catch(error => {
                showStatus('Error saving configuration', 'error');
            });
        }
        
        function resetConfig() {
            if (confirm('Are you sure you want to reset WiFi configuration?')) {
                fetch('/reset', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        showStatus(data.message, 'success');
                        setTimeout(() => {
                            showStatus('Device is restarting...', 'success');
                        }, 2000);
                    })
                    .catch(error => {
                        showStatus('Error resetting configuration', 'error');
                    });
            }
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        // Auto-scan on page load
        window.onload = function() {
            scanNetworks();
        };
    </script>
</body>
</html>
)HTML";
    return html;
}

String WiFiStation::generateScanResults() {
    int n = WiFi.scanNetworks();
    String result = "{\"networks\":[";
    
    for (int i = 0; i < n; i++) {
        if (i > 0) result += ",";
        result += "{";
        result += "\"ssid\":\"" + WiFi.SSID(i) + "\",";
        result += "\"rssi\":" + String(WiFi.RSSI(i)) + ",";
        result += "\"encryption\":\"" + String((WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Secured") + "\"";
        result += "}";
    }
    
    result += "]}";
    return result;
}
