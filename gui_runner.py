import threading
import time
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import helper as main  # imports find_largest_directories, find_largest_files, format_size

def browse_path():
    d = filedialog.askdirectory()
    if d:
        path_var.set(d)

def run_scan_background():
    # Prepare UI state and cancellation event
    global scan_cancel_event
    scan_cancel_event = threading.Event()
    set_ui_enabled(False)
    try:
        text_output.delete("1.0", tk.END)
    except Exception:
        try:
            text_output.delete("0.0", tk.END)
        except Exception:
            pass

    try:
        path = path_var.get().strip()
        if not path:
            raise ValueError("Path is required.")
        if not os.path.isdir(path):
            raise ValueError("Path is not a directory.")

        try:
            folders_num = int(folders_var.get())
        except Exception:
            folders_num = 10
        try:
            files_num = int(files_var.get())
        except Exception:
            files_num = 10

        thread = threading.Thread(target=worker, args=(path, max(0, folders_num), max(0, files_num)))
        thread.daemon = True
        thread.start()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        set_ui_enabled(True)

def append_text(text: str):
    """Insert text into the GUI text widget (must be called from main thread via root.after)."""
    try:
        text_output.insert(tk.END, text)
        text_output.see(tk.END)
    except Exception:
        # if widget isn't ready or has been destroyed, ignore
        pass


# Global cancellation event (set when user requests stop)
scan_cancel_event = None


def set_ui_enabled(enabled: bool):
    """Enable or disable main UI controls depending on scanning state."""
    try:
        if enabled:
            btn_start.configure(state="normal")
            btn_browse.configure(state="normal")
            btn_stop.configure(state="disabled")
        else:
            btn_start.configure(state="disabled")
            btn_browse.configure(state="disabled")
            btn_stop.configure(state="normal")
    except Exception:
        pass


def stop_scan():
    """Handler for Stop button: request cancellation."""
    global scan_cancel_event
    if scan_cancel_event is not None:
        scan_cancel_event.set()
        root.after(0, append_text, "\nCancellation requested — stopping soon...\n")
    try:
        btn_stop.configure(state="disabled")
    except Exception:
        pass


def worker(path, folders_num, files_num):
    start_total = time.perf_counter()

    # Folders
    entries = []
    try:
        entries = os.listdir(path)
    except OSError as e:
        root.after(0, append_text, f"Error accessing path: {e}\n")
        return

    immediate_subdirs = [os.path.join(path, item) for item in entries
                         if os.path.isdir(os.path.join(path, item)) and not os.path.islink(os.path.join(path, item))]
    available_subdirs_count = len(immediate_subdirs)
    folders_to_request = min(folders_num, available_subdirs_count)

    # Check cancellation before starting heavy work
    if scan_cancel_event is not None and scan_cancel_event.is_set():
        root.after(0, append_text, "Scan cancelled before starting folder scan.\n")
        root.after(0, set_ui_enabled, True)
        return

    if available_subdirs_count == 0 or folders_to_request == 0:
        root.after(0, append_text, "No immediate subdirectories found or requested 0.\n")
        largest_dirs = []
    else:
        root.after(0, append_text, f"Working: scanning {available_subdirs_count} subdirectories (returning top {folders_to_request})...\n")
        t0 = time.perf_counter()
        largest_dirs = main.find_largest_directories(path, num_largest=folders_to_request)
        t1 = time.perf_counter()
        root.after(0, append_text, f"Finished scanning folders in {t1 - t0:.2f}s.\n")
        # Check cancellation after folder scan
        if scan_cancel_event is not None and scan_cancel_event.is_set():
            root.after(0, append_text, "Scan cancelled after folder scan.\n")
            root.after(0, set_ui_enabled, True)
            return

    if largest_dirs:
        root.after(0, append_text, f"\nTop {len(largest_dirs)} largest subdirectories in '{path}':\n")
        for dir_path, size in largest_dirs:
            root.after(0, append_text, f"- {dir_path}: {main.format_size(size)}\n")
    else:
        root.after(0, append_text, "\nNo subdirectories found or an error occurred.\n")

    # Files
    if files_num == 0:
        root.after(0, append_text, "\nSkipping file scan (requested 0).\n")
        largest_files = []
    else:
        root.after(0, append_text, f"\nWorking: scanning files recursively (returning top {files_num})...\n")
        t0 = time.perf_counter()
        largest_files = main.find_largest_files(path, num_files=files_num)
        t1 = time.perf_counter()
        root.after(0, append_text, f"Finished scanning files in {t1 - t0:.2f}s.\n")

    if largest_files:
        root.after(0, append_text, f"\nTop {len(largest_files)} largest files in '{path}':\n")
        for file_path, size in largest_files:
            root.after(0, append_text, f"- {file_path}: {main.format_size(size)}\n")
    else:
        root.after(0, append_text, "\nNo files found or an error occurred.\n")

    # final elapsed
    end_total = time.perf_counter()
    root.after(0, append_text, f"\nTotal elapsed time: {end_total - start_total:.2f}s\n")
    # Re-enable UI
    root.after(0, set_ui_enabled, True)

