import sys
import cv2
import time
import numpy as np
from mss import MSS
import tkinter as tk
import threading
from ultralytics import YOLO

# Ép Terminal Windows dùng UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("⏳ Đang nạp mô hình AI bằng OpenVINO (Size: 640)...")
model = YOLO("best_openvino_model", task="detect")

# Cấu hình Full Màn Hình (1920x1080)
W, H = 1920, 1080
monitor = {"top": 0, "left": 0, "width": W, "height": H}
sct = MSS()

detected_boxes = []

def ai_worker():
    global detected_boxes
    fps_start_time = time.time()
    fps_counter = 0
    
    while True:
        sct_img = sct.grab(monitor)
        # Chuyển đổi BGRA sang BGR để AI xử lý
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        # Chạy AI trên Intel Iris Xe GPU ở size 640 để có độ nét
        results = model.predict(source=frame, conf=0.45, imgsz=640, verbose=False, device="intel:gpu")
        
        temp_boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            name = results[0].names[cls_id]
            # Chỉ dùng màu trắng đơn giản để vẽ viền
            temp_boxes.append((int(x1), int(y1), int(x2), int(y2), name))
            
        detected_boxes = temp_boxes
        
        fps_counter += 1
        if (time.time() - fps_start_time) > 1:
            fps = fps_counter / (time.time() - fps_start_time)
            # In FPS của AI ra Terminal để ông theo dõi
            print(f"⚡ Tốc độ xử lý của Não AI (OpenVINO GPU): {fps:.2f} FPS")
            fps_counter = 0
            fps_start_time = time.time()

# Kích hoạt luồng AI
threading.Thread(target=ai_worker, daemon=True).start()
print("✅ Radar AI đã bật! Quét toàn màn hình...")

# --- LUỒNG UI GIAO DIỆN TRONG SUỐT ---
overlay = tk.Tk()
overlay.geometry(f"{W}x{H}+0+0")
overlay.overrideredirect(True)
overlay.attributes("-transparentcolor", "black")
overlay.attributes("-topmost", True)

canvas = tk.Canvas(overlay, width=W, height=H, bg="black", highlightthickness=0)
canvas.pack()

def update_ui():
    canvas.delete("all")
    
    # Hiển thị FPS và trạng thái ở góc trên bên phải để chắc chắn code đang chạy
    status_text = "RADAR: ACTIVE (FULL SCREEN - SIMPLE MODE)"
    canvas.create_text(W - 10, 20, text=status_text, fill="white", font=("Arial", 12, "bold"), anchor="e")
    
    # Vẽ các khung nhận diện với viền trắng mỏng, tag tên có nền đen mờ
    for (x1, y1, x2, y2, name) in detected_boxes:
        canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2)
        # Nền tag đen mờ giúp chữ trắng nổi bật
        canvas.create_rectangle(x1, y1-20, x1 + len(name)*10 + 10, y1, fill="black", outline="")
        canvas.create_text(x1+5, y1-10, text=name, fill="white", font=("Arial", 10, "bold"), anchor="w")
    
    # Vòng lặp vẽ mượt mà (~60 FPS)
    overlay.after(16, update_ui)

update_ui()
overlay.mainloop()