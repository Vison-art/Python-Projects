import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
from tkinter import scrolledtext
import os
import json
import re
import platform

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Text Editor")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.current_file = None
        self.current_font = font.Font(family="Arial", size=10)
        self.current_font_size = 10
        self.current_font_family = "Arial"
        self.recent_files = []
        self.max_recent_files = 5
        self.auto_save = True
        self.auto_save_interval = 300000  # 5 minutes
        self.format_start_mark = None
        self.current_format_tags = set()
        self.line_number_update_id = None
        self.status_update_id = None
        
        # Create UI components
        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
        self.create_text_area()
        self.bind_events()
        self.load_recent_files()
        self.start_auto_save()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        
        # Recent Files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Print", command=self.print_file, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=lambda: self.text_area.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=lambda: self.text_area.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=lambda: self.text_area.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=lambda: self.text_area.tag_add("sel", "1.0", tk.END), accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self.show_find_dialog, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self.show_replace_dialog, accelerator="Ctrl+H")
        
        # Format Menu
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Bold", command=self.toggle_bold, accelerator="Ctrl+B")
        format_menu.add_command(label="Italic", command=self.toggle_italic, accelerator="Ctrl+I")
        format_menu.add_command(label="Underline", command=self.toggle_underline, accelerator="Ctrl+U")
        format_menu.add_separator()
        format_menu.add_command(label="Font", command=self.show_font_dialog)
        format_menu.add_command(label="Text Color", command=self.show_color_dialog)
        format_menu.add_separator()
        format_menu.add_checkbutton(label="Word Wrap", command=self.toggle_word_wrap)
        format_menu.add_checkbutton(label="Show Line Numbers", command=self.toggle_line_numbers)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_checkbutton(label="Auto-save", command=self.toggle_auto_save)
        tools_menu.add_command(label="Word Count", command=self.show_word_count)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # File operations
        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Font controls
        self.font_family_var = tk.StringVar(value="Arial")
        self.font_family_combo = ttk.Combobox(
            toolbar,
            textvariable=self.font_family_var,
            values=sorted(font.families()),
            width=15,
            state="readonly"
        )
        self.font_family_combo.pack(side=tk.LEFT, padx=2)
        self.font_family_combo.bind('<<ComboboxSelected>>', self.change_font_family)
        
        self.font_size_var = tk.StringVar(value="10")
        self.font_size_combo = ttk.Combobox(
            toolbar,
            textvariable=self.font_size_var,
            values=["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"],
            width=5,
            state="readonly"
        )
        self.font_size_combo.pack(side=tk.LEFT, padx=2)
        self.font_size_combo.bind('<<ComboboxSelected>>', self.change_font_size)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Style buttons
        self.bold_var = tk.BooleanVar(value=False)
        self.italic_var = tk.BooleanVar(value=False)
        self.underline_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(toolbar, text="B", variable=self.bold_var, command=self.toggle_bold).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(toolbar, text="I", variable=self.italic_var, command=self.toggle_italic).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(toolbar, text="U", variable=self.underline_var, command=self.toggle_underline).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(toolbar, text="Color", command=self.show_color_dialog).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(toolbar, text="Find", command=self.show_find_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Replace", command=self.show_replace_dialog).pack(side=tk.LEFT, padx=2)

    def create_text_area(self):
        text_frame = ttk.Frame(self.root)
        text_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.line_numbers = tk.Text(
            text_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            background='lightgray',
            foreground='black',
            state='disabled'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            width=80,
            height=30,
            font=self.current_font
        )
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')
        
        # Configure tags
        self.text_area.tag_configure("bold", font=font.Font(family=self.current_font_family, size=self.current_font_size, weight="bold"))
        self.text_area.tag_configure("italic", font=font.Font(family=self.current_font_family, size=self.current_font_size, slant="italic"))
        self.text_area.tag_configure("underline", underline=True)
        
        # Bind events
        self.text_area.bind('<<Selection>>', self.update_format_buttons)
        self.text_area.bind('<Key>', lambda e: (self.update_line_numbers(), self.apply_format_to_new_text()))
        self.text_area.bind('<MouseWheel>', self.update_line_numbers)

    def create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_events(self):
        # File operations
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_as_file())
        self.root.bind('<Control-p>', lambda e: self.print_file())
        
        # Edit operations
        self.root.bind('<Control-x>', lambda e: self.text_area.event_generate("<<Cut>>"))
        self.root.bind('<Control-c>', lambda e: self.text_area.event_generate("<<Copy>>"))
        self.root.bind('<Control-v>', lambda e: self.text_area.event_generate("<<Paste>>"))
        self.root.bind('<Control-a>', lambda e: self.text_area.tag_add("sel", "1.0", tk.END))
        
        # Format operations
        self.root.bind('<Control-b>', lambda e: self.toggle_bold())
        self.root.bind('<Control-i>', lambda e: self.toggle_italic())
        self.root.bind('<Control-u>', lambda e: self.toggle_underline())
        self.root.bind('<Control-f>', lambda e: self.show_find_dialog())
        self.root.bind('<Control-h>', lambda e: self.show_replace_dialog())
        self.root.bind('<Control-Shift-C>', lambda e: self.show_color_dialog())
        
        # Status bar update
        self.text_area.bind('<Key>', self.update_status)
        self.text_area.bind('<Button-1>', self.update_status)
        
        # Format tracking
        self.text_area.bind('<Key>', self.apply_format_to_new_text)
        self.text_area.bind('<Button-1>', self.clear_format_mark)

    def save_file(self):
        if not self.current_file:
            return self.save_as_file()
            
        try:
            with open(self.current_file, 'w', encoding='utf-8') as file:
                file.write(self.text_area.get(1.0, tk.END))
            self.status_bar.config(text=f"Saved: {os.path.basename(self.current_file)}")
            self.add_recent_file(self.current_file)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            return False

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.current_file = file_path
            if self.save_file():
                self.update_title()
                return True
        return False

    def check_save(self):
        if not self.text_area.edit_modified():
            return True
            
        response = messagebox.askyesnocancel(
            "Save File",
            "Do you want to save the current file?"
        )
        if response:
            return self.save_file()
        elif response is None:
            return False
        return True

    def new_file(self):
        if self.check_save():
            self.text_area.delete(1.0, tk.END)
            self.current_file = None
            self.update_title()
            self.status_bar.config(text="New file")

    def open_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
        if file_path and self.check_save():
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, file.read())
                self.current_file = file_path
                self.update_title()
                self.status_bar.config(text=f"Opened: {os.path.basename(file_path)}")
                self.add_recent_file(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def update_title(self):
        if self.current_file:
            self.root.title(f"Text Editor - {os.path.basename(self.current_file)}")
        else:
            self.root.title("Text Editor - Untitled")

    def start_auto_save(self):
        if self.auto_save and self.current_file:
            self.save_file()
        self.root.after(self.auto_save_interval, self.start_auto_save)

    def toggle_auto_save(self):
        self.auto_save = not self.auto_save
        if self.auto_save:
            self.start_auto_save()

    def print_file(self):
        try:
            if platform.system() != 'Windows':
                messagebox.showerror("Error", "Printing is only supported on Windows")
                return

            printer = filedialog.askstring("Print", "Enter printer name:")
            if not printer:
                return
                
            text = self.text_area.get("1.0", tk.END)
            
            temp_file = "temp_print.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            os.startfile(temp_file, "print")
            self.root.after(2000, lambda: os.remove(temp_file))
            messagebox.showinfo("Print", "Print job sent to printer")
            
        except Exception as e:
            messagebox.showerror("Print Error", str(e))
            
    def toggle_word_wrap(self):
        self.text_area.configure(wrap=tk.NONE if self.text_area.cget("wrap") == tk.WORD else tk.WORD)
            
    def toggle_line_numbers(self):
        if self.line_numbers.winfo_viewable():
            self.line_numbers.pack_forget()
        else:
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            
    def show_word_count(self):
        text = self.text_area.get("1.0", tk.END)
        words = len(text.split())
        chars = len(text)
        lines = text.count('\n')
        
        messagebox.showinfo(
            "Word Count",
            f"Words: {words}\nCharacters: {chars}\nLines: {lines}"
        )
        
    def load_recent_files(self):
        try:
            with open("recent_files.json", "r", encoding='utf-8') as f:
                self.recent_files = json.load(f)
                self.update_recent_menu()
        except:
            self.recent_files = []
            
    def save_recent_files(self):
        with open("recent_files.json", "w", encoding='utf-8') as f:
            json.dump(self.recent_files, f)
            
    def update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for file_path in self.recent_files:
            self.recent_menu.add_command(
                label=os.path.basename(file_path),
                command=lambda f=file_path: self.open_recent_file(f)
            )
            
    def add_recent_file(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self.update_recent_menu()
        self.save_recent_files()
        
    def open_recent_file(self, file_path):
        if os.path.exists(file_path):
            self.open_file(file_path)
        else:
            messagebox.showerror("Error", "File not found")
            self.recent_files.remove(file_path)
            self.update_recent_menu()
            self.save_recent_files()

    def show_find_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Find")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Find:").pack(pady=5)
        find_var = tk.StringVar()
        find_entry = ttk.Entry(dialog, textvariable=find_var)
        find_entry.pack(pady=5)
        
        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Case sensitive", variable=case_var).pack()
        
        def find_next():
            search_text = find_var.get()
            if not search_text:
                return
                
            start_pos = self.text_area.index(tk.INSERT)
            
            if case_var.get():
                pos = self.text_area.search(search_text, start_pos)
            else:
                pos = self.text_area.search(search_text, start_pos, nocase=True)
                
            if pos:
                end_pos = f"{pos}+{len(search_text)}c"
                self.text_area.tag_remove("sel", "1.0", tk.END)
                self.text_area.tag_add("sel", pos, end_pos)
                self.text_area.see(pos)
            else:
                messagebox.showinfo("Find", "Text not found")
        
        ttk.Button(dialog, text="Find Next", command=find_next).pack(pady=10)
        
    def show_replace_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Replace")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Find:").pack(pady=5)
        find_var = tk.StringVar()
        find_entry = ttk.Entry(dialog, textvariable=find_var)
        find_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Replace with:").pack(pady=5)
        replace_var = tk.StringVar()
        replace_entry = ttk.Entry(dialog, textvariable=replace_var)
        replace_entry.pack(pady=5)
        
        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Case sensitive", variable=case_var).pack()
        
        def find_next():
            search_text = find_var.get()
            if not search_text:
                return
                
            start_pos = self.text_area.index(tk.INSERT)
            
            if case_var.get():
                pos = self.text_area.search(search_text, start_pos)
            else:
                pos = self.text_area.search(search_text, start_pos, nocase=True)
                
            if pos:
                end_pos = f"{pos}+{len(search_text)}c"
                self.text_area.tag_remove("sel", "1.0", tk.END)
                self.text_area.tag_add("sel", pos, end_pos)
                self.text_area.see(pos)
            else:
                messagebox.showinfo("Find", "Text not found")
        
        def replace():
            if self.text_area.tag_ranges("sel"):
                self.text_area.delete("sel.first", "sel.last")
                self.text_area.insert("sel.first", replace_var.get())
                find_next()
        
        def replace_all():
            search_text = find_var.get()
            if not search_text:
                return
                
            text = self.text_area.get("1.0", tk.END)
            
            if case_var.get():
                new_text = text.replace(search_text, replace_var.get())
            else:
                new_text = re.sub(re.escape(search_text), replace_var.get(), text, flags=re.IGNORECASE)
            
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", new_text)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Find Next", command=find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace", command=replace).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace All", command=replace_all).pack(side=tk.LEFT, padx=5)
        
    def update_status(self, event=None):
        if self.status_update_id:
            self.root.after_cancel(self.status_update_id)
        self.status_update_id = self.root.after(200, self._update_status)

    def _update_status(self):
        self.status_update_id = None
        cursor_pos = self.text_area.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        text = self.text_area.get('1.0', 'end-1c')
        words = len(text.split()) if text else 0
        chars = len(text)
        self.status_bar.config(text=f"Line: {line} | Column: {col} | Words: {words} | Chars: {chars}")

    def apply_format_to_new_text(self, event=None):
        if self.format_start_mark and self.current_format_tags:
            current_pos = self.text_area.index("insert")
            for tag in self.current_format_tags:
                self.text_area.tag_add(tag, self.format_start_mark, current_pos)
                
    def clear_format_mark(self, event=None):
        self.format_start_mark = None
        self.current_format_tags.clear()

    def show_font_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Font")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Font Family:").pack(pady=5)
        font_family_var = tk.StringVar(value=self.current_font_family)
        font_family_combo = ttk.Combobox(
            dialog,
            textvariable=font_family_var,
            values=sorted(font.families()),
            state="readonly"
        )
        font_family_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Font Size:").pack(pady=5)
        font_size_var = tk.StringVar(value=str(self.current_font_size))
        font_size_combo = ttk.Combobox(
            dialog,
            textvariable=font_size_var,
            values=["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"],
            state="readonly"
        )
        font_size_combo.pack(pady=5)
        
        def apply_font():
            self.current_font_family = font_family_var.get()
            self.current_font_size = int(font_size_var.get())
            self.update_font()
            dialog.destroy()
        
        ttk.Button(dialog, text="Apply", command=apply_font).pack(pady=10)
        
    def show_color_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Text Color")
        dialog.geometry("300x200")
        
        colors = ["Black", "Red", "Green", "Blue", "Yellow", "Purple", "Orange"]
        color_var = tk.StringVar(value="Black")
        
        for color in colors:
            ttk.Radiobutton(
                dialog,
                text=color,
                value=color,
                variable=color_var
            ).pack(pady=5)
        
        def apply_color():
            try:
                if self.text_area.tag_ranges("sel"):
                    start, end = "sel.first", "sel.last"
                else:
                    start, end = "1.0", tk.END
                
                for color in colors:
                    self.text_area.tag_remove(color.lower(), start, end)
                
                self.text_area.tag_add(color_var.get().lower(), start, end)
                self.text_area.tag_config(color_var.get().lower(), foreground=color_var.get().lower())
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could apply color: {str(e)}")
        
        ttk.Button(dialog, text="Apply", command=apply_color).pack(pady=10)
        
    def change_font_family(self, event=None):
        self.current_font_family = self.font_family_var.get()
        self.update_font()
        
    def change_font_size(self, event=None):
        self.current_font_size = int(self.font_size_var.get())
        self.update_font()
        
    def update_font(self):
        new_font = font.Font(
            family=self.current_font_family,
            size=self.current_font_size,
            weight="normal",
            slant="roman"
        )
        
        self.current_font = new_font
        self.text_area.configure(font=self.current_font)
        
        self.text_area.tag_configure("bold", font=font.Font(
            family=self.current_font_family,
            size=self.current_font_size,
            weight="bold"
        ))
        self.text_area.tag_configure("italic", font=font.Font(
            family=self.current_font_family,
            size=self.current_font_size,
            slant="italic"
        ))
        
    def _toggle_tag(self, tag_name, var):
        try:
            if self.text_area.tag_ranges("sel"):
                start, end = "sel.first", "sel.last"
                self.format_start_mark = None
            else:
                start = end = "insert"
                self.format_start_mark = start

            current_tags = self.text_area.tag_names(start)
            if tag_name in current_tags:
                self.text_area.tag_remove(tag_name, start, end)
                var.set(False)
                self.current_format_tags.discard(tag_name)
            else:
                self.text_area.tag_add(tag_name, start, end)
                var.set(True)
                self.current_format_tags.add(tag_name)
        except Exception as e:
            print(f"Error toggling tag: {e}")

    def toggle_bold(self):
        self._toggle_tag("bold", self.bold_var)

    def toggle_italic(self):
        self._toggle_tag("italic", self.italic_var)

    def toggle_underline(self):
        self._toggle_tag("underline", self.underline_var)

    def update_format_buttons(self, event=None):
        try:
            if self.text_area.tag_ranges("sel"):
                pos = "sel.first"
            else:
                pos = "insert"
            
            current_tags = self.text_area.tag_names(pos)
            
            self.bold_var.set("bold" in current_tags)
            self.italic_var.set("italic" in current_tags)
            self.underline_var.set("underline" in current_tags)
            
        except Exception as e:
            print(f"Error updating format buttons: {e}")

    def update_line_numbers(self, event=None):
        if self.line_number_update_id:
            self.root.after_cancel(self.line_number_update_id)
        self.line_number_update_id = self.root.after(200, self._update_line_numbers)

    def _update_line_numbers(self):
        self.line_number_update_id = None
        end_index = self.text_area.index('end-1c')
        line_count = int(end_index.split('.')[0]) if end_index != '1.0' else 1
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert(tk.END, '\n'.join(str(i) for i in range(1, line_count + 1)))
        self.line_numbers.config(state='disabled')

    def show_about(self):
        messagebox.showinfo(
            "About Text Editor",
            "Text Editor\nVersion 1.0\n\nA feature-rich text editor with formatting options, "
            "find/replace, and auto-save functionality."
        )

def main():
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()