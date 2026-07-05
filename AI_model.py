import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk  # Thêm thư viện giao diện mặc định của Python

# Ép Terminal Windows dùng UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Định nghĩa vùng màn hình cần chụp (ROI)
T = 100
L = 100
W = 640
H = 640
monitor = {"top": T, "left": L, "width": W, "height": H}

# =====================================================================
# THỦ THUẬT: TẠO KHUNG NGẮM TRONG SUỐT (OVERLAY VIEWFINDER)
# =====================================================================
overlay = tk.Tk()
overlay.geometry(f"{W}x{H}+{L}+{T}")  # Đặt đúng vị trí và kích thước khung chụp
overlay.overrideredirect(True)        # XÓA THANH TIÊU ĐỀ CHƯƠNG TRÌNH
overlay.attributes("-transparentcolor", "black") # Làm biến mất màu đen thành trong suốt
overlay.attributes("-topmost", True)  # Ép khung này luôn nổi trên cùng mọi ứng dụng

# Vẽ một cái viền màu đỏ dày 4 pixel
canvas = tk.Canvas(overlay, width=W, height=H, bg="black", highlightthickness=0)
canvas.pack()
canvas.create_rectangle(0, 0, W-1, H-1, outline="red", width=4)
# =====================================================================

sct = MSS()
print("✅ Đang chạy... Nhấn 'q' tại cửa sổ Preview (OpenCV) để THOÁT.")

fps_start_time = time.time()
fps_counter = 0

while True:
    # Cập nhật khung ngắm để nó không bị đơ
    overlay.update()
    
    # 1. Chụp vùng màn hình
    sct_img = sct.grab(monitor)
    frame = np.array(sct_img)
    
    # 2. Tính FPS
    fps_counter += 1
    if (time.time() - fps_start_time) > 1:
        fps = fps_counter / (time.time() - fps_start_time)
        print(f"⚡ Tốc độ chụp: {fps:.2f} FPS")
        fps_counter = 0
        fps_start_time = time.time()
        
    # 3. Hiển thị cửa sổ Preview của OpenCV
    cv2.imshow("OpenCV Preview", frame)
    
    # Điều kiện dừng
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Dọn dẹp tài nguyên
cv2.destroyAllWindows()
overlay.destroy()