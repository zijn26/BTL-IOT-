"""
Test script - Demo Conversation Service với Multi-User support
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_service import conversation_service

async def demo_multi_user():
    """Demo nhiều users chat đồng thời"""
    
    print("\n" + "="*80)
    print("🎯 DEMO: CONVERSATION SERVICE - MULTI-USER")
    print("="*80)
    
    # ========== User 1: Nguyễn Văn A ==========
    print("\n📱 User 1 (Nguyễn Văn A) - Chat lần 1:")
    result1 = await conversation_service.chat(
        client_id="user_nguyenvana",
        user_message="Xin chào, tôi tên là Nguyễn Văn A",
        metadata={"user_name": "Nguyễn Văn A", "device": "mobile"}
    )
    print(f"   AI: {result1['response']}")
    print(f"   Messages count: {result1['message_count']}")
    
    # ========== User 2: Trần Thị B ==========
    print("\n📱 User 2 (Trần Thị B) - Chat lần 1:")
    result2 = await conversation_service.chat(
        client_id="user_tranthib",
        user_message="Xin chào, tôi là Trần Thị B",
        metadata={"user_name": "Trần Thị B", "device": "web"}
    )
    print(f"   AI: {result2['response']}")
    print(f"   Messages count: {result2['message_count']}")
    
    # ========== User 1: Chat lần 2 (có context) ==========
    print("\n📱 User 1 (Nguyễn Văn A) - Chat lần 2:")
    result3 = await conversation_service.chat(
        client_id="user_nguyenvana",
        user_message="Bạn còn nhớ tên tôi không?",
    )
    print(f"   AI: {result3['response']}")
    print(f"   Messages count: {result3['message_count']}")
    
    # ========== User 2: Chat lần 2 (có context) ==========
    print("\n📱 User 2 (Trần Thị B) - Chat lần 2:")
    result4 = await conversation_service.chat(
        client_id="user_tranthib",
        user_message="Tên tôi là gì?",
    )
    print(f"   AI: {result4['response']}")
    print(f"   Messages count: {result4['message_count']}")
    
    # ========== Xem statistics ==========
    print("\n" + "-"*80)
    print("📊 STATISTICS:")
    stats = conversation_service.get_statistics()
    print(f"   Total active clients: {stats['total_active_clients']}")
    print(f"   Total messages: {stats['total_messages']}")
    
    for client_id, info in stats['clients'].items():
        print(f"\n   Client: {client_id}")
        print(f"     Messages: {info['message_count']}")
        print(f"     Last activity: {info['last_activity']}")
        print(f"     Metadata: {info['metadata']}")
    
    # ========== Lấy history của User 1 ==========
    print("\n" + "-"*80)
    print("📜 HISTORY của User 1 (Nguyễn Văn A):")
    history1 = conversation_service.get_conversation_history("user_nguyenvana")
    for i, msg in enumerate(history1, 1):
        role = "User" if msg["role"] == "user" else "AI"
        print(f"   {i}. {role}: {msg['content'][:60]}...")
    
    # ========== Lấy history của User 2 ==========
    print("\n📜 HISTORY của User 2 (Trần Thị B):")
    history2 = conversation_service.get_conversation_history("user_tranthib")
    for i, msg in enumerate(history2, 1):
        role = "User" if msg["role"] == "user" else "AI"
        print(f"   {i}. {role}: {msg['content'][:60]}...")
    
    # ========== Clear conversation ==========
    print("\n" + "-"*80)
    print("🧹 CLEANUP:")
    print("   Xóa conversation của User 1...")
    conversation_service.clear_conversation("user_nguyenvana")
    
    print("   Xóa conversation của User 2...")
    conversation_service.clear_conversation("user_tranthib")
    
    print("   ✅ Đã xóa tất cả conversations")
    
    # Verify
    stats_after = conversation_service.get_statistics()
    print(f"   Active clients sau khi xóa: {stats_after['total_active_clients']}")
    
    print("\n" + "="*80)
    print("✅ DEMO HOÀN THÀNH!")
    print("="*80)
    print("\n💡 Key Points:")
    print("   - Mỗi client có conversation history riêng")
    print("   - AI nhớ context của từng user")
    print("   - Thread-safe, hỗ trợ concurrent users")
    print("   - Auto cleanup sessions cũ")
    print()


async def demo_voice_assistant():
    """Demo Voice Assistant use case"""
    
    print("\n" + "="*80)
    print("🎤 DEMO: VOICE ASSISTANT (ESP32)")
    print("="*80)
    
    # Giả lập ESP32 gửi lệnh giọng nói
    esp32_id = "esp32_living_room"
    
    print(f"\n🔊 ESP32 ({esp32_id}) - Lệnh 1:")
    result1 = await conversation_service.process_voice_command(
        client_id=esp32_id,
        text="Bật đèn phòng khách",
        metadata={"device_type": "ESP32", "location": "Living Room"}
    )
    print(f"   🤖 AI Response: {result1}")
    
    print(f"\n🔊 ESP32 ({esp32_id}) - Lệnh 2 (có context):")
    result2 = await conversation_service.process_voice_command(
        client_id=esp32_id,
        text="Tắt nó đi",  # AI biết "nó" = đèn phòng khách
    )
    print(f"   🤖 AI Response: {result2}")
    
    print(f"\n🔊 ESP32 ({esp32_id}) - Lệnh 3:")
    result3 = await conversation_service.process_voice_command(
        client_id=esp32_id,
        text="Nhiệt độ hiện tại là bao nhiêu?",
    )
    print(f"   🤖 AI Response: {result3}")
    
    # Xem history
    print("\n📜 Lịch sử lệnh:")
    history = conversation_service.get_conversation_history(esp32_id)
    for i, msg in enumerate(history, 1):
        role = "🗣️ User" if msg["role"] == "user" else "🤖 AI"
        print(f"   {i}. {role}: {msg['content']}")
    
    # Cleanup
    conversation_service.clear_conversation(esp32_id)
    print("\n✅ Demo Voice Assistant hoàn thành!")


async def main():
    """Main entry point"""
    
    print("\n" + "🚀"*40)
    print("CONVERSATION SERVICE - MULTI-USER TEST")
    print("🚀"*40)
    
    try:
        # Demo 1: Multi-user chat
        await demo_multi_user()
        
        # Demo 2: Voice assistant
        # await demo_voice_assistant()
        
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

