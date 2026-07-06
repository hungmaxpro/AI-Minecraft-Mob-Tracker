import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk
from tkinter import messagebox  # THÊM: Thư viện tạo hộp thoại thông báo
import threading
import pygetwindow as gw
import keyboard
from ultralytics import YOLO

# Ép Terminal Windows dùng UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =====================================================================
# TẢI MÔ HÌNH 1 LẦN DUY NHẤT LÚC MỞ TOOL
# =====================================================================
print("⏳ Đang nạp mô hình AI (OpenVINO - Size 640)... Vui lòng đợi vài giây.")
model = YOLO("best_openvino_model", task="detect")
print("✅ Nạp mô hình thành công! Đang khởi động Giao diện...")

# Biến toàn cục kiểm soát trạng thái
detected_boxes = []
ai_fps = 0.0
is_running = False
mc_lost = False
current_monitor = None
overlay = None

# =====================================================================
# HÀM TÌM CỬA SỔ MINECRAFT
# =====================================================================
def get_mc_window():
    windows = gw.getWindowsWithTitle('Minecraft')
    if windows:
        win = windows[0]
        if win.width > 0 and win.height > 0:
            return {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
    return None

# =====================================================================
# LUỒNG AI XỬ LÝ NGẦM
# =====================================================================
def ai_worker():
    global detected_boxes, ai_fps, is_running, current_monitor, mc_lost
    sct = MSS()
    fps_start_time = time.time()
    fps_counter = 0
    
    while is_running:
        monitor = get_mc_window()
        current_monitor = monitor
        
        # LOGIC MỚI: Nếu đang chạy mà mất tab MC -> Báo cờ lỗi và dừng luồng
        if not monitor:
            mc_lost = True
            is_running = False
            break
            
        sct_img = sct.grab(monitor)
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        results = model.predict(source=frame, conf=0.45, imgsz=640, verbose=False, device="intel:gpu")
        
        temp_boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            name = results[0].names[cls_id]
            
            real_x1 = int(x1) + monitor["left"]
            real_y1 = int(y1) + monitor["top"]
            real_x2 = int(x2) + monitor["left"]
            real_y2 = int(y2) + monitor["top"]
            
            temp_boxes.append((real_x1, real_y1, real_x2, real_y2, name))
            
        detected_boxes = temp_boxes
        
        fps_counter += 1
        if (time.time() - fps_start_time) > 1:
            ai_fps = fps_counter / (time.time() - fps_start_time)
            fps_counter = 0
            fps_start_time = time.time()

# =====================================================================
# PHÍM TẮT THOÁT RADAR (TRỞ VỀ MENU)
# =====================================================================
def stop_radar_hotkey():
    global is_running
    if is_running:
        print("🛑 Nhận lệnh tắt từ Phím tắt!")
        is_running = False # Kích hoạt cờ dừng hệ thống

keyboard.add_hotkey('ctrl+shift+f', stop_radar_hotkey)

# =====================================================================
# GIAO DIỆN KÍNH TRONG SUỐT (OVERLAY)
# =====================================================================
def start_overlay():
    global overlay
    
    # Tạo cửa sổ con (Toplevel) đè lên mọi thứ
    overlay = tk.Toplevel(root)
    W_SCREEN = overlay.winfo_screenwidth()
    H_SCREEN = overlay.winfo_screenheight()
    
    overlay.geometry(f"{W_SCREEN}x{H_SCREEN}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-transparentcolor", "black")
    overlay.attributes("-topmost", True)

    canvas = tk.Canvas(overlay, width=W_SCREEN, height=H_SCREEN, bg="black", highlightthickness=0)
    canvas.pack()

    def update_ui():
        global is_running, mc_lost
        
        # KIỂM TRA ĐIỀU KIỆN DỪNG: Bị tắt bằng phím tắt HOẶC mất tab MC
        if not is_running:
            canvas.delete("all")
            overlay.destroy()  # Đóng kính trong suốt
            root.deiconify()   # HIỆN LẠI BẢNG MENU BAN ĐẦU
            
            # Hiện thông báo nếu nguyên nhân tắt là do mất tab MC
            if mc_lost:
                messagebox.showwarning("Cảnh báo", "Đã mất dấu tab Minecraft!\nRadar tự động ngắt để tiết kiệm tài nguyên.")
            return # Thoát vòng lặp vẽ
            
        canvas.delete("all")
        
        if current_monitor:
            L, T = current_monitor["left"], current_monitor["top"]
            R, B = L + current_monitor["width"], T + current_monitor["height"]
            
            canvas.create_rectangle(L, T, R, B, outline="red", width=2, dash=(4, 4))
            
            status_text = f"RADAR ACTIVE | AI FPS: {ai_fps:.1f}"
            canvas.create_rectangle(L, T-25, L+220, T, fill="black", outline="red")
            canvas.create_text(L+5, T-12, text=status_text, fill="#00FFFF", font=("Arial", 10, "bold"), anchor="w")

        for (x1, y1, x2, y2, name) in detected_boxes:
            canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2)
            canvas.create_rectangle(x1, y1-20, x1 + len(name)*9 + 10, y1, fill="black", outline="")
            canvas.create_text(x1+5, y1-10, text=name, fill="white", font=("Arial", 10, "bold"), anchor="w")
        
        overlay.after(16, update_ui)

    update_ui()

# =====================================================================
# HÀM KÍCH HOẠT TỪ NÚT BẤM
# =====================================================================
def start_app():
    global is_running, mc_lost
    
    # 1. KIỂM TRA XEM CÓ MỞ GAME CHƯA TRƯỚC KHI BẬT
    if not get_mc_window():
        messagebox.showerror("Lỗi hệ thống", "Không tìm thấy tab Minecraft nào!\nHãy mở game trước khi bật Radar.")
        return
        
    # 2. ẨN BẢNG MENU ĐI
    root.withdraw() 
    
    # 3. KÍCH HOẠT LUỒNG VÀ GIAO DIỆN
    is_running = True
    mc_lost = False
    threading.Thread(target=ai_worker, daemon=True).start()
    start_overlay()

# =====================================================================
# GIAO DIỆN MENU GỐC (ROOT LAUNCHER)
# =====================================================================
root = tk.Tk()
root.title("Minecraft AI Radar V1")
root.geometry("450x300")
root.configure(bg="#2C2F33")
root.eval('tk::PlaceWindow . center')

tk.Label(root, text="🎯 AI NHẬN DIỆN MOB MC", font=("Arial", 16, "bold"), fg="white", bg="#2C2F33").pack(pady=15)

mobs_list = "Bò, Lợn, Cừu, Gà, Thỏ, Ngựa,\nChó, Mèo, Dân Làng, Iron Golem"
tk.Label(root, text="Những mob hiện tại AI có thể nhận diện:", font=("Arial", 10, "italic"), fg="#99AAB5", bg="#2C2F33").pack()
tk.Label(root, text=mobs_list, font=("Arial", 11, "bold"), fg="#43B581", bg="#2C2F33").pack(pady=5)

tk.Label(root, text="⚠️ Vùng nhận diện của AI trên màn hình sẽ tùy thuộc\nvào kích thước tab minecraft hiện tại.", font=("Arial", 10), fg="#FAA61A", bg="#2C2F33", justify="center").pack(pady=10)

tk.Button(root, text="🚀 NÚT BẮT ĐẦU", font=("Arial", 12, "bold"), bg="#7289DA", fg="white", activebackground="#5B6EAE", activeforeground="white", width=20, command=start_app).pack(pady=10)

tk.Label(root, text="Tắt đi nhấn tổ hợp: Ctrl + Shift + F", font=("Arial", 9), fg="#99AAB5", bg="#2C2F33").pack()

# Chạy vòng lặp giao diện chính
root.mainloop()