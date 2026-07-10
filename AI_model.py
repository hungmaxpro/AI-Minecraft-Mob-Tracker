import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk
import threading
import pygetwindow as gw
import keyboard
import socket
from ultralytics import YOLO

# Ép Terminal Windows dùng UTF-8
try:
    if sys.stdout is not None and hasattr(sys.stdout, 'encoding'):
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Biến toàn cục
is_running = False
ai_model = None 

# CẤU HÌNH UDP BẮN TỌA ĐỘ SANG C++
UDP_IP = "127.0.0.1"
UDP_PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def get_mc_window():
    windows = gw.getWindowsWithTitle('Minecraft')
    for win in windows:
        if "AI" in win.title or "Launcher" in win.title:
            continue
        if win.width > 300 and win.height > 300 and win.left > -10000:
            return {"top": max(0, win.top), "left": max(0, win.left), "width": win.width, "height": win.height}
    return None

def ai_worker():
    global is_running, ai_model
    
    if ai_model is None:
        print("Đang nạp AI OpenVINO...")
        ai_model = YOLO("best_openvino_model", task="detect")
        
    sct = MSS()
    
    while is_running:
        monitor = get_mc_window()
        
        if not monitor:
            sock.sendto(b"EMPTY", (UDP_IP, UDP_PORT))
            time.sleep(1)
            continue
            
        sct_img = sct.grab(monitor)
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        results = ai_model.predict(source=frame, conf=0.45, imgsz=640, verbose=False, device="intel:gpu")
        
        data_string = ""
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            name = results[0].names[cls_id]
            
            real_x1 = int(x1) + monitor["left"]
            real_y1 = int(y1) + monitor["top"]
            real_x2 = int(x2) + monitor["left"]
            real_y2 = int(y2) + monitor["top"]
            
            data_string += f"{real_x1},{real_y1},{real_x2},{real_y2},{name}|"
            
        if data_string:
            data_string = data_string.rstrip('|')
        else:
            data_string = "EMPTY"
            
        # Bắn chuỗi dữ liệu sang C++
        sock.sendto(data_string.encode('utf-8'), (UDP_IP, UDP_PORT))

# ==========================================
# GIAO DIỆN VÀ PHÍM TẮT
# ==========================================
def force_exit():
    global is_running
    if is_running:
        is_running = False
        # Gửi tín hiệu rỗng để C++ xóa sạch khung vẽ trên màn hình
        sock.sendto(b"EMPTY", (UDP_IP, UDP_PORT))
        launcher.deiconify() # Hiện lại Menu

keyboard.add_hotkey('ctrl+shift+f', force_exit)

def start_app():
    global is_running
    launcher.withdraw() 
    is_running = True
    threading.Thread(target=ai_worker, daemon=True).start()

launcher = tk.Tk()
launcher.title("AI Minecraft Mob Tracker V2 (C++ Overlay)")
launcher.geometry("450x300")
launcher.configure(bg="#2C2F33")
launcher.eval('tk::PlaceWindow . center') 

tk.Label(launcher, text="🎯 AI NHẬN DIỆN MOB MC (BẢN UDP)", font=("Arial", 16, "bold"), fg="white", bg="#2C2F33").pack(pady=15)
tk.Label(launcher, text="Hệ thống đã chẻ luồng:\n- Python: Xử lý AI\n- C++: Hiển thị Đồ họa Win32", font=("Arial", 10, "italic"), fg="#99AAB5", bg="#2C2F33").pack()
tk.Button(launcher, text="🚀 BẮT ĐẦU", font=("Arial", 12, "bold"), bg="#7289DA", fg="white", activebackground="#5B6EAE", width=20, command=start_app).pack(pady=20)
tk.Label(launcher, text="Quay lại Menu nhấn tổ hợp: Ctrl + Shift + F", font=("Arial", 9), fg="#99AAB5", bg="#2C2F33").pack()

if __name__ == "__main__":
    launcher.mainloop()