import configparser
import datetime
import subprocess
import threading
import time
import tkinter as tk
import tkinter.scrolledtext as tkst
import traceback
from tkinter import filedialog, messagebox


class GameServer:
    def __init__(self):
        self.process = None
        self.start_command = None  # 用于存储启动命令
        self.is_running = False  # 添加用于跟踪服务器是否运行的标志
        self.was_stopped = False  # 服务器启动时重置标志

    def start_server(self):
        """启动服务器，使用类中存储的启动命令"""
        if self.is_process_running():
            raise Exception("服务器已经在运行。")
        try:
            self.process = subprocess.Popen(self.start_command, shell=True)
            self.is_running = True
            self.was_stopped = False  # 服务器启动时重置标志
        except Exception as e:
            raise Exception(f"无法启动服务器: {e}")

    def stop_server(self):
        if self.process is None:
            print("服务器没有在运行.")
            return
        self.process.terminate()
        self.process = None
        self.is_running = False
        self.was_stopped = True  # 服务器停止时设置标志
        print("服务器停止.")

    def restart_server(self):
        """重启服务器"""
        if self.process is not None:
            self.was_stopped = False  # 服务器重启时重置标志
            self.stop_server()
            time.sleep(1)  # 稍等一会儿以确保服务器已完全停止
        if self.start_command is not None:
            self.start_server()

    def is_process_running(self):
        """检查进程是否仍在运行。"""
        if self.process is not None:
            running = self.process.poll() is None
            if running != self.is_running:
                self.is_running = running
                if not running:
                    self.was_stopped = True  # 如果服务器停止运行，设置标志
            return running
        return False


