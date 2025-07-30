#include "pch.h"

#include <windows.h>
#include <vector>
#include <string>
#include <algorithm>
#include <atomic>

// 全局变量
HHOOK g_hHook = NULL;
HWND g_hWnd = NULL;
std::wstring g_window_title;
std::vector<int> g_src_keys, g_dst_keys;
std::atomic<bool> g_running(false);
HANDLE g_hThread = NULL;
DWORD g_threadId = 0;
bool g_exact_match = false;  // 是否启用精确匹配

#define WM_HOOK_CONTROL (WM_USER + 1)
#define HOOK_START 1
#define HOOK_STOP 2

// 获取前台窗口标题
std::wstring get_foreground_window_title() {
    HWND hwnd = GetForegroundWindow();
    wchar_t title[256] = { 0 };
    GetWindowTextW(hwnd, title, 256);
    return std::wstring(title);
}

// 去除首尾空白字符
std::wstring trim(const std::wstring& str) {
    size_t first = str.find_first_not_of(L" \t\n\r");
    size_t last = str.find_last_not_of(L" \t\n\r");
    return (first == std::wstring::npos) ? L"" : str.substr(first, last - first + 1);
}

// 判断是否是“可见”字符（简单版，允许字母数字和部分中文）
bool is_visible_char(wchar_t ch) {
    return
        (ch >= L'!' && ch <= L'~') ||          // ASCII 可打印字符
        (ch >= 0x4E00 && ch <= 0x9FA5);       // 中文常用区
}

// 清理字符串，仅保留可见字符，并转小写
std::wstring clean_title(const std::wstring& str) {
    std::wstring result;
    for (wchar_t ch : str) {
        if (is_visible_char(ch)) {
            result += ::towlower(ch);
        }
    }
    return result;
}

// 辅助：打印字符串每个字符的 Unicode 编码，用于调试
void debug_output_wstring(const std::wstring& label, const std::wstring& str) {
    std::wstring output = label + L": ";
    for (wchar_t ch : str) {
        wchar_t buf[16];
        swprintf(buf, 16, L"\\u%04X", ch);
        output += buf;
    }
    OutputDebugStringW((output + L"\n").c_str());
}

// 判断当前窗口是否是目标窗口
bool is_target_window() {
    std::wstring fg_title_raw = trim(get_foreground_window_title());
    std::wstring config_title_raw = trim(g_window_title);

    // 调试输出原始标题
    debug_output_wstring(L"[原始窗口标题]", fg_title_raw);
    debug_output_wstring(L"[配置窗口标题]", config_title_raw);

    std::wstring fg_title = clean_title(fg_title_raw);
    std::wstring config_title = clean_title(config_title_raw);

    // 调试输出清理后的标题
    debug_output_wstring(L"[清理后窗口标题]", fg_title);
    debug_output_wstring(L"[清理后配置标题]", config_title);

    if (g_exact_match) {
        return fg_title == config_title;
    }
    else {
        return fg_title.find(config_title) != std::wstring::npos;
    }
}

// 配置接口：由 Python 调用
extern "C" __declspec(dllexport) void set_config(const wchar_t* title, const int* src, const int* dst, int count, bool exact) {
    g_window_title = title;
    g_src_keys.assign(src, src + count);
    g_dst_keys.assign(dst, dst + count);
    g_exact_match = exact;
}

// 按键映射查找
int find_mapped_key(int vk) {
    for (size_t i = 0; i < g_src_keys.size(); ++i) {
        if (g_src_keys[i] == vk) return g_dst_keys[i];
    }
    return 0;
}

// 低层钩子回调
LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        KBDLLHOOKSTRUCT* p = (KBDLLHOOKSTRUCT*)lParam;
        if (is_target_window()) {
            int mapped_vk = find_mapped_key(p->vkCode);
            if (mapped_vk) {
                if (wParam == WM_KEYDOWN) {
                    keybd_event(mapped_vk, 0, 0, 0);
                    return 1;
                }
                if (wParam == WM_KEYUP) {
                    keybd_event(mapped_vk, 0, KEYEVENTF_KEYUP, 0);
                    return 1;
                }
            }
        }
    }
    return CallNextHookEx(g_hHook, nCode, wParam, lParam);
}

// 消息处理
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_HOOK_CONTROL:
        if (wParam == HOOK_START) {
            if (!g_hHook) {
                g_hHook = SetWindowsHookEx(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0);
                OutputDebugStringW(g_hHook ? L"钩子安装成功\n" : L"钩子安装失败\n");
            }
        }
        else if (wParam == HOOK_STOP) {
            if (g_hHook) {
                UnhookWindowsHookEx(g_hHook);
                g_hHook = NULL;
                OutputDebugStringW(L"钩子已卸载\n");
            }
        }
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

// 钩子线程入口
DWORD WINAPI HookThreadProc(LPVOID lpParam) {
    WNDCLASS wc = { 0 };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = L"HookWindowClass";
    RegisterClass(&wc);

    g_hWnd = CreateWindow(wc.lpszClassName, L"HookWindow", 0, 0, 0, 0, 0, HWND_MESSAGE, NULL, wc.hInstance, NULL);

    PostMessage(g_hWnd, WM_HOOK_CONTROL, HOOK_START, 0);

    g_running = true;

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    PostMessage(g_hWnd, WM_HOOK_CONTROL, HOOK_STOP, 0);  // 确保卸载钩子
    g_running = false;
    return 0;
}

// 启动钩子
extern "C" __declspec(dllexport) bool start_hook() {
    if (g_running) return true;

    if (g_hThread) {
        CloseHandle(g_hThread);
        g_hThread = NULL;
    }

    g_hThread = CreateThread(NULL, 0, HookThreadProc, NULL, 0, &g_threadId);
    if (!g_hThread) return false;

    Sleep(100);  // 等待线程初始化
    return true;
}

// 停止钩子
extern "C" __declspec(dllexport) void stop_hook() {
    if (!g_running) return;

    if (g_hWnd) {
        PostMessage(g_hWnd, WM_HOOK_CONTROL, HOOK_STOP, 0);
        PostMessage(g_hWnd, WM_QUIT, 0, 0);
    }

    if (g_hThread) {
        WaitForSingleObject(g_hThread, INFINITE);
        CloseHandle(g_hThread);
        g_hThread = NULL;
    }

    g_hWnd = NULL;
    g_running = false;
}

// 判断钩子是否正在运行
extern "C" __declspec(dllexport) bool is_hook_running() {
    return g_running && g_hHook != NULL;
}
