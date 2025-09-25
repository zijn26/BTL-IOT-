#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>

class MQTTAudioStreamer {
private:
    WiFiClient espClient;
    PubSubClient mqtt;
    String sessionId;
    int chunkCounter = 0;
    
    // Chunking parameters
    static const int CHUNK_SIZE = 4096;        // 4KB chunks
    static const int OVERLAP_SIZE = 512;       // 512 bytes overlap
    int16_t overlapBuffer[OVERLAP_SIZE/2];
    bool hasOverlap = false;
    
public:
    void setup() {
        mqtt.setClient(espClient);
        mqtt.setServer("your-mqtt-broker.com", 1883);
        mqtt.setBufferSize(8192); // Increase buffer for audio chunks
        mqtt.setCallback([this](char* topic, byte* payload, unsigned int length) {
            handleMQTTMessage(topic, payload, length);
        });
        
        connectToMQTT();
        
        // Subscribe to response topic
        mqtt.subscribe(("audio/response/" + WiFi.macAddress()).c_str());
    }
    
    void startAudioStreaming() {
        sessionId = String(millis()) + "_" + WiFi.macAddress();
        chunkCounter = 0;
        hasOverlap = false;
        
        Serial.println("🎙️ Starting MQTT audio streaming...");
        
        // Send session start message
        sendSessionStart();
        
        // Start recording task
        xTaskCreate(audioRecordingTask, "MQTTAudioRecord", 8192, this, 2, NULL);
    }
    
    void sendSessionStart() {
        DynamicJsonDocument doc(512);
        doc["session_id"] = sessionId;
        doc["sample_rate"] = 16000;
        doc["channels"] = 1;
        doc["bits_per_sample"] = 16;
        doc["chunk_size"] = CHUNK_SIZE;
        doc["overlap_size"] = OVERLAP_SIZE;
        doc["timestamp"] = millis();
        
        String payload;
        serializeJson(doc, payload);
        
        String topic = "audio/session/" + WiFi.macAddress();
        mqtt.publish(topic.c_str(), payload.c_str());
        Serial.println("📤 Session started: " + sessionId);
    }
    
    static void audioRecordingTask(void* parameter) {
        MQTTAudioStreamer* streamer = (MQTTAudioStreamer*)parameter;
        int16_t audioBuffer[CHUNK_SIZE/2];
        size_t bytes_read = 0;
        
        while (streamer->mqtt.connected()) {
            // Record chunk
            esp_err_t result = i2s_read(I2S_PORT, audioBuffer, CHUNK_SIZE, &bytes_read, 100);
            
            if (result == ESP_OK && bytes_read > 0) {
                int samples = bytes_read / 2;
                
                // Basic preprocessing trên ESP32
                streamer->basicPreprocessing(audioBuffer, samples);
                
                // Send overlapping chunk
                streamer->sendAudioChunk(audioBuffer, samples);
                
                // Delay để control streaming rate
                vTaskDelay(pdMS_TO_TICKS(250)); // ~4 chunks/second
            }
            
            streamer->mqtt.loop(); // Maintain MQTT connection
        }
        vTaskDelete(NULL);
    }
    
    void sendAudioChunk(int16_t* audioData, int samples) {
        // Create overlapping chunk
        int16_t chunkWithOverlap[CHUNK_SIZE/2 + OVERLAP_SIZE/2];
        int totalSamples = samples;
        
        if (hasOverlap) {
            // Add overlap at beginning
            memcpy(chunkWithOverlap, overlapBuffer, OVERLAP_SIZE);
            memcpy(chunkWithOverlap + OVERLAP_SIZE/2, audioData, samples * 2);
            totalSamples += OVERLAP_SIZE/2;
            
            // Cross-fade overlap region
            crossFadeOverlap(chunkWithOverlap, OVERLAP_SIZE/2);
        } else {
            memcpy(chunkWithOverlap, audioData, samples * 2);
        }
        
        // Save overlap for next chunk
        if (samples >= OVERLAP_SIZE/2) {
            memcpy(overlapBuffer, audioData + samples - OVERLAP_SIZE/2, OVERLAP_SIZE);
            hasOverlap = true;
        }
        
        // Create chunk message
        DynamicJsonDocument metadata(256);
        metadata["session_id"] = sessionId;
        metadata["chunk_id"] = chunkCounter++;
        metadata["samples"] = totalSamples;
        metadata["timestamp"] = millis();
        metadata["has_overlap"] = hasOverlap;
        
        String metaString;
        serializeJson(metadata, metaString);
        
        // Send metadata first
        String metaTopic = "audio/meta/" + WiFi.macAddress();
        mqtt.publish(metaTopic.c_str(), metaString.c_str());
        
        // Send audio data (binary)
        String dataTopic = "audio/data/" + WiFi.macAddress();
        mqtt.publish(dataTopic.c_str(), (uint8_t*)chunkWithOverlap, totalSamples * 2);
        
        Serial.printf("📤 Sent chunk %d: %d samples\n", chunkCounter-1, totalSamples);
    }
    
    void basicPreprocessing(int16_t* samples, int count) {
        // 1. DC offset removal
        static float dcFilter = 0.0f;
        for (int i = 0; i < count; i++) {
            float input = samples[i] / 32767.0f;
            dcFilter = dcFilter * 0.995f + input * 0.005f;
            samples[i] = (int16_t)((input - dcFilter) * 32767.0f);
        }
        
        // 2. Simple AGC
        float rms = calculateRMS(samples, count);
        if (rms > 0 && rms < 8000) { // Nếu tín hiệu quá yếu
            float gain = 8000.0f / rms;
            gain = fminf(gain, 4.0f); // Limit gain
            
            for (int i = 0; i < count; i++) {
                samples[i] = (int16_t)fminf(fmaxf(samples[i] * gain, -32767), 32767);
            }
        }
    }
    
    void crossFadeOverlap(int16_t* buffer, int overlapSamples) {
        for (int i = 0; i < overlapSamples; i++) {
            float fadeOut = 1.0f - (float)i / overlapSamples;
            float fadeIn = (float)i / overlapSamples;
            
            float oldSample = buffer[i];
            float newSample = buffer[i + overlapSamples];
            
            buffer[i] = (int16_t)(oldSample * fadeOut + newSample * fadeIn);
        }
    }
    
    void handleMQTTMessage(char* topic, byte* payload, unsigned int length) {
        if (strstr(topic, "audio/response/") != NULL) {
            // Parse response từ server
            DynamicJsonDocument doc(1024);
            deserializeJson(doc, payload, length);
            
            if (doc["type"] == "transcription") {
                String text = doc["text"];
                float confidence = doc["confidence"];
                Serial.printf("🎯 STT Result: %s (%.1f%%)\n", text.c_str(), confidence * 100);
                
                // Callback for transcription result
                onTranscriptionReceived(text, confidence);
            }
            else if (doc["type"] == "error") {
                Serial.println("❌ Server error: " + doc["message"].as<String>());
            }
        }
    }
    
    void connectToMQTT() {
        while (!mqtt.connected()) {
            Serial.print("🔄 Connecting to MQTT...");
            String clientId = "ESP32_" + WiFi.macAddress();
            
            if (mqtt.connect(clientId.c_str())) {
                Serial.println(" connected!");
            } else {
                Serial.printf(" failed, rc=%d. Retry in 5s\n", mqtt.state());
                delay(5000);
            }
        }
    }
};
