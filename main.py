import ctypes
import webview
import pystray
from PIL import Image, ImageDraw
from config import GameConfig
from hook import KeyHook 
from vk_table import vk_table
import threading

CONFIG_PATH = "./config/config.toml"
tray_icon = None


class Api:
    def __init__(self):
        self.config = GameConfig(CONFIG_PATH)  # 仅持有实例，不缓存配置
        self.hook = None
        self.hook_thread = None
        self.is_hook_running = False
    
    # 所有获取配置的方法都实时调用config的方法，不缓存结果
    def get_games(self):
        return self.config.get_games()  # 实时读取
    
    def get_keymaps(self, game_id):
        return self.config.get_keymaps(game_id)  # 实时读取
    
    def save_config(self, obj):
        # 保存后无需刷新（因为读取时已实时）
        return self.config.save_config(obj)

    def start_hook(self, game_id,exact_match):
        # 避免重复启动
        if self.is_hook_running:
            print("钩子已在运行中")
            return False

        # 获取游戏配置
        game = self.config.get_game_by_id(game_id)
        if not game:
            print(f"错误: 未找到ID为 {game_id} 的游戏配置")
            return False

        # 获取按键映射
        keymaps = self.config.get_keymaps(game_id)
        if not keymaps:
            print(f"错误: 游戏 {game['name']} 没有配置按键映射")
            return False

        # 选择第一个按键映射
        if isinstance(keymaps, list) and keymaps:
            selected_keymap = keymaps[0]
        else:
            selected_keymap = keymaps

        # 转换按键为VK码
        src_keys = []
        dst_keys = []
        try:
            for k, v in selected_keymap.items():
                src_keys.append(vk_table[k])
                dst_keys.append(vk_table[v])
        except KeyError as e:
            print(f"按键映射错误: 找不到键 {e}")
            return False

        # 启动钩子（在独立线程中运行，避免阻塞GUI）
        def run_hook():
            print(exact_match)
            # 初始化钩子（确保实例不被回收）
            self.hook = KeyHook()
            # 调用钩子启动方法（参数顺序与KeyHook类匹配）
            success = self.hook.start(
                window_title=game["window_name"],
                src_keys=src_keys,
                dst_keys=dst_keys,
                exact_match=exact_match
            )
            
            # 更新状态
            self.is_hook_running = success
            if not success:
                print("钩子启动失败")

        # 启动线程
        self.hook_thread = threading.Thread(target=run_hook)
        self.hook_thread.daemon = True  # 随主线程退出
        self.hook_thread.start()

        # 等待线程初始化（短暂延时，确保状态更新）
        threading.Timer(0.3, self._check_hook_start).start()
        return True

    def _force_kill_thread(self,thread):
        """危险操作：强制终止线程"""
        if not thread.is_alive():
            return
        tid = ctypes.c_long(thread.ident)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
        if res == 0:
            print("无效线程 ID，无法强制终止")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            print("强制终止失败，影响多个线程")
        else:
            print("成功强制终止线程")
    def stop_hook(self, force=False):
        if not self.is_hook_running or not self.hook:
            print("钩子未运行")
            return False

        try:
            self.hook.stop()  # 异步调用dll.stop_hook()，不阻塞
            self.is_hook_running = False

            # 等待钩子线程结束
            if self.hook_thread and self.hook_thread.is_alive():
                self.hook_thread.join(timeout=1.0)
                if self.hook_thread.is_alive():
                    if force:
                        print("强制终止钩子线程")
                        self._force_kill_thread(self.hook_thread)
                    else:
                        print("钩子线程未正常结束")

            self.hook_thread = None
            self.hook = None
            print("钩子已停止")
            return True

        except Exception as e:
            print(f"停止钩子失败: {e}")
            return False
    def _check_hook_start(self):
        """检查钩子是否真的启动成功"""
        if not self.is_hook_running:
            print("钩子启动后意外停止")



def create_tray_icon(window):
    """创建系统托盘图标及菜单"""
    # 创建图标图像
    image = Image.open('iconx64.png')
    
    # 尝试获取并保存窗口句柄
    hwnd = None
    def save_window_handle():
        nonlocal hwnd
        try:
            # 尝试多种方式获取窗口句柄
            if hasattr(window, 'native_window'):
                hwnd = window.native_window
            elif hasattr(window, 'uid'):
                hwnd = window.uid
            else:
                print("无法获取窗口句柄")
        except Exception as e:
            print(f"获取窗口句柄失败: {e}")
    
    # 在创建托盘图标时尝试保存句柄
    save_window_handle()
    # 受技术限制,暂时无法将窗口重新至于前端
    # def on_show(icon, item):
    #     """显示窗口并置于前端"""
    #     nonlocal hwnd
        
    #     if window:
    #         window.restore()  # 尝试通过 pywebview 恢复
    #         window.show()     # 尝试通过 pywebview 显示
            
    #         # 如果之前获取到了句柄，使用句柄操作
    #         if hwnd:
    #             try:
    #                 # 确保窗口未最小化
    #                 if win32gui.IsIconic(hwnd):
    #                     win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
    #                 # 将窗口置于前端
    #                 user32 = ctypes.windll.user32
    #                 user32.SetForegroundWindow(hwnd)
                    
    #                 # 激活窗口
    #                 win32gui.SetActiveWindow(hwnd)
                    
    #                 # 临时置顶再取消
    #                 win32gui.SetWindowPos(
    #                     hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
    #                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    #                 )
    #                 win32gui.SetWindowPos(
    #                     hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
    #                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    #                 )
    #             except Exception as e:
    #                 print(f"无法将窗口置于前端: {e}")
    #                 # 如果失败，尝试重新获取句柄
    #                 save_window_handle()
    #         else:
    #             # 如果没有句柄，尝试重新获取
    #             save_window_handle()

    def on_quit(icon, item):
        """退出应用程序"""
        if window:
            api = window._js_api
            if api and hasattr(api, 'stop_hook'):
                api.stop_hook(force=True)
            icon.stop()
            window.destroy()

    # 创建托盘菜单
    menu = pystray.Menu(
        # pystray.MenuItem('打开窗口', on_show),
        pystray.MenuItem('退出', on_quit)
    )

    # 创建并启动托盘图标
    icon = pystray.Icon("keyrefit", image, "KeyRefit", menu)
    icon.run_detached()
    return icon
def start_app():
    global tray_icon
    # 创建窗口并绑定API(固定窗口大小才不是因为懒得写自适应的布局)
    window = webview.create_window(
        'KeyRefit',
        './vue_dist/index.html',
        # "http://localhost:5173/",
        width=868,
        height=574,
        resizable=False,
        confirm_close=False,
        js_api=Api()
    )

    tray_icon = create_tray_icon(window)
    # 启动webview
    webview.start(debug=True)
    # webview.start()

if __name__ == '__main__':
    start_app()