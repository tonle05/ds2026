#!/usr/bin/env python3
import sys

current_word = None
current_count = 0
word = None

# Đọc từng dòng từ stdin (dữ liệu này đã được lệnh 'sort' sắp xếp trước đó)
for line in sys.stdin:
    line = line.strip()
    
    # Tách word và count bằng dấu tab
    try:
        word, count = line.split('\t', 1)
        count = int(count)
    except ValueError:
        # Bỏ qua các dòng lỗi format
        continue

    # Vì dữ liệu đã sort, các từ giống nhau sẽ nằm liên tiếp
    if current_word == word:
        current_count += count
    else:
        # Nếu gặp từ mới, in kết quả từ cũ ra (nếu có)
        if current_word:
            print(f"{current_word}\t{current_count}")
        # Reset lại bộ đếm cho từ mới
        current_count = count
        current_word = word

# In ra từ cuối cùng
if current_word == word:
    print(f"{current_word}\t{current_count}")