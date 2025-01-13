import sys
import subprocess
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import requests
import json
import qrcode
from PIL import ImageTk
from urllib.parse import quote
import datetime
import xml.etree.ElementTree as ET

class BilibiliDownloaderGUI:
    def __init__(self):
        try:
            self.window = tk.Tk()
            self.window.title('B站视频下载器')
            self.window.geometry('530x450')
            self.current_action = None
            # 初始化 BilibiliCrawler
            self.crawler = BilibiliCrawler()
            # 标志变量,记录当前选择的按钮
            self.current_action = False

            def handle_error(exc, val, tb):
                messagebox.showerror("错误", str(val))
                self.window.destroy()

            self.window.report_callback_exception = handle_error

            self.main_frame = ttk.Frame(self.window, padding="10")
            self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 视频BV号
            ttk.Label(self.main_frame, text="视频BV号:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.bv_entry = ttk.Entry(self.main_frame, width=40)
            self.bv_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

            # 保存位置
            ttk.Label(self.main_frame, text="保存位置:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.path_entry = ttk.Entry(self.main_frame, width=40)
            self.path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
            self.path_entry.insert(0, os.path.abspath('../python-bilibili-downloads-main/downloads'))

            # 浏览按钮
            self.browse_button = ttk.Button(self.main_frame, text="浏览", command=self.browse_path)
            self.browse_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

            # 清晰度
            ttk.Label(self.main_frame, text="视频清晰度:").grid(row=2, column=0, sticky=tk.W, pady=5)
            self.quality_var = tk.StringVar(value='80')
            self.quality_combo = ttk.Combobox(self.main_frame, textvariable=self.quality_var, width=20)
            self.quality_combo['values'] = ['16', '32', '64', '80', '112', '116', '120']
            self.quality_combo['state'] = 'readonly'
            self.quality_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

            quality_tips = {
                '16': '360P',
                '32': '480P',
                '64': '720P',
                '80': '1080P',
                '112': '1080P+',
                '116': '1080P60',
                '120': '4K'
            }
            self.quality_label = ttk.Label(self.main_frame,
                                           text=f"当前: {quality_tips.get(self.quality_var.get(), '')}")
            self.quality_label.grid(row=2, column=2, sticky=tk.W, pady=5)

            self.quality_combo.bind('<<ComboboxSelected>>', lambda e: self.quality_label.config(
                text=f"当前: {quality_tips.get(self.quality_var.get(), '')}"
            ))

            # 用户昵称显示
            self.nickname_label = ttk.Label(self.main_frame, text="未登录", foreground="blue")
            self.nickname_label.grid(row=3, column=2, sticky=tk.E)

            # 登录和注销按钮（移动到原本 Cookie 的位置）
            self.login_button = ttk.Button(self.main_frame, text="登录", command=self.login)
            self.login_button.grid(row=3, column=1, padx=0, pady=5)

            self.logout_button = ttk.Button(self.main_frame, text="注销", command=self.logout, state=tk.DISABLED)
            self.logout_button.grid(row=3, column=1, sticky=tk.E, padx=10, pady=5)

            # 下载按钮布局
            button_frame = ttk.Frame(self.main_frame)
            button_frame.grid(row=4, column=0, columnspan=3, pady=10)

            # 开始下载按钮
            self.download_button = ttk.Button(button_frame, text="下载视频", command=lambda: self.set_action("video"))
            self.download_button.grid(row=0, column=0, padx=5)

            # 下载封面按钮
            self.download_picture_button = ttk.Button(button_frame, text="下载封面", command=lambda: self.set_action("picture"))
            self.download_picture_button.grid(row=0, column=1, padx=5)

            # 下载视频信息按钮
            self.download_introduction_button = ttk.Button(button_frame, text="视频信息", command=lambda: self.set_action("introduction"))
            self.download_introduction_button.grid(row=0, column=2, padx=5)

            # 下载弹幕按钮
            self.download_barrage_button = ttk.Button(button_frame, text="下载弹幕", command=lambda: self.set_action("barrage"))
            self.download_barrage_button.grid(row=0, column=3, padx=5)

            # 下载评论按钮
            self.download_comment_button = ttk.Button(button_frame, text="下载评论", command=lambda: self.set_action("comment"))
            self.download_comment_button.grid(row=0, column=4, padx=5)


            # 进度条
            self.progress = ttk.Progressbar(self.main_frame, length=400, mode='determinate')
            self.progress.grid(row=6, column=0, columnspan=3, pady=10)

            # 状态文本框
            self.status_text = tk.Text(self.main_frame, height=10, width=50)
            self.status_text.grid(row=7, column=0, columnspan=3, pady=10)

            # 初始化二维码窗口
            self.qr_window = None

            # 绑定 BilibiliCrawler 的 GUI
            self.crawler.gui = self

        except Exception as e:
            messagebox.showerror("初始化错误", str(e))
            sys.exit(1)


    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)

    def update_status(self, message):
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.see(tk.END)

    def update_progress(self, value):
        self.progress['value'] = value

    def login(self):
        if self.login_button['text'] == "重新登录":
            self.clear_cookie()  # 释放 cookie
            self.update_status("已注销，请重新登录")

        # 调用 BilibiliCrawler 的 login 方法生成二维码
        self.crawler.login()
        # 启动定时器检查登录状态
        self.check_login_status()

    def logout(self):
        confirm = messagebox.askyesno("确认", "确定要注销登录吗？")

        if confirm:  # 用户点击“是”
            self.clear_cookie()

            # 更新 UI 状态
            self.login_button.config(text="登录", state=tk.NORMAL)  # 启用登录按钮
            self.logout_button.config(state=tk.DISABLED)  # 禁用注销按钮
            self.nickname_label.config(text="未登录", foreground="blue")  # 清空昵称显示
            self.update_status("已注销")
        else:  # 用户点击“否”
            self.update_status("取消")

    def check_login_status(self):
        if self.crawler.cookie:
            # 登录成功，更新 UI
            self.update_login_ui(True)
            return  # 停止定时器

        # 检查是否超时（120 秒）
        if not hasattr(self, 'login_start_time'):
            self.login_start_time = time.time()  # 记录登录开始时间

        if time.time() - self.login_start_time > 120:  # 超时时间为 120 秒
            # 超时后更新 UI
            self.update_login_ui(False)
            return  # 停止定时器

        # 每隔 2 秒检查一次登录状态
        self.window.after(2000, self.check_login_status)

    def update_login_ui(self, success):
        if success:
            # 登录成功，更新按钮状态
            self.login_button.config(text="重新登录", state=tk.NORMAL)  # 禁用登录按钮
            self.logout_button.config(state=tk.NORMAL)  # 启用注销按钮
            self.update_status("登录成功")
            # 获取用户昵称，保存cookie并更新 UI
            self.save_cookie()
            nickname = self.crawler.get_user()
            if nickname:
                self.nickname_label.config(text='已登录:'+nickname, foreground="green")
        else:
            self.update_status("登录超时，请重试")


    def load_cookie(self):
        try:
            if os.path.exists('../python-bilibili-downloads-main/config.json'):
                with open('../python-bilibili-downloads-main/config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'cookie' in config:
                        self.crawler.cookie = config['cookie']
        except Exception as e:
            self.update_status(f"加载 Cookie 失败: {str(e)}")

    def save_cookie(self):
        if self.crawler.cookie:
            config = {}
            try:
                config['cookie'] = self.crawler.cookie
                with open('../python-bilibili-downloads-main/config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.update_status(f"保存 Cookie 失败: {str(e)}")

    def clear_cookie(self):
        self.crawler.cookie = ''  # 清空 cookie
        self.crawler.qrcode_key = ''  # 清空二维码 key
        self.crawler.token = '' # 清空token

        # 如果有配置文件，清除其中的 cookie
        if os.path.exists('../python-bilibili-downloads-main/config.json'):
            try:
                with open('../python-bilibili-downloads-main/config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if 'cookie' in config:
                    config.pop('cookie')  # 删除 cookie
                with open('../python-bilibili-downloads-main/config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"清除配置文件中的 cookie 失败: {str(e)}")

        # 关闭二维码窗口（如果存在）
        if hasattr(self, 'qr_window') and self.qr_window.winfo_exists():
            self.qr_window.destroy()

    def start_handle(self):
        bv_id = self.bv_entry.get().strip()
        if not bv_id:
            messagebox.showerror("错误", "请输入视频BV号")
            return

        if not re.match(r'^BV[a-zA-Z0-9]+$', bv_id):
            messagebox.showerror("错误", "请输入正确的BV号格式")
            return

    def start_download(self):

        bv_id = self.bv_entry.get().strip()
        if not bv_id:
            messagebox.showerror("错误", "请输入视频BV号")
            return

        if not re.match(r'^BV[a-zA-Z0-9]+$', bv_id):
            messagebox.showerror("错误", "请输入正确的BV号格式")
            return

        self.crawler.download_path = self.path_entry.get()
        self.crawler.quality = self.quality_var.get()
        self.progress['value'] = 0

        # 根据 current_action 执行对应的功能
        if self.current_action == "video":
            target = self.download_video_thread
        elif self.current_action == "picture":
            target = self.download_picture_thread
        elif self.current_action == "introduction":
            target = self.download_introduction_thread
        elif self.current_action == "barrage":
            target = self.download_barrage_thread
        elif self.current_action == "comment":
            target = self.download_comment_thread
        else:
            self.update_status("未选择下载功能")
            return

        thread = threading.Thread(target=target, args=(bv_id,))
        thread.start()

        # 重置 current_action
        self.current_action = None

    def download_video_thread(self, bv_id):
        try:
            if self.crawler.download_video(bv_id):
                self.progress['value'] = 100
                self.update_status("视频下载完成！")
                messagebox.showinfo("成功", "视频下载完成！")
            else:
                self.update_status("视频下载失败")
                messagebox.showerror("错误", "视频下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))

    def download_picture_thread(self, bv_id):
        try:
            if self.crawler.download_picture(bv_id):
                self.progress['value'] = 100
                self.update_status("封面下载完成！")
                messagebox.showinfo("成功", "封面下载完成！")
            else:
                self.update_status("封面下载失败")
                messagebox.showerror("错误", "封面下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))

    def download_introduction_thread(self, bv_id):
        try:
            if self.crawler.download_introduction(bv_id):
                self.progress['value'] = 100
                self.update_status("视频信息下载完成！")
                messagebox.showinfo("成功", "视频信息下载完成！")
            else:
                self.update_status("简介下载失败")
                messagebox.showerror("错误", "视频信息下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))

    def download_barrage_thread(self, bv_id):
        try:
            if self.crawler.download_barrage(bv_id):
                self.progress['value'] = 100
                self.update_status("弹幕下载完成！")
                messagebox.showinfo("成功", "弹幕下载完成！")
            else:
                self.update_status("弹幕下载失败")
                messagebox.showerror("错误", "弹幕下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))

    def download_comment_thread(self, bv_id):
        try:
            # 检查是否登录
            if not self.crawler.cookie:  # 如果 cookie 不存在
                self.update_status("未登录，请先登录后再下载评论")
                messagebox.showerror("错误", "未登录，请先登录后再下载评论")
                return False
            elif self.crawler.download_comment(bv_id):
                self.progress['value'] = 100
                self.update_status("评论下载完成！")
                messagebox.showinfo("成功", "评论下载完成！")
            else:
                self.update_status("评论下载失败")
                messagebox.showerror("错误", "评论下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))

    def set_action(self, action):
        """
        设置当前需要执行的功能，并调用 start_download。
        """
        self.current_action = action
        self.start_download()


class BilibiliCrawler:
    def __init__(self, download_path='downloads'):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }
        self.download_path = os.path.abspath(download_path)
        self.quality = '80'
        self.cookie = ''
        self.qrcode_key = ''
        self.token = ''
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        self.gui = None

    def update_status(self, message):
        if self.gui:
            self.gui.update_status(message)

    def update_progress(self, value):
        if self.gui:
            self.gui.update_progress(value)

    def get_headers(self):
        headers = self.headers.copy()
        if self.cookie:
            headers['Cookie'] = self.cookie
            if 'SESSDATA' not in self.cookie:
                self.update_status("警告: Cookie 中缺少 SESSDATA，可能无法下载高清视频")
        return headers

    # 生成二维码
    def QR(self, url, qrcode_key):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # 将二维码图片转换为 tkinter 可用的格式
        img_tk = ImageTk.PhotoImage(img)

        # 创建新窗口显示二维码
        self.qr_window = tk.Toplevel()
        self.qr_window.title("扫码登录")
        self.qr_window.geometry("300x300")

        # 在窗口中显示二维码
        qr_label = tk.Label(self.qr_window, image=img_tk)
        qr_label.image = img_tk
        qr_label.pack(pady=20)

        # 添加状态显示区域
        self.status_label = tk.Label(self.qr_window, text="请使用 B站 App 扫描二维码...", wraplength=250)
        self.status_label.pack(pady=10)
        # 开始轮询扫码状态
        self.poll_login_status()

    # 二维码登录
    def login(self):
        # 获取登录二维码的 URL
        url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
        response = requests.get(url, headers=self.headers)
        data = response.json()

        if data['code'] == 0:
            qr_url = data['data']['url']
            qrcode_key = data['data']['qrcode_key']
            self.qrcode_key = qrcode_key
            # 调用 QR 方法生成二维码并显示扫码状态
            self.QR(qr_url, self.qrcode_key)
        else:
            self.update_status("获取二维码失败")

    def poll_login_status(self, interval=1000):
        if not hasattr(self, 'qr_window') or not self.qr_window.winfo_exists():
            return  # 如果窗口已关闭，停止轮询

        # 调用 get_status 方法检查扫码状态
        cookie = self.get_status()

        if cookie:
            # 登录成功，关闭二维码窗口
            if hasattr(self, 'status_label'):
                self.status_label.config(text="登录成功,3秒后自动退出")
            if hasattr(self, 'qr_window') and self.qr_window:
                self.qr_window.after(3000, self.qr_window.destroy)  # 3 秒后关闭窗口
            return True
        else:
            # 继续轮询
            self.qr_window.after(interval, self.poll_login_status, interval)

    def get_status(self):
        url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'
        params = {
            'qrcode_key': self.qrcode_key
        }
        response = requests.get(url, headers=self.headers, params=params)
        data = response.json()
        # print(data['data']['code'])
        # 更新二维码窗口中的状态显示
        if hasattr(self, 'status_label'):
            self.status_label.config(text=data.get('message', '未知状态'))

        # 根据 code 处理不同状态
        if data['data']['code'] == 0:
            # 登录成功，获取 cookie
            url = data['data']['url']
            if url:
                self.cookie = 'SESSDATA=' + quote(re.search(r'SESSDATA=([^&]+)', url).group(1))
                self.token = 'csrf=' + quote(re.search(r'bili_jct=([^&]+)', url).group(1))
                return True
            else:
                return False
        elif data['data']['code'] == 86038:
            if hasattr(self, 'status_label'):
                self.status_label.config(text="二维码已失效，请重新生成二维码。")
        elif data['data']['code'] == 86090:
            if hasattr(self, 'status_label'):
                self.status_label.config(text="二维码已扫码，请在 App 中确认登录...")
        elif data['data']['code'] == 86101:
            if hasattr(self, 'status_label'):
                self.status_label.config(text="未扫码，请使用 B站 App 扫描二维码...")
        else:
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"未知状态: {data.get('message', '未知错误')}")

        return False

    def get_user(self):
        try:
            url = 'https://api.bilibili.com/x/member/web/account'
            if self.cookie:
                cookies = {
                    'SESSDATA': self.cookie.split('=')[1]
                }
                response = requests.get(url, headers=self.headers, cookies=cookies)
                data = response.json()
                if data['code'] == 0:
                    uname = data['data']['uname']
                    # print(uname)
                    return uname
        except Exception as e:
            self.update_status(f"获取用户信息时发生未知错误: {str(e)}")
            return None

    def get_video_info(self, bv_id):
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
        response = requests.get(url, headers=self.get_headers())
        data = response.json()
        if data['code'] == 0:
            video_data = data['data']
            owner_data = data['data']['owner']
            stat_data = data['data']['stat']
            return {
                'title': video_data['title'],   # 视频标题
                'cid': video_data['cid'],   # cid
                'aid': video_data['aid'],   # aid
                'pic': video_data['pic'],   # pid
                'desc': video_data['desc'],  # 视频简介
                'tname': video_data['tname'], # 视频分区
                'ctime' : video_data['ctime'],   # 投稿日期(时间戳)
                'pubdate': video_data['pubdate'],   # 发布日期(时间戳)
                'duration': video_data['duration'],     # 视频时长(秒)
                'name': owner_data['name'],     # up昵称
                'face': owner_data['face'],     # 头像
                'view': stat_data['view'],      # 观看人数
                'danmaku': stat_data['danmaku'],    # 弹幕数
                'reply': stat_data['reply'],    # 评论数
                'favorite': stat_data['favorite'],      # 收藏数
                'like': stat_data['like'],  # 点赞数
                'coin': stat_data['coin'],   # 投币数
                'share': stat_data['share']   # 分享数
            }
        return None

    def get_barrage(self, cid):
        try:
            url = f'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}'
            headers = self.get_headers()
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            root = ET.fromstring(response.content)
            # 提取弹幕内容
            barrage_content = '\n'.join([element.text for element in root.iter('d') if element.text])
            return barrage_content

        except ET.ParseError as e:
            self.update_status(f'解析XML失败: {str(e)}')
            return None

    def get_comment(self, oid):
        comment_list = []
        try:
            for page in range(1, 1000):  # 遍历每一页评论
                url = 'https://api.bilibili.com/x/v2/reply'
                params = {
                    'pn': page,  # 当前页码
                    'type': 1,  # 评论类型（1 表示视频评论）
                    'oid': oid,  # 视频的 oid
                    'ps': 20  # 每页评论数量
                }
                headers = self.get_headers()
                # 将 cookie 字符串转换为字典
                cookies = dict([self.cookie.split('=', 1)])
                response = requests.get(url, headers=headers, cookies=cookies, params=params)
                data = response.json()
                if data['code'] == 0:
                    replies = data['data']['replies']
                    if not replies:
                        break
                    for reply in replies:
                        message = reply['content']['message']
                        comment_list.append(message)
                else:
                    if data['code'] == -400:
                        self.update_status("请求错误")
                    elif data['code'] == -404:
                        self.update_status("无此项")
                    elif data['code'] == 12002:
                        self.update_status("评论区已关闭")
                    elif data['code'] == 12009:
                        self.update_status("评论主体的type不合法")
                    else:
                        self.update_status(f"获取评论失败: {data.get('message', '未知错误')}")
                    break

            return comment_list

        except requests.RequestException as e:
            self.update_status(f"请求评论信息失败: {str(e)}")
            return None

    def get_video_url(self, aid, cid):
        try:
            url = (f'https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn={self.quality}'
                   f'&fnval=4048&fourk=1&fnver=0&session=')
            # print(url)
            headers = self.get_headers()
            headers.update({
                'Referer': f'https://www.bilibili.com/video/av{aid}',
                'Origin': 'https://www.bilibili.com',
            })

            self.update_status(f"正在请求视频地址: {url}")
            response = requests.get(url, headers=headers)
            self.update_status(f"API 响应状态码: {response.status_code}")

            try:
                data = response.json()
                self.update_status(f"API 返回代码: {data.get('code')}")
                self.update_status(f"API 返回信息: {data.get('message', '无')}")
            except Exception as e:
                self.update_status(f"解析响应失败: {str(e)}")
                self.update_status(f"原始响应: {response.text[:200]}...")
                return None

            if data['code'] == 0:
                # 获取视频的清晰度[64,32,16]
                accept_quality = data['data'].get('accept_quality', [])
                quality_list = [str(q) for q in accept_quality]

                quality_desc = {
                    '16': '360P',
                    '32': '480P',
                    '64': '720P',
                    '80': '1080P',
                    '112': '1080P+',
                    '116': '1080P60',
                    '120': '4K',
                    '125': 'HDR',
                    '126': 'Dolby Vision',
                    '127': '8K'
                }
                available_qualities = [f"{q}({quality_desc.get(q, '未知')})" for q in quality_list]
                # print(available_qualities) —— ['64(720P)', '32(480P)', '16(360P)']
                self.update_status(f"可用清晰度: {', '.join(available_qualities)}")

                if self.quality not in quality_list:
                    self.update_status(f"当前清晰度不可用，自动切换到最高可用清晰度: {quality_list[0]}")
                    self.quality = quality_list[0]
                    return self.get_video_url(aid, cid)

                if 'dash' in data['data']:
                    dash = data['data']['dash']
                    video_url = None
                    audio_url = None

                    for video in dash['video']:
                        if str(video['id']) == self.quality:
                            # 视频地址
                            video_url = video['baseUrl']
                            # print(video_url)
                            self.update_status(
                                f"找到视频流: {video['id']}({quality_desc.get(str(video['id']), '未知')})")
                            break

                    if dash['audio']:
                        audio_url = dash['audio'][0]['baseUrl']
                        self.update_status("找到音频流")

                    if video_url and audio_url:
                        self.update_status("成功获取视频和音频地址")
                        return {'video': video_url, 'audio': audio_url, 'is_dash': True}
                    else:
                        self.update_status("无法获取完整的视频/音频地址")

                elif 'durl' in data['data']:
                    self.update_status("使用普通格式下载")
                    return {'video': data['data']['durl'][0]['url'], 'is_dash': False}
                else:
                    self.update_status("未找到可用的视频格式")

            elif data['code'] == -404:
                self.update_status("视频不存在或已被删除")
            elif data['code'] == -403:
                self.update_status("权限不足，是否具有大会员权限")
            else:
                self.update_status(f"获取视频地址失败: {data.get('message', '未知错误')}")
                self.update_status("请检查视频是否可以正常播放")

        except Exception as e:
            self.update_status(f"请求视频地址时发生错误: {str(e)}")
            import traceback
            self.update_status(f"错误详情: {traceback.format_exc()}")
        return None

    def download_file(self, url, filepath, chunk_size=1024 * 1024):
        response = requests.get(url, headers=self.get_headers(), stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = chunk_size
        downloaded = 0

        with open(filepath, 'wb') as f:
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                if total_size:
                    progress = int((downloaded / total_size) * 100)
                    self.update_progress(progress)
                    self.update_status(f'下载进度: {progress}%')

    def download_comment(self, bv_id):
        try:

            self.update_status('获取评论信息...')
            comment_info = self.get_video_info(bv_id)
            if not comment_info:
                self.update_status("获取评论内容失败")
                return False
            title = comment_info['title'].replace('/', '_').replace('\\', '_')
            comment_dir = os.path.join(self.download_path, title)
            os.makedirs(comment_dir, exist_ok=True)
            self.update_status(f'开始下载: {title}')
            self.update_status(f'保存位置: {comment_dir}')
            # 获取评论内容
            oid = comment_info.get('aid')
            comment_content = self.get_comment(oid)
            if not comment_content:
                self.update_status("获取评论内容失败")
                return False

            # 保存评论到文件
            comment_file_path = os.path.join(comment_dir, f'{title}_评论.txt')
            with open(comment_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(comment_content))

            self.update_status(f'评论下载完成: {comment_file_path}')
            return True
        except Exception as e:
            self.update_status(f'下载失败: {str(e)}')
            return False
    def download_barrage(self, bv_id):
        try:
            self.update_status("获取弹幕信息...")
            barrage_info = self.get_video_info(bv_id)
            if not barrage_info:
                self.update_status("获取弹幕信息失败")
                return False
            title = barrage_info['title'].replace('/', '_').replace('\\', '_')
            barrage_dir = os.path.join(self.download_path, title)
            os.makedirs(barrage_dir, exist_ok=True)
            self.update_status(f'开始下载: {title}')
            self.update_status(f'保存位置: {barrage_dir}')
            # 获取弹幕内容
            cid = barrage_info.get('cid')
            barrage_content = self.get_barrage(cid)
            if not barrage_content:
                self.update_status("获取弹幕内容失败")
                return False

            # 保存弹幕到文件
            barrage_file_path = os.path.join(barrage_dir, f'{title}_弹幕.txt')
            with open(barrage_file_path, 'w', encoding='utf-8') as f:
                f.write(barrage_content)

            self.update_status(f'弹幕下载完成: {barrage_file_path}')
            return True

        except Exception as e:
            self.update_status(f'下载失败: {str(e)}')
            return False


    # 下载视频简介
    def download_introduction(self, bv_id):

        try:
            self.update_status("获取视频基本信息...")
            video_info = self.get_video_info(bv_id)
            timestamp1 = video_info['ctime']
            timestamp2 = video_info['pubdate']
            dt1 = datetime.datetime.fromtimestamp(timestamp1)
            dt2 = datetime.datetime.fromtimestamp(timestamp2)
            submit_time = dt1.strftime('%Y-%m-%d %H:%M:%S')
            release_time = dt2.strftime('%Y-%m-%d %H:%M:%S')
            if not video_info:
                self.update_status("获取视频信息失败")
                return False

            title = video_info['title'].replace('/', '_').replace('\\', '_')
            introduction_dir = os.path.join(self.download_path, title)

            if not os.path.exists(introduction_dir):
                os.makedirs(introduction_dir)

            self.update_status(f'开始下载视频信息: {title}')
            self.update_status(f'保存位置: {introduction_dir}')

            # 保存视频信息到文本文件
            introduction_path = os.path.join(introduction_dir, f'{title}_视频信息.txt')
            with open(introduction_path, 'w', encoding='utf-8') as f:
                f.write(f"标题: {video_info['title']}\n")
                f.write(f"up主: {video_info['name']}\n")
                f.write(f"up头像: {video_info['face']}\n")
                f.write(f"简介: {video_info.get('desc', '无')}\n")
                f.write(f"视频分区: {video_info['tname']}\n")
                f.write(f"视频投稿日期: {submit_time}\n")
                f.write(f"视频发布日期: {release_time}\n")
                f.write(f"视频时长: {video_info['duration'] // 60}分, {video_info['duration'] % 60}秒\n")
                f.write(f"观看人数: {video_info['view']}人\n")
                f.write(f"弹幕数: {video_info['danmaku']}\n")
                f.write(f"评论数: {video_info['reply']}\n")
                f.write(f"点赞数: {video_info['like']}\n")
                f.write(f"投币数: {video_info['coin']}\n")
                f.write(f"收藏数: {video_info['favorite']}\n")
                f.write(f"分享数: {video_info['share']}\n")

            self.update_status(f'视频信息下载完成: {title}_视频信息.txt')
            return True

        except Exception as e:
            self.update_status(f'简介下载失败: {str(e)}')
            return False

    # 下载封面
    def download_picture(self, bv_id):
        try:
            self.update_status("获取封面信息...")
            picture_info = self.get_video_info(bv_id)
            if not picture_info:
                self.update_status("获取封面信息失败")
                return False

            title = picture_info['title'].replace('/', '_').replace('\\', '_')
            picture_dir = os.path.join(self.download_path, title)

            if not os.path.exists(picture_dir):
                os.makedirs(picture_dir)

            self.update_status(f'开始下载: {title}')
            self.update_status(f'保存位置: {picture_dir}')

            if picture_info.get('pic'):
                self.update_status("下载封面...")
                picture_path = os.path.join(picture_dir, f'{title}.png')
                self.download_file(picture_info['pic'], picture_path)
                self.update_status(f'下载完成: {title}.png')
            return True

        except Exception as e:
            self.update_status(f'下载失败: {str(e)}')
            return False


    def download_video(self, bv_id):
        try:
            self.update_status("获取视频信息...")
            video_info = self.get_video_info(bv_id)
            if not video_info:
                self.update_status("获取视频信息失败")
                return False

            title = video_info['title'].replace('/', '_').replace('\\', '_')
            video_dir = os.path.join(self.download_path, title)
            print(video_dir)
            if not os.path.exists(video_dir):
                os.makedirs(video_dir)

            self.update_status(f'开始下载: {title}')
            self.update_status(f'保存位置: {video_dir}')

            urls = self.get_video_url(video_info['aid'], video_info['cid'])
            if not urls:
                self.update_status("获取视频地址失败")
                return False

            if urls.get('is_dash'):
                self.update_status("下载视频流...")
                video_path = os.path.join(video_dir, f'{title}_video.m4s')
                self.download_file(urls['video'], video_path)

                self.update_status("下载音频流...")
                audio_path = os.path.join(video_dir, f'{title}_audio.m4s')
                self.download_file(urls['audio'], audio_path)

                self.update_status("合并音视频...")
                output_path = os.path.join(video_dir, f'{title}.mp4')

                ffmpeg_path = self.get_ffmpeg_path()
                cmd = [
                    ffmpeg_path,
                    '-i', video_path,
                    '-i', audio_path,
                    '-c', 'copy',
                    output_path
                ]

                subprocess.run(cmd, check=True)

                os.remove(video_path)
                os.remove(audio_path)

            else:
                video_path = os.path.join(video_dir, f'{title}.mp4')
                self.download_file(urls['video'], video_path)
            self.update_status(f'下载完成: {title}')
            return True

        except Exception as e:
            self.update_status(f'下载失败: {str(e)}')
            return False

    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            ffmpeg_path = os.path.join(application_path, 'ffmpeg.exe')
        else:
            ffmpeg_path = 'ffmpeg'
        return ffmpeg_path


def main():
    app = BilibiliDownloaderGUI()
    app.window.mainloop()


if __name__ == '__main__':
    main()