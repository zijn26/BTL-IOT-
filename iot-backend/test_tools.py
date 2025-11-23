"""
Test script - Kiểm tra Tool Service hoạt động
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tool_service import registry

# Import tools để đăng ký
import app.tools

async def main():
    print("\n" + "="*60)
    print("🧪 TESTING TOOL SERVICE")
    print("="*60)
    
    # Test 1: Kiểm tra số lượng tools
    tools = registry.get_schemas()
    print(f"\n✅ Đã load {len(tools)} tools")
    
    # Test 2: Liệt kê tất cả tools
    print("\n📋 Danh sách tools:")
    for idx, tool in enumerate(tools, 1):
        name = tool["function"]["name"]
        desc = tool["function"]["description"]
        params = list(tool["function"]["parameters"]["properties"].keys())
        print(f"  {idx}. {name}")
        print(f"     Description: {desc}")
        print(f"     Parameters: {params}")
    
    # Test 3: Thực thi một tool đơn giản
    print("\n" + "-"*60)
    print("🔧 Test thực thi tool: list_all_devices")
    print("-"*60)
    
    try:
        result = await registry.execute("list_all_devices", {})
        print(f"\n✅ Kết quả:")
        print(result)
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
    
    # Test 4: Test với tool có parameters
    print("\n" + "-"*60)
    print("🔧 Test thực thi tool: turn_on_device")
    print("-"*60)
    
    try:
        result = await registry.execute("turn_on_device", {
            "device_name": "Test Device"
        })
        print(f"\n✅ Kết quả:")
        print(result)
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ TEST HOÀN THÀNH!")
    print("="*60)
    print("\n💡 Tips:")
    print("  - Xem full guide: TOOL_SERVICE_GUIDE.md")
    print("  - Quick start: QUICK_START.md")
    print("  - Start server: uvicorn app.main:app --reload")
    print("  - API docs: http://localhost:8000/docs")
    print()

if __name__ == "__main__":
    asyncio.run(main())

