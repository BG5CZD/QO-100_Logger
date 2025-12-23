#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QO-100 Satellite Log Recording Software
An application for recording QO-100 satellite communication logs
Supports GUI interface and ADI file export
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta, timezone
import json
import os
import locale
import re
from pathlib import Path
from languages import get_language, get_available_languages, get_language_names

# Modern UI style configuration
ACCENT_COLOR = "#0078d4"
SUCCESS_COLOR = "#17a2b8"
WARNING_COLOR = "#ff6b6b"


def get_system_language():
    """Detect system language"""
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            lang_code = system_locale.split('_')[0]  # e.g., 'zh_CN' -> 'zh'
            available_langs = get_available_languages()
            if lang_code in available_langs:
                return lang_code
    except Exception:
        pass
    # Default to English if system language not found
    return "en"


def get_font_for_text(text, lang_code="zh"):
    """Get appropriate font for text based on language and content"""
    if lang_code == "zh":
        # For Chinese interface, check if text contains Chinese characters
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        has_english = bool(re.search(r'[a-zA-Z]', text))
        
        if has_chinese and has_english:
            # For mixed content in Chinese interface, we'll use a font that supports both
            # Fallback to HuawenFangsong as it supports both
            return "HuawenFangsong"
        elif has_english and not has_chinese:
            return "Times New Roman"
        else:
            return "HuawenFangsong"
    else:
        # For other languages, use Times New Roman
        return "Times New Roman"


class SettingsDialog(tk.Toplevel):
    """Settings dialog"""
    
    def __init__(self, parent, settings, lang_dict):
        super().__init__(parent)
        self.title(lang_dict["settings"])
        self.geometry("540x580")
        self.resizable(False, False)
        self.result = None
        self.lang = lang_dict
        
        # Get appropriate font
        current_lang = settings.get("language", "en")
        font_family = "HuawenFangsong" if current_lang == "zh" else "Times New Roman"
        
        # Center display
        self.transient(parent)
        self.grab_set()
        
        # Create window widgets
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=lang_dict["common_settings"], font=(font_family, 16, "bold")).pack(pady=15)
        
        # Form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Auto-detect system language button
        auto_detect_frame = ttk.Frame(form_frame)
        auto_detect_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        ttk.Button(auto_detect_frame, text="Auto-detect System Language", 
                  command=self.auto_detect_language).pack(side=tk.LEFT, padx=5)
        self.system_lang_label = ttk.Label(auto_detect_frame, text="", font=(font_family, 9), foreground="gray")
        self.system_lang_label.pack(side=tk.LEFT, padx=10)
        
        # Language selection
        ttk.Label(form_frame, text="Language:", font=(font_family, 10)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.lang_var = tk.StringVar(value=settings.get("language", "en"))
        lang_names = get_language_names()
        ttk.Combobox(form_frame, textvariable=self.lang_var, 
                     values=list(lang_names.values()), 
                     width=40, state="readonly").grid(row=1, column=1, sticky=tk.EW, padx=10)
        
        # My callsign
        ttk.Label(form_frame, text=lang_dict["my_call"], font=(font_family, 10)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.my_call_var = tk.StringVar(value=settings.get("my_call", ""))
        ttk.Entry(form_frame, textvariable=self.my_call_var, width=40).grid(row=2, column=1, sticky=tk.EW, padx=10)
        
        # Grid
        ttk.Label(form_frame, text=lang_dict["my_grid"], font=(font_family, 10)).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.grid_var = tk.StringVar(value=settings.get("grid", ""))
        ttk.Entry(form_frame, textvariable=self.grid_var, width=40).grid(row=3, column=1, sticky=tk.EW, padx=10)
        
        # CQ Zone
        ttk.Label(form_frame, text=lang_dict["cq_zone"], font=(font_family, 10)).grid(row=4, column=0, sticky=tk.W, pady=10)
        self.cq_var = tk.StringVar(value=settings.get("cq_zone", ""))
        cq_values = [""] + [str(i) for i in range(1, 41)]
        ttk.Combobox(form_frame, textvariable=self.cq_var, values=cq_values, width=38, state="readonly").grid(row=4, column=1, sticky=tk.EW, padx=10)
        
        # ITU Zone
        ttk.Label(form_frame, text=lang_dict["itu_zone"], font=(font_family, 10)).grid(row=5, column=0, sticky=tk.W, pady=10)
        self.itu_var = tk.StringVar(value=settings.get("itu_zone", ""))
        itu_values = [""] + [str(i) for i in range(1, 76)]
        ttk.Combobox(form_frame, textvariable=self.itu_var, values=itu_values, width=38, state="readonly").grid(row=5, column=1, sticky=tk.EW, padx=10)
        
        # Country
        ttk.Label(form_frame, text=lang_dict["country_code"], font=(font_family, 10)).grid(row=6, column=0, sticky=tk.W, pady=10)
        self.country_var = tk.StringVar(value=settings.get("country", ""))
        ttk.Entry(form_frame, textvariable=self.country_var, width=40).grid(row=6, column=1, sticky=tk.EW, padx=10)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text=lang_dict["save"], command=self.save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text=lang_dict["cancel"], command=self.cancel).pack(side=tk.LEFT, padx=10)
        
        # Show detected system language
        self.show_system_language()
    
    def show_system_language(self):
        """Show detected system language"""
        system_lang = get_system_language()
        lang_names = get_language_names()
        lang_display = lang_names.get(system_lang, "Unknown")
        self.system_lang_label.config(text=f"Detected: {lang_display}")
    
    def auto_detect_language(self):
        """Auto-detect and set system language"""
        system_lang = get_system_language()
        lang_names = get_language_names()
        if system_lang in lang_names:
            display_name = lang_names[system_lang]
            self.lang_var.set(display_name)
            self.show_system_language()
    
    def save_settings(self):
        """Save settings"""
        # Get language code
        lang_names_rev = {v: k for k, v in get_language_names().items()}
        lang_code = lang_names_rev.get(self.lang_var.get(), "zh")
        
        self.result = {
            "language": lang_code,
            "my_call": self.my_call_var.get().strip().upper(),
            "grid": self.grid_var.get().strip().upper(),
            "cq_zone": self.cq_var.get(),
            "itu_zone": self.itu_var.get(),
            "country": self.country_var.get().strip(),
        }
        self.destroy()
    
    def cancel(self):
        """Cancel"""
        self.result = None
        self.destroy()


class EditLogDialog(tk.Toplevel):
    """Edit log dialog"""
    
    def __init__(self, parent, log_entry, lang_dict):
        super().__init__(parent)
        self.title(lang_dict.get("edit_log", "Edit Log"))
        self.geometry("530x560")
        self.resizable(True, True)
        self.result = None
        self.lang = lang_dict
        self.log_entry = log_entry.copy()
        
        # Get appropriate font (default to Chinese for consistency)
        font_family = "HuawenFangsong"
        
        # Center display
        self.transient(parent)
        self.grab_set()
        
        # Create window widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Date
        ttk.Label(main_frame, text=lang_dict["date"], font=(font_family, 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.date_var = tk.StringVar(value=log_entry["date"])
        ttk.Entry(main_frame, textvariable=self.date_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Time
        ttk.Label(main_frame, text=lang_dict["time"], font=(font_family, 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.time_var = tk.StringVar(value=log_entry["time"])
        ttk.Entry(main_frame, textvariable=self.time_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        
        # My callsign
        ttk.Label(main_frame, text=lang_dict["my_call"], font=(font_family, 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.my_call_var = tk.StringVar(value=log_entry["my_call"])
        ttk.Entry(main_frame, textvariable=self.my_call_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Other callsign
        ttk.Label(main_frame, text=lang_dict["other_call"], font=(font_family, 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.other_call_var = tk.StringVar(value=log_entry["other_call"])
        ttk.Entry(main_frame, textvariable=self.other_call_var, width=30).grid(row=3, column=1, sticky=tk.W, padx=5, pady=8)
        
        # TX frequency
        ttk.Label(main_frame, text=lang_dict["up_freq"], font=(font_family, 10)).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.my_freq_var = tk.StringVar(value=log_entry["my_freq"])
        ttk.Entry(main_frame, textvariable=self.my_freq_var, width=30).grid(row=4, column=1, sticky=tk.W, padx=5, pady=8)
        
        # RX frequency
        ttk.Label(main_frame, text=lang_dict["down_freq"], font=(font_family, 10)).grid(row=5, column=0, sticky=tk.W, pady=8)
        self.other_freq_var = tk.StringVar(value=log_entry["other_freq"])
        ttk.Entry(main_frame, textvariable=self.other_freq_var, width=30).grid(row=5, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Mode
        ttk.Label(main_frame, text=lang_dict["mode"], font=(font_family, 10)).grid(row=6, column=0, sticky=tk.W, pady=8)
        self.mode_var = tk.StringVar(value=log_entry["mode"])
        ttk.Combobox(main_frame, textvariable=self.mode_var, 
                     values=["SSB", "CW", "FM", "BPSK", "QPSK", "PSK31"],
                     width=28, state="readonly").grid(row=6, column=1, sticky=tk.W, padx=5, pady=8)
        
        # My RST
        ttk.Label(main_frame, text=lang_dict["my_rst"], font=(font_family, 10)).grid(row=7, column=0, sticky=tk.W, pady=8)
        self.my_rst_var = tk.StringVar(value=log_entry["my_rst"])
        ttk.Entry(main_frame, textvariable=self.my_rst_var, width=30).grid(row=7, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Other RST
        ttk.Label(main_frame, text=lang_dict["other_rst"], font=(font_family, 10)).grid(row=8, column=0, sticky=tk.W, pady=8)
        self.other_rst_var = tk.StringVar(value=log_entry["other_rst"])
        ttk.Entry(main_frame, textvariable=self.other_rst_var, width=30).grid(row=8, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Comment
        ttk.Label(main_frame, text=lang_dict["comment"], font=(font_family, 10), anchor=tk.NW).grid(row=9, column=0, sticky=tk.NW, pady=8)
        self.comment_text = tk.Text(main_frame, height=3, width=32, font=(font_family, 9))
        self.comment_text.insert("1.0", log_entry.get("comment", ""))
        self.comment_text.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=5, pady=8)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text=lang_dict.get("save", "Save"), command=self.save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text=lang_dict["cancel"], command=self.cancel).pack(side=tk.LEFT, padx=10)
        
        main_frame.columnconfigure(1, weight=1)
    
    def save_changes(self):
        """Save changes"""
        self.log_entry["date"] = self.date_var.get()
        self.log_entry["time"] = self.time_var.get()
        self.log_entry["my_call"] = self.my_call_var.get()
        self.log_entry["other_call"] = self.other_call_var.get()
        self.log_entry["my_freq"] = self.my_freq_var.get()
        self.log_entry["other_freq"] = self.other_freq_var.get()
        self.log_entry["mode"] = self.mode_var.get()
        self.log_entry["my_rst"] = self.my_rst_var.get()
        self.log_entry["other_rst"] = self.other_rst_var.get()
        self.log_entry["comment"] = self.comment_text.get("1.0", tk.END).strip()
        
        self.result = self.log_entry
        self.destroy()
    
    def cancel(self):
        """Cancel"""
        self.result = None
        self.destroy()


class QO100Logger:
    """QO-100 Log Recorder Main Class"""
    
    def __init__(self, root):
        self.root = root
        
        # Log data storage
        self.logs = []
        self.log_file = "qo100_logs.json"
        self.settings_file = "qo100_settings.json"
        self.settings = {}
        
        self.load_settings()
        
        # Load language - auto-detect system language if first time
        if not self.settings.get("language"):
            system_lang = get_system_language()
            self.settings["language"] = system_lang
            self.save_settings()
        
        self.current_lang = self.settings.get("language", "en")
        self.lang = get_language(self.current_lang)
        
        # Set font based on language
        self.font_family = "HuawenFangsong" if self.current_lang == "zh" else "Times New Roman"
        
        self.root.title(self.lang["title"])
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Fullscreen status flag
        self.is_fullscreen = False
        self.window_geometry = None
        
        # Bind fullscreen shortcut key (F11)
        self.root.bind("<F11>", self.toggle_fullscreen)
        # Esc to exit fullscreen
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen() if self.is_fullscreen else None)
        
        # Set modern theme
        self.setup_modern_theme()
        
        self.load_logs()
        
        # Create GUI
        self.create_widgets()
        
    
    def setup_modern_theme(self):
        """Set up modern theme (follow system)"""
        style = ttk.Style()
        
        # Use system default theme, auto-adapt to dark/light
        style.theme_use('clam')
        
        # Set font family based on language
        font_family = "HuawenFangsong" if self.current_lang == "zh" else "Times New Roman"
        
        # Button style - increase width and font
        style.configure('TButton', 
                       font=(font_family, 10),
                       padding=8)
        
        # Labelframe style - increase margins
        style.configure('TLabelframe.Label', font=(font_family, 11, 'bold'))
        style.configure('TLabelframe', padding=15)
        
        # Entry style
        style.configure('TEntry', padding=5)
        style.configure('TCombobox', padding=5)
    
    def create_widgets(self):
        """Create GUI interface"""
        # Get appropriate font
        font_family = "HuawenFangsong" if self.current_lang == "zh" else "Times New Roman"
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ===== Header section =====
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text=self.lang["title"], 
                               font=(font_family, 20, "bold"))
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Settings and export buttons on the right
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(controls_frame, text=self.lang["settings"], 
                  command=self.open_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=self.lang["export_adi"], 
                  command=self.export_adi).pack(side=tk.LEFT, padx=5)
        
        # ===== Date/Time frame =====
        datetime_frame = ttk.LabelFrame(main_frame, text=self.lang["date_time"], padding="12")
        datetime_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Use grid layout to beautify date/time display
        ttk.Label(datetime_frame, text=self.lang["utc_date"], font=(font_family, 11)).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        self.date_label = ttk.Label(datetime_frame, text=datetime.now(timezone.utc).strftime("%Y-%m-%d"), 
                                   font=(font_family, 12, "bold"), foreground=ACCENT_COLOR)
        self.date_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 25))
        
        ttk.Label(datetime_frame, text=self.lang["utc_time"], font=(font_family, 11)).grid(row=0, column=2, sticky=tk.W, padx=(0, 15))
        self.time_label = ttk.Label(datetime_frame, text=datetime.now(timezone.utc).strftime("%H:%M:%S"), 
                                   font=(font_family, 13, "bold"), foreground=SUCCESS_COLOR)
        self.time_label.grid(row=0, column=3, sticky=tk.W)
        
        # Start auto-update time
        self.update_time()
        
        # ===== Information input frame =====
        info_frame = ttk.LabelFrame(main_frame, text=self.lang["info_input"], padding="12")
        info_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Row 1: Callsign info
        ttk.Label(info_frame, text=self.lang["my_call"], font=(font_family, 11, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.my_call_var = tk.StringVar()
        my_call_entry = ttk.Entry(info_frame, textvariable=self.my_call_var, width=15, state="readonly")
        my_call_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        if self.settings.get("my_call"):
            self.my_call_var.set(self.settings["my_call"])
        
        ttk.Label(info_frame, text=self.lang["other_call"], font=(font_family, 11, "bold")).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.other_call_var = tk.StringVar()
        self.other_call_entry = ttk.Entry(info_frame, textvariable=self.other_call_var, width=15)
        self.other_call_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        self.other_call_entry.bind("<Return>", lambda e: self.save_log())
        
        # Row 2: Frequency info
        ttk.Label(info_frame, text=self.lang["down_freq"], font=(font_family, 11, "bold")).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.down_freq_var = tk.StringVar()
        self.down_freq_entry = ttk.Entry(info_frame, textvariable=self.down_freq_var, width=15)
        self.down_freq_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        self.down_freq_entry.bind("<KeyRelease>", self.calculate_up_freq)
        
        ttk.Label(info_frame, text=self.lang["up_freq"], font=(font_family, 11, "bold")).grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.up_freq_var = tk.StringVar()
        self.up_freq_label = ttk.Label(info_frame, textvariable=self.up_freq_var, font=(font_family, 11, "bold"), 
                                       foreground=SUCCESS_COLOR)
        self.up_freq_label.grid(row=1, column=3, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Row 3: RST info
        ttk.Label(info_frame, text=self.lang["my_rst"], font=(font_family, 11, "bold")).grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.my_rst_var = tk.StringVar(value="59")
        ttk.Entry(info_frame, textvariable=self.my_rst_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        ttk.Label(info_frame, text=self.lang["other_rst"], font=(font_family, 11, "bold")).grid(row=2, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.other_rst_var = tk.StringVar(value="59")
        ttk.Entry(info_frame, textvariable=self.other_rst_var, width=15).grid(row=2, column=3, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Row 4: Mode
        ttk.Label(info_frame, text=self.lang["mode"], font=(font_family, 11, "bold")).grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.mode_var = tk.StringVar(value="SSB")
        mode_combo = ttk.Combobox(info_frame, textvariable=self.mode_var, 
                                  values=["SSB", "CW", "FM", "BPSK", "QPSK", "PSK31"], 
                                  width=13, state="readonly")
        mode_combo.grid(row=3, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Row 5: Comment
        ttk.Label(info_frame, text=self.lang["comment"], font=(font_family, 11, "bold"), anchor=tk.NW).grid(row=4, column=0, sticky=tk.NW, pady=(10, 0), padx=(0, 10))
        self.notes_text = tk.Text(info_frame, height=2, width=65, 
                                 font=(font_family, 9), relief="solid", borderwidth=1)
        self.notes_text.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0), padx=(0, 0))
        
        # ===== Log display frame =====
        log_frame = ttk.LabelFrame(main_frame, text=f"{self.lang['logs']} (0)", padding="10")
        log_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_frame = log_frame
        self.log_font_family = font_family
        self.update_log_display()
        
        # Configure row/column weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(3, weight=1)
        info_frame.columnconfigure(1, weight=0)
        info_frame.columnconfigure(3, weight=1)
        
    def update_log_display(self):
        """Update log display"""
        # Get appropriate font
        font_family = "HuawenFangsong" if self.current_lang == "zh" else "Times New Roman"
        
        # Clear old log display
        for widget in self.log_frame.winfo_children():
            if not isinstance(widget, ttk.Label) or not widget.cget("text").startswith(self.lang['logs']):
                widget.destroy()
        
        if not self.logs:
            empty_label = ttk.Label(self.log_frame, text=self.lang["no_logs"], 
                                   foreground="gray", font=(font_family, 10))
            empty_label.pack(pady=20)
            # Update title
            self.log_frame.config(text=f"{self.lang['logs']} (0)")
            return
        
        # Create scrollable frame
        canvas_frame = ttk.Frame(self.log_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add log entries (right-click interactive)
        for i, log in enumerate(self.logs):
            log_text = f"#{i+1}  [{log['date']} {log['time']}] {log['my_call']} <-> {log['other_call']}  " \
                      f"{log['mode']}  {log['my_freq']}/{log['other_freq']} MHz"
            
            # Create log item frame
            log_item_frame = tk.Frame(scrollable_frame, relief="flat", bd=0, padx=10, pady=10)
            log_item_frame.pack(anchor=tk.W, pady=2, fill=tk.X, padx=0)
            
            log_label = tk.Label(log_item_frame, text=log_text,
                                foreground=ACCENT_COLOR, cursor="hand2", font=(font_family, 10),
                                wraplength=700, justify=tk.LEFT)
            log_label.pack(anchor=tk.W, fill=tk.X)
            
            # Bind right-click menu to each log
            log_label.bind("<Button-3>", lambda e, idx=i: self.show_log_context_menu(e, idx))
            log_item_frame.bind("<Button-3>", lambda e, idx=i: self.show_log_context_menu(e, idx))
            
            # Hover effect
            def on_enter(e, frame=log_item_frame):
                frame.config(relief="solid", bd=1)
            
            def on_leave(e, frame=log_item_frame):
                frame.config(relief="flat", bd=0)
            
            log_label.bind("<Enter>", on_enter)
            log_label.bind("<Leave>", on_leave)
            log_item_frame.bind("<Enter>", on_enter)
            log_item_frame.bind("<Leave>", on_leave)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Update title
        self.log_frame.config(text=f"{self.lang['logs']} ({len(self.logs)})")
        
    def save_log(self):
        """Save a log entry"""
        # Check if basic information is set
        if not self.settings.get("my_call"):
            messagebox.showwarning(self.lang["error"], self.lang["input_my_call"])
            return
        
        my_call = self.settings["my_call"]
        other_call = self.other_call_var.get().strip().upper()
        
        if not other_call:
            messagebox.showwarning(self.lang["error"], self.lang["input_other_call"])
            return
        
        down_freq = self.down_freq_var.get().strip()
        
        if not down_freq:
            messagebox.showwarning(self.lang["error"], self.lang["input_down_freq"])
            return
        
        try:
            down_freq_float = float(down_freq)
            up_freq_float = down_freq_float - 8089.5
        except ValueError:
            messagebox.showwarning(self.lang["error"], self.lang["freq_error"])
            return
        
        # Get current UTC time and date
        now = datetime.now(timezone.utc)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        log_entry = {
            "date": current_date,
            "time": current_time,
            "my_call": my_call,
            "other_call": other_call,
            "my_freq": f"{up_freq_float:.5f}",  # TX frequency
            "other_freq": down_freq,  # RX frequency
            "my_rst": self.my_rst_var.get(),
            "other_rst": self.other_rst_var.get(),
            "mode": self.mode_var.get(),
            "comment": self.notes_text.get("1.0", tk.END).strip(),
            "grid": self.settings.get("grid", ""),
            "cq_zone": self.settings.get("cq_zone", ""),
            "itu_zone": self.settings.get("itu_zone", ""),
            "country": self.settings.get("country", "")
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        self.update_log_display()
        # No prompt, just clear the form
        self.clear_form()
        
    def update_time(self):
        """Auto-update system time"""
        now = datetime.now(timezone.utc)
        self.date_label.config(text=now.strftime("%Y-%m-%d"))
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        # Update every 1000 milliseconds
        self.root.after(1000, self.update_time)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            # Save current window geometry
            self.window_geometry = self.root.geometry()
            # Enter fullscreen
            self.root.attributes('-fullscreen', True)
        else:
            # Exit fullscreen
            self.root.attributes('-fullscreen', False)
            # Restore window size
            if self.window_geometry:
                self.root.geometry(self.window_geometry)
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes('-fullscreen', False)
            if self.window_geometry:
                self.root.geometry(self.window_geometry)
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            dialog = SettingsDialog(self.root, self.settings, self.lang)
            self.root.wait_window(dialog)
            
            if dialog.result:
                old_lang = self.current_lang
                self.settings = dialog.result
                self.save_settings()
                
                # Reload language
                new_lang = self.settings.get("language", "en")
                if new_lang != old_lang:
                    self.current_lang = new_lang
                    self.lang = get_language(self.current_lang)
                    # Update font family based on new language
                    self.font_family = "HuawenFangsong" if self.current_lang == "zh" else "Times New Roman"
                    # Prompt user to restart to apply language changes
                    messagebox.showinfo(self.lang["success"], "Language switched. Please restart the application for changes to take effect")
                
                self.my_call_var.set(self.settings.get("my_call", ""))
                messagebox.showinfo(self.lang["success"], self.lang["settings_saved"])
        except Exception as e:
            messagebox.showerror(self.lang["error"], f"{self.lang['settings_open_error']} {str(e)}")
    
    def calculate_up_freq(self, event=None):
        """Calculate TX frequency from RX frequency"""
        down_freq_str = self.down_freq_var.get().strip()
        if down_freq_str:
            try:
                down_freq = float(down_freq_str)
                up_freq = down_freq - 8089.5
                self.up_freq_var.set(f"{up_freq:.5f}")
            except ValueError:
                self.up_freq_var.set("Input error")
        else:
            self.up_freq_var.set("")
    
    def clear_form(self):
        """Clear form (keep frequency, only clear callsign and comment)"""
        self.other_call_var.set("")
        # RX frequency remains unchanged (N1MM style)
        # self.down_freq_var.set("")
        self.mode_var.set("SSB")
        self.my_rst_var.set("59")
        self.other_rst_var.set("59")
        self.notes_text.delete("1.0", tk.END)
        # Focus back to other callsign input
        self.other_call_entry.focus()
        
    def show_log_context_menu(self, event, log_index):
        """Show log right-click menu"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label=self.lang.get("edit_log", "Edit"), 
                                command=lambda: self.edit_log(log_index))
        context_menu.add_command(label=self.lang.get("delete_log", "Delete"), 
                                command=lambda: self.delete_log(log_index))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def edit_log(self, log_index):
        """Edit log"""
        try:
            dialog = EditLogDialog(self.root, self.logs[log_index], self.lang)
            self.root.wait_window(dialog)
            
            if dialog.result is not None:
                self.logs[log_index] = dialog.result
                self.save_logs()
                self.update_log_display()
                messagebox.showinfo(self.lang["success"], self.lang.get("log_updated", "Log updated"))
        except Exception as e:
            messagebox.showerror(self.lang["error"], f"{self.lang.get('edit_failed', 'Edit failed')} {str(e)}")
    
    def delete_log(self, log_index):
        """Delete specified log"""
        if messagebox.askyesno(self.lang.get("confirm", "Confirm"), self.lang.get("confirm_delete_log", "Are you sure you want to delete this log?")):
            try:
                del self.logs[log_index]
                self.save_logs()
                self.update_log_display()
                messagebox.showinfo(self.lang["success"], self.lang["last_deleted"])
            except Exception as e:
                messagebox.showerror(self.lang["error"], f"{self.lang['export_failed']} {str(e)}")
    
    def export_adi(self):
        """Export as ADI format"""
        if not self.logs:
            messagebox.showwarning(self.lang["warning"], self.lang["no_logs_to_export"])
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".adi",
            filetypes=[(self.lang["adi_file"], "*.adi"), (self.lang["all_files"], "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            adi_content = self.generate_adi()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(adi_content)
            messagebox.showinfo(self.lang["success"], f"{self.lang['export_adi_success']}\n{file_path}")
        except Exception as e:
            messagebox.showerror(self.lang["error"], f"{self.lang['export_failed']} {str(e)}")
    
    def generate_adi(self):
        """Generate ADI format content"""
        lines = []
        lines.append("ADIF export from QO-100 Logger")
        lines.append("")
        lines.append("<ADIF_VER:5>3.1.0")
        lines.append("<PROGRAMID:11>QO-100 Logger>")
        lines.append("<PROGRAMVERSION:5>1.0.0>")
        lines.append("<EOH>")
        lines.append("")
        
        for log in self.logs:
            lines.append(self.format_qso_adi(log))
        
        lines.append("<EOR>")
        return "\n".join(lines)
    
    def format_qso_adi(self, log):
        """Format single QSO as ADI format"""
        adi_parts = []
        
        # My callsign (STATION_CALLSIGN)
        my_call = log['my_call']
        adi_parts.append(f"<STATION_CALLSIGN:{len(my_call)}>{my_call}")
        
        # Other callsign (CALL)
        other_call = log['other_call']
        adi_parts.append(f"<CALL:{len(other_call)}>{other_call}")
        
        # QSO date
        date_str = log['date'].replace('-', '')
        adi_parts.append(f"<QSO_DATE:{len(date_str)}>{date_str}")
        
        # QSO time ON
        time_str = log['time'].replace(':', '')
        adi_parts.append(f"<TIME_ON:{len(time_str)}>{time_str}")
        
        # QSO time OFF (same as ON)
        adi_parts.append(f"<TIME_OFF:{len(time_str)}>{time_str}")
        
        # Band (BAND) - Determine by RX frequency
        try:
            freq = float(log['other_freq'])
            if 10400 <= freq <= 10500:
                band = "13CM"
            elif 2400 <= freq <= 2500:
                band = "3CM"
            else:
                band = "UNK"
        except:
            band = "UNK"
        
        adi_parts.append(f"<BAND:{len(band)}>{band}")
        
        # Frequency (FREQ) - TX frequency
        freq_tx = log['my_freq']
        try:
            freq_tx_float = float(freq_tx)
            freq_tx_str = f"{freq_tx_float:.1f}"
            adi_parts.append(f"<FREQ:{len(freq_tx_str)}>{freq_tx_str}")
        except:
            adi_parts.append(f"<FREQ:{len(freq_tx)}>{freq_tx}")
        
        # Comment (COMMENT) - Separate field
        comment = log.get('comment', '')
        if comment:
            adi_parts.append(f"<COMMENT:{len(comment)}>{comment}")
        
        # RX frequency (FREQ_RX)
        freq_rx = log['other_freq']
        try:
            freq_rx_float = float(freq_rx)
            freq_rx_str = f"{freq_rx_float:.5f}"
            adi_parts.append(f"<FREQ_RX:{len(freq_rx_str)}>{freq_rx_str}")
        except:
            adi_parts.append(f"<FREQ_RX:{len(freq_rx)}>{freq_rx}")
        
        # Mode (MODE)
        mode = log['mode']
        adi_parts.append(f"<MODE:{len(mode)}>{mode}")
        
        # Received RST (RST_RCVD)
        rst_rcvd = log['other_rst']
        adi_parts.append(f"<RST_RCVD:{len(rst_rcvd)}>{rst_rcvd}")
        
        # Sent RST (RST_SENT)
        rst_sent = log['my_rst']
        adi_parts.append(f"<RST_SENT:{len(rst_sent)}>{rst_sent}")
        
        # Satellite name
        sat_name = "QO-100"
        adi_parts.append(f"<SAT_NAME:{len(sat_name)}>{sat_name}")
        
        # Propagation mode (Satellite)
        prop_mode = "SAT"
        adi_parts.append(f"<PROP_MODE:{len(prop_mode)}>{prop_mode}")
        
        # RX band (BAND_RX)
        band_rx = "3CM" if 2400 <= float(log['other_freq']) <= 2500 else "13CM"
        adi_parts.append(f"<BAND_RX:{len(band_rx)}>{band_rx}")
        
        # Satellite mode
        sat_mode = "SX"
        adi_parts.append(f"<SAT_MODE:{len(sat_mode)}>{sat_mode}")
        
        # My grid (MY_GRIDSQUARE)
        grid = log.get('grid', '')
        if grid:
            adi_parts.append(f"<MY_GRIDSQUARE:{len(grid)}>{grid}")
        
        # CQ zone
        cq_zone = log.get('cq_zone', '')
        if cq_zone:
            adi_parts.append(f"<CQZ:{len(cq_zone)}>{cq_zone}")
        
        # ITU zone
        itu_zone = log.get('itu_zone', '')
        if itu_zone:
            adi_parts.append(f"<ITUZ:{len(itu_zone)}>{itu_zone}")
        
        # Country
        country = log.get('country', '')
        if country:
            adi_parts.append(f"<COUNTRY:{len(country)}>{country}")
        
        # End marker
        
        return "\n".join(adi_parts)
    
    def export_csv(self):
        """Export as CSV format"""
        if not self.logs:
            messagebox.showwarning("Warning", "No logs to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Header
                headers = ["Date", "Time", "My Callsign", "Other Callsign", "TX Frequency", "RX Frequency", 
                          "My RST", "Other RST", "Mode", "Comment", "Grid", "CQ Zone", "ITU Zone", "Country"]
                f.write(",".join(headers) + "\n")
                
                # Data
                for log in self.logs:
                    values = [
                        log['date'],
                        log['time'],
                        log['my_call'],
                        log['other_call'],
                        log['my_freq'],
                        log['other_freq'],
                        log['my_rst'],
                        log['other_rst'],
                        log['mode'],
                        f'"{log.get("comment", "")}"',
                        log.get('grid', ''),
                        log.get('cq_zone', ''),
                        log.get('itu_zone', ''),
                        log.get('country', '')
                    ]
                    f.write(",".join(values) + "\n")
            
            messagebox.showinfo("Success", f"CSV file exported:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def save_logs(self):
        """Save logs to JSON file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}")
    
    def load_logs(self):
        """Load logs from JSON file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []
        else:
            self.logs = []
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Settings save failed: {str(e)}")
    
    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}


def main():
    """Main program"""
    root = tk.Tk()
    app = QO100Logger(root)
    root.mainloop()


if __name__ == "__main__":
    main()
