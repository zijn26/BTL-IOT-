"""
Conversation Service - Xử lý hội thoại AI với người dùng và điều khiển thiết bị IoT
Hỗ trợ multi-user với lưu trữ conversation history theo client_id
"""
import os
from groq import Groq
from app.services.tool_service import registry
import json
import threading
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app.database import db
TAG = "CONVERSATION_SERVICE"

class ConversationService:
    """
    Service xử lý hội thoại AI tích hợp Function Calling
    Hỗ trợ nhiều người dùng cùng lúc với conversation history riêng biệt
    """
    
    def __init__(self):
        # Khởi tạo Groq client
        api_key = os.getenv("GROQ_API_KEY", "gsk_xxxxxxx")
        self.client = Groq(api_key=api_key)
        self.model = "moonshotai/kimi-k2-instruct-0905"
        
        # Lưu trữ conversation history theo client_id
        # Format: {client_id: {"history": [...], "last_activity": datetime, "metadata": {...}}}
        self.conversations: Dict[str, dict] = {}
        self.agent_config : Dict[str, dict] = {}

        # Lock để thread-safe khi nhiều users cùng lúc
        self.lock = threading.Lock()
        self.lock_agent_config = threading.Lock()
        # Cấu hình
        self.max_history_length = 20  # Giới hạn số lượng messages trong history
        self.session_timeout_minutes = 30  # Timeout cho session không hoạt động
        
        # System prompt
        # "Bạn là trợ lý ảo AI hãy thực hiện các công việc dựa trên tool người dùng cung cấp"
        self.system_prompt = """Bạn là trợ lý AI với Style nói: nhí nhảnh đáng yêu, cuốn hút. Và tưởng tượng bạn là một cô gái trẻ 21 tuổi tên là Huyền.

QUAN TRỌNG - QUY TẮC GỌI TOOL:
- Khi người dùng yêu cầu thực hiện một hành động (như "bật đèn", "tắt đèn", "bật đèn nhà", "bật đèn bếp"), BẠN PHẢI GỌI TOOL tương ứng để thực hiện hành động đó.
- KHÔNG BAO GIỜ chỉ trả lời bằng text như "đã bật đèn" mà không gọi tool.
- Luôn luôn sử dụng tool khi có yêu cầu điều khiển thiết bị.
- Sau khi tool được thực thi, bạn mới trả lời người dùng dựa trên kết quả từ tool.

Quy tắc khác:
- Trả lời ngắn gọn, dễ hiểu
- Giữ phong cách nhí nhảnh, đáng yêu
""" 
    def clear_agent_config(self , client_id: str  ):
        """Xóa config AI của một client"""
        with self.lock_agent_config:
            if client_id in self.agent_config:
                del self.agent_config[client_id]
                print(f"{TAG} Đã xóa config AI của client: {client_id}")
                
    def _cleanup_old_sessions(self):
        """Tự động xóa các session cũ không hoạt động"""
        try:
            current_time = datetime.now()
            timeout_delta = timedelta(minutes=self.session_timeout_minutes)
            
            with self.lock:
                expired_clients = []
                for client_id, data in self.conversations.items():
                    last_activity = data.get("last_activity")
                    if last_activity and current_time - last_activity > timeout_delta:
                        expired_clients.append(client_id)
                
                for client_id in expired_clients:
                    # self.clear_agent_config(client_id)
                    del self.conversations[client_id]
                    print(f"{TAG} Đã xóa session cũ của client: {client_id}")
                    
        except Exception as e:
            print(f"{TAG} Lỗi khi cleanup sessions: {e}")
    
    def get_conversation_history(self, client_id: str) -> List[dict]:
        """
        Lấy lịch sử hội thoại của một client
        
        Args:
            client_id: ID của client
            
        Returns:
            List các messages trong conversation history
        """
        with self.lock:
            if client_id in self.conversations:
                return self.conversations[client_id]["history"].copy()
            return []
    
    def save_conversation_history(self, client_id: str, history: List[dict], metadata: dict = None):
        """
        Lưu lịch sử hội thoại cho một client
        
        Args:
            client_id: ID của client
            history: List các messages
            metadata: Thông tin bổ sung (user_name, device_info, etc.)
        """
        with self.lock:
            self.conversations[client_id] = {
                "history": history,
                "last_activity": datetime.now(),
                "metadata": metadata or {}
            }
            
            print(f"{TAG} Đã lưu conversation cho client {client_id} ({len(history)} messages)")
    
    def clear_conversation(self, client_id: str):
        """
        Xóa lịch sử hội thoại của một client
        
        Args:
            client_id: ID của client
        """
        with self.lock:
            if client_id in self.conversations:
                del self.conversations[client_id]
                print(f"{TAG} Đã xóa conversation của client: {client_id}")
    
    async def chat(self, client_id: str, user_message: str, metadata: dict = None):
        """
        Xử lý một câu chat từ người dùng với client_id
        Hỗ trợ multi-turn function calling và multi-client concurrent
        
        Args:
            client_id: ID của client (user/device)
            user_message: Tin nhắn từ người dùng
            metadata: Thông tin bổ sung (user_name, device_type, etc.)
        
        Returns:
            dict: {
                "response": "Câu trả lời của AI",
                "tool_calls": [...],  # Các tool đã gọi
                "conversation": [...]  # Lịch sử hội thoại mới
            }
        """
        conversation_history = []
        try:
            # Cleanup các session cũ trước khi xử lý
            self._cleanup_old_sessions()
            
            # Lấy conversation history của client này (thread-safe)
            conversation_history = self.get_conversation_history(client_id)
            config_ai = self.agent_config.get(client_id)
            if not config_ai:
                config_ai = db.execute_query(
                    table="agent_config",
                    operation="select",
                    filters={"token_verify": client_id}
                )
                
                if not config_ai:
                    config_ai = {
                        "style": "nhí nhảnh đáng yêu , cuốn hút",
                        "name": "Linh",
                        "describe": "Bạn tên là một cô gái trẻ 21 tuổi , trợ giúp tôi các công việc như một trợ lý "
                    }
                else:
                    config_ai = config_ai[0]
                with self.lock_agent_config:
                    self.agent_config[client_id] = config_ai

            # system_prompt = "Style nói : " + config_ai["style"] + " . Bạn tên là " + config_ai["name"] + " . " + config_ai["describe"]
            # system_prompt += "Quy tắc:\n- Khi cần dùng tool sẽ trả về danh sách tool \n- khi không cần dùng thì sẽ không trả về danh sáng tool \n- Trả lời ngắn gọn, dễ hiểu"
            # ✅ FIX: System prompt CHỈ thêm vào messages, KHÔNG lưu vào history
            # → Tránh spam system prompt mỗi lần chat
            system_prompt = f""" \n
                Bạn là trợ lý AI với Style nói: {config_ai['style']}.
                Tên bạn là {config_ai['name']}.
                Mô tả: {config_ai['describe']}.
                QUAN TRỌNG – QUY TẮC GỌI TOOL:
                1. Khi user yêu cầu một hành động có thể thực hiện qua tool (ví dụ: bật/tắt thiết bị, mở cửa…), PHẢI tạo tool_call JSON tương ứng và KHÔNG chỉ trả lời bằng lời.
                2. Nếu user chưa nêu rõ target, hỏi để xác nhận trước khi sinh tool_call.
                3. Sau khi tool được thực thi, mới trả lời người dùng dựa trên kết quả từ tool.
                4. Nếu user yêu cầu nhiều hành động liên tiếp, xử lý lần lượt, từng tool một.
                5. Luôn kiểm tra conversation history để biết trạng thái thiết bị, nhưng nếu user muốn thực hiện lại, PHẢI gọi lại tool.
                6. Nếu không có tool phù hợp với yêu cầu của user, chỉ trả lời bằng text.
                QUY TẮC TRẢ LỜI:
                - Trả lời ngắn gọn, dễ hiểu.
                - Giữ phong cách {config_ai['style']}.
                - Khi có tool_calls, content nên để trống hoặc null.
                
                VÍ DỤ VỀ CÁCH PHẢN HỒI KHI USER YÊU CẦU THỰC HIỆN TOOL:
                
                User: "bật đèn nhà"
                → Bạn PHẢI trả về tool_call với:
                   - name: "turn_on_device_home"
                   - arguments: {{}} (rỗng vì function không có tham số)
                   - content: "" (để trống khi có tool_calls)
                
                User: "bật đèn bếp"
                → Bạn PHẢI trả về tool_call với:
                   - name: "turn_on_device_kitchen"
                   - arguments: {{}}
                   - content: ""
                
                User: "mở cửa"
                → Bạn PHẢI trả về tool_call với:
                   - name: "open_the_door"
                   - arguments: {{}}
                   - content: ""
                
                LƯU Ý: Khi response có tool_calls, finish_reason sẽ là 'tool_calls' và content sẽ trống. 
                Sau khi tool được thực thi, bạn mới trả lời người dùng dựa trên kết quả từ tool.
            """

            messages = [{"role": "system", "content": system_prompt}]
            # messages.extend([
            #         {"role": "system", "content": "Ưu tiên cao nhất :Bạn là trợ lý AI. Khi user yêu cầu một hành động có thể thực hiện qua tool , PHẢI tạo tool_call JSON tương ứng và không chỉ nói bằng lời."} ,
            #         {"role": "system", "content": "Ưu tiên cao nhất :Nếu tool đã được thực hiện trước đó, bạn vẫn kiểm tra và gọi lại nếu user yêu cầu. "},
            #         # {"role": "user", "content": "bật đèn nhà sau đó là đền bếp , tiếp đến là mở cửa cho tôii "}
            #     ])
            # Thêm history + user message mới
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})
            
            # Lấy danh sách tools từ registry
            tools = registry.get_schemas()
            
            print(f"{TAG} [Client: {client_id}] User: {user_message}")
            print(f"{TAG} [Client: {client_id}] Available tools: {len(tools)}")
            print(f"{TAG} [Client: {client_id}] History messages: {len(conversation_history)}")
            
            # Lưu user message vào history
            conversation_history.append({"role": "user", "content": user_message})
            
            # Track tất cả tool calls
            all_tool_calls = []
            iteration = 0
            print(f"{TAG} [Client: {client_id}] Tool schemas: {tools}")
            while True:
                iteration += 1
                print(f"{TAG} [Client: {client_id}] Iteration {iteration}")
                # messagesss = [
                #     {"role": "system", "content": "Bạn là trợ lý AI, hãy truy vấn và in dữ liệu người dùng.và luôn thực hiện lần lượt các công việc mà người dùng yêu cầu. Không thựcc hiện cùng một lúc "},
                #     {"role": "user", "content": "bật đèn nhà sau đó là đền bếp , tiếp đến là mở cửa cho tôii "}
                # ]
                # Gọi Groq API
                print(f"{TAG} [Client: {client_id}] Messages: {len(messages)} messages")
                print(f"{TAG} [Client: {client_id}] Available tools: {len(tools)} tools")
                if tools:
                    print(f"{TAG} [Client: {client_id}] Tool names: {[t['function']['name'] for t in tools]}")
                
                response = await asyncio.to_thread(self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    # temperature=0.2,
                    tools=tools if tools else None,  # Chỉ gửi tools nếu có
                    tool_choice="auto" if tools else None,  # Chỉ set tool_choice nếu có tools
                )
                print(f"{TAG} [Client: {client_id}] Response: {response}")
                
                assistant_message = response.choices[0].message
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                })
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                })
                print(f"{TAG} [Client: {client_id}] Assistant message: {assistant_message.content}")
                # Kiểm tra xem AI có muốn gọi tool không
                if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
                    print(f"{TAG} [Client: {client_id}] AI muốn gọi {len(assistant_message.tool_calls)} tool(s)")
                
                    # Thực thi từng tool call
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"{TAG} [Client: {client_id}] Executing: {tool_name}({tool_args})")
                        
                        # Gọi tool qua registry.execute()
                        tool_result = await registry.execute(tool_name, tool_args)
                        
                        print(f"{TAG} [Client: {client_id}] Result: {tool_result}")
                        
                        # Track tool call
                        all_tool_calls.append({
                            "name": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
                        # ✅ FIX: Lưu tool result vào messages
                        tool_result_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result)
                        }
                        messages.append(tool_result_msg)
                        conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result)
                        })
                    
                else:
                    # ✅ AI KHÔNG gọi tool nữa - Thoát vòng lặp
                    final_answer = assistant_message.content
                    print(f"{TAG} [Client: {client_id}] AI final response: {final_answer}")
                    # Thoát vòng lặp
                    break
            
            # Nếu vượt quá max_iterations
            # if iteration >= max_iterations:
            #     final_answer = "Đã xử lý tối đa số lần cho phép. Vui lòng thử lại."
            #     conversation_history.append({"role": "assistant", "content": final_answer})
            
            # ✅ FIX: Lưu conversation history cho client này (thread-safe)
            self.save_conversation_history(client_id, conversation_history)
            
            return {
                "client_id": client_id,
                "response": final_answer,
                "tool_calls": all_tool_calls,
                "conversation": conversation_history,
                "message_count": len(conversation_history),
                "iterations": iteration,
                "message" : messages
            }
            
        except Exception as e:
            print(f"{TAG} [Client: {client_id}] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "client_id": client_id,
                "response": f"Xin lỗi, đã có lỗi xảy ra: {str(e)}",
                "tool_calls": [],
                "conversation": conversation_history,
                "error": str(e)
            }
# Khởi tạo singleton
conversation_service = ConversationService()

