import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk
import threading
import pygetwindow as gw
import keyboard
import os
from ultralytics import YOLO

# Ép Terminal Windows dùng UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Biến toàn cục
detected_boxes = []
ai_fps = 0.0
is_running = True
current_monitor = None
W_SCREEN, H_SCREEN = 1920, 1080 # Kích thước màn hình ảo ban đầu

# =====================================================================
# HÀM TÌM CỬA SỔ MINECRAFT TỰ ĐỘNG
# =====================================================================
def get_mc_window():
    # Tìm tất cả cửa sổ có chữ 'Minecraft' trong tiêu đề
    windows = gw.getWindowsWithTitle('Minecraft')
    if windows:
        win = windows[0]
        # Xử lý trường hợp cửa sổ bị thu nhỏ (minimized)
        if win.width > 0 and win.height > 0:
            return {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
    return None

# =====================================================================
# LUỒNG AI (Tự động thích ứng kích thước game)
# =====================================================================
def ai_worker():
    global detected_boxes, ai_fps, is_running, current_monitor
    
    print("⏳ Đang nạp mô hình AI bằng OpenVINO (Size: 640)...")
    model = YOLO("best_openvino_model", task="detect")
    sct = MSS()
    
    fps_start_time = time.time()
    fps_counter = 0
    
    while is_running:
        # 1. Tìm vị trí hiện tại của game
        monitor = get_mc_window()
        current_monitor = monitor # Cập nhật cho UI biết để vẽ viền đỏ
        
        if not monitor:
            time.sleep(1) # Nếu không tìm thấy MC, đợi 1s rồi tìm lại
            continue
            
        # 2. Chụp đúng vùng game
        sct_img = sct.grab(monitor)
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        # 3. Chạy AI
        results = model.predict(source=frame, conf=0.45, imgsz=640, verbose=False, device="intel:gpu")
        
        temp_boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            name = results[0].names[cls_id]
            
            # CỘNG THÊM TỌA ĐỘ GÓC ĐỂ UI VẼ ĐÚNG VỊ TRÍ TRÊN TOÀN MÀN HÌNH
            real_x1 = int(x1) + monitor["left"]
            real_y1 = int(y1) + monitor["top"]
            real_x2 = int(x2) + monitor["left"]
            real_y2 = int(y2) + monitor["top"]
            
            temp_boxes.append((real_x1, real_y1, real_x2, real_y2, name))
            
        detected_boxes = temp_boxes
        
        # 4. Tính FPS
        fps_counter += 1
        if (time.time() - fps_start_time) > 1:
            ai_fps = fps_counter / (time.time() - fps_start_time)
            fps_counter = 0
            fps_start_time = time.time()

# =====================================================================
# HÀM THOÁT CHƯƠNG TRÌNH NÓNG (Ctrl+Shift+F)
# =====================================================================
def force_exit():
    print("🛑 Đã nhận lệnh thoát (Ctrl+Shift+F). Tắt Radar!")
    os._exit(0) # Thoát lập tức toàn bộ các luồng

keyboard.add_hotkey('ctrl+shift+f', force_exit)

# =====================================================================
# LUỒNG UI OVERLAY (Kính trong suốt toàn màn hình)
# =====================================================================
def start_overlay():
    global W_SCREEN, H_SCREEN
    
    overlay = tk.Tk()
    # Lấy kích thước thực tế của màn hình máy tính
    W_SCREEN = overlay.winfo_screenwidth()
    H_SCREEN = overlay.winfo_screenheight()
    
    overlay.geometry(f"{W_SCREEN}x{H_SCREEN}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-transparentcolor", "black")
    overlay.attributes("-topmost", True)

    canvas = tk.Canvas(overlay, width=W_SCREEN, height=H_SCREEN, bg="black", highlightthickness=0)
    canvas.pack()

    def update_ui():
        canvas.delete("all")
        
        # 1. Vẽ Viền đỏ và Bảng thông số nếu tìm thấy game
        if current_monitor:
            L, T = current_monitor["left"], current_monitor["top"]
            R, B = L + current_monitor["width"], T + current_monitor["height"]
            
            # Vẽ viền đỏ bo quanh tab Minecraft
            canvas.create_rectangle(L, T, R, B, outline="red", width=2, dash=(4, 4))
            
            # Vẽ bảng thông số ở góc tab Minecraft
            status_text = f"RADAR ACTIVE | AI FPS: {ai_fps:.1f}"
            canvas.create_rectangle(L, T-25, L+220, T, fill="black", outline="red")
            canvas.create_text(L+5, T-12, text=status_text, fill="#00FFFF", font=("Arial", 10, "bold"), anchor="w")
        else:
            # Báo hiệu đang đợi mở game
            canvas.create_text(W_SCREEN//2, H_SCREEN//2, text="ĐANG TÌM CỬA SỔ MINECRAFT...", fill="yellow", font=("Arial", 20, "bold"))

        # 2. Vẽ Box quái vật
        for (x1, y1, x2, y2, name) in detected_boxes:
            canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2)
            canvas.create_rectangle(x1, y1-20, x1 + len(name)*9 + 10, y1, fill="black", outline="")
            canvas.create_text(x1+5, y1-10, text=name, fill="white", font=("Arial", 10, "bold"), anchor="w")
        
        overlay.after(16, update_ui)

    update_ui()
    overlay.mainloop()

# =====================================================================
# GIAO DIỆN KHỞI ĐỘNG (LAUNCHER)
# =====================================================================
def start_app():
    # Khi bấm Nút Bắt Đầu
    launcher.destroy() # Đóng Launcher
    threading.Thread(target=ai_worker, daemon=True).start() # Bật não AI
    start_overlay() # Bật kính trong suốt

launcher = tk.Tk()
launcher.title("Minecraft AI Radar V1")
launcher.geometry("450x300")
launcher.configure(bg="#2C2F33")
launcher.eval('tk::PlaceWindow . center') # Canh giữa màn hình

# Tiêu đề
tk.Label(launcher, text="🎯 AI NHẬN DIỆN MOB MC", font=("Arial", 16, "bold"), fg="white", bg="#2C2F33").pack(pady=15)

# Danh sách quái vật
mobs_list = "Bò, Lợn, Cừu, Gà, Thỏ, Ngựa,\nChó, Mèo, Dân Làng, Iron Golem"
tk.Label(launcher, text="Những mob hiện tại AI có thể nhận diện:", font=("Arial", 10, "italic"), fg="#99AAB5", bg="#2C2F33").pack()
tk.Label(launcher, text=mobs_list, font=("Arial", 11, "bold"), fg="#43B581", bg="#2C2F33").pack(pady=5)

# Lưu ý
tk.Label(launcher, text="⚠️ Vùng nhận diện của AI trên màn hình sẽ tùy thuộc\nvào kích thước tab minecraft hiện tại.", font=("Arial", 10), fg="#FAA61A", bg="#2C2F33", justify="center").pack(pady=10)

# Nút bắt đầu
tk.Button(launcher, text="🚀 NÚT BẮT ĐẦU", font=("Arial", 12, "bold"), bg="#7289DA", fg="white", activebackground="#5B6EAE", activeforeground="white", width=20, command=start_app).pack(pady=10)

# Phím tắt
tk.Label(launcher, text="Tắt đi nhấn tổ hợp: Ctrl + Shift + F", font=("Arial", 9), fg="#99AAB5", bg="#2C2F33").pack()

launcher.mainloop()