def finish(lines, start_total):
    end_total = time.perf_counter()
    lines.append(f"\nTotal elapsed time: {end_total - start_total:.2f}s")
    text = "\n".join(lines)
    root.after(0, display_output, text)

def display_output(text):
    text_output.insert("1.0", text)
    try:
        btn_start.configure(state="normal")
        btn_browse.configure(state="normal")
    except Exception:
        pass

# Configure CustomTkinter
ctk.set_appearance_mode("System")  # System, Dark, Light
ctk.set_default_color_theme("blue")

# GUI
root = ctk.CTk()
root.title("Folder/File Size Scanner")

frm = ctk.CTkFrame(root, corner_radius=8)
frm.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

ctk.CTkLabel(frm, text="Path:").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 0))
path_var = tk.StringVar()
entry_path = ctk.CTkEntry(frm, width=560, textvariable=path_var)
entry_path.grid(row=0, column=1, pady=(6, 0))
btn_browse = ctk.CTkButton(frm, text="Browse...", command=browse_path)
btn_browse.grid(row=0, column=2, padx=6, pady=(6, 0))

ctk.CTkLabel(frm, text="Return folders (num):").grid(row=1, column=0, sticky="w", pady=(6,0), padx=6)
folders_var = tk.StringVar(value="10")
ctk.CTkEntry(frm, width=120, textvariable=folders_var).grid(row=1, column=1, sticky="w", pady=(6,0), padx=6)

ctk.CTkLabel(frm, text="Return files (num):").grid(row=2, column=0, sticky="w", pady=(6,0), padx=6)
files_var = tk.StringVar(value="10")
ctk.CTkEntry(frm, width=120, textvariable=files_var).grid(row=2, column=1, sticky="w", pady=(6,0), padx=6)

btn_start = ctk.CTkButton(frm, text="Start scan", command=run_scan_background)
btn_start.grid(row=3, column=1, pady=(10,0))

# Stop button (red) — disabled until a scan starts
btn_stop = ctk.CTkButton(frm, text="Stop scan", fg_color="#d9534f", hover_color="#c9302c", command=stop_scan)
btn_stop.grid(row=3, column=2, pady=(10,0))
btn_stop.configure(state="disabled")

# CTk has CTkTextbox in recent versions; fall back to tk.Text if not available
CTkTextbox = getattr(ctk, "CTkTextbox", None)
if CTkTextbox is not None:
    text_output = CTkTextbox(frm, width=880, height=400)
else:
    text_output = tk.Text(frm, width=100, height=25)
text_output.grid(row=4, column=0, columnspan=3, pady=(8,0))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

root.mainloop()