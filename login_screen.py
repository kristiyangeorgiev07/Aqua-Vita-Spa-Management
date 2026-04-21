"""
Login screen for SPA Management System
"""
import tkinter as tk
from theme import COLORS, FONTS
from widgets import make_button, make_entry, show_message
from db_config import authenticate_user


class LoginScreen(tk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, bg=COLORS['bg_dark'])
        self.on_login = on_login
        self._build()

    def _build(self):
        self.pack(fill='both', expand=True)

        # Left decorative panel — packed FIRST so it fills full height incl. top
        left = tk.Frame(self, bg=COLORS['bg_medium'], width=320)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)

        # Right container holds the topbar + login form
        right_wrap = tk.Frame(self, bg=COLORS['bg_dark'])
        right_wrap.pack(side='left', fill='both', expand=True)

        # Minimal top bar with close button (inside right_wrap only)
        topbar = tk.Frame(right_wrap, bg=COLORS['bg_dark'], pady=4)
        topbar.pack(fill='x', side='top')
        tk.Button(topbar, text='✕  Изход', command=self._confirm_close,
                  bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
                  relief='flat', font=('Calibri', 9), cursor='hand2',
                  bd=0, padx=12, pady=2,
                  activebackground=COLORS['danger'],
                  activeforeground='white').pack(side='right', padx=8)

        # Decorative content on left
        tk.Frame(left, height=80, bg=COLORS['bg_medium']).pack()

        # Logo/Brand area
        brand = tk.Frame(left, bg=COLORS['bg_medium'], padx=30)
        brand.pack(fill='x')

        tk.Label(brand, text='✦', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=('Georgia', 40)).pack()
        tk.Label(brand, text='AQUA VITA', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=('Georgia', 20, 'bold')).pack()
        tk.Label(brand, text='SPA & WELLNESS CENTER', bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted'], font=('Calibri', 9)).pack(pady=(2, 0))

        tk.Frame(left, height=1, bg=COLORS['border_gold']).pack(fill='x', padx=30, pady=25)

        # Features list
        features = [
            '⟡  Управление на абонаменти',
            '⟡  Регистрация на посещения',
            '⟡  Клиентски досиета',
            '⟡  Административен панел',
        ]
        for feat in features:
            tk.Label(left, text=feat, bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary'], font=('Calibri', 10),
                     justify='left').pack(anchor='w', padx=30, pady=3)

        tk.Frame(left, height=1, bg=COLORS['border']).pack(fill='x', padx=30, pady=25)

        tk.Label(left, text='Версия 1.0  ·  2026', bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted'], font=('Calibri', 8)).pack()

        # Right login panel (inside right_wrap)
        right = tk.Frame(right_wrap, bg=COLORS['bg_dark'])
        right.pack(side='left', fill='both', expand=True)

        # Center the login form
        center = tk.Frame(right, bg=COLORS['bg_dark'])
        center.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(center, text='Добре дошли', bg=COLORS['bg_dark'],
                 fg=COLORS['text_muted'], font=('Calibri', 12)).pack()
        tk.Label(center, text='Влезте в системата', bg=COLORS['bg_dark'],
                 fg=COLORS['text_primary'], font=('Georgia', 22, 'bold')).pack(pady=(2, 30))

        # Form card
        card = tk.Frame(center, bg=COLORS['bg_card'], padx=40, pady=35)
        card.pack(ipadx=20)

        # Username
        tk.Label(card, text='ПОТРЕБИТЕЛСКО ИМЕ', bg=COLORS['bg_card'],
                 fg=COLORS['text_muted'], font=('Calibri', 8, 'bold')).pack(anchor='w')
        tk.Frame(card, height=4, bg=COLORS['bg_card']).pack()
        self.username_var = tk.StringVar()
        u_entry = make_entry(card, textvariable=self.username_var, width=32)
        u_entry.pack(ipady=6)
        u_entry.bind('<Return>', lambda e: self.p_entry.focus())

        tk.Frame(card, height=18, bg=COLORS['bg_card']).pack()

        # Password
        tk.Label(card, text='ПАРОЛА', bg=COLORS['bg_card'],
                 fg=COLORS['text_muted'], font=('Calibri', 8, 'bold')).pack(anchor='w')
        tk.Frame(card, height=4, bg=COLORS['bg_card']).pack()
        self.password_var = tk.StringVar()
        self.p_entry = make_entry(card, textvariable=self.password_var, width=32, show='•')
        self.p_entry.pack(ipady=6)
        self.p_entry.bind('<Return>', lambda e: self._login())

        tk.Frame(card, height=24, bg=COLORS['bg_card']).pack()

        # Error label
        self.error_var = tk.StringVar()
        self.error_lbl = tk.Label(card, textvariable=self.error_var,
                                   bg=COLORS['bg_card'], fg=COLORS['danger'],
                                   font=('Calibri', 9))
        self.error_lbl.pack()

        # Login button
        btn = make_button(card, 'ВЛЕЗ В СИСТЕМАТА', command=self._login,
                          style='primary', width=28)
        btn.pack(pady=(4, 0), ipady=4)

        tk.Frame(card, height=8, bg=COLORS['bg_card']).pack()

        # Default credentials hint
        hint = tk.Label(card, text='По подразбиране: admin / admin123',
                        bg=COLORS['bg_card'], fg=COLORS['text_muted'],
                        font=('Calibri', 8))
        hint.pack()

        # DB settings link
        tk.Frame(center, height=14, bg=COLORS['bg_dark']).pack()
        db_btn = tk.Button(
            center, text='⚙  Настройки на база данни',
            command=self._open_db_settings,
            bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
            relief='flat', font=('Calibri', 8), cursor='hand2',
            activeforeground=COLORS['gold'], activebackground=COLORS['bg_dark'],
            bd=0,
        )
        db_btn.pack()

        u_entry.focus()

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.error_var.set('Моля попълнете всички полета')
            return

        user = authenticate_user(username, password)
        if user:
            self.error_var.set('')
            self.on_login(user)
        else:
            self.error_var.set('Грешно потребителско име или парола')
            self.password_var.set('')

    def _confirm_close(self):
        from widgets import confirm_dialog
        if confirm_dialog(self.master, 'Затваряне на програмата',
                          'Сигурни ли сте, че искате да затворите програмата?'):
            self.master.destroy()

    def _open_db_settings(self):
        from db_settings import DBSettingsDialog
        DBSettingsDialog(self.master)
