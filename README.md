# AI Minecraft Mob Tracker (OpenVINO Optimized)

![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![AI Framework](https://img.shields.io/badge/AI-OpenVINO%20%7C%20YOLO-orange.svg)

This project is a real-time Mob tracking and detection radar for Minecraft. The software operates as a transparent overlay on top of the game window, utilizing artificial intelligence to lock onto targets without injecting or reading the game's memory.

The technical highlight of this project is its extreme hardware optimization (Edge AI), allowing a heavy Deep Learning model to run smoothly on standard Integrated Graphics (iGPUs) with a stable 20-30+ FPS.

---

## Core Technologies & Features

* **Hardware Acceleration:** The AI model is quantized (FP16) and compiled specifically for the Intel ecosystem using **OpenVINO**. The computational load is offloaded to the iGPU to free up CPU resources.
* **Multi-threading Architecture:** The system is separated into two independent threads. The UI Render thread ensures a smooth 60 FPS interface, while the AI Inference thread runs in the background to process image data without causing rendering bottlenecks.
* **Smart Window Tracking:** Integrates automatic detection, coordinate anchoring (Clamp Algorithm), and game window tracking. The radar automatically adjusts its scanning frame even if the user moves, resizes, or minimizes the game window.
* **UI/UX Handling:** Resolves coordinate offset issues caused by OS scaling features using DPI Awareness. Features a minimalist, high-contrast user interface.

---

## What I Learned

Building this project from scratch to a deployable executable was a hands-on journey in solving practical system optimization problems:

1. **Computer Vision & Edge AI:**
   * Gained a deep understanding of the **Speed-Accuracy Trade-off** in computer vision models.
   * Applied **Quantization** techniques (FP32 to FP16) and mathematical layer fusion to maximize iGPU performance via the Intel OpenVINO toolkit.

2. **Systems Optimization:**
   * Designed parallel processing pipelines using Multi-threading.
   * Addressed real-world latency and frame-ghosting between threads to achieve optimal data synchronization.

3. **Spatial & Coordinate Algorithms:**
   * Solved out-of-bounds coordinate exceptions (negative coordinates) using the **Clamp** algorithm.
   * Mapped relative coordinates from the AI bounding boxes to absolute desktop screen coordinates for pixel-perfect UI rendering.

4. **Deployment & Packaging:**
   * Overcame **Silent Crash** issues when packaging Python applications into standalone `.exe` files using PyInstaller.
   * Improved debugging skills through exception handling (Try-Except) and automated crash logging.
   * Learned how to manage dynamic-link libraries (`.dll`) and I/O streams (`sys.stdout`) when running applications in headless/windowed mode (`--windowed`).

---

## Installation & Usage

*Note: This release is optimized specifically for systems utilizing Intel hardware (CPUs/iGPUs) via OpenVINO. For NVIDIA/AMD GPU setups, please clone the source code and switch the backend to standard PyTorch, TensorRT, or CUDA.*

1. Download the `AI_Minecraft_Mob_Tracker_V1.zip` file from the **Releases** section.
2. Extract the files to any local folder.
3. Launch Minecraft (ensure the game window is not minimized).
4. Run `AI_model.exe` from the extracted folder.
5. Click **START** on the Launcher.
6. To safely terminate the system and free up resources, press the **`Ctrl + Shift + F`** hotkey.

---

## Supported Mobs
`Cow`, `Pig`, `Sheep`, `Chicken`, `Horse`, `Dog`, `Villager`, `Iron Golem`
