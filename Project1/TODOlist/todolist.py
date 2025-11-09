import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json
import os

# --- Global variables ---
tasks = []
file_path = None

# --- Core functions ---
def add_task():
    text = entry.get().strip()
    if not text:
        messagebox.showinfo("Empty Task", "Type a task to add.")
        return
    tasks.append({"text": text, "done": False})
    entry.delete(0, tk.END)
    refresh()
    save_tasks()

def delete_task():
    idx = get_index()
    if idx is None:
        return
    if messagebox.askyesno("Delete", f"Delete:\n{tasks[idx]['text']}?"):
        tasks.pop(idx)
        refresh()
        save_tasks()

def edit_task():
    idx = get_index()
    if idx is None:
        return
    new_text = simpledialog.askstring("Edit Task", "Modify task:", initialvalue=tasks[idx]["text"])
    if new_text:
        tasks[idx]["text"] = new_text.strip()
        refresh()
        save_tasks()

def toggle_complete():
    idx = get_index()
    if idx is None:
        return
    tasks[idx]["done"] = not tasks[idx]["done"]
    refresh()
    save_tasks()

# --- Helpers ---
def get_index():
    sel = listbox.curselection()
    if not sel:
        messagebox.showinfo("Select", "Select a task first.")
        return None
    return sel[0]

def refresh():
    listbox.delete(0, tk.END)
    for t in tasks:
        mark = "☑" if t["done"] else "☐"
        listbox.insert(tk.END, f"{mark} {t['text']}")
    total = len(tasks)
    done = sum(t["done"] for t in tasks)
    pending = total - done
    status_label.config(text=f"Total: {total} | Pending: {pending} | Completed: {done}")

# --- File handling ---
def choose_folder():
    global file_path
    folder = filedialog.askdirectory(title="Select folder to store tasks.json")
    if not folder:
        messagebox.showwarning("Folder required", "You must select a folder.")
        root.destroy()
    file_path = os.path.join(folder, "tasks.json")

def save_tasks():
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

def load_tasks():
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            global tasks
            tasks = [{"text": t.get("text",""), "done": t.get("done", False)} for t in data]

def on_close():
    save_tasks()
    root.destroy()

# --- GUI setup ---
root = tk.Tk()
root.title("Simple To-Do")
root.geometry("400x400")

entry = tk.Entry(root, font=("Segoe UI", 12))
entry.pack(fill="x", padx=10, pady=5)
entry.bind("<Return>", lambda e: add_task())

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Add", width=10, command=add_task).pack(side="left", padx=5)
tk.Button(btn_frame, text="Edit", width=10, command=edit_task).pack(side="left", padx=5)
tk.Button(btn_frame, text="Delete", width=10, command=delete_task).pack(side="left", padx=5)
tk.Button(btn_frame, text="Check/Uncheck", width=12, command=toggle_complete).pack(side="left", padx=5)

listbox = tk.Listbox(root, font=("Segoe UI", 12), selectmode=tk.SINGLE)
listbox.pack(fill="both", expand=True, padx=10, pady=5)
listbox.bind("<Double-Button-1>", lambda e: toggle_complete())

status_label = tk.Label(root, text="", anchor="w")
status_label.pack(fill="x", padx=10, pady=5)

# --- Initialize ---
choose_folder()
load_tasks()
refresh()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
