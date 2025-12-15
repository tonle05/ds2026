#!/usr/bin/env python3
import sys

# Đọc từng dòng từ đầu vào chuẩn (stdin)
for line in sys.stdin:
    # Xóa khoảng trắng thừa ở đầu/cuối
    line = line.strip()
    # Tách dòng thành các từ
    words = line.split()
    
    # Xuất ra output dạng: word <tab> 1
    for word in words:
        # Ghi ra stdout
        print(f"{word}\t1")