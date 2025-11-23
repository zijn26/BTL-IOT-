"""
HƯỚNG DẪN SỬ DỤNG TOOL SERVICE
================================

File này demo cách sử dụng tool_service.py trong dự án
"""

import asyncio
from app.services.tool_service import registry

# ============================================================
# CÁCH 1: ĐĂNG KÝ TOOL MỚI
# ============================================================

# Ví dụ 1: Sync function đơn giản
@registry.register("Tính tổng hai số")
def add_numbers(a: int, b: int):
    """Cộng hai số"""
    return a + b


# Ví dụ 2: Sync function chạy lâu (AI processing)
@registry.register("Xử lý ảnh bằng AI")
def process_image_with_ai(image_path: str):
    """
    Xử lý ảnh bằng AI (giả lập)
    Function này chạy lâu nên cần to_thread()
    """
    import time
    print(f"Đang xử lý ảnh: {image_path}")
    time.sleep(3)  # Giả lập AI processing 3 giây
    return f"Đã xử lý xong ảnh {image_path}"


# # Ví dụ 3: Async function
# @registry.register("Gửi request HTTP")
# async def send_http_request(url: str):
#     """
#     Gửi HTTP request (async)
#     """
#     import aiohttp
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:
#             return await response.text()


# ============================================================
# CÁCH 2: THỰC THI TOOL
# ============================================================

async def demo_execute_tools():
    """Demo cách gọi các tools"""
    
    print("\n" + "="*60)
    print("DEMO: THỰC THI TOOLS")
    print("="*60)
    
    # Test 1: Gọi sync function nhanh
    print("\n📌 Test 1: Sync function (nhanh)")
    result = await registry.execute("add_numbers", {"a": 10, "b": 20})
    print(f"Result: {result}")
    
    # Test 2: Gọi sync function chạy lâu
    print("\n📌 Test 2: Sync function (chạy lâu - sẽ dùng to_thread)")
    result = await registry.execute("process_image_with_ai", {"image_path": "photo.jpg"})
    print(f"Result: {result}")
    
    # Test 3: Gọi async function
    print("\n📌 Test 3: Async function")
    result = await registry.execute("send_http_request", {"url": "https://api.github.com"})
    print(f"Result length: {len(result)} characters")
    
    # Test 4: Gọi nhiều tools song song
    print("\n📌 Test 4: Chạy 3 tools song song")
    import time
    start = time.time()
    
    results = await asyncio.gather(
        registry.execute("process_image_with_ai", {"image_path": "photo1.jpg"}),
        registry.execute("process_image_with_ai", {"image_path": "photo2.jpg"}),
        registry.execute("process_image_with_ai", {"image_path": "photo3.jpg"}),
    )
    
    elapsed = time.time() - start
    print(f"✅ Xong 3 tasks trong {elapsed:.1f}s (nếu không dùng to_thread sẽ mất 9s!)")
    for idx, result in enumerate(results, 1):
        print(f"   Task {idx}: {result}")


# ============================================================
# CÁCH 3: LẤY DANH SÁCH TOOLS (Để gửi cho Groq AI)
# ============================================================

def demo_get_schemas():
    """Demo cách lấy schemas cho Groq"""
    
    print("\n" + "="*60)
    print("DEMO: LẤY SCHEMAS CHO GROQ AI")
    print("="*60)
    
    schemas = registry.get_schemas()
    
    print(f"\nTổng số tools: {len(schemas)}")
    print("\nDanh sách tools:")
    for idx, schema in enumerate(schemas, 1):
        func_info = schema["function"]
        print(f"\n{idx}. {func_info['name']}")
        print(f"   Description: {func_info['description']}")
        print(f"   Parameters: {list(func_info['parameters']['properties'].keys())}")
    
    print("\n💡 Schemas này được gửi cho Groq để AI biết cách gọi functions!")


# ============================================================
# CÁCH 4: TÍCH HỢP VỚI GROQ AI (REAL-WORLD EXAMPLE)
# ============================================================

async def demo_with_groq_ai():
    """
    Demo tích hợp với Groq AI
    (Cần cài: pip install groq)
    """
    print("\n" + "="*60)
    print("DEMO: TÍCH HỢP VỚI GROQ AI")
    print("="*60)
    
    try:
        from groq import Groq
        import os
        import json
        
        # Khởi tạo Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY", "your_api_key"))
        
        # Lấy schemas
        tools = registry.get_schemas()
        
        # User message
        user_message = "Hãy tính tổng của 15 và 25"
        
        print(f"\n👤 User: {user_message}")
        
        # Gọi Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI hữu ích"},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            tool_choice="auto"
        )
        
        # Kiểm tra xem AI có muốn gọi tool không
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"\n🤖 AI muốn gọi: {tool_name}({tool_args})")
            
            # Thực thi tool
            result = await registry.execute(tool_name, tool_args)
            print(f"\n⚙️ Kết quả: {result}")
            
        else:
            print(f"\n🤖 AI: {response.choices[0].message.content}")
    
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        print("💡 Tip: Set GROQ_API_KEY environment variable")


# ============================================================
# MAIN - CHẠY TẤT CẢ DEMOS
# ============================================================

async def main():
    """Chạy tất cả demos"""
    
    print("\n" + "🚀"*30)
    print("TOOL SERVICE - COMPLETE DEMO")
    print("🚀"*30)
    
    # Demo 1: Lấy schemas
    demo_get_schemas()
    
    # Demo 2: Thực thi tools
    await demo_execute_tools()
    
    # Demo 3: Tích hợp Groq (comment nếu chưa có API key)
    # await demo_with_groq_ai()
    
    print("\n" + "✅"*30)
    print("DEMO HOÀN THÀNH!")
    print("✅"*30 + "\n")


if __name__ == "__main__":
    # Chạy demo
    asyncio.run(main())

