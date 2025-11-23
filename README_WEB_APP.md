# 🎙️ WAV to Text Web Converter

Ứng dụng web đơn giản để chuyển đổi file âm thanh WAV thành text sử dụng Wit.ai API.

## ✨ Tính năng

- 📁 Upload file WAV qua giao diện web
- 🎯 Drag & drop file trực tiếp
- 🔍 Hiển thị thông tin chi tiết file audio
- 🤖 Sử dụng Wit.ai API để chuyển đổi speech-to-text
- 📊 Hiển thị response đầy đủ từ API
- ⚠️ Validation file và error handling
- 🎨 Giao diện đẹp và responsive

## 🚀 Cách chạy ứng dụng

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng

```bash
python test1.py
```

### 3. Mở trình duyệt

Truy cập: `http://localhost:5000`

## 📋 Yêu cầu

- Python 3.7+
- File WAV định dạng:
  - Sample rate: 16000 Hz (khuyến nghị)
  - Channels: 1 (mono)
  - Duration: tối đa 20 giây
- Token Wit.ai hợp lệ

## 🔧 Cấu hình

Trong file `test1.py`, thay đổi token Wit.ai:

```python
WIT_AI_TOKEN = "YOUR_WIT_AI_TOKEN_HERE"
```

## 📁 Cấu trúc file

```
IOTBTL/
├── test1.py              # Flask web app
├── templates/
│   └── index.html        # Giao diện web
├── uploads/              # Thư mục tạm cho file upload
├── requirements.txt      # Dependencies
└── README_WEB_APP.md     # Hướng dẫn này
```

## 🎯 Cách sử dụng

1. Mở trình duyệt và truy cập `http://localhost:5000`
2. Click "Choose File" hoặc kéo thả file WAV vào vùng upload
3. Chờ ứng dụng xử lý file
4. Xem kết quả transcription và thông tin chi tiết

## ⚠️ Lưu ý

- File WAV phải có định dạng hợp lệ
- Kích thước file tối đa: 16MB
- Wit.ai có giới hạn 20 giây cho mỗi file audio
- Token Wit.ai phải có quyền truy cập Speech API

## 🐛 Troubleshooting

### Lỗi "No module named 'flask'"
```bash
pip install Flask
```

### Lỗi "Rate limit reached"
- Đợi một chút rồi thử lại
- Kiểm tra giới hạn API của Wit.ai

### Lỗi "Invalid WAV file"
- Kiểm tra file có đúng định dạng WAV không
- Thử convert file sang định dạng khác

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Token Wit.ai có hợp lệ không
2. File WAV có đúng định dạng không
3. Kết nối internet có ổn định không