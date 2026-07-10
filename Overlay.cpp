#include <iostream>
#include <winsock2.h>
#include <windows.h>
#include <string>
#include <vector>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

struct BBox { int x1, y1, x2, y2; std::string name; };
std::vector<BBox> current_boxes;

void ParseData(std::string data) {
    current_boxes.clear();
    if (data == "EMPTY") return;

    std::stringstream ss(data);
    std::string item;
    while (std::getline(ss, item, '|')) {
        std::stringstream ss_box(item);
        std::string val;
        BBox box;
        std::getline(ss_box, val, ','); box.x1 = std::stoi(val);
        std::getline(ss_box, val, ','); box.y1 = std::stoi(val);
        std::getline(ss_box, val, ','); box.x2 = std::stoi(val);
        std::getline(ss_box, val, ','); box.y2 = std::stoi(val);
        std::getline(ss_box, box.name, ',');
        current_boxes.push_back(box);
    }
}

DWORD WINAPI UDPListener(LPVOID lpParam) {
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
    SOCKET recvSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    sockaddr_in recvAddr;
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(9999);
    recvAddr.sin_addr.s_addr = htonl(INADDR_ANY);

    bind(recvSocket, (SOCKADDR*)&recvAddr, sizeof(recvAddr));
    char recvBuf[2048]; // Tăng buffer đề phòng nhiều quái

    while (true) {
        int bytesRecv = recvfrom(recvSocket, recvBuf, 2048, 0, NULL, NULL);
        if (bytesRecv > 0) {
            recvBuf[bytesRecv] = '\0';
            ParseData(std::string(recvBuf));
        }
    }
    return 0;
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    if (uMsg == WM_PAINT) {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);

        FillRect(hdc, &ps.rcPaint, (HBRUSH)CreateSolidBrush(RGB(0, 0, 0)));
        HPEN hPen = CreatePen(PS_SOLID, 2, RGB(255, 0, 0));
        SelectObject(hdc, hPen);
        SelectObject(hdc, GetStockObject(NULL_BRUSH));

        for (const auto& box : current_boxes) {
            Rectangle(hdc, box.x1, box.y1, box.x2, box.y2);
            TextOutA(hdc, box.x1 + 5, box.y1 - 15, box.name.c_str(), box.name.length());
        }

        DeleteObject(hPen);
        EndPaint(hwnd, &ps);
        InvalidateRect(hwnd, NULL, TRUE);
    }
    else if (uMsg == WM_DESTROY) {
        PostQuitMessage(0);
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 1. TỰ ĐỘNG GỌI GIAO DIỆN PYTHON LÊN (File exe của ông)
    ShellExecuteA(NULL, "open", "AI_model.exe", NULL, NULL, SW_SHOW);

    // 2. Kích hoạt luồng nghe ngóng dữ liệu UDP
    CreateThread(NULL, 0, UDPListener, NULL, 0, NULL);

    WNDCLASSA wc = { 0 }; // Đã sửa về ANSI
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "MinecraftOverlay";
    wc.hbrBackground = CreateSolidBrush(RGB(0, 0, 0));
    RegisterClassA(&wc);

    int w = GetSystemMetrics(SM_CXSCREEN);
    int h = GetSystemMetrics(SM_CYSCREEN);

    HWND hwnd = CreateWindowExA( // Đã sửa về ANSI
        WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW,
        "MinecraftOverlay", "Radar", WS_POPUP,
        0, 0, w, h, NULL, NULL, hInstance, NULL
    );

    SetLayeredWindowAttributes(hwnd, RGB(0, 0, 0), 0, LWA_COLORKEY);
    ShowWindow(hwnd, nCmdShow);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return 0;
}