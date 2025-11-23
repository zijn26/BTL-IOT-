# 📘 HƯỚNG DẪN SỬ DỤNG TOOL SERVICE

## 🎯 Tổng quan

**Tool Service** là hệ thống quản lý và thực thi các tools (functions) trong dự án IoT, tích hợp với Groq AI để xử lý Function Calling.

### ✨ Tính năng chính:
- ✅ Tự động tạo JSON Schema từ Python type hints
- ✅ Hỗ trợ cả sync và async functions
- ✅ Chạy sync functions trong thread pool (không block event loop)
- ✅ Tích hợp sẵn với Groq AI Function Calling
- ✅ Dễ dàng đăng ký tools mới bằng decorator

---

## 📁 Cấu trúc thư mục

```
app/
├── services/
│   ├── tool_service.py          # Core tool registry
│   └── conversation_service.py  # AI conversation service
├── tools/
│   ├── __init__.py              # Auto-import tools
│   ├── device_tools.py          # IoT device control tools
│   └── example_usage.py         # Ví dụ sử dụng
├── routers/
│   └── ai_chat.py               # API endpoints
└── main.py                      # Import tools tại đây
```

---

## 🚀 Cách 1: Đăng ký Tool mới

### Bước 1: Tạo file tool (hoặc thêm vào file có sẵn)

**File: `app/tools/my_custom_tools.py`**

```python
from app.services.tool_service import registry
import time

# ✅ Sync function nhanh
@registry.register("Chào hỏi người dùng")
def greet_user(name: str, language: str = "vi"):
    """Chào hỏi người dùng bằng ngôn ngữ chỉ định"""
    greetings = {
        "vi": f"Xin chào {name}!",
        "en": f"Hello {name}!",
        "ja": f"こんにちは {name}!"
    }
    return greetings.get(language, greetings["vi"])


# ✅ Sync function chạy lâu (AI processing)
@registry.register("Phân tích văn bản bằng AI")
def analyze_text(text: str):
    """Phân tích sentiment của văn bản"""
    # Giả lập AI processing
    time.sleep(2)
    return f"Đã phân tích: '{text}' - Sentiment: Positive"


# ✅ Async function
@registry.register("Gọi API bên ngoài")
async def call_external_api(endpoint: str):
    """Gọi API bên ngoài"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.json()
```

### Bước 2: Import tool trong `app/tools/__init__.py`

```python
from . import device_tools
from . import my_custom_tools  # Thêm dòng này

__all__ = ['device_tools', 'my_custom_tools']
```

### Bước 3: Restart server

```bash
uvicorn app.main:app --reload
```

✅ **Tool đã được tự động đăng ký!**

---

## 🔧 Cách 2: Sử dụng Tools

### Option A: Qua API Endpoints

#### 1. Liệt kê tất cả tools

```bash
GET http://localhost:8000/ai/tools
```

**Response:**
```json
{
  "total": 12,
  "tools": [
    {
      "name": "turn_on_device",
      "description": "Bật thiết bị IoT theo tên thiết bị",
      "parameters": {
        "device_name": {"type": "string"}
      }
    },
    ...
  ]
}
```

#### 2. Chat với AI (AI tự động gọi tool)

```bash
POST http://localhost:8000/ai/chat
Content-Type: application/json

{
  "message": "Bật đèn phòng khách",
  "conversation_history": []
}
```

**Response:**
```json
{
  "response": "Đã bật đèn phòng khách thành công!",
  "tool_calls": [
    {
      "name": "turn_on_device",
      "arguments": {"device_name": "Đèn phòng khách"},
      "result": "Đã bật thiết bị 'Đèn phòng khách' thành công"
    }
  ],
  "conversation": [...]
}
```

#### 3. Thực thi tool trực tiếp (test)

```bash
POST http://localhost:8000/ai/execute-tool?tool_name=turn_on_device
Content-Type: application/json

{
  "device_name": "Đèn phòng khách"
}
```

**Response:**
```json
{
  "tool": "turn_on_device",
  "arguments": {"device_name": "Đèn phòng khách"},
  "result": "Đã bật thiết bị 'Đèn phòng khách' thành công"
}
```

---

### Option B: Trong Python code

```python
from app.services.tool_service import registry
import asyncio

async def main():
    # Thực thi tool
    result = await registry.execute(
        tool_name="turn_on_device",
        arguments={"device_name": "Đèn phòng khách"}
    )
    
    print(result)  # "Đã bật thiết bị 'Đèn phòng khách' thành công"

asyncio.run(main())
```

---

## 🤖 Cách 3: Tích hợp với Groq AI

### Ví dụ trong Conversation Service

```python
from app.services.conversation_service import conversation_service

async def handle_voice_command(text_from_stt: str):
    """Xử lý lệnh giọng nói"""
    
    # AI tự động hiểu và gọi tool phù hợp
    result = await conversation_service.chat(text_from_stt)
    
    response_text = result["response"]
    tools_called = result["tool_calls"]
    
    # Chuyển response_text sang giọng nói bằng TTS
    # ...
    
    return response_text
```

### Flow hoạt động:

1. User nói: **"Bật đèn phòng khách"**
2. STT → Text: `"Bật đèn phòng khách"`
3. Groq AI nhận text + tool schemas
4. AI quyết định: Gọi `turn_on_device(device_name="Đèn phòng khách")`
5. `registry.execute()` thực thi tool
6. Tool gửi MQTT command tới ESP32
7. AI tổng hợp kết quả: **"Đã bật đèn phòng khách thành công"**
8. TTS → Giọng nói

---

## 📋 Danh sách Tools có sẵn

### Device Control Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `turn_on_device` | Bật thiết bị IoT | `device_name: str` |
| `turn_off_device` | Tắt thiết bị IoT | `device_name: str` |
| `set_brightness` | Điều chỉnh độ sáng đèn | `device_name: str`, `brightness: int` |
| `read_temperature` | Đọc nhiệt độ từ cảm biến | `sensor_name: str` |
| `read_humidity` | Đọc độ ẩm từ cảm biến | `sensor_name: str` |
| `list_all_devices` | Liệt kê tất cả thiết bị | (no params) |
| `check_device_status` | Kiểm tra trạng thái thiết bị | `device_name: str` |
| `schedule_turn_on` | Hẹn giờ bật thiết bị | `device_name: str`, `delay_seconds: int` |

---

## 🧪 Testing

### 1. Test trực tiếp trong Python

```bash
cd d:\IOTBTL\iot-backend
python -m app.tools.example_usage
```

### 2. Test qua API (Postman / curl)

```bash
# Liệt kê tools
curl http://localhost:8000/ai/tools

# Chat với AI
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bật đèn phòng khách"}'

# Thực thi tool trực tiếp
curl -X POST "http://localhost:8000/ai/execute-tool?tool_name=list_all_devices" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Test trong FastAPI Docs

Mở trình duyệt: `http://localhost:8000/docs`

---

## ⚡ Performance: Sync vs Async

### ❌ Không dùng `to_thread()` (BAD)

```python
# 3 users cùng gọi tool chạy lâu (mỗi tool 3s)
→ User 1: 0s-3s
→ User 2: 3s-6s (phải đợi User 1!)
→ User 3: 6s-9s (phải đợi User 2!)
→ Tổng: 9 giây
```

### ✅ Dùng `to_thread()` (GOOD)

```python
# 3 users cùng gọi tool chạy lâu (mỗi tool 3s)
→ User 1: 0s-3s (thread A)
→ User 2: 0s-3s (thread B) ← Song song!
→ User 3: 0s-3s (thread C) ← Song song!
→ Tổng: 3 giây
```

**Tool Service tự động xử lý điều này!** 🎉

---

## 🔍 Troubleshooting

### Lỗi: "Tool not found"

**Nguyên nhân:** Tool chưa được import  
**Giải pháp:** Kiểm tra `app/tools/__init__.py` và restart server

### Lỗi: "asyncio.to_thread() not found"

**Nguyên nhân:** Python < 3.9  
**Giải pháp:** Upgrade Python hoặc dùng `loop.run_in_executor()`

### AI không gọi tool đúng

**Nguyên nhân:** 
- Description không rõ ràng
- Type hints sai
- Schema không đúng format

**Giải pháp:**
```bash
# Kiểm tra schemas
GET http://localhost:8000/ai/tools

# Xem log khi AI gọi tool
# Check console output
```

---

## 🎓 Best Practices

### ✅ DO:
- Viết description rõ ràng, cụ thể
- Sử dụng type hints đầy đủ
- Handle exceptions trong tool functions
- Test tool trước khi tích hợp với AI
- Dùng async functions cho I/O operations

### ❌ DON'T:
- Tool function quá phức tạp (nên tách thành nhiều tools nhỏ)
- Trả về objects phức tạp (AI khó xử lý)
- Gọi `registry.execute()` mà không `await`
- Dùng blocking I/O trong async context

---

## 📚 Tài liệu tham khảo

- [Groq Function Calling](https://console.groq.com/docs/function-calling)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## 💬 Support

Có thắc mắc? Mở issue hoặc liên hệ team!

**Happy Coding! 🚀**