class ServerApp:
    def __init__(self, root, server):
        self.config = None
        self.log_frame = None
        self.clear_button = None
        self.filepath_entry = None
        self.status_label = None
        self.stop_button = None
        self.restart_button = None
        self.choose_exe_button = None
        self.start_parameters_entry = None
        self.choose_config_button = None
        self.config_file_entry = None
        self.start_button = None
        self.server_status = "停止"
        self.log_text = None
        self.restart_interval_entry = None  # 用于输入重启间隔的Entry
        self.config = configparser.ConfigParser()  # 初始化配置解析器
        self.complex_value_param = 3  # 可以根据需要设置一个合适的默认值
        self.search_index = '1.0'  # 初始化搜索索引
        self.auto_restart_var = tk.IntVar()
        self.dynamic_widgets = {}
        #     self.by_label = tk.Label(root, text="by lgnoer", fg="gray")  #
        #     self.by_label.pack(side=tk.BOTTOM, fill=tk.X)  #
        self.server = server
        self.root = root

        # 创建顶部的菜单按钮
        self.menu_frame = tk.Frame(root)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        self.page1_button = tk.Button(self.menu_frame, text="服务器控制",
                                      command=lambda: self.show_frame(self.page1))
        self.page1_button.pack(side=tk.LEFT)

        self.page2_button = tk.Button(self.menu_frame, text="配置文件设置", command=lambda: self.show_frame(self.page2))
        self.page2_button.pack(side=tk.LEFT)

        # 创建页面1 (Server Control)
        self.page1 = tk.Frame(root)
        self.init_page1(self.page1)

        # 创建页面2 (Settings)
        self.page2 = tk.Frame(root)
        self.init_page2(self.page2)

        self.frames = [self.page1, self.page2]
        self.show_frame(self.page1)

    def show_frame(self, frame):
        for f in self.frames:
            f.pack_forget()
        frame.pack()

    def load_config(self, config_path):
        """从给定路径加载配置文件"""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        return self.config

    def save_config(self, config_path):
        """保存配置到给定路径"""
        with open(config_path, 'w') as configfile:
            self.config.write(configfile)

    def init_page1(self, frame):
        self.status_label = tk.Label(frame, text=f"服务器状态: {self.server_status}")
        self.status_label.grid(row=2, column=0, columnspan=3, sticky='w', pady=2)

        tk.Label(frame, text="服务器启动文件:").grid(row=3, column=0, sticky='w', pady=2)
        self.filepath_entry = tk.Entry(frame, width=50, state='readonly')
        self.filepath_entry.grid(row=3, column=1, sticky='we', pady=2)
        self.choose_exe_button = tk.Button(frame, text="...", command=self.choose_exe)
        self.choose_exe_button.grid(row=3, column=2, padx=5)
        self.clear_button = tk.Button(frame, text="清除", command=self.clear_filepath)
        self.clear_button.grid(row=3, column=3, padx=5)

        tk.Label(frame, text="服务器参数(可以为空):").grid(row=4, column=0, sticky='w', pady=2)
        self.start_parameters_entry = tk.Entry(frame, width=50)
        self.start_parameters_entry.grid(row=4, column=1, sticky='we', columnspan=2, pady=2)

        self.start_button = tk.Button(frame, text="启动服务器", command=self.start_server, state=tk.DISABLED)
        self.start_button.grid(row=6, column=0, pady=5)
        self.stop_button = tk.Button(frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=6, column=1, pady=5)
        self.restart_button = tk.Button(frame, text="重启服务器", command=self.restart_server, state=tk.DISABLED)
        self.restart_button.grid(row=6, column=2, pady=5)

        # 确保列1和列2能够扩展填充额外空间
        frame.grid_columnconfigure(1, weight=1)

        self.log_frame = tk.Frame(frame)  # 创建一个容纳日志框和滚动条的框架
        self.log_frame.grid(row=5, column=0, columnspan=4, sticky='we', padx=5, pady=5)

        self.log_text = tkst.ScrolledText(self.log_frame, state='disabled', height=10, wrap='word')
        self.log_text.pack(expand=True, fill='both')

        # 确保列能够扩展填充额外空间
        frame.grid_columnconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        # 日志框初始化
        self.log_frame = tk.Frame(frame)
        self.log_frame.grid(row=5, column=0, columnspan=4, sticky='we', padx=5, pady=5)
        self.log_text = tkst.ScrolledText(self.log_frame, state='disabled', height=10, wrap='word')
        self.log_text.pack(expand=True, fill='both')
        frame.grid_columnconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        tk.Label(frame, text="重启间隔（秒）:").grid(row=7, column=0, sticky='w')
        self.restart_interval_entry = tk.Entry(frame, width=50)

        self.restart_interval_entry.grid(row=7, column=1, sticky='w')

        schedule_restart_button = tk.Button(frame, text="定时重启服务器", command=self.schedule_restart)
        schedule_restart_button.grid(row=7, column=2, padx=5, pady=5)

        self.auto_restart_checkbox = tk.Checkbutton(self.page1, text="崩溃时自动重启服务器",
                                                    variable=self.auto_restart_var)
        self.auto_restart_checkbox.grid(row=8, column=0, columnspan=3, pady=5)

        self.monitor_server_process()  # 启动服务器进程监控

    def init_page2(self, frame):
        tk.Label(frame, text="服务器配置文件:").grid(row=0, column=0, sticky='w', pady=5)
        self.config_file_entry = tk.Entry(frame, width=50, state='readonly')
        self.config_file_entry.grid(row=0, column=1, sticky='we', pady=5)
        self.choose_config_button = tk.Button(frame, text="...", command=self.choose_config)
        self.choose_config_button.grid(row=0, column=2, padx=5, pady=5)

        self.read_config_button = tk.Button(frame, text="读取文件", command=self.read_config)
        self.read_config_button.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(frame, text="参数长度>=(默认3):").grid(row=1, column=0, sticky='w', pady=2)

        self.complex_value_param_entry = tk.Entry(frame, width=20)
        self.complex_value_param_entry.grid(row=1, column=1, padx=5, pady=8)

        self.set_complex_param_button = tk.Button(frame, text="确定", command=self.set_complex_value_param)
        self.set_complex_param_button.grid(row=1, column=2, padx=5, pady=8)

        self.clear_layout_button = tk.Button(frame, text="清除布局", command=self.clear_dynamic_widgets)
        self.clear_layout_button.grid(row=1, column=3, padx=5, pady=8)

        self.save_config_button = tk.Button(frame, text="保存配置", command=self.save_config_to_file)
        self.save_config_button.grid(row=3, column=3, padx=5, pady=5)

        # 确保列1和列2能够扩展填充额外空间
        frame.grid_columnconfigure(0, weight=0)  # 第0列不自动缩放
        frame.grid_columnconfigure(1, weight=1)  # 第1列不自动缩放

    def save_config_to_file(self):
        config_path = self.config_file_entry.get()
        if not config_path:
            messagebox.showerror("错误", "未指定配置文件路径")
            return

        # 更新配置对象
        for section in self.config.sections():
            for option in self.config.options(section):
                widget_name = f"{section}_{option}"
                if widget_name in self.dynamic_widgets:
                    widget = self.dynamic_widgets[widget_name]
                    self.config.set(section, option, widget.get())

        # 将配置写入文件
        try:
            with open(config_path, 'w') as file:
                self.config.write(file)
            self.log_message(f"配置已保存到: {config_path}")
        except Exception as e:
            messagebox.showerror("保存错误", f"无法保存配置: {str(e)}")
            self.log_message(f"保存配置错误: {str(e)}")

    def find_widget_by_name(self, name):
        """根据名称找到相应的输入框"""
        for widget in self.page2.winfo_children():
            if hasattr(widget, 'config_name') and widget.config_name == name:
                return widget
        return None

    def log_message(self, message):
        """ 在日志框中显示带时间戳的消息 """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.config(state='disabled')
        self.log_text.yview(tk.END)

    def choose_exe(self):
        """打开文件选择对话框以选择可执行文件"""
        filepath = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if filepath:
            self.filepath_entry.config(state='normal')
            self.filepath_entry.delete(0, tk.END)
            self.filepath_entry.insert(0, filepath)
            self.filepath_entry.config(state='readonly')
            self.server.start_command = filepath  # 更新服务器的启动命令
            self.start_button.config(state=tk.NORMAL)  # 启动按钮现在可用

    def choose_config(self):
        """打开文件选择对话框以选择配置文件"""
        config_path = filedialog.askopenfilename(filetypes=[("Config Files", "*.ini")])
        if config_path:
            self.config_file_entry.config(state='normal')  # 设置为可编辑状态
            self.config_file_entry.delete(0, tk.END)  # 清除当前内容
            self.config_file_entry.insert(0, config_path)  # 插入新选择的路径
            self.config_file_entry.config(state='readonly')  # 设置回只读状态

    def search_in_text(self):
        """在文本框中搜索用户输入的字符串，并跳转到第一个匹配项"""
        self.text.tag_remove('found', '1.0', tk.END)
        search_query = self.search_entry.get()

        if search_query:
            idx = '1.0'
            self.search_index, lastidx = self.find_next(search_query, idx)
            if self.search_index:
                self.text.tag_add('found', self.search_index, lastidx)
                self.text.tag_config('found', foreground='blue')
                self.text.see(self.search_index)  # 跳转到第一个匹配项
            else:
                messagebox.showinfo("搜索", "找不到匹配项")

    def find_next(self, search_query, start_idx):
        """在文本框中查找下一个匹配项，并返回其索引"""
        idx = self.text.search(search_query, start_idx, nocase=1, stopindex=tk.END)
        if idx:
            lastidx = f"{idx}+{len(search_query)}c"
            return idx, lastidx
        return None, None

    def goto_next_search_result(self):
        """跳转到下一个搜索结果"""
        search_query = self.search_entry.get()
        if search_query and self.search_index:
            self.search_index, lastidx = self.find_next(search_query, self.search_index)
            if self.search_index:
                self.text.tag_remove('found', '1.0', tk.END)
                self.text.tag_add('found', self.search_index, lastidx)
                self.text.see(self.search_index)
            else:
                messagebox.showinfo("搜索", "没有更多匹配项")

    def read_config(self):
        """读取并显示配置文件的参数"""
        global entry
        config_path = self.config_file_entry.get()
        if not config_path:
            messagebox.showerror("错误", "没有选择配置文件")
            return

        # 读取配置文件
        self.config.read(config_path)

        # 清除之前的布局
        self.clear_dynamic_widgets()

        # 在页面2上创建新的控件以显示配置参数
        row = 4
        for section in self.config.sections():
            for key, value in self.config.items(section):
                label = tk.Label(self.page2, text=f"{section}.{key}:")
                label.grid(row=row, column=0, sticky='w')
                label._is_dynamic = True  # 标记为动态生成
                entry.config_name = f"{section}_{key}"

                if self.is_complex_value(value):
                    # 为复杂的值创建一个大的滚动文本框
                    if self.is_complex_value(value):
                        # 为复杂的值创建一个大的滚动文本框
                        text_frame = tk.Frame(self.page2)
                        text_frame.grid(row=row, column=1, sticky='we')
                        text_frame._is_dynamic = True

                        self.text = tk.Text(text_frame, height=5, width=50, wrap=tk.WORD)
                        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        self.text.insert('1.0', value)

                        # 使用 self.text 来创建滚动条
                        scrollbar = tk.Scrollbar(text_frame, command=self.text.yview)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                        # 设置滚动条与文本框的关联
                        self.text.config(yscrollcommand=scrollbar.set)

                        row += 1

                    # 添加搜索框和按钮
                    self.search_entry = tk.Entry(self.page2)
                    self.search_entry.grid(row=3, column=1, pady=5)
                    self.search_entry._is_dynamic = True
                    search_button = tk.Button(self.page2, text="搜索", command=self.search_in_text)
                    search_button.grid(row=3, column=2, padx=5)
                    search_button._is_dynamic = True
                    row += 2  # 增加行号以放置下一个控件


                else:
                    # 为简单的值创建一个单行文本框
                    entry = tk.Entry(self.page2, width=50)
                    entry.grid(row=row, column=1, sticky='we')
                    entry.insert(0, value)
                    entry._is_dynamic = True
                    entry.config_name = f"{section}_{key}"

                row += 1

        # 更新日志
        self.log_message(f"读取配置文件: {config_path}")

    def set_complex_value_param(self):
        """设置用于判断复杂值的参数"""
        try:
            param = int(self.complex_value_param_entry.get())
            # 定义参数的下限和上限
            MIN_PARAM = 1
            MAX_PARAM = 99
            if MIN_PARAM <= param <= MAX_PARAM:
                # 在此处更新 is_complex_value 方法使用的参数
                self.complex_value_param = param
                self.log_message(f"设置复杂值参数为: {param}")
            else:
                raise ValueError(f"参数必须在 {MIN_PARAM} 和 {MAX_PARAM} 之间")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def is_complex_value(self, value):
        """判断配置值是否复杂，无法直接识别分割"""
        # 使用 self.complex_value_param 作为判断条件
        return len(value.split()) >= self.complex_value_param

    def clear_dynamic_widgets(self):
        """清除页面上动态创建的控件"""
        for widget in self.page2.winfo_children():
            if hasattr(widget, '_is_dynamic'):
                widget.destroy()

    def clear_filepath(self):
        self.filepath_entry.config(state='normal')  # 设置文本框为可编辑状态
        self.filepath_entry.delete(0, tk.END)
        self.filepath_entry.config(state='readonly')
        self.server.start_command = None  # 清除服务器启动命令
        self.start_button.config(state=tk.DISABLED)  # 禁用启动服务器按钮

    def start_server(self):
        try:
            start_params = self.start_parameters_entry.get()
            full_command = f"{self.server.start_command} {start_params}"
            self.server.start_server(full_command)
            self.server_status = "运行中"
            self.status_label.config(text=f"服务器状态: {self.server_status}")
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            self.log_message("服务器启动命令: " + full_command)
        except Exception as e:
            error_message = f"启动服务器时出错: {e}"
            self.log_message(error_message)
            self.log_error(error_message)

    def update_ui_on_server_start(self):
        """更新 UI 以反映服务器启动状态"""
        self.status_label.config(text=f"服务器状态: {self.server_status}")
        self.stop_button.config(state=tk.NORMAL)
        self.restart_button.config(state=tk.NORMAL)

    def update_ui_on_server_stop(self):
        """更新 UI 以反映服务器停止状态"""
        self.status_label.config(text=f"服务器状态: {self.server_status}")
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)

    def stop_server(self):
        try:
            if self.server_status == "运行中":
                self.server.stop_server()
                self.server_status = "停止"
                self.status_label.config(text=f"服务器状态: {self.server_status}")
                self.stop_button.config(state=tk.DISABLED)
                self.restart_button.config(state=tk.DISABLED)
                self.log_message("服务器停止。")
            else:
                self.log_message("服务器现在没有运行。")
        except Exception as e:
            error_message = f"停止服务器时出错: {e}"
            self.log_message(error_message)
            self.log_error(error_message)

    def restart_server(self):
        try:
            if self.server_status == "运行中":
                self.stop_server()  # 首先停止服务器
                time.sleep(10)  # 确保服务器完全停止
            self.start_server()  # 然后启动服务器
        except Exception as e:
            error_message = f"重启服务器时出错: {e}"
            self.log_message(error_message)
            self.log_error(error_message)

    def schedule_restart(self):
        """定时重启服务器"""
        try:
            interval = int(self.restart_interval_entry.get())
            threading.Timer(interval, self.server.restart_server).start()
            self.log_message(f"已计划在{interval}秒后重启服务器。")
        except ValueError:
            self.log_message("错误: 请输入有效的秒数。")

    def monitor_server_process(self):
        """监控服务器进程并更新日志，如果需要则重启服务器"""
        if self.server.is_process_running():
            self.server.was_stopped = False  # 如果服务器正在运行，重置标志
        elif not self.server.was_stopped:
            self.log_message("服务器进程已停止。")
            self.server.was_stopped = True  # 设置标志，避免重复记录
            if self.auto_restart_var.get() == 1:
                # 重启逻辑
                self.log_message("正在尝试重启服务器...")
                try:
                    self.start_server()
                except Exception as e:
                    self.log_message(f"重启服务器失败: {e}")
                    self.log_message(f"每60秒将尝试一次")

        # 每60秒钟检查一次
        self.root.after(1000, self.monitor_server_process)

    def log_error(self, error):
        """记录错误信息到日志文件"""
        with open("error_log.txt", "a") as log_file:  # 打开日志文件
            log_file.write(f"[{datetime.datetime.now()}] Error: {error}\n")
            log_file.write(traceback.format_exc())  # 记录错误的堆栈跟踪
            try:
                self.root.after()
            except Exception as e:
                self.log_error(e)  # 记录错误
                # ... 其他错误处理代码 ...


if __name__ == "__main__":
    server = GameServer()
    root = tk.Tk()
    frame = tk.Frame(root)
    root.title("简易服务器工具")
    root.geometry("700x550")
    app = ServerApp(root, server)
    app.monitor_server_process()  # 启动服务器进程监控
    root.mainloop()
