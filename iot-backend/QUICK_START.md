# ⚡ QUICK START - Tool Service

## 🚀 Chạy ngay trong 3 phút!

### Bước 1: Cài đặt dependencies

```bash
pip install groq aiohttp
```

### Bước 2: Set API Key (Optional - để test với AI)

```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_api_key_here"

# Windows CMD
set GROQ_API_KEY=gsk_your_api_key_here

# Linux/Mac
export GROQ_API_KEY="gsk_your_api_key_here"
```

### Bước 3: Start server

```bash
cd d:\IOTBTL\iot-backend
uvicorn app.main:app --reload
```

**Output:**
```
✅ Đã đăng ký tool: turn_on_device | Desc: Bật thiết bị IoT theo tên thiết bị
✅ Đã đăng ký tool: turn_off_device | Desc: Tắt thiết bị IoT theo tên thiết bị
...
✅ Đã load Device Tools thành công!
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Bước 4: Test!

#### Option A: Mở trình duyệt

```
http://localhost:8000/docs
```

→ Thử endpoint `/ai/tools` để xem danh sách tools

#### Option B: Test bằng curl

```bash
# 1. Liệt kê tools
curl http://localhost:8000/ai/tools

# 2. Chat với AI
curl -X POST http://localhost:8000/ai/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Liệt kê tất cả thiết bị\"}"

# 3. Thực thi tool trực tiếp
curl -X POST "http://localhost:8000/ai/execute-tool?tool_name=list_all_devices" ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

#### Option C: Test trong Python

```python
# File: test_tool.py
import asyncio
from app.services.tool_service import registry

async def test():
    # Liệt kê tất cả tools
    tools = registry.get_schemas()
    print(f"Có {len(tools)} tools")
    
    # Thực thi một tool
    result = await registry.execute("list_all_devices", {})
    print(result)

asyncio.run(test())
```

```bash
python test_tool.py
```

---

## 🎯 Ví dụ Chat với AI

### Request:
```json
POST http://localhost:8000/ai/chat

{
  "message": "Nhiệt độ hiện tại là bao nhiêu?",
  "conversation_history": []
}
```

### Response:
```json
{
  "response": "Nhiệt độ tại 'Cảm biến phòng khách' là 25.5°C",
  "tool_calls": [
    {
      "name": "read_temperature",
      "arguments": {"sensor_name": "Cảm biến phòng khách"},
      "result": "Nhiệt độ tại 'Cảm biến phòng khách' là 25.5°C..."
    }
  ],
  "conversation": [...]
}
```

---

## ✅ Checklist

- [ ] Server đã chạy (`uvicorn app.main:app --reload`)
- [ ] Thấy message "Đã đăng ký tool: ..." trong console
- [ ] `/docs` hiển thị endpoint `/ai/tools`, `/ai/chat`
- [ ] Test endpoint `/ai/tools` thành công
- [ ] (Optional) Set `GROQ_API_KEY` để test AI chat

---

## 🐛 Nếu gặp lỗi:

### Import Error: No module 'app.tools'

```bash
# Kiểm tra file tồn tại
ls app/tools/__init__.py
ls app/tools/device_tools.py
```

### Import Error: No module 'groq'

```bash
pip install groq
```

### Tool không được đăng ký

**Kiểm tra:** Console có in ra `✅ Đã đăng ký tool: ...` không?

**Nếu không:**
1. Check `app/tools/__init__.py` đã import đúng chưa
2. Check `app/main.py` có dòng `import app.tools` chưa
3. Restart server

---

## 📖 Đọc thêm

- Full guide: `TOOL_SERVICE_GUIDE.md`
- Code examples: `app/tools/example_usage.py`
- API docs: `http://localhost:8000/docs`

**Chúc bạn thành công! 🎉**

