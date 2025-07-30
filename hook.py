import ctypes
import threading
import time

class KeyHook:
    def __init__(self, dllpath="./hook.dll"):
        self.dll = ctypes.WinDLL(dllpath)

        # 绑定 DLL 函数签名（含 exact_match 参数）
        self.dll.set_config.argtypes = [
            ctypes.c_wchar_p,              # window_title
            ctypes.POINTER(ctypes.c_int),  # src_keys
            ctypes.POINTER(ctypes.c_int),  # dst_keys
            ctypes.c_int,                  # count
            ctypes.c_bool                  # exact_match
        ]
        self.dll.set_config.restype = None

        self.dll.start_hook.argtypes = []
        self.dll.start_hook.restype = ctypes.c_bool

        self.dll.stop_hook.argtypes = []
        self.dll.stop_hook.restype = None

        self.dll.is_hook_running.argtypes = []
        self.dll.is_hook_running.restype = ctypes.c_bool

        self.running = False
        self.msg_loop_thread = None  # 消息循环线程

    def start(self, window_title, src_keys, dst_keys, exact_match=True):
        """启动钩子：支持 exact_match 控制窗口标题是否精确匹配"""
        if self.running:
            return False

        if self.msg_loop_thread is None or not self.msg_loop_thread.is_alive():
            self.msg_loop_thread = threading.Thread(target=self._msg_loop, daemon=True)
            self.msg_loop_thread.start()

        # 转换为 C 数组
        src_arr = (ctypes.c_int * len(src_keys))(*src_keys)
        dst_arr = (ctypes.c_int * len(dst_keys))(*dst_keys)

        # 配置并启动
        self.dll.set_config(window_title, src_arr, dst_arr, len(src_keys), ctypes.c_bool(exact_match))
        result = self.dll.start_hook()
        print("钩子运行结果:", result)

        if result:
            self.running = True
            self.msg_loop_thread = threading.Thread(target=self._msg_loop, daemon=True)
            self.msg_loop_thread.start()
            return True

        return False

    def stop(self):
        """停止钩子，安全退出消息循环"""
        print("stop hook ing ...")
        if not self.running:
            print("钩子未运行，直接返回")
            return

        def _stop_dll():
            try:
                print("开始调用 dll.stop_hook()，请稍等")
                self.dll.stop_hook()
                print("dll.stop_hook() 已返回")
            except Exception as e:
                print(f"调用 dll.stop_hook() 异常: {e}")
            finally:
                self.running = False

        stop_thread = threading.Thread(target=_stop_dll, daemon=True)
        stop_thread.start()

        # 等待消息循环线程退出
        if self.msg_loop_thread and self.msg_loop_thread.is_alive():
            print("等待消息循环线程退出")
            self.msg_loop_thread.join(timeout=1.0)
            if self.msg_loop_thread.is_alive():
                print("警告：消息循环线程未正常退出")

        stop_thread.join(timeout=1.0)
        if stop_thread.is_alive():
            print("警告：dll.stop_hook() 线程仍未结束")

        print("钩子已停止")

    def is_alive(self):
        """检查钩子状态"""
        return self.running and self.dll.is_hook_running()

    def _msg_loop(self):
        """维持消息循环，同步状态"""
        while self.running:
            if not self.dll.is_hook_running():
                self.running = False
                break
            time.sleep(0.1)
