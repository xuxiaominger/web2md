"""
GUI界面模块
提供图形界面进行网页到Markdown的转换
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from typing import Optional, Callable

from .extractor import WebExtractor
from .markdown_formatter import MarkdownFormatter
from .obsidian_sync import ObsidianSync


class Web2MDGUI:
    """Web2MD图形界面"""

    def __init__(self, obsidian_path: str = None):
        self.root = tk.Tk()
        self.root.title("Web2MD - 网页转Markdown")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 配置Obsidian路径
        self.obsidian_path = obsidian_path

        # 初始化组件
        self.extractor = WebExtractor()
        self.formatter = MarkdownFormatter()
        self.obsidian_sync = ObsidianSync(obsidian_path) if obsidian_path else None

        # 状态变量
        self.is_processing = False
        self.current_url = ""
        self.current_markdown = ""
        self.current_title = ""

        # 创建界面
        self._create_widgets()

        # 自动读取剪贴板
        self._check_clipboard()

    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== 顶部：URL输入区域 =====
        input_frame = ttk.LabelFrame(main_frame, text="网页链接", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # URL输入框
        self.url_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 读取剪贴板按钮
        self.paste_btn = ttk.Button(input_frame, text="📋 粘贴", command=self.paste_from_clipboard)
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 转换按钮（红色）
        self.convert_btn = tk.Button(
            input_frame,
            text="🔴 转换",
            command=self.start_convert,
            bg='#e74c3c',  # 红色背景
            fg='white',
            font=('Microsoft YaHei', 11, 'bold'),
            padx=20,
            pady=5,
            relief=tk.RAISED,
            cursor='hand2'
        )
        self.convert_btn.pack(side=tk.LEFT)

        # ===== 中间：转换状态 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(status_frame, text="等待输入...", foreground='gray')
        self.status_label.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
        self.progress.pack(side=tk.RIGHT)

        # ===== 底部：结果显示区域 =====
        result_frame = ttk.LabelFrame(main_frame, text="转换结果 (Markdown)", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Markdown预览区
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            font=('Consolas', 10),
            wrap=tk.WORD,
            undo=True
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # ===== 底部按钮区 =====
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        # 保存到Obsidian按钮
        self.save_btn = ttk.Button(
            btn_frame,
            text="💾 保存到Obsidian",
            command=self.save_to_obsidian,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 复制到剪贴板按钮
        self.copy_btn = ttk.Button(
            btn_frame,
            text="📋 复制Markdown",
            command=self.copy_to_clipboard,
            state=tk.DISABLED
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存为文件按钮
        self.save_file_btn = ttk.Button(
            btn_frame,
            text="💿 保存为文件",
            command=self.save_to_file,
            state=tk.DISABLED
        )
        self.save_file_btn.pack(side=tk.LEFT)

        # 绑定快捷键
        self.root.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.root.bind('<Return>', lambda e: self.start_convert() if not self.is_processing else None)

    def paste_from_clipboard(self):
        """从剪贴板读取URL"""
        try:
            # 尝试读取剪贴板
            clipboard_text = self.root.clipboard_get()

            if clipboard_text:
                # 检查是否是有效的URL
                clipboard_text = clipboard_text.strip()
                if clipboard_text.startswith('http://') or clipboard_text.startswith('https://'):
                    self.url_entry.delete(0, tk.END)
                    self.url_entry.insert(0, clipboard_text)
                    self.current_url = clipboard_text
                    self.status_label.config(text="已读取剪贴板链接", foreground='blue')
                else:
                    messagebox.showwarning("提示", "剪贴板中未包含有效的网页链接")
        except Exception as e:
            # 回退到其他方法
            try:
                clipboard_text = self.root.clipboard_get()
                if clipboard_text and (clipboard_text.startswith('http://') or clipboard_text.startswith('https://')):
                    self.url_entry.delete(0, tk.END)
                    self.url_entry.insert(0, clipboard_text)
                    self.current_url = clipboard_text
                    self.status_label.config(text="已读取剪贴板链接", foreground='blue')
            except:
                messagebox.showwarning("提示", "无法读取剪贴板")

    def _check_clipboard(self):
        """检查剪贴板是否有URL"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text and (clipboard_text.startswith('http://') or clipboard_text.startswith('https://')):
                self.url_entry.insert(0, clipboard_text)
                self.current_url = clipboard_text
                self.status_label.config(text="检测到剪贴板中有链接", foreground='blue')
        except:
            pass

    def start_convert(self):
        """开始转换"""
        if self.is_processing:
            return

        # 获取URL
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入网页链接")
            return

        # 验证URL格式
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        self.current_url = url

        # 开始处理
        self.is_processing = True
        self.convert_btn.config(state=tk.DISABLED, bg='#95a5a6')
        self.progress.start(10)
        self.status_label.config(text="正在提取网页内容...", foreground='orange')

        # 在后台线程中运行
        thread = threading.Thread(target=self._convert_in_thread)
        thread.daemon = True
        thread.start()

    def _convert_in_thread(self):
        """在后台线程中执行转换"""
        try:
            # 提取内容
            content = self.extractor.extract(self.current_url)

            # 格式化
            if 'error' in content and content['error']:
                self.root.after(0, self._show_error, content['error'])
                return

            # 转换为Markdown
            markdown = self.formatter.format(content)

            # 保存结果
            self.current_markdown = markdown
            self.current_title = content.get('title', 'untitled')

            # 更新界面
            self.root.after(0, self._show_result, markdown)

        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _show_result(self, markdown: str):
        """显示转换结果"""
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', markdown)

        self.status_label.config(text=f"转换完成: {self.current_title}", foreground='green')

        # 启用按钮
        self.save_btn.config(state=tk.NORMAL)
        self.copy_btn.config(state=tk.NORMAL)
        self.save_file_btn.config(state=tk.NORMAL)

        # 停止进度条
        self.progress.stop()
        self.convert_btn.config(state=tk.NORMAL, bg='#e74c3c')
        self.is_processing = False

    def _show_error(self, error: str):
        """显示错误信息"""
        messagebox.showerror("错误", f"转换失败: {error}")
        self.status_label.config(text="转换失败", foreground='red')

        self.progress.stop()
        self.convert_btn.config(state=tk.NORMAL, bg='#e74c3c')
        self.is_processing = False

    def save_to_obsidian(self):
        """保存到Obsidian"""
        if not self.current_markdown:
            return

        if not self.obsidian_path:
            messagebox.showwarning("提示", "未配置Obsidian路径")
            return

        # 生成文件名
        date = self.formatter.generate_filename(self.current_title)
        filename = f"{date}.md"

        # 保存文件
        success, message = self.obsidian_sync.save_markdown(filename, self.current_markdown)

        if success:
            messagebox.showinfo("成功", f"已保存到Obsidian:\n{message}")
            self.status_label.config(text=f"已保存: {filename}", foreground='green')
        else:
            messagebox.showerror("错误", f"保存失败: {message}")

    def save_to_file(self):
        """保存为文件"""
        if not self.current_markdown:
            return

        # 生成默认文件名
        date = self.formatter.generate_filename(self.current_title)
        filename = f"{date}.md"

        # 选择保存位置
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")],
            initialfile=filename
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_markdown)
                messagebox.showinfo("成功", f"已保存到:\n{file_path}")
                self.status_label.config(text=f"已保存: {filename}", foreground='green')
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

    def copy_to_clipboard(self):
        """复制到剪贴板"""
        if not self.current_markdown:
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_markdown)
            self.status_label.config(text="已复制到剪贴板", foreground='green')
        except:
            messagebox.showwarning("提示", "复制失败")

    def run(self):
        """运行程序"""
        self.root.mainloop()

    def close(self):
        """关闭程序"""
        self.extractor.close()
        self.root.destroy()


def create_gui(obsidian_path: str = None) -> Web2MDGUI:
    """
    创建GUI实例

    Args:
        obsidian_path: Obsidian库路径

    Returns:
        Web2MDGUI实例
    """
    return Web2MDGUI(obsidian_path)
