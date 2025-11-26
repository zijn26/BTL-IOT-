#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>
#include <nvs_flash.h>
#include <nvs.h>

class Settings {
public:
    // Hàm static để khởi tạo NVS một lần duy nhất
    static bool initializeNVS();
    
    Settings(const String& ns, bool read_write = false);
    ~Settings();

    String getString(const String& key, const String& default_value = "");
    void setString(const String& key, const String& value);

    int32_t getInt(const String& key, int32_t default_value = 0);
    void setInt(const String& key, int32_t value);

    bool getBool(const String& key, bool default_value = false);
    void setBool(const String& key, bool value);

    void eraseKey(const String& key);
    void eraseAll();

private:
    String _namespace;
    nvs_handle_t _handle = 0;
    bool _readWrite = false;
    bool _dirty = false;
};

#endif
