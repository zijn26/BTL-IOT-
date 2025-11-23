# 🚀 IoT Backend API Tester - Hướng dẫn sử dụng

## 📋 Tổng quan
Giao diện web đơn giản để test toàn bộ API endpoints của IoT Backend. Đây là một công cụ test trực quan và dễ sử dụng.

## 🛠️ Cài đặt và chạy

### 1. Khởi động Backend API
```bash
cd iot-backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
.venv/Scripts/activate
```

### 2. Mở giao diện test
Mở file `frontend_test.html` trong trình duyệt web:
- Chrome: `file:///path/to/iot-backend/frontend_test.html`
- Firefox: `file:///path/to/iot-backend/frontend_test.html`

## 🔧 Các tính năng chính

### 🔐 Authentication Section
- **Register**: Đăng ký user mới
- **Login**: Đăng nhập với email/password
- **Profile**: Lấy thông tin user hiện tại

### 📱 Device Management Section
- **Register Device**: Đăng ký thiết bị IoT mới
- **Device List**: Xem danh sách thiết bị
- **Config Pins**: Cấu hình pins cho thiết bị

## 📝 Hướng dẫn test từng bước

### Bước 1: Test Authentication
1. **Đăng ký user mới:**
   - Email: `test@example.com`
   - Tên: `Test User`
   - Password: `password123`
   - Click "Đăng ký"

2. **Đăng nhập:**
   - Email: `test@example.com`
   - Password: `password123`
   - Click "Đăng nhập"

3. **Lấy thông tin user:**
   - Click "Lấy thông tin user"

### Bước 2: Test Device Management
1. **Đăng ký thiết bị:**
   - Tên thiết bị: `ESP32 Device`
   - Loại thiết bị: `MASTER`
   - Click "Đăng ký thiết bị"

2. **Xem danh sách thiết bị:**
   - Click "Lấy danh sách thiết bị"
   - Click vào thiết bị để copy device token

3. **Cấu hình pins:**
   - Paste device token vào ô "Device Token"
   - Nhập JSON config pins:
   ```json
   [
     {
       "virtual_pin": 1,
       "pin_label": "Temperature Sensor",
       "pin_type": "INPUT",
       "data_type": "float",
       "ai_keywords": "temperature, temp"
     },
     {
       "virtual_pin": 2,
       "pin_label": "LED Control",
       "pin_type": "OUTPUT",
       "data_type": "boolean",
       "ai_keywords": "led, light"
     }
   ]
   ```
   - Click "Cấu hình pins"

## 🧪 Test Cases được hỗ trợ

### Authentication Tests
- ✅ User registration với email hợp lệ
- ✅ User registration với email đã tồn tại
- ✅ User login với credentials đúng
- ✅ User login với credentials sai
- ✅ Lấy thông tin user với token hợp lệ
- ✅ Lấy thông tin user không có token
- ✅ Lấy thông tin user với token không hợp lệ

### Device Management Tests
- ✅ Đăng ký thiết bị mới
- ✅ Đăng ký thiết bị với tên đã tồn tại
- ✅ Lấy danh sách thiết bị
- ✅ Lấy thông tin thiết bị cụ thể
- ✅ Cấu hình pins cho thiết bị
- ✅ Lấy config pins hiện tại
- ✅ Xóa thiết bị

## 🔍 Kiểm tra Response

### Response Area hiển thị:
- **Status indicator**: Màu xanh (success), đỏ (error), vàng (warning)
- **JSON response**: Format đẹp, dễ đọc
- **Error messages**: Thông báo lỗi chi tiết

### Các loại response:
```json
// Success Response
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}

// Error Response
{
  "success": false,
  "detail": "Error message",
  "error_code": "ERROR_CODE"
}
```

## 🚨 Troubleshooting

### Lỗi thường gặp:

1. **"Chưa đăng nhập!"**
   - Giải pháp: Đăng nhập trước khi test device APIs

2. **"CORS error"**
   - Giải pháp: Đảm bảo backend đang chạy trên port 8000

3. **"Connection refused"**
   - Giải pháp: Kiểm tra backend có đang chạy không

4. **"JSON không hợp lệ"**
   - Giải pháp: Kiểm tra format JSON trong pin config

## 📊 Test Coverage

Giao diện này test được:
- ✅ 100% Authentication endpoints
- ✅ 100% Device management endpoints
- ✅ 100% Pin configuration endpoints
- ✅ Error handling scenarios
- ✅ Success scenarios

## 🎯 Lợi ích

1. **Trực quan**: Giao diện đẹp, dễ sử dụng
2. **Toàn diện**: Test được tất cả API endpoints
3. **Real-time**: Xem response ngay lập tức
4. **Debug-friendly**: Hiển thị chi tiết lỗi
5. **User-friendly**: Không cần biết cURL hay Postman

## 🔄 Workflow Test

1. **Setup**: Khởi động backend + mở frontend
2. **Auth**: Đăng ký/đăng nhập user
3. **Device**: Đăng ký thiết bị
4. **Config**: Cấu hình pins
5. **Verify**: Kiểm tra kết quả trong response area

**Chúc bạn test API thành công! 🚀**