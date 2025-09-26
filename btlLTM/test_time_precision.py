#!/usr/bin/env python3
"""
Test script to verify time precision conversion
Kiểm tra độ chính xác của việc chuyển đổi thời gian
"""

import time

def test_time_precision():
    print("=== KIỂM TRA ĐỘ CHÍNH XÁC THỜI GIAN ===")
    
    # Simulate ESP32 timestamp_us (microseconds since epoch)
    current_time = time.time()
    timestamp_us = int(current_time * 1000000)
    timestamp_ms = int(current_time * 1000)
    timestamp_sec = int(current_time)
    
    print(f"Original time: {current_time:.6f} seconds")
    print(f"timestamp_us: {timestamp_us}")
    print(f"timestamp_ms: {timestamp_ms}")
    print(f"timestamp_sec: {timestamp_sec}")
    print()
    
    # Test conversion back to seconds
    converted_from_us = timestamp_us / 1000000.0
    converted_from_ms = timestamp_ms / 1000.0
    converted_from_sec = float(timestamp_sec)
    
    print("=== CHUYỂN ĐỔI NGƯỢC ===")
    print(f"From timestamp_us: {converted_from_us:.6f} seconds")
    print(f"From timestamp_ms: {converted_from_ms:.6f} seconds")
    print(f"From timestamp_sec: {converted_from_sec:.6f} seconds")
    print()
    
    # Test precision loss
    print("=== KIỂM TRA MẤT ĐỘ CHÍNH XÁC ===")
    loss_us = abs(current_time - converted_from_us)
    loss_ms = abs(current_time - converted_from_ms)
    loss_sec = abs(current_time - converted_from_sec)
    
    print(f"Precision loss from us: {loss_us:.10f} seconds")
    print(f"Precision loss from ms: {loss_ms:.10f} seconds")
    print(f"Precision loss from sec: {loss_sec:.10f} seconds")
    print()
    
    # Test tx_time calculation
    print("=== KIỂM TRA TÍNH TOÁN TX_TIME ===")
    recv_time = current_time + 0.001  # Simulate 1ms delay
    
    tx_time_us = recv_time - converted_from_us
    tx_time_ms = recv_time - converted_from_ms
    tx_time_sec = recv_time - converted_from_sec
    
    print(f"Real tx_time: {0.001:.6f} seconds")
    print(f"Calculated from us: {tx_time_us:.6f} seconds")
    print(f"Calculated from ms: {tx_time_ms:.6f} seconds")
    print(f"Calculated from sec: {tx_time_sec:.6f} seconds")
    print()
    
    # Test with very small differences
    print("=== KIỂM TRA VỚI ĐỘ CHÊNH LỆCH NHỎ ===")
    small_delay = 0.0001  # 0.1ms
    recv_time_small = current_time + small_delay
    
    tx_time_small_us = recv_time_small - converted_from_us
    tx_time_small_ms = recv_time_small - converted_from_ms
    tx_time_small_sec = recv_time_small - converted_from_sec
    
    print(f"Real tx_time (0.1ms): {small_delay:.6f} seconds")
    print(f"Calculated from us: {tx_time_small_us:.6f} seconds")
    print(f"Calculated from ms: {tx_time_small_ms:.6f} seconds")
    print(f"Calculated from sec: {tx_time_small_sec:.6f} seconds")
    print()
    
    # Conclusion
    print("=== KẾT LUẬN ===")
    if loss_us < 0.000001:  # Less than 1 microsecond
        print("✅ timestamp_us: Độ chính xác cao (microsecond)")
    else:
        print("❌ timestamp_us: Có mất độ chính xác")
        
    if loss_ms < 0.001:  # Less than 1 millisecond
        print("✅ timestamp_ms: Độ chính xác tốt (millisecond)")
    else:
        print("❌ timestamp_ms: Có mất độ chính xác")
        
    if loss_sec < 1.0:  # Less than 1 second
        print("✅ timestamp_sec: Độ chính xác cơ bản (second)")
    else:
        print("❌ timestamp_sec: Mất độ chính xác đáng kể")

if __name__ == "__main__":
    test_time_precision()