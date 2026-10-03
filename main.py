import tkinter as tk
import socket
import getpass


class ShellEmulator:
    def __init__(self, root):
        self.root = root

        username = getpass.getuser()
        hostname = socket.gethostname()
        title = f"Эмулятор - [{username}@{hostname}]"
        self.root.title(title)
        self.root.geometry("800x600")

        self.output = tk.Text(root, bg="black", fg="white", font=("Courier", 12))
        self.output.pack(fill=tk.BOTH, expand=True)

        self.input = tk.Entry(root, bg="black", fg="white", font=("Courier", 12))
        self.input.pack(fill=tk.X)
        self.input.bind("<Return>", self.on_enter)

        self.input.focus_set()

    def on_enter(self, event):
        command_line = self.input.get()
        self.input.delete(0, tk.END)

        self.print_line(f"> {command_line}")

        parts = command_line.split()
        if not parts:
            return

        command = parts[0]
        args = parts[1:]

        if command == "exit":
            self.root.destroy()
        elif command in ("ls", "cd"):
            self.print_line(f"Команда: {command}")
            self.print_line(f"Аргументы: {args}")
        else:
            self.print_line(f"Команда не найдена: {command}")

    def print_line(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = ShellEmulator(root)
    root.mainloop()