import tkinter as tk #Создаёт окна и элементы интерфейса
import socket #Узнаёт имя компьютера
import getpass#Узнаёт имя пользователя
import argparse #библиотека для разбора параметров командной строки
import json #библиотека для работы с JSON-файлами
import os #библиотека для проверки существования файлов


class ShellEmulator:
    def __init__(self, root, vfs_path, script_path): 
        self.root = root
        self.vfs_path = vfs_path #сохраняем путь к VFS 
        self.script_path = script_path # сохраняем путь к скрипту
        self.vfs = None #  хранится загруженная VFS

        username = getpass.getuser() #Возвращает имя пользователя, который вошёл в систему
        hostname = socket.gethostname() #Возвращает имя компьютера в сети
        title = f"Эмулятор - [{username}@{hostname}]"
        self.root.title(title)
        self.root.geometry("800x600")

        self.output = tk.Text(root, bg="black", fg="white", font=("Courier", 12))
        self.output.pack(fill=tk.BOTH, expand=True) #Размещаем область вывода и растягиваем её по горизонтали и вертикали; expand=True - растягиваться при увеличении окна

        self.input = tk.Entry(root, bg="black", fg="white", font=("Courier", 12))
        self.input.pack(fill=tk.X) # tk.both - во все стороны, tk.x- по горизонатли, tk.y -по вертикали
        self.input.bind("<Return>", self.on_enter) # типа кода нажмет энтер все запустится 

        self.input.focus_set() # Ставим фокус в поле ввода

        
        self.print_line(f"[DEBUG] VFS: {self.vfs_path}")
        self.print_line(f"[DEBUG] Скрипт: {self.script_path}")

        # НОВОЕ: загружаем VFS из JSON-файла
        self.load_vfs()
        # показываем motd (приветствие), если есть
        self.show_motd()

        if self.script_path:
            self.run_script(self.script_path)

    def load_vfs(self): # метод load_vfs - загружает виртуальную файловую систему из JSON
        # Проверяем, существует ли файл VFS
        if not os.path.exists(self.vfs_path):
            self.print_line(f"Ошибка: файл VFS не найден: {self.vfs_path}")
            return
        try:
            # Открываем файл и читаем его как JSON
            with open(self.vfs_path, "r", encoding="utf-8") as f:
                self.vfs = json.load(f)
            self.print_line(f"[DEBUG] VFS загружена: {self.vfs_path}")
        except json.JSONDecodeError:
            self.print_line(f"Ошибка: неверный формат JSON в файле: {self.vfs_path}")
        except Exception as e:
            self.print_line(f"Ошибка загрузки VFS: {e}")

    def show_motd(self):    # метод show_motd - показывает содержимое файла /motd.txt
        if not self.vfs:
            return
        root_dir = self.vfs.get("/", {})
        motd = root_dir.get("children", {}).get("motd.txt")
        if motd and motd.get("type") == "file":
            self.print_line("=== MOTD ===")
            self.print_line(motd.get("content", ""))
            self.print_line("============")

    def on_enter(self, event):
        command_line = self.input.get() # Получаем строку, которую ввёл пользователь
        self.input.delete(0, tk.END) 
        self.execute_command(command_line) # отдельный метод для выполнения команды

    
    def execute_command(self, command_line):
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

    def run_script(self, script_path):    # метод run_script-читает файл скрипта и выполняет команды
        self.print_line(f"[DEBUG] Выполняем скрипт: {script_path}")
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    command = line.strip()
                    if command:
                        self.execute_command(command)
        except FileNotFoundError:
            self.print_line(f"Ошибка: файл скрипта не найден: {script_path}")

    def print_line(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Эмулятор оболочки UNIX")
    parser.add_argument("--vfs", default="vfs.json", help="Путь к файлу VFS")
    parser.add_argument("--script", default=None, help="Путь к стартовому скрипту")
    args = parser.parse_args()

    root = tk.Tk() # tk.Tk() — это класс «главное окно»
    app = ShellEmulator(root, args.vfs, args.script) # НОВОЕ: передаём параметры
    root.mainloop()#апускаем главный цикл