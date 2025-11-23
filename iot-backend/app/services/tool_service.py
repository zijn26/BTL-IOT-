import inspect
import json
import functools
import asyncio
from typing import Callable, Dict, List, Any, Type
from pydantic import BaseModel, TypeAdapter

class ToolRegistry:
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []

    def register(self, description: str):
        """
        Decorator nhận vào description từ code (không phải docstring).
        """
        def decorator(func):
            func_name = func.__name__
            
            # --- TỰ ĐỘNG TẠO SCHEMA ---
            # Sử dụng Pydantic TypeAdapter để convert Python Type hint sang JSON Schema
            # Đây là cách mạnh mẽ nhất để xử lý cả List, Object, Nested structures
            sig = inspect.signature(func)
            properties = {}
            required_params = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'): continue
                
                # 1. Lấy schema từ Type Hint (ví dụ: int, str, List[User])
                if param.annotation != inspect.Parameter.empty:
                    # Pydantic magic: Chuyển type hint thành JSON schema
                    adapter = TypeAdapter(param.annotation)
                    param_schema = adapter.json_schema()
                    
                    # Clean schema (bỏ title, definition thừa nếu có)
                    if "title" in param_schema: del param_schema["title"]
                    if "definitions" in param_schema: del param_schema["definitions"]
                else:
                    # Mặc định nếu không có type hint
                    param_schema = {"type": "string"}
                
                # Thêm description cho từng tham số (Optional: bạn có thể mở rộng để truyền vào sau)
                # Ở đây tạm để mặc định hoặc lấy từ docstring nếu cần chi tiết từng biến
                
                properties[param_name] = param_schema
                
                # 2. Check Required (nếu không có default value)
                if param.default == inspect.Parameter.empty:
                    required_params.append(param_name)

            # --- CẤU TRÚC CHUẨN GROQ ---
            tool_schema = {
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": description, # Lấy từ tham số truyền vào
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required_params,
                        "additionalProperties": False # BẮT BUỘC CHO GROQ
                    }
                }
            }

            # Lưu vào kho
            self._functions[func_name] = func
            self._schemas.append(tool_schema)
            
            print(f"✅ Đã đăng ký tool: {func_name} | Desc: {description}")

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_schemas(self):
        """Lấy danh sách schema để gửi cho Groq"""
        return self._schemas

    async def execute(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Thực thi hàm một cách bất đồng bộ
        - Với sync function: Chạy trong thread pool để tránh blocking event loop
        - Với async function: Await trực tiếp
        """
        if tool_name not in self._functions:
            return f"Error: Tool {tool_name} not found"
        
        func = self._functions[tool_name]
        try:
            # Kiểm tra xem function có phải là async không
            if asyncio.iscoroutinefunction(func):
                # Function là async → await trực tiếp
                return await func(**arguments)
            else:
                # Function là sync → chạy trong thread pool để không block event loop
                return await asyncio.to_thread(func, **arguments)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

# Khởi tạo
registry = ToolRegistry()