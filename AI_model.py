import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk
from tkinter import messagebox
import threading
import pygetwindow as gw
import keyboard
import os
from ultralytics import YOLO

# =====================================================================
# ÉP WINDOWS TRẢ VỀ ĐÚNG ĐỘ PHÂN GIẢI THỰC (CHỐNG LỖI HIỂN THỊ SCALE)
# =====================================================================
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Kích hoạt chế độ DPI thực cho Windows 8.1/10/11
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # Dự phòng cho Windows cũ hơn
    except Exception:
        pass

# Ép Terminal Windows dùng UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Biến toàn cục
detected_boxes = []
ai_fps = 0.0
is_running = False
should_return = False 
mc_not_found = False 
current_monitor = None
W_SCREEN, H_SCREEN = 1920, 1080
ai_model = None 

# =====================================================================
# HÀM TÌM CỬA SỔ MINECRAFT TỰ ĐỘNG
# =====================================================================
def get_mc_window():
    windows = gw.getWindowsWithTitle('Minecraft')
    for win in windows:
        if "AI" in win.title or "Launcher" in win.title:
            continue
        if win.width > 300 and win.height > 300 and win.left > -10000:
            return {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
    return None

# =====================================================================
# LUỒNG AI
# =====================================================================
def ai_worker():
    global detected_boxes, ai_fps, is_running, current_monitor, ai_model, should_return, mc_not_found
    
    if ai_model is None:
        print("Đang nạp mô hình AI bằng OpenVINO (Size: 640)...")
        ai_model = YOLO("best_openvino_model", task="detect")
        
    sct = MSS()
    fps_start_time = time.time()
    fps_counter = 0
    retry_count = 0 
    
    while is_running:
        monitor = get_mc_window()
        current_monitor = monitor 
        
        if not monitor:
            detected_boxes = [] 
            retry_count += 1
            if retry_count >= 3: 
                print("Không tìm thấy game! Đang tự động quay về Menu...")
                mc_not_found = True
                should_return = True
                break 
                
            time.sleep(1)
            continue
            
        retry_count = 0 
            
        sct_img = sct.grab(monitor)
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        results = ai_model.predict(source=frame, conf=0.45, imgsz=640, verbose=False, device="intel:gpu")
        
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
            
    print("🛑 Đã dừng luồng AI!")

# =====================================================================
# XỬ LÝ PHÍM TẮT QUAY VỀ MENU (Ctrl+Shift+F)
# =====================================================================
def trigger_return():
    global should_return, is_running
    if is_running:
        print("Đã nhận lệnh (Ctrl+Shift+F). Đang quay về Menu...")
        should_return = True

keyboard.add_hotkey('ctrl+shift+f', trigger_return)

# =====================================================================
# LUỒNG UI OVERLAY (Kính trong suốt toàn màn hình)
# =====================================================================
def start_overlay():
    global W_SCREEN, H_SCREEN, should_return, is_running, mc_not_found
    
    overlay = tk.Tk()
    
    # Lấy lại kích thước màn hình sau khi đã áp dụng DPI Awareness
    W_SCREEN = overlay.winfo_screenwidth()
    H_SCREEN = overlay.winfo_screenheight()
    
    overlay.geometry(f"{W_SCREEN}x{H_SCREEN}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-transparentcolor", "black")
    overlay.attributes("-topmost", True)

    canvas = tk.Canvas(overlay, width=W_SCREEN, height=H_SCREEN, bg="black", highlightthickness=0)
    canvas.pack()

    def update_ui():
        global should_return, is_running
        
        if should_return:
            is_running = False 
            overlay.destroy()  
            show_launcher(show_error=mc_not_found) 
            return             
            
        canvas.delete("all")
        
        if current_monitor:
            L, T = current_monitor["left"], current_monitor["top"]
            R, B = L + current_monitor["width"], T + current_monitor["height"]
            
            canvas.create_rectangle(L, T, R, B, outline="red", width=2, dash=(4, 4))
            
            status_text = f"AI ACTIVE | AI FPS: {ai_fps:.1f}"
            canvas.create_rectangle(L, T-25, L+220, T, fill="black", outline="red")
            canvas.create_text(L+5, T-12, text=status_text, fill="#00FFFF", font=("Arial", 10, "bold"), anchor="w")
        else:
            # Đảm bảo căn giữa tuyệt đối
            canvas.create_text(W_SCREEN//2, H_SCREEN//2, text="ĐANG TÌM CỬA SỔ MINECRAFT...", fill="yellow", font=("Arial", 20, "bold"), justify="center")

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
def show_launcher(show_error=False):
    global should_return, is_running, detected_boxes, current_monitor, mc_not_found
    
    should_return = False
    is_running = False
    mc_not_found = False
    detected_boxes = []
    current_monitor = None
    
    launcher = tk.Tk()
    launcher.title("AI Minecraft Mob Tracker V1")
    launcher.geometry("450x300")
    launcher.configure(bg="#2C2F33")
    launcher.eval('tk::PlaceWindow . center') 

    if show_error:
        launcher.after(200, lambda: messagebox.showwarning(
            "Cảnh báo", 
            "Không tìm thấy cửa sổ Minecraft (hoặc bạn đã tắt game)!\nAI tự động dừng để tránh lỗi hiển thị.", 
            parent=launcher
        ))

    def start_app():
        global is_running
        launcher.destroy() 
        is_running = True
        threading.Thread(target=ai_worker, daemon=True).start()
        start_overlay() 

    tk.Label(launcher, text="AI NHẬN DIỆN MOB MC", font=("Arial", 16, "bold"), fg="white", bg="#2C2F33").pack(pady=15)

    mobs_list = "Bò, Lợn, Cừu, Gà, Ngựa,\nChó, Dân Làng, Iron Golem"
    tk.Label(launcher, text="Những mob hiện tại AI có thể nhận diện:", font=("Arial", 10, "italic"), fg="#99AAB5", bg="#2C2F33").pack()
    tk.Label(launcher, text=mobs_list, font=("Arial", 11, "bold"), fg="#43B581", bg="#2C2F33").pack(pady=5)

    tk.Label(launcher, text="Vùng nhận diện của AI trên màn hình sẽ tùy thuộc\nvào kích thước tab minecraft hiện tại.", font=("Arial", 10), fg="#FAA61A", bg="#2C2F33", justify="center").pack(pady=10)

    tk.Button(launcher, text="BẮT ĐẦU", font=("Arial", 12, "bold"), bg="#7289DA", fg="white", activebackground="#5B6EAE", activeforeground="white", width=20, command=start_app).pack(pady=10)

    tk.Label(launcher, text="Quay lại Menu nhấn tổ hợp: Ctrl + Shift + F", font=("Arial", 9), fg="#99AAB5", bg="#2C2F33").pack()

    launcher.mainloop()

if __name__ == "__main__":
    show_launcher()