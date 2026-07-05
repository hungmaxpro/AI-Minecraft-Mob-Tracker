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

print("⏳ Đang nạp mô hình AI bằng OpenVINO (Size: 320)...")
model = YOLO("best_openvino_model", task="detect")

T, L, W, H = 0, 0, 800, 640
monitor = {"top": T, "left": L, "width": W, "height": H}
sct = MSS()

detected_boxes = []

# =====================================================================
# BẢNG MÀU CHUẨN CỦA ULTRALYTICS YOLO
# =====================================================================
YOLO_COLORS = [
    "#FF3838", "#FF9D97", "#FF701F", "#FFB21D", "#CFD231",
    "#48F90A", "#92CC17", "#3DDB86", "#1A9334", "#00D4BB",
    "#2C99A8", "#00C2FF", "#344593", "#6473FF", "#0018EC",
    "#8438FF", "#520085", "#CB38FF", "#FF95C8", "#FF37C7"
]

def ai_worker():
    global detected_boxes
    fps_start_time = time.time()
    fps_counter = 0
    
    while True:
        sct_img = sct.grab(monitor)
        frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2BGR)
        
        results = model.predict(source=frame, conf=0.45, imgsz=320, verbose=False, device="intel:gpu")
        
        temp_boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            name = results[0].names[cls_id]
            
            color = YOLO_COLORS[cls_id % len(YOLO_COLORS)]
            temp_boxes.append((int(x1), int(y1), int(x2), int(y2), name, color))
            
        detected_boxes = temp_boxes
        
        fps_counter += 1
        if (time.time() - fps_start_time) > 1:
            fps = fps_counter / (time.time() - fps_start_time)
            print(f"Tốc độ xử lý thực tế (Iris Xe): {fps:.2f} FPS")
            fps_counter = 0
            fps_start_time = time.time()

threading.Thread(target=ai_worker, daemon=True).start()
print("Radar AI đã bật! Giao diện đã được nâng cấp làm đẹp.")

overlay = tk.Tk()
overlay.geometry(f"{W}x{H}+{L}+{T}")
overlay.overrideredirect(True)
overlay.attributes("-transparentcolor", "black")
overlay.attributes("-topmost", True)

canvas = tk.Canvas(overlay, width=W, height=H, bg="black", highlightthickness=0)
canvas.pack()

def update_ui():
    canvas.delete("all")
    
    # =====================================================================
    # TRẢ LẠI KHUNG CAMERA ĐỎ ĐỊNH VỊ CHO ÔNG ĐÂY
    # =====================================================================
    canvas.create_rectangle(0, 0, W-1, H-1, outline="red", width=2)
    
    # Vẽ các khung nhận diện quái vật
    for (x1, y1, x2, y2, name, color) in detected_boxes:
        # Viền Box
        canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
        
        # Tag nền màu
        text_width = len(name) * 8 + 10 
        canvas.create_rectangle(x1, y1-20, x1 + text_width, y1, fill=color, outline="")
        
        # Chữ trắng
        canvas.create_text(x1+5, y1-10, text=name, fill="white", font=("Arial", 10, "bold"), anchor="w")
    
    overlay.after(16, update_ui)

update_ui()
overlay.mainloop()