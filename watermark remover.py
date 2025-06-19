import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, ttk
from ttkbootstrap import Style
from ttkbootstrap.widgets import Button, Label, Frame, Meter, Checkbutton, Scale
import os
from PIL import Image, ImageTk
import json
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import queue

class WatermarkRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watermark Remover Pro")
        self.root.geometry("1280x900")
        self.root.minsize(1024, 800)
        self.style = Style(theme='darkly')
        self.program_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Inicjalizacja logowania
        self.setup_logging()
        
        # Zmienne
        self.input_path = None
        self.input_paths = []  # Dla batch processing
        self.custom_areas = []
        self.first_frame = None
        self.processing_cancelled = False
        self.processing_thread = None
        self.preview_window = None
        self.frame_queue = queue.Queue(maxsize=10)
        
        # Główna ramka
        self.main_frame = Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nagłówek
        self.header_label = Label(self.main_frame, text="Watermark Remover Pro by Swir", 
                                 font=("Helvetica", 18, "bold"))
        self.header_label.pack(pady=10)
        
        # Tworzenie interfejsu z zakładkami
        self.create_tabbed_interface()
        
        # Pasek postępu i status
        self.create_progress_section()
        
        # Przyciski akcji
        self.create_action_buttons()
        
        logging.info("Aplikacja uruchomiona")
    
    def setup_logging(self):
        """Konfiguracja systemu logowania"""
        log_filename = f'watermark_remover_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def create_tabbed_interface(self):
        """Tworzenie interfejsu z zakładkami"""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Zakładka główna
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Główne")
        self.create_main_tab()
        
        # Zakładka ustawień
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Ustawienia")
        self.create_settings_tab()
        
        # Zakładka zaawansowana
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_tab, text="Zaawansowane")
        self.create_advanced_tab()
        
        # Zakładka batch
        self.batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_tab, text="Przetwarzanie wsadowe")
        self.create_batch_tab()
    
    def create_main_tab(self):
        """Tworzenie głównej zakładki"""
        # Sekcja wyboru pliku
        file_frame = Frame(self.main_tab, padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.select_button = Button(file_frame, text="Wybierz plik wideo", 
                                   command=self.select_file, bootstyle="primary")
        self.select_button.pack(side=tk.LEFT, padx=5)
        
        self.file_label = Label(file_frame, text="Nie wybrano pliku", wraplength=400)
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Sekcja wyboru rogów
        corners_frame = Frame(self.main_tab, padding=10)
        corners_frame.pack(fill=tk.X, pady=5)
        
        Label(corners_frame, text="Domyślne obszary:", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        self.bottom_right_var = tk.BooleanVar(value=True)
        self.top_left_var = tk.BooleanVar(value=False)
        self.bottom_left_var = tk.BooleanVar(value=False)
        self.top_right_var = tk.BooleanVar(value=False)
        
        corners_grid = Frame(corners_frame)
        corners_grid.pack(pady=5)
        
        Checkbutton(corners_grid, text="Prawy dolny róg", 
                   variable=self.bottom_right_var).grid(row=0, column=0, padx=5, sticky=tk.W)
        Checkbutton(corners_grid, text="Lewy górny róg", 
                   variable=self.top_left_var).grid(row=0, column=1, padx=5, sticky=tk.W)
        Checkbutton(corners_grid, text="Lewy dolny róg", 
                   variable=self.bottom_left_var).grid(row=1, column=0, padx=5, sticky=tk.W)
        Checkbutton(corners_grid, text="Prawy górny róg", 
                   variable=self.top_right_var).grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # Przyciski ręcznego ustawienia
        custom_frame = Frame(self.main_tab, padding=10)
        custom_frame.pack(fill=tk.X, pady=5)
        
        self.custom_button = Button(custom_frame, text="Ręczne ustawienie obszaru", 
                                   command=self.open_custom_area_window, bootstyle="info")
        self.custom_button.pack(side=tk.LEFT, padx=5)
        
        self.save_areas_button = Button(custom_frame, text="Zapisz obszary", 
                                       command=self.save_areas_to_file, bootstyle="secondary")
        self.save_areas_button.pack(side=tk.LEFT, padx=5)
        
        self.load_areas_button = Button(custom_frame, text="Wczytaj obszary", 
                                       command=self.load_areas_from_file, bootstyle="secondary")
        self.load_areas_button.pack(side=tk.LEFT, padx=5)
        
        # Informacja o obszarach
        self.areas_info_label = Label(self.main_tab, text="Brak ręcznych obszarów", 
                                     font=("Helvetica", 10))
        self.areas_info_label.pack(pady=5)
    
    def create_settings_tab(self):
        """Tworzenie zakładki ustawień"""
        # Ustawienia algorytmu
        algo_frame = Frame(self.settings_tab, padding=10)
        algo_frame.pack(fill=tk.X, pady=10)
        
        Label(algo_frame, text="Ustawienia algorytmu:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        # Metoda inpaintingu
        method_frame = Frame(algo_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        Label(method_frame, text="Metoda wypełniania:").pack(side=tk.LEFT, padx=5)
        
        self.inpaint_method = tk.StringVar(value="mixed")
        methods = [("Mieszana", "mixed"), ("Telea", "telea"), ("Navier-Stokes", "ns")]
        
        for text, value in methods:
            tk.Radiobutton(method_frame, text=text, variable=self.inpaint_method, 
                          value=value).pack(side=tk.LEFT, padx=5)
        
        # Siła rozmycia
        blur_frame = Frame(algo_frame)
        blur_frame.pack(fill=tk.X, pady=5)
        
        Label(blur_frame, text="Siła rozmycia:").pack(side=tk.LEFT, padx=5)
        self.blur_strength = tk.IntVar(value=11)
        Scale(blur_frame, from_=1, to=31, variable=self.blur_strength, 
              orient=tk.HORIZONTAL, length=300).pack(side=tk.LEFT, padx=5)
        Label(blur_frame, textvariable=self.blur_strength).pack(side=tk.LEFT)
        
        # Rozmiar marginesu
        margin_frame = Frame(algo_frame)
        margin_frame.pack(fill=tk.X, pady=5)
        
        Label(margin_frame, text="Margines obszaru:").pack(side=tk.LEFT, padx=5)
        self.margin_size = tk.IntVar(value=20)
        Scale(margin_frame, from_=0, to=50, variable=self.margin_size, 
              orient=tk.HORIZONTAL, length=300).pack(side=tk.LEFT, padx=5)
        Label(margin_frame, textvariable=self.margin_size).pack(side=tk.LEFT)
        
        # Ustawienia wydajności
        perf_frame = Frame(self.settings_tab, padding=10)
        perf_frame.pack(fill=tk.X, pady=10)
        
        Label(perf_frame, text="Ustawienia wydajności:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        # Liczba wątków
        threads_frame = Frame(perf_frame)
        threads_frame.pack(fill=tk.X, pady=5)
        
        Label(threads_frame, text="Liczba wątków:").pack(side=tk.LEFT, padx=5)
        self.thread_count = tk.IntVar(value=4)
        Scale(threads_frame, from_=1, to=8, variable=self.thread_count, 
              orient=tk.HORIZONTAL, length=300).pack(side=tk.LEFT, padx=5)
        Label(threads_frame, textvariable=self.thread_count).pack(side=tk.LEFT)
        
        # Hardware acceleration
        self.use_hw_accel = tk.BooleanVar(value=True)
        Checkbutton(perf_frame, text="Użyj akceleracji sprzętowej (jeśli dostępna)", 
                   variable=self.use_hw_accel).pack(anchor=tk.W, pady=5)
        
        # Buforowanie klatek
        self.use_buffering = tk.BooleanVar(value=True)
        Checkbutton(perf_frame, text="Włącz buforowanie klatek", 
                   variable=self.use_buffering).pack(anchor=tk.W, pady=5)
    
    def create_advanced_tab(self):
        """Tworzenie zakładki zaawansowanej"""
        # Post-processing
        post_frame = Frame(self.advanced_tab, padding=10)
        post_frame.pack(fill=tk.X, pady=10)
        
        Label(post_frame, text="Przetwarzanie końcowe:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        self.denoise_var = tk.BooleanVar(value=False)
        Checkbutton(post_frame, text="Redukcja szumów", 
                   variable=self.denoise_var).pack(anchor=tk.W, pady=2)
        
        self.sharpen_var = tk.BooleanVar(value=False)
        Checkbutton(post_frame, text="Wyostrzanie", 
                   variable=self.sharpen_var).pack(anchor=tk.W, pady=2)
        
        self.color_correction_var = tk.BooleanVar(value=False)
        Checkbutton(post_frame, text="Automatyczna korekcja kolorów", 
                   variable=self.color_correction_var).pack(anchor=tk.W, pady=2)
        
        # Podgląd
        preview_frame = Frame(self.advanced_tab, padding=10)
        preview_frame.pack(fill=tk.X, pady=10)
        
        Label(preview_frame, text="Opcje podglądu:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        self.show_preview_var = tk.BooleanVar(value=True)
        Checkbutton(preview_frame, text="Pokaż podgląd podczas przetwarzania", 
                   variable=self.show_preview_var).pack(anchor=tk.W, pady=2)
        
        preview_freq_frame = Frame(preview_frame)
        preview_freq_frame.pack(fill=tk.X, pady=5)
        
        Label(preview_freq_frame, text="Częstotliwość podglądu (klatki):").pack(side=tk.LEFT, padx=5)
        self.preview_frequency = tk.IntVar(value=30)
        Scale(preview_freq_frame, from_=10, to=100, variable=self.preview_frequency, 
              orient=tk.HORIZONTAL, length=300).pack(side=tk.LEFT, padx=5)
        Label(preview_freq_frame, textvariable=self.preview_frequency).pack(side=tk.LEFT)
        
        # Format wyjściowy
        output_frame = Frame(self.advanced_tab, padding=10)
        output_frame.pack(fill=tk.X, pady=10)
        
        Label(output_frame, text="Format wyjściowy:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        codec_frame = Frame(output_frame)
        codec_frame.pack(fill=tk.X, pady=5)
        
        Label(codec_frame, text="Kodek:").pack(side=tk.LEFT, padx=5)
        self.output_codec = tk.StringVar(value="mp4v")
        codecs = [("MP4V", "mp4v"), ("H264", "h264"), ("XVID", "xvid")]
        
        for text, value in codecs:
            tk.Radiobutton(codec_frame, text=text, variable=self.output_codec, 
                          value=value).pack(side=tk.LEFT, padx=5)
    
    def create_batch_tab(self):
        """Tworzenie zakładki przetwarzania wsadowego"""
        # Lista plików
        files_frame = Frame(self.batch_tab, padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(files_frame, text="Pliki do przetworzenia:", 
              font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        
        # Ramka z listą i scrollbarem
        list_frame = Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Przyciski batch
        batch_buttons = Frame(files_frame)
        batch_buttons.pack(fill=tk.X, pady=5)
        
        Button(batch_buttons, text="Dodaj pliki", command=self.add_batch_files, 
               bootstyle="primary").pack(side=tk.LEFT, padx=5)
        Button(batch_buttons, text="Usuń zaznaczone", command=self.remove_batch_files, 
               bootstyle="danger").pack(side=tk.LEFT, padx=5)
        Button(batch_buttons, text="Wyczyść listę", command=self.clear_batch_files, 
               bootstyle="warning").pack(side=tk.LEFT, padx=5)
        
        # Opcje batch
        batch_options = Frame(self.batch_tab, padding=10)
        batch_options.pack(fill=tk.X)
        
        self.batch_same_areas = tk.BooleanVar(value=True)
        Checkbutton(batch_options, text="Użyj tych samych obszarów dla wszystkich plików", 
                   variable=self.batch_same_areas).pack(anchor=tk.W)
        
        self.batch_parallel = tk.BooleanVar(value=False)
        Checkbutton(batch_options, text="Przetwarzaj pliki równolegle (wymaga dużo RAM)", 
                   variable=self.batch_parallel).pack(anchor=tk.W)
    
    def create_progress_section(self):
        """Tworzenie sekcji postępu"""
        progress_frame = Frame(self.main_frame, padding=10)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = Label(progress_frame, text="Gotowy", wraplength=600)
        self.status_label.pack(pady=5)
        
        self.progress_meter = Meter(progress_frame, bootstyle="success", 
                                   subtext="Postęp", interactive=False, 
                                   amounttotal=100, amountused=0)
        self.progress_meter.pack(pady=5)
        
        # Szczegółowe informacje o postępie
        self.detail_label = Label(progress_frame, text="", font=("Helvetica", 9))
        self.detail_label.pack(pady=2)
    
    def create_action_buttons(self):
        """Tworzenie przycisków akcji"""
        action_frame = Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = Button(action_frame, text="Przetwarzaj wideo", 
                                    command=self.start_processing, 
                                    state=tk.DISABLED, bootstyle="success")
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        self.batch_process_button = Button(action_frame, text="Przetwarzaj wsadowo", 
                                          command=self.start_batch_processing, 
                                          state=tk.DISABLED, bootstyle="success")
        self.batch_process_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = Button(action_frame, text="Anuluj", 
                                   command=self.cancel_processing, 
                                   state=tk.DISABLED, bootstyle="danger")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.preview_button = Button(action_frame, text="Podgląd", 
                                    command=self.toggle_preview, 
                                    state=tk.DISABLED, bootstyle="info")
        self.preview_button.pack(side=tk.LEFT, padx=5)
    
    def select_file(self):
        """Wybór pojedynczego pliku"""
        self.input_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov")]
        )
        if self.input_path:
            self.file_label.config(text=f"Wybrano: {os.path.basename(self.input_path)}")
            self.process_button.config(state=tk.NORMAL)
            self.load_first_frame()
            logging.info(f"Wybrano plik: {self.input_path}")
        else:
            self.file_label.config(text="Nie wybrano pliku")
            self.process_button.config(state=tk.DISABLED)
    
    def load_first_frame(self):
        """Wczytaj pierwszą klatkę wideo"""
        try:
            cap = cv2.VideoCapture(self.input_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                self.first_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                self.first_frame = None
                logging.warning("Nie udało się wczytać pierwszej klatki")
        except Exception as e:
            logging.error(f"Błąd wczytywania pierwszej klatki: {e}")
            self.first_frame = None
    
    def open_custom_area_window(self):
        """Otwórz okno do ręcznego rysowania obszarów"""
        if not self.input_path or self.first_frame is None:
            messagebox.showwarning("Ostrzeżenie", "Proszę najpierw wybrać plik wideo!")
            return
        
        self.custom_areas = []
        self.custom_window = Toplevel(self.root)
        self.custom_window.title("Rysuj obszary zamazywania")
        self.custom_window.geometry("1024x800")
        
        # Instrukcje
        instructions = Label(self.custom_window, 
                           text="Kliknij i przeciągnij, aby narysować prostokąty. " +
                                "Kliknij prawym przyciskiem, aby usunąć ostatni prostokąt.",
                           font=("Helvetica", 10))
        instructions.pack(pady=5)
        
        # Skaluj obraz do podglądu
        height, width = self.first_frame.shape[:2]
        max_size = 600
        scale = min(max_size / width, max_size / height)
        self.preview_scale = scale
        preview_width = int(width * scale)
        preview_height = int(height * scale)
        preview_frame = cv2.resize(self.first_frame, (preview_width, preview_height))
        
        # Canvas
        self.canvas = tk.Canvas(self.custom_window, width=preview_width, 
                               height=preview_height, bg='gray')
        self.canvas.pack(pady=10)
        
        # Konwertuj obraz
        img = Image.fromarray(preview_frame)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Zmienne do rysowania
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.drawn_rects = []
        
        # Bindowanie zdarzeń
        self.canvas.bind("<Button-1>", self.start_rectangle)
        self.canvas.bind("<B1-Motion>", self.update_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_rectangle)
        self.canvas.bind("<Button-3>", self.remove_last_rectangle)
        
        # Przyciski
        button_frame = Frame(self.custom_window)
        button_frame.pack(pady=10)
        
        Button(button_frame, text="Zapisz obszary", command=self.save_custom_areas, 
               bootstyle="success").pack(side=tk.LEFT, padx=5)
        Button(button_frame, text="Wyczyść wszystko", command=self.clear_custom_areas, 
               bootstyle="warning").pack(side=tk.LEFT, padx=5)
        Button(button_frame, text="Anuluj", command=self.custom_window.destroy, 
               bootstyle="danger").pack(side=tk.LEFT, padx=5)
    
    def start_rectangle(self, event):
        """Rozpocznij rysowanie prostokąta"""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline="red", width=2
        )
    
    def update_rectangle(self, event):
        """Aktualizuj rysowany prostokąt"""
        if self.current_rect:
            curr_x = self.canvas.canvasx(event.x)
            curr_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, curr_x, curr_y)
    
    def end_rectangle(self, event):
        """Zakończ rysowanie prostokąta"""
        if self.current_rect:
            curr_x = self.canvas.canvasx(event.x)
            curr_y = self.canvas.canvasy(event.y)
            x1, y1 = min(self.start_x, curr_x), min(self.start_y, curr_y)
            x2, y2 = max(self.start_x, curr_x), max(self.start_y, curr_y)
            
            # Przeskaluj do oryginalnych rozmiarów
            cap = cv2.VideoCapture(self.input_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            orig_x1 = int(x1 / self.preview_scale)
            orig_y1 = int(y1 / self.preview_scale)
            orig_w = int((x2 - x1) / self.preview_scale)
            orig_h = int((y2 - y1) / self.preview_scale)
            
            if orig_w > 10 and orig_h > 10:  # Minimalny rozmiar
                self.custom_areas.append((orig_x1, orig_y1, orig_w, orig_h))
                self.drawn_rects.append(self.current_rect)
                # Zmień kolor na zielony po zapisaniu
                self.canvas.itemconfig(self.current_rect, outline="green")
    
    def remove_last_rectangle(self, event):
        """Usuń ostatni narysowany prostokąt"""
        if self.drawn_rects and self.custom_areas:
            rect_to_remove = self.drawn_rects.pop()
            self.canvas.delete(rect_to_remove)
            self.custom_areas.pop()
    
    def save_custom_areas(self):
        """Zapisz ręcznie zdefiniowane obszary"""
        self.custom_window.destroy()
        self.update_areas_info()
        messagebox.showinfo("Sukces", f"Zapisano {len(self.custom_areas)} obszarów.")
        logging.info(f"Zapisano {len(self.custom_areas)} ręcznych obszarów")
    
    def clear_custom_areas(self):
        """Wyczyść wszystkie obszary na canvas"""
        self.custom_areas = []
        self.drawn_rects = []
        self.canvas.delete("all")
        # Przywróć obraz
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
    
    def update_areas_info(self):
        """Aktualizuj informację o obszarach"""
        corners_count = sum([
            self.bottom_right_var.get(),
            self.top_left_var.get(),
            self.bottom_left_var.get(),
            self.top_right_var.get()
        ])
        custom_count = len(self.custom_areas)
        
        info_text = f"Aktywne obszary: {corners_count} rogów, {custom_count} ręcznych"
        self.areas_info_label.config(text=info_text)
    
    def save_areas_to_file(self):
        """Zapisz obszary do pliku JSON"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            try:
                data = {
                    "areas": self.custom_areas,
                    "corners": {
                        "bottom_right": self.bottom_right_var.get(),
                        "top_left": self.top_left_var.get(),
                        "bottom_left": self.bottom_left_var.get(),
                        "top_right": self.top_right_var.get()
                    },
                    "settings": {
                        "inpaint_method": self.inpaint_method.get(),
                        "blur_strength": self.blur_strength.get(),
                        "margin_size": self.margin_size.get()
                    }
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Sukces", "Obszary zostały zapisane!")
                logging.info(f"Zapisano obszary do: {filepath}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zapisać pliku: {e}")
                logging.error(f"Błąd zapisu obszarów: {e}")
    
    def load_areas_from_file(self):
        """Wczytaj obszary z pliku JSON"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                self.custom_areas = data.get("areas", [])
                corners = data.get("corners", {})
                self.bottom_right_var.set(corners.get("bottom_right", False))
                self.top_left_var.set(corners.get("top_left", False))
                self.bottom_left_var.set(corners.get("bottom_left", False))
                self.top_right_var.set(corners.get("top_right", False))
                
                # Wczytaj ustawienia jeśli istnieją
                if "settings" in data:
                    settings = data["settings"]
                    self.inpaint_method.set(settings.get("inpaint_method", "mixed"))
                    self.blur_strength.set(settings.get("blur_strength", 11))
                    self.margin_size.set(settings.get("margin_size", 20))
                
                self.update_areas_info()
                messagebox.showinfo("Sukces", "Obszary zostały wczytane!")
                logging.info(f"Wczytano obszary z: {filepath}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wczytać pliku: {e}")
                logging.error(f"Błąd wczytywania obszarów: {e}")
    
    def add_batch_files(self):
        """Dodaj pliki do przetwarzania wsadowego"""
        files = filedialog.askopenfilenames(
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov")]
        )
        for file in files:
            if file not in self.input_paths:
                self.input_paths.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
        
        if self.input_paths:
            self.batch_process_button.config(state=tk.NORMAL)
    
    def remove_batch_files(self):
        """Usuń zaznaczone pliki z listy"""
        selected = self.files_listbox.curselection()
        for index in reversed(selected):
            self.files_listbox.delete(index)
            del self.input_paths[index]
        
        if not self.input_paths:
            self.batch_process_button.config(state=tk.DISABLED)
    
    def clear_batch_files(self):
        """Wyczyść całą listę plików"""
        self.files_listbox.delete(0, tk.END)
        self.input_paths = []
        self.batch_process_button.config(state=tk.DISABLED)
    
    def get_watermark_areas(self, frame, corners):
        """Zwraca obszary maskowania"""
        height, width = frame.shape[:2]
        watermark_areas = self.custom_areas.copy()
        
        if "bottom_right" in corners:
            default_x = int(width * 0.75)
            default_y = int(height * 0.75)
            default_w = int(width * 0.25)
            default_h = int(height * 0.25)
            watermark_areas.append((default_x, default_y, default_w, default_h))
        
        if "top_left" in corners:
            default_x_top = 0
            default_y_top = 0
            default_w_top = int(width * 0.2)
            default_h_top = int(height * 0.2)
            watermark_areas.append((default_x_top, default_y_top, default_w_top, default_h_top))
        
        if "bottom_left" in corners:
            default_x_bottom = 0
            default_y_bottom = int(height * 0.8)
            default_w_bottom = int(width * 0.2)
            default_h_bottom = int(height * 0.2)
            watermark_areas.append((default_x_bottom, default_y_bottom, default_w_bottom, default_h_bottom))
        
        if "top_right" in corners:
            default_x_top_right = int(width * 0.8)
            default_y_top_right = 0
            default_w_top_right = int(width * 0.2)
            default_h_top_right = int(height * 0.2)
            watermark_areas.append((default_x_top_right, default_y_top_right, default_w_top_right, default_h_top_right))
        
        return watermark_areas
    
    def remove_watermark_advanced(self, frame, watermark_areas):
        """Ulepszona metoda usuwania znaków wodnych"""
        result = frame.copy()
        margin = self.margin_size.get()
        
        for (x, y, w, h) in watermark_areas:
            # Rozszerz obszar analizy
            x1, y1 = max(0, x - margin), max(0, y - margin)
            x2, y2 = min(frame.shape[1], x + w + margin), min(frame.shape[0], y + h + margin)
            
            # Wytnij obszar roboczy
            working_area = frame[y1:y2, x1:x2].copy()
            
            # Tworzenie maski
            mask = np.zeros(working_area.shape[:2], dtype=np.uint8)
            mask_x1 = x - x1
            mask_y1 = y - y1
            mask_x2 = mask_x1 + w
            mask_y2 = mask_y1 + h
            cv2.rectangle(mask, (mask_x1, mask_y1), (mask_x2, mask_y2), 255, -1)
            
            # Wybór metody inpaintingu
            method = self.inpaint_method.get()
            if method == "telea":
                inpainted = cv2.inpaint(working_area, mask, 7, cv2.INPAINT_TELEA)
            elif method == "ns":
                inpainted = cv2.inpaint(working_area, mask, 7, cv2.INPAINT_NS)
            else:  # mixed
                # Analiza tekstury
                gray = cv2.cvtColor(working_area, cv2.COLOR_BGR2GRAY)
                texture_score = np.std(gray)
                
                if texture_score > 30:
                    inpainted = cv2.inpaint(working_area, mask, 7, cv2.INPAINT_TELEA)
                else:
                    inpainted_ns = cv2.inpaint(working_area, mask, 7, cv2.INPAINT_NS)
                    inpainted_telea = cv2.inpaint(working_area, mask, 7, cv2.INPAINT_TELEA)
                    inpainted = cv2.addWeighted(inpainted_ns, 0.5, inpainted_telea, 0.5, 0)
            
            # Dodatkowe rozmycie na obszarze znaku wodnego
            blur_strength = self.blur_strength.get()
            if blur_strength > 1:
                roi = inpainted[mask_y1:mask_y2, mask_x1:mask_x2]
                blurred_roi = cv2.bilateralFilter(roi, d=blur_strength, sigmaColor=100, sigmaSpace=100)
                inpainted[mask_y1:mask_y2, mask_x1:mask_x2] = blurred_roi
            
            # Gradient blending
            blend_mask = np.zeros(working_area.shape[:2], dtype=np.float32)
            cv2.rectangle(blend_mask, (mask_x1, mask_y1), (mask_x2, mask_y2), 1.0, -1)
            blend_mask = cv2.GaussianBlur(blend_mask, (31, 31), 0)
            
            # Rozszerz blend_mask do 3 kanałów
            blend_mask_3ch = np.stack([blend_mask] * 3, axis=-1)
            
            # Mieszanie
            blended = (inpainted * blend_mask_3ch + working_area * (1 - blend_mask_3ch)).astype(np.uint8)
            
            # Wstaw z powrotem do obrazu
            result[y1:y2, x1:x2] = blended
        
        return result
    
    def apply_post_processing(self, frame):
        """Zastosuj przetwarzanie końcowe"""
        result = frame.copy()
        
        if self.denoise_var.get():
            result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
        
        if self.sharpen_var.get():
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            result = cv2.filter2D(result, -1, kernel)
        
        if self.color_correction_var.get():
            # Konwersja do LAB
            lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Wyrównanie histogramu kanału L
            l = cv2.equalizeHist(l)
            
            # Złączenie i konwersja z powrotem
            result = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        
        return result
    
    def create_preview_window(self):
        """Utwórz okno podglądu"""
        if self.preview_window is None:
            self.preview_window = Toplevel(self.root)
            self.preview_window.title("Podgląd przetwarzania")
            self.preview_window.geometry("900x650")
            self.preview_window.protocol("WM_DELETE_WINDOW", self.close_preview)
            
            self.preview_label = Label(self.preview_window)
            self.preview_label.pack(pady=10)
            
            self.preview_info = Label(self.preview_window, text="", font=("Helvetica", 10))
            self.preview_info.pack(pady=5)
    
    def update_preview(self, frame, frame_number, total_frames):
        """Aktualizuj okno podglądu"""
        if self.preview_window is None or not self.show_preview_var.get():
            return
        
        try:
            # Zmniejsz rozmiar dla podglądu
            height, width = frame.shape[:2]
            scale = 500 / max(width, height)
            preview_width = int(width * scale)
            preview_height = int(height * scale)
            preview = cv2.resize(frame, (preview_width, preview_height))
            
            # Konwertuj do RGB i utwórz obraz
            preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(preview_rgb)
            photo = ImageTk.PhotoImage(img)
            
            # Aktualizuj w głównym wątku
            self.root.after(0, lambda: self._update_preview_display(photo, frame_number, total_frames))
        except Exception as e:
            logging.error(f"Błąd aktualizacji podglądu: {e}")
    
    def _update_preview_display(self, photo, frame_number, total_frames):
        """Aktualizuj wyświetlanie podglądu (w głównym wątku)"""
        if self.preview_window and self.preview_label.winfo_exists():
            self.preview_label.config(image=photo)
            self.preview_label.photo = photo  # Zachowaj referencję
            self.preview_info.config(text=f"Klatka {frame_number}/{total_frames}")
    
    def toggle_preview(self):
        """Przełącz widoczność okna podglądu"""
        if self.preview_window is None:
            self.create_preview_window()
        else:
            self.close_preview()
    
    def close_preview(self):
        """Zamknij okno podglądu"""
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
    
    def process_video_optimized(self, input_path, output_path, corners):
        """Zoptymalizowana metoda przetwarzania wideo"""
        try:
            self.update_status("Otwieranie wideo...")
            
            # Otwórz wideo z opcjonalną akceleracją sprzętową
            cap = cv2.VideoCapture(input_path)
            if self.use_hw_accel.get():
                cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
            
            # Pobierz parametry wideo
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0:
                raise Exception("Wideo nie zawiera klatek lub jest uszkodzone.")
            
            logging.info(f"Wideo: {width}x{height}, {fps} FPS, {total_frames} klatek")
            
            # Konfiguracja kodeka
            codec_map = {
                'mp4v': cv2.VideoWriter_fourcc(*'mp4v'),
                'h264': cv2.VideoWriter_fourcc(*'H264'),
                'xvid': cv2.VideoWriter_fourcc(*'XVID')
            }
            fourcc = codec_map.get(self.output_codec.get(), cv2.VideoWriter_fourcc(*'mp4v'))
            
            # Utwórz writer
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if not out.isOpened():
                raise Exception(f"Nie można utworzyć pliku wyjściowego: {output_path}")
            
            # Pobierz obszary znaku wodnego z pierwszej klatki
            ret, first_frame = cap.read()
            if not ret:
                raise Exception("Nie można odczytać pierwszej klatki.")
            
            watermark_areas = self.get_watermark_areas(first_frame, corners)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Przetwarzanie z buforowaniem
            frame_count = 0
            frame_buffer = []
            buffer_size = 10 if self.use_buffering.get() else 1
            
            # Użyj ThreadPoolExecutor dla równoległego przetwarzania
            with ThreadPoolExecutor(max_workers=self.thread_count.get()) as executor:
                futures = []
                
                while True:
                    if self.processing_cancelled:
                        self.update_status("Anulowano przetwarzanie")
                        break
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Dodaj klatkę do przetwarzania
                    future = executor.submit(self.process_single_frame, frame, watermark_areas)
                    futures.append((frame_count, future))
                    
                    # Przetwarzaj bufor gdy jest pełny
                    if len(futures) >= buffer_size:
                        for fc, future in futures[:buffer_size]:
                            processed_frame = future.result()
                            out.write(processed_frame)
                            
                            # Aktualizuj podgląd
                            if fc % self.preview_frequency.get() == 0:
                                self.update_preview(processed_frame, fc, total_frames)
                        
                        futures = futures[buffer_size:]
                    
                    frame_count += 1
                    
                    # Aktualizuj postęp
                    progress = (frame_count / total_frames) * 100
                    self.update_progress(progress, f"Przetwarzanie klatki {frame_count}/{total_frames}")
                
                # Przetwórz pozostałe klatki
                for fc, future in futures:
                    if not self.processing_cancelled:
                        processed_frame = future.result()
                        out.write(processed_frame)
            
            # Zakończ
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            if not self.processing_cancelled:
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.update_status(f"Zapisano: {output_path} ({file_size_mb:.2f} MB)")
                messagebox.showinfo("Sukces", f"Przetworzono {frame_count} klatek\nPlik: {output_path}")
                logging.info(f"Sukces: {frame_count} klatek, {file_size_mb:.2f} MB")
            
        except Exception as e:
            self.update_status(f"Błąd: {str(e)}")
            messagebox.showerror("Błąd", f"Wystąpił błąd: {str(e)}")
            logging.error(f"Błąd przetwarzania: {e}")
            
            if 'cap' in locals():
                cap.release()
            if 'out' in locals():
                out.release()
    
    def process_single_frame(self, frame, watermark_areas):
        """Przetwórz pojedynczą klatkę"""
        # Usuń znak wodny
        processed = self.remove_watermark_advanced(frame, watermark_areas)
        
        # Zastosuj post-processing
        processed = self.apply_post_processing(processed)
        
        return processed
    
    def update_status(self, message):
        """Aktualizuj status (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def update_progress(self, progress, detail=""):
        """Aktualizuj pasek postępu (thread-safe)"""
        self.root.after(0, lambda: self._update_progress_ui(progress, detail))
    
    def _update_progress_ui(self, progress, detail):
        """Aktualizuj UI postępu"""
        self.progress_meter.configure(amountused=progress)
        self.detail_label.config(text=detail)
    
    def start_processing(self):
        """Rozpocznij przetwarzanie pojedynczego pliku"""
        if not self.input_path:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać plik wideo!")
            return
        
        # Sprawdź czy wybrano obszary
        corners = self.get_selected_corners()
        if not corners and not self.custom_areas:
            messagebox.showwarning("Ostrzeżenie", 
                                 "Proszę wybrać przynajmniej jeden obszar do usunięcia!")
            return
        
        # Przygotuj ścieżkę wyjściową
        base, ext = os.path.splitext(os.path.basename(self.input_path))
        output_path = os.path.join(self.program_dir, f"{base}_no_watermark{ext}")
        
        # Resetuj anulowanie
        self.processing_cancelled = False
        
        # Aktualizuj UI
        self.process_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.preview_button.config(state=tk.NORMAL)
        
        # Utwórz okno podglądu jeśli włączone
        if self.show_preview_var.get():
            self.create_preview_window()
        
        # Uruchom przetwarzanie w osobnym wątku
        self.processing_thread = threading.Thread(
            target=self._process_in_thread,
            args=(self.input_path, output_path, corners),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_in_thread(self, input_path, output_path, corners):
        """Przetwarzanie w osobnym wątku"""
        try:
            self.process_video_optimized(input_path, output_path, corners)
        finally:
            # Przywróć UI
            self.root.after(0, self._restore_ui_after_processing)
    
    def _restore_ui_after_processing(self):
        """Przywróć UI po przetwarzaniu"""
        self.process_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.preview_button.config(state=tk.DISABLED)
        self.progress_meter.configure(amountused=0)
        self.detail_label.config(text="")
    
    def get_selected_corners(self):
        """Pobierz wybrane rogi"""
        corners = []
        if self.bottom_right_var.get():
            corners.append("bottom_right")
        if self.top_left_var.get():
            corners.append("top_left")
        if self.bottom_left_var.get():
            corners.append("bottom_left")
        if self.top_right_var.get():
            corners.append("top_right")
        return corners
    
    def cancel_processing(self):
        """Anuluj przetwarzanie"""
        self.processing_cancelled = True
        self.cancel_button.config(state=tk.DISABLED)
        self.update_status("Anulowanie...")
        logging.info("Przetwarzanie anulowane przez użytkownika")
    
    def start_batch_processing(self):
        """Rozpocznij przetwarzanie wsadowe"""
        if not self.input_paths:
            messagebox.showwarning("Ostrzeżenie", "Brak plików do przetworzenia!")
            return
        
        corners = self.get_selected_corners()
        if not corners and not self.custom_areas:
            messagebox.showwarning("Ostrzeżenie", 
                                 "Proszę wybrać przynajmniej jeden obszar do usunięcia!")
            return
        
        # Resetuj anulowanie
        self.processing_cancelled = False
        
        # Aktualizuj UI
        self.batch_process_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Uruchom w osobnym wątku
        self.processing_thread = threading.Thread(
            target=self._batch_process_in_thread,
            args=(corners,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _batch_process_in_thread(self, corners):
        """Przetwarzanie wsadowe w osobnym wątku"""
        try:
            total_files = len(self.input_paths)
            
            for i, input_path in enumerate(self.input_paths):
                if self.processing_cancelled:
                    break
                
                # Aktualizuj status
                self.update_status(f"Przetwarzanie pliku {i+1}/{total_files}: {os.path.basename(input_path)}")
                
                # Przygotuj ścieżkę wyjściową
                base, ext = os.path.splitext(os.path.basename(input_path))
                output_path = os.path.join(self.program_dir, f"{base}_no_watermark{ext}")
                
                # Przetwórz plik
                if not self.batch_same_areas.get() and i > 0:
                    # Pozwól użytkownikowi wybrać nowe obszary dla każdego pliku
                    self.root.after(0, lambda p=input_path: self._select_areas_for_file(p))
                    # Czekaj na wybór obszarów
                    # TODO: Implementacja czekania na wybór
                
                self.process_video_optimized(input_path, output_path, corners)
                
                # Ogólny postęp
                overall_progress = ((i + 1) / total_files) * 100
                self.update_progress(overall_progress, f"Ukończono {i+1}/{total_files} plików")
            
            if not self.processing_cancelled:
                self.update_status(f"Zakończono przetwarzanie {total_files} plików")
                messagebox.showinfo("Sukces", f"Przetworzono wszystkie {total_files} plików!")
            
        except Exception as e:
            self.update_status(f"Błąd batch: {str(e)}")
            messagebox.showerror("Błąd", f"Błąd przetwarzania wsadowego: {str(e)}")
            logging.error(f"Błąd batch processing: {e}")
        finally:
            self.root.after(0, self._restore_ui_after_batch)
    
    def _restore_ui_after_batch(self):
        """Przywróć UI po przetwarzaniu wsadowym"""
        self.batch_process_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_meter.configure(amountused=0)
        self.detail_label.config(text="")
    
    def _select_areas_for_file(self, filepath):
        """Pozwól wybrać obszary dla konkretnego pliku"""
        # TODO: Implementacja wyboru obszarów dla każdego pliku osobno
        pass


def main():
    """Główna funkcja uruchamiająca aplikację"""
    root = tk.Tk()
    app = WatermarkRemoverApp(root)
    
    # Obsługa zamykania aplikacji
    def on_closing():
        if app.processing_thread and app.processing_thread.is_alive():
            if messagebox.askokcancel("Zamknij", 
                                     "Przetwarzanie jest w toku. Czy na pewno chcesz zamknąć?"):
                app.processing_cancelled = True
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except Exception as e:
        logging.critical(f"Krytyczny błąd aplikacji: {e}")
        messagebox.showerror("Błąd krytyczny", f"Aplikacja napotkała błąd: {e}")


if __name__ == "__main__":
    main()