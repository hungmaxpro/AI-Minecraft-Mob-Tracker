#include <iostream>
#include <winsock2.h>
#include <windows.h>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>

#pragma comment(lib, "ws2_32.lib")

struct BBox { int x1, y1, x2, y2; std::string name; };
std::vector<BBox> current_boxes;
std::string current_fps = "0.0";
RECT current_mc_rect = { 0, 0, 0, 0 };
bool is_mc_active = false;

HWND g_hwnd = NULL;
CRITICAL_SECTION data_cs;

// Hàm cắt chuỗi và xử lý dữ liệu từ Python
void ParseData(std::string data) {
    EnterCriticalSection(&data_cs);

    current_boxes.clear();
    is_mc_active = false;
    if (data == "EMPTY") {
        LeaveCriticalSection(&data_cs);
        return;
    }

    try {
        std::stringstream ss(data);
        std::string item;
        std::vector<std::string> parts;
        while (std::getline(ss, item, '|')) {
            parts.push_back(item);
        }

        if (parts.size() >= 2) {
            is_mc_active = true;
            current_fps = parts[0];

            std::stringstream ss_rect(parts[1]);
            std::string val;
            std::getline(ss_rect, val, ','); current_mc_rect.left = std::stoi(val);
            std::getline(ss_rect, val, ','); current_mc_rect.top = std::stoi(val);
            std::getline(ss_rect, val, ','); current_mc_rect.right = std::stoi(val);
            std::getline(ss_rect, val, ','); current_mc_rect.bottom = std::stoi(val);

            for (size_t i = 2; i < parts.size(); ++i) {
                if (parts[i] == "NO_MOB" || parts[i].empty()) continue;
                std::stringstream ss_box(parts[i]);
                BBox box;
                std::getline(ss_box, val, ','); box.x1 = std::stoi(val);
                std::getline(ss_box, val, ','); box.y1 = std::stoi(val);
                std::getline(ss_box, val, ','); box.x2 = std::stoi(val);
                std::getline(ss_box, val, ','); box.y2 = std::stoi(val);
                std::getline(ss_box, box.name, ',');
                current_boxes.push_back(box);
            }
        }
    }
    catch (...) {}

    LeaveCriticalSection(&data_cs);
}

// Luồng nhận UDP
DWORD WINAPI UDPListener(LPVOID lpParam) {
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
    SOCKET recvSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    sockaddr_in recvAddr;
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(9999);
    recvAddr.sin_addr.s_addr = htonl(INADDR_ANY);

    bind(recvSocket, (SOCKADDR*)&recvAddr, sizeof(recvAddr));
    char recvBuf[4096];

    while (true) {
        int bytesRecv = recvfrom(recvSocket, recvBuf, 4096, 0, NULL, NULL);
        if (bytesRecv > 0) {
            recvBuf[bytesRecv] = '\0';
            ParseData(std::string(recvBuf));

            if (g_hwnd) {
                InvalidateRect(g_hwnd, NULL, TRUE); // Kích hoạt lệnh vẽ lại
            }
        }
    }
    return 0;
}

// Hàm vẽ chính (GDI)
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    if (uMsg == WM_PAINT) {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);

        FillRect(hdc, &ps.rcPaint, (HBRUSH)CreateSolidBrush(RGB(0, 0, 0)));
        SetBkMode(hdc, TRANSPARENT);

        EnterCriticalSection(&data_cs);

        if (is_mc_active) {
            // Vẽ viền bao quanh game
            HPEN hPenDash = CreatePen(PS_DASH, 1, RGB(255, 0, 0));
            SelectObject(hdc, hPenDash);
            SelectObject(hdc, GetStockObject(NULL_BRUSH));
            Rectangle(hdc, current_mc_rect.left, current_mc_rect.top, current_mc_rect.right, current_mc_rect.bottom);

            // Vẽ khung thông số FPS
            SetTextColor(hdc, RGB(0, 255, 255));
            std::string fps_text = "RADAR ACTIVE | AI FPS: " + current_fps;
            TextOutA(hdc, current_mc_rect.left + 5, std::max(0L, current_mc_rect.top - 20), fps_text.c_str(), fps_text.length());
            DeleteObject(hPenDash);

            // Vẽ Box quái vật
            HPEN hPenBox = CreatePen(PS_SOLID, 2, RGB(255, 255, 255));
            SelectObject(hdc, hPenBox);
            SetTextColor(hdc, RGB(255, 255, 255));

            for (const auto& box : current_boxes) {
                Rectangle(hdc, box.x1, box.y1, box.x2, box.y2);
                TextOutA(hdc, box.x1 + 5, box.y1 - 15, box.name.c_str(), box.name.length());
            }
            DeleteObject(hPenBox);
        }

        LeaveCriticalSection(&data_cs);
        EndPaint(hwnd, &ps);
    }
    else if (uMsg == WM_DESTROY) {
        PostQuitMessage(0);
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

// Khai báo ẩn để MinGW bỏ qua lỗi DPI
typedef HRESULT(WINAPI* SetProcessDpiAwareness_t)(int);
typedef BOOL(WINAPI* SetProcessDPIAware_t)(void);

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {

    // Tối ưu hóa phân giải cho Windows
    HMODULE hShcore = LoadLibraryA("Shcore.dll");
    if (hShcore) {
        SetProcessDpiAwareness_t SetDpi = (SetProcessDpiAwareness_t)GetProcAddress(hShcore, "SetProcessDpiAwareness");
        if (SetDpi) SetDpi(2);
        FreeLibrary(hShcore);
    }
    else {
        HMODULE hUser32 = LoadLibraryA("user32.dll");
        if (hUser32) {
            SetProcessDPIAware_t SetDpiUser32 = (SetProcessDPIAware_t)GetProcAddress(hUser32, "SetProcessDPIAware");
            if (SetDpiUser32) SetDpiUser32();
            FreeLibrary(hUser32);
        }
    }

    InitializeCriticalSection(&data_cs);

    // Tự động kích hoạt file Python lên
    ShellExecuteA(NULL, "open", "AI_model.exe", NULL, NULL, SW_SHOW);
    CreateThread(NULL, 0, UDPListener, NULL, 0, NULL);

    WNDCLASSA wc = { 0 };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "MinecraftOverlay";
    wc.hbrBackground = CreateSolidBrush(RGB(0, 0, 0));
    RegisterClassA(&wc);

    int w = GetSystemMetrics(SM_CXSCREEN);
    int h = GetSystemMetrics(SM_CYSCREEN);

    // Kích hoạt cửa sổ tàng hình
    g_hwnd = CreateWindowExA(
        WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW,
        "MinecraftOverlay", "Radar", WS_POPUP,
        0, 0, w, h, NULL, NULL, hInstance, NULL
    );

    SetLayeredWindowAttributes(g_hwnd, RGB(0, 0, 0), 0, LWA_COLORKEY);
    ShowWindow(g_hwnd, nCmdShow);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    DeleteCriticalSection(&data_cs);
    return 0;
}