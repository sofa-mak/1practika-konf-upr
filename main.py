import tkinter as tk #Создаёт окна и элементы интерфейса
import socket #Узнаёт имя компьютера
import getpass #Узнаёт имя пользователя
import argparse #Библиотека для разбора параметров командной строки
import json #Библиотека для работы с JSON-файлами
import os #Библиотека для проверки существования файлов


class ShellEmulator: # Класс-эмулятор оболочки
    def __init__(self, root, vfs_path, script_path):
        self.root = root
        self.vfs_path = vfs_path #сохраняем путь к VFS
        self.script_path = script_path #сохраняем путь к скрипту
        self.vfs = None #здесь будет храниться загруженная VFS
        self.current_path = ["/"] #текущая папка (начинаем с корня)

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

        self.input.focus_set() #Ставим фокус в поле ввода

        self.print_line(f"[DEBUG] VFS: {self.vfs_path}")
        self.print_line(f"[DEBUG] Скрипт: {self.script_path}")

        #Загружаем VFS из JSON-файла
        self.load_vfs()
        #Показываем motd (приветствие), если есть
        self.show_motd()

        if self.script_path:
            self.run_script(self.script_path)

    def load_vfs(self): #Метод load_vfs - загружает виртуальную файловую систему из JSON
        #Проверяем, существует ли файл VFS
        if not os.path.exists(self.vfs_path):
            self.print_line(f"Ошибка: файл VFS не найден: {self.vfs_path}")
            return
        try:
            #Открываем файл и читаем его как JSON
            with open(self.vfs_path, "r", encoding="utf-8") as f:
                self.vfs = json.load(f)
            self.print_line(f"[DEBUG] VFS загружена: {self.vfs_path}")
        except json.JSONDecodeError:
            self.print_line(f"Ошибка: неверный формат JSON в файле: {self.vfs_path}")
        except Exception as e:
            self.print_line(f"Ошибка загрузки VFS: {e}")

    def show_motd(self): #Метод show_motd - показывает содержимое файла /motd.txt
        if not self.vfs:
            return
        root_dir = self.vfs.get("/", {})
        motd = root_dir.get("children", {}).get("motd.txt")
        if motd and motd.get("type") == "file":
            self.print_line("=== MOTD ===")
            self.print_line(motd.get("content", ""))
            self.print_line("============")

    def get_current_dir(self): #Метод get_current_dir - возвращает содержимое текущей папки
        #Начинаем с корня
        current = self.vfs.get("/", {})
        #Проходим по всем папкам в current_path, кроме первой ("/")
        for part in self.current_path[1:]:
            children = current.get("children", {})
            if part in children:
                current = children[part]
            else:
                #Если папки нет - возвращаемся в корень
                return self.vfs.get("/", {})
        return current

    def cmd_ls(self): #Метод cmd_ls - реализует команду ls (показать файлы)
        current = self.get_current_dir()
        children = current.get("children", {})
        if not children:
            self.print_line("(пусто)")
            return
        #Выводим имена всех файлов и папок в алфавитном порядке
        for name in sorted(children.keys()):
            self.print_line(name)

    def cmd_cd(self, args): #Метод cmd_cd - реализует команду cd (перейти в папку)
        #Если аргументов нет - возвращаемся в корень
        if not args:
            self.current_path = ["/"]
            return
        target = args[0]
        #Если ".." - поднимаемся на уровень выше
        if target == "..":
            if len(self.current_path) > 1:
                self.current_path.pop()
            return
        #Ищем папку с таким именем в текущей директории
        current = self.get_current_dir()
        children = current.get("children", {})
        if target in children and children[target].get("type") == "dir":
            self.current_path.append(target)
        else:
            self.print_line(f"cd: {target}: нет такой папки")

    def cmd_tail(self, args): #Метод cmd_tail - реализует команду tail (последние строки файла)
        if not args:
            self.print_line("tail: не указан файл")
            return
        filename = args[0]
        #Определяем количество строк (по умолчанию 5)
        num_lines = 5
        if len(args) > 1:
            try:
                num_lines = int(args[1])
            except ValueError:
                self.print_line("tail: неверное число строк")
                return
        #Ищем файл в текущей директории
        current = self.get_current_dir()
        children = current.get("children", {})
        if filename not in children or children[filename].get("type") != "file":
            self.print_line(f"tail: {filename}: файл не найден")
            return
        #Получаем содержимое и разбиваем на строки
        content = children[filename].get("content", "")
        lines = content.splitlines()
        #Берём последние num_lines строк
        for line in lines[-num_lines:]:
            self.print_line(line)

    def cmd_tac(self, args): #Метод cmd_tac - реализует команду tac (файл в обратном порядке)
        if not args:
            self.print_line("tac: не указан файл")
            return
        filename = args[0]
        current = self.get_current_dir()
        children = current.get("children", {})
        if filename not in children or children[filename].get("type") != "file":
            self.print_line(f"tac: {filename}: файл не найден")
            return
        content = children[filename].get("content", "")
        lines = content.splitlines()
        #Выводим строки в обратном порядке
        for line in reversed(lines):
            self.print_line(line)

    def cmd_clear(self): #Метод cmd_clear - реализует команду clear (очистка экрана)
        #Очищаем область вывода
        self.output.delete("1.0", tk.END)

    def on_enter(self, event): #Срабатывает при нажатии Enter
        command_line = self.input.get() #Получаем строку, которую ввёл пользователь
        self.input.delete(0, tk.END) #Очищаем поле ввода
        self.execute_command(command_line) #Отдельный метод для выполнения команды

    def execute_command(self, command_line): #Выполняет одну команду
        self.print_line(f"> {command_line}")

        parts = command_line.split() #Разбиваем строку на команду и аргументы
        if not parts:
            return

        command = parts[0] #Первое слово - команда
        args = parts[1:] #Остальное - аргументы

        #Вызываем нужный метод для команды
        if command == "exit":
            self.root.destroy()
        elif command == "ls":
            self.cmd_ls()
        elif command == "cd":
            self.cmd_cd(args)
        elif command == "tail":
            self.cmd_tail(args)
        elif command == "tac":
            self.cmd_tac(args)
        elif command == "clear":
            self.cmd_clear()
        else:
            self.print_line(f"Команда не найдена: {command}")

    def run_script(self, script_path): #Метод run_script - читает скрипт и выполняет команды
        self.print_line(f"[DEBUG] Выполняем скрипт: {script_path}")
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    command = line.strip() #Убираем пробелы и перевод строки
                    if command:
                        self.execute_command(command)
        except FileNotFoundError:
            self.print_line(f"Ошибка: файл скрипта не найден: {script_path}")

    def print_line(self, text): #Метод print_line - выводит текст в область вывода
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)


if __name__ == "__main__":
    #Парсер параметров командной строки
    parser = argparse.ArgumentParser(description="Эмулятор оболочки UNIX")
    parser.add_argument("--vfs", default="vfs.json", help="Путь к файлу VFS")
    parser.add_argument("--script", default=None, help="Путь к стартовому скрипту")
    args = parser.parse_args()

    root = tk.Tk() #tk.Tk() — это класс «главное окно»
    app = ShellEmulator(root, args.vfs, args.script) #Передаём параметры
    root.mainloop() #Запускаем главный цикл