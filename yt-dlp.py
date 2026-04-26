import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import os

from PIL import Image, ImageTk

ydl_instance = None
stop_download = False
browser_choice = None
proxy_address = None

# -------------------
def update_ui(percent, speed, eta):
    progress_bar['value'] = percent
    status_label.config(text=f"{percent:.1f}% | {speed} | ETA {eta}")

# -------------------
def progress_hook(d):
    global stop_download

    if stop_download:
        raise Exception("CANCELLED")

    if d.get('status') == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)

        if total:
            percent = downloaded / total * 100

            speed = d.get('speed')
            speed_str = f"{speed/1024/1024:.2f} MB/s" if speed else "?"

            eta = d.get('eta')
            eta_str = f"{eta}s" if eta else "?"

            root.after(0, update_ui, percent, speed_str, eta_str)

    elif d.get('status') == 'finished':
        root.after(0, lambda: status_label.config(text="Finished ✔"))

# -------------------
def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path.set(folder)

# -------------------
def ask_browser(callback):
    win = tk.Toplevel(root)
    win.title("Browser")

    def set_browser(b):
        global browser_choice
        browser_choice = b
        win.destroy()
        callback()

    tk.Label(win, text="Cookies browser").pack()
    tk.Button(win, text="Chrome", command=lambda: set_browser("chrome")).pack()
    tk.Button(win, text="Firefox", command=lambda: set_browser("firefox")).pack()
    tk.Button(win, text="Edge", command=lambda: set_browser("edge")).pack()

# -------------------
def ask_proxy(callback):
    win = tk.Toplevel(root)
    win.title("Proxy")

    tk.Label(win, text="Enter proxy (http://ip:port)").pack()

    entry = tk.Entry(win, width=40)
    entry.pack()

    def save():
        global proxy_address
        proxy_address = entry.get()
        win.destroy()
        callback()

    tk.Button(win, text="OK", command=save).pack()

# -------------------
def download():
    mode = mode_var.get()

    if "Cookies" in mode:
        ask_browser(download_real)

    elif mode == "Proxy":
        ask_proxy(download_real)

    else:
        download_real()

# -------------------
def download_real():
    global ydl_instance, stop_download

    stop_download = False

    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter URL!")
        return

    def run():
        global ydl_instance

        try:
            opts = {
                'progress_hooks': [progress_hook],
                'outtmpl': os.path.join(download_path.get(), '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4'
            }

            # ---------------- MODE
            mode = mode_var.get()

            if mode == "Playlist":
                opts['noplaylist'] = False
            else:
                opts['noplaylist'] = True

            if mode == "Cookies 1":
                opts['cookiesfrombrowser'] = (browser_choice,)

            elif mode == "Cookies 2":
                opts['cookiesfrombrowser'] = (browser_choice,)
                opts['http_headers'] = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": url.split("/")[0]
                }

            elif mode == "Proxy" and proxy_address:
                opts['proxy'] = proxy_address

            # ---------------- THREADS (-N)
            threads = threads_var.get()
            if threads != "off":
                opts['concurrent_fragment_downloads'] = int(threads)

            # ---------------- QUALITY
            quality = quality_var.get()

            if quality == "Best":
                opts['format'] = "bv*+ba/b"

            elif quality == "Video only":
                opts['format'] = "bv*/b"

                fmt = video_format_var.get().lower()

                opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': fmt
                }]

            elif quality == "Audio only":
                opts['format'] = "ba/b"

                codec = audio_var.get().lower()
                bitrate = min(max(bitrate_var.get(), 33), 320)

                opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': codec,
                    'preferredquality': str(bitrate) if codec == "mp3" else None,
                }]

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl_instance = ydl
                ydl.download([url])

            if not stop_download:
                messagebox.showinfo("Done", "Download completed!")

        except Exception as e:
            if "CANCELLED" not in str(e):
                messagebox.showerror("Error", str(e))

    threading.Thread(target=run).start()

# -------------------
def cancel():
    global stop_download, ydl_instance
    stop_download = True

    if ydl_instance:
        try:
            ydl_instance.abort_download()
        except:
            pass

    status_label.config(text="Cancelled ✖")

# -------------------
# GUI
# -------------------
root = tk.Tk()
root.title("Video Downloader")
root.geometry("550x260")

# VARIABLES
mode_var = tk.StringVar(value="Video and audio only")
quality_var = tk.StringVar(value="Best video and audio")
video_format_var = tk.StringVar(value="mp4")
audio_var = tk.StringVar(value="mp3")
threads_var = tk.StringVar(value="off")
bitrate_var = tk.IntVar(value=160)
download_path = tk.StringVar(value=os.getcwd())

# -------------------
# LOGO + ICON
# -------------------
img = Image.open("YT-DLP GUI.png")
img = img.resize((100, 100))
img = ImageTk.PhotoImage(img)

root.iconphoto(False, img)

# ===================
# LEFT
# ===================
left = tk.Frame(root)
left.grid(row=0, column=0, padx=5, pady=5)

tk.Label(left, image=img).pack()

tk.Label(left, text="URL").pack()
url_entry = tk.Entry(left, width=25)
url_entry.pack()

tk.Button(left, text="Download ▶", command=download).pack(pady=2)
tk.Button(left, text="Cancel ✖", command=cancel).pack()

progress_bar = ttk.Progressbar(left, length=180)
progress_bar.pack(pady=3)

status_label = tk.Label(left, text="0%")
status_label.pack()

# ===================
# MIDDLE
# ===================
middle = tk.Frame(root)
middle.grid(row=0, column=1, padx=5, pady=5)

tk.Label(middle, text="Quality").pack()
tk.OptionMenu(middle, quality_var,
              "Best video and audio",
              "Video only",
              "Audio only").pack()

tk.Label(middle, text="Video format").pack()
tk.OptionMenu(middle, video_format_var,
              "mp4", "mkv", "webm", "avi").pack()

tk.Label(middle, text="Audio format").pack()
tk.OptionMenu(middle, audio_var,
              "mp3", "wav", "flac", "opus").pack()

tk.Label(middle, text="Bitrate only works with audio only").pack()
tk.Scale(middle, from_=33, to=320,
         orient="horizontal",
         variable=bitrate_var).pack()

# ===================
# RIGHT
# ===================
right = tk.Frame(root)
right.grid(row=0, column=2, padx=5, pady=5)

tk.Label(right, text="Mode").pack()
tk.OptionMenu(right, mode_var,
              "Video and audio only",
              "Playlist",
              "Cookies 1",
              "Cookies 2",
              "Proxy").pack()

tk.Label(right, text="Threads (-N)").pack()
tk.OptionMenu(right, threads_var,
              "off", "1", "2", "4", "5", "8", "16").pack()

tk.Label(right, text="Folder").pack()
tk.Label(right, textvariable=download_path, wraplength=150).pack()
tk.Button(right, text="Choose 📁", command=choose_folder).pack()

root.mainloop()