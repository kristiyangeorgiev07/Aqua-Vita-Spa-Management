"""
Main Application Window - SPA Management System
"""
import tkinter as tk
from datetime import date
from theme import COLORS, FONTS
from widgets import make_button, confirm_dialog
from login_screen import LoginScreen
from dashboard import Dashboard
from reception_panel import ReceptionPanel
from visits_panel import VisitsPanel
from subscriptions_panel import SubscriptionsPanel
from admin_panel import AdminPanel


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Aqua Vita — СПА Управление')
        self.configure(bg=COLORS['bg_dark'])

        # Full screen without OS title bar
        # Use platform-appropriate method so Toplevel dialogs still work
        import platform
        if platform.system() == 'Windows':
            self.state('zoomed')
            self.overrideredirect(True)
            # Bind Alt+F4 so window can still be closed
            self.bind('<Alt-F4>', lambda e: self._quit_app())
        else:
            # Linux / macOS — maximise via window manager
            try:
                self.attributes('-zoomed', True)
            except Exception:
                pass
            self.overrideredirect(True)
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f'{sw}x{sh}+0+0')

        self._current_user = None
        self._panels = {}
        self._active_nav = None

        self._show_login()

    def _quit_app(self):
        """Hard quit."""
        self.destroy()

    def _confirm_quit(self):
        """Ask for confirmation before quitting."""
        if confirm_dialog(self, 'Изход', 'Сигурни ли сте, че искате да излезете от програмата?'):
            self.destroy()

    def _minimize(self):
        """Temporarily restore the OS decoration to allow minimizing."""
        self.overrideredirect(False)
        self.iconify()
        # Re-apply borderless when restored
        self.bind('<Map>', self._on_restore)

    def _on_restore(self, event=None):
        self.unbind('<Map>')
        self.overrideredirect(True)
        import platform
        if platform.system() == 'Windows':
            self.state('zoomed')
        else:
            try:
                self.attributes('-zoomed', True)
            except Exception:
                pass

    # ─── LOGIN ───────────────────────────────────────────────────

    def _show_login(self):
        # Cancel any pending after() jobs from the main UI
        for attr in ('_date_job',):
            job = getattr(self, attr, None)
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        for w in self.winfo_children():
            w.destroy()
        self._panels = {}
        LoginScreen(self, on_login=self._on_login)

    def _on_login(self, user):
        self._current_user = user
        for w in self.winfo_children():
            w.destroy()
        self._build_main_ui()

    # ─── MAIN UI ─────────────────────────────────────────────────

    def _build_main_ui(self):
        user = self._current_user

        # Sidebar
        sidebar = tk.Frame(self, bg=COLORS['bg_medium'], width=200)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        # Brand
        brand = tk.Frame(sidebar, bg=COLORS['bg_medium'], pady=16, padx=18)
        brand.pack(fill='x')
        tk.Label(brand, text='✦ AQUA VITA', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=('Georgia', 12, 'bold')).pack(anchor='w')
        tk.Label(brand, text='СПА управление', bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted'], font=('Calibri', 8)).pack(anchor='w')

        tk.Frame(sidebar, height=1, bg=COLORS['border']).pack(fill='x', padx=14)

        # Navigation buttons
        nav_defs = [
            ('dashboard',     'Табло'),
            ('visits',        'Посещения'),
            ('reception',     'Регистрация'),
            ('subscriptions', 'Абонаменти'),
        ]
        if user['role'] == 'admin':
            nav_defs.append(('admin', 'Администрация'))

        self._nav_buttons = {}
        for key, label in nav_defs:
            btn = tk.Button(
                sidebar, text=label,
                command=lambda k=key: self._navigate(k),
                bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
                relief='flat', font=FONTS['nav'], cursor='hand2',
                padx=18, pady=9, bd=0, anchor='w',
            )
            btn.pack(fill='x', pady=1)
            self._nav_buttons[key] = btn

        # Bottom: user info + logout
        tk.Frame(sidebar, bg=COLORS['bg_medium']).pack(fill='both', expand=True)
        tk.Frame(sidebar, height=1, bg=COLORS['border']).pack(fill='x', padx=14)

        user_frame = tk.Frame(sidebar, bg=COLORS['bg_medium'], padx=16, pady=10)
        user_frame.pack(fill='x')

        role_label = 'Администратор' if user['role'] == 'admin' else 'Рецепционист'
        tk.Label(user_frame, text=user['full_name'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_primary'], font=FONTS['body_bold'],
                 wraplength=160, justify='left').pack(anchor='w')
        tk.Label(user_frame, text=role_label, bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['small']).pack(anchor='w', pady=(2, 4))

        make_button(user_frame, 'Смени парола',
                    command=self._change_password_dialog,
                    style='ghost', width=16).pack(anchor='w', pady=(0, 2))
        make_button(user_frame, 'База данни',
                    command=self._open_db_settings_dialog,
                    style='ghost', width=16).pack(anchor='w', pady=(0, 2))
        make_button(user_frame, 'За програмата',
                    command=self._about_dialog,
                    style='ghost', width=16).pack(anchor='w', pady=(0, 2))
        make_button(user_frame, 'Изход', command=self._logout,
                    style='ghost', width=16).pack(anchor='w')

        # ── Right side: topbar + content ──
        right_side = tk.Frame(self, bg=COLORS['bg_dark'])
        right_side.pack(side='left', fill='both', expand=True)

        # Global topbar with Bulgarian date — always visible
        self._topbar = tk.Frame(right_side, bg=COLORS['bg_medium'], padx=24, pady=10)
        self._topbar.pack(fill='x')
        self._topbar_title = tk.Label(self._topbar, text='', bg=COLORS['bg_medium'],
                                      fg=COLORS['gold'], font=FONTS['heading'])
        self._topbar_title.pack(side='left')

        # Window controls (since OS bar is hidden)
        ctrl_frame = tk.Frame(self._topbar, bg=COLORS['bg_medium'])
        ctrl_frame.pack(side='right')
        self._date_label = tk.Label(ctrl_frame, text='', bg=COLORS['bg_medium'],
                                    fg=COLORS['text_secondary'], font=FONTS['body'])
        self._date_label.pack(side='left', padx=(0, 20))
        # Close button — asks confirmation, then exits
        tk.Button(ctrl_frame, text='✕', command=self._confirm_quit,
                  bg=COLORS['bg_medium'], fg=COLORS['text_muted'],
                  relief='flat', font=FONTS['body_bold'], cursor='hand2',
                  bd=0, padx=12, pady=4,
                  activebackground=COLORS['danger'],
                  activeforeground='white').pack(side='left')

        self._update_date()

        # Main content area
        self._content = tk.Frame(right_side, bg=COLORS['bg_dark'])
        self._content.pack(fill='both', expand=True)

        # Build all panels
        self._panels['dashboard'] = Dashboard(
            self._content, user, on_navigate=self._navigate)
        self._panels['reception'] = ReceptionPanel(self._content, user)
        self._panels['visits'] = VisitsPanel(self._content, user)
        self._panels['subscriptions'] = SubscriptionsPanel(self._content, user)
        if user['role'] == 'admin':
            self._panels['admin'] = AdminPanel(
                self._content, user,
                on_user_changed=self._on_user_changed)

        for panel in self._panels.values():
            panel.place(x=0, y=0, relwidth=1, relheight=1)

        self._navigate('dashboard')

        # Keyboard shortcuts
        self.bind_all('<F5>', lambda e: self._refresh_current())
        self.bind_all('<Control-r>', lambda e: self._refresh_current())
        self.bind_all('<Control-1>', lambda e: self._navigate('dashboard'))
        self.bind_all('<Control-2>', lambda e: self._navigate('visits'))
        self.bind_all('<Control-3>', lambda e: self._navigate('reception'))
        self.bind_all('<Control-4>', lambda e: self._navigate('subscriptions'))

        # Show expiring notification after short delay
        self.after(800, self._check_expiring_notification)

    _NAV_TITLES = {
        'dashboard':     'Табло за управление',
        'reception':     'Регистрация на клиенти',
        'visits':        'Посещения',
        'subscriptions': 'Регистър на абонаменти',
        'reports':       'Справки и отчети',
        'admin':         'Административен панел',
    }

    def _update_date(self):
        """Update the topbar date label with Bulgarian weekday name."""
        bg_days = ['Понеделник', 'Вторник', 'Сряда', 'Четвъртък',
                   'Петък', 'Събота', 'Неделя']
        today = date.today()
        day_name = bg_days[today.weekday()]
        self._date_label.config(text=f'{today.strftime("%d.%m.%Y")}  —  {day_name}')
        # Store job so we can cancel on logout/rebuild
        self._date_job = self.after(60_000, self._update_date)

    def _navigate(self, key):
        if key not in self._panels:
            return

        # Don't re-navigate to the already active panel (no double-refresh)
        if key == self._active_nav:
            return

        # Update visual state FIRST (before refresh, so a crash there doesn't break UI)
        for k, btn in self._nav_buttons.items():
            btn.config(
                bg=COLORS['gold_dark'] if k == key else COLORS['bg_medium'],
                fg=COLORS['gold_light'] if k == key else COLORS['text_secondary'],
            )
        self._topbar_title.config(text=self._NAV_TITLES.get(key, ''))
        self._active_nav = key

        # Raise the panel
        for panel in self._panels.values():
            panel.lower()
        self._panels[key].lift()

        # Refresh panel data (in try/except so UI state is never left broken)
        if hasattr(self._panels[key], 'refresh'):
            try:
                self._panels[key].refresh()
            except Exception as e:
                import sys
                print(f"[navigate] refresh error on '{key}': {e}", file=sys.stderr)

    def _refresh_current(self):
        if self._active_nav and self._active_nav in self._panels:
            panel = self._panels[self._active_nav]
            if hasattr(panel, 'refresh'):
                panel.refresh()

    def _check_expiring_notification(self):
        """Show a top banner if memberships are expiring within 3 days."""
        try:
            import dal
            from datetime import date, timedelta
            today_str = date.today().strftime('%Y-%m-%d')
            cutoff = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')
            expiring = dal.get_subscriptions(
                end_from=today_str,
                end_to=cutoff,
                status_filter='active',
            )
            # Filter out visit-exhausted cards
            real_expiring = [s for s in expiring
                             if not (s.get('visits_limit') and s['visits_used'] >= s['visits_limit'])]
            if real_expiring:
                self._show_notification_banner(
                    f'⚠  {len(real_expiring)} абонамента изтичат в следващите 3 дни!',
                    COLORS['warning']
                )
        except Exception:
            pass

    def _show_notification_banner(self, message, color):
        """Show a dismissible banner at the top of the content area."""
        banner = tk.Frame(self._content, bg=color, pady=6)
        banner.place(x=0, y=0, relwidth=1)

        tk.Label(banner, text=message, bg=color, fg='#0D1B2A',
                 font=FONTS['body_bold']).pack(side='left', padx=16)

        def dismiss():
            banner.place_forget()

        tk.Button(banner, text='✕', command=dismiss, bg=color, fg='#0D1B2A',
                  relief='flat', font=FONTS['body_bold'], cursor='hand2',
                  bd=0, padx=10).pack(side='right', padx=8)

        # Auto-dismiss after 8 seconds
        self.after(8000, dismiss)

    def _logout(self):
        if confirm_dialog(self, 'Изход от акаунта',
                          'Сигурни ли сте, че искате да излезете от акаунта си?'):
            self._current_user = None
            self._show_login()

    def _confirm_quit(self):
        """Ask for confirmation before closing the program."""
        if confirm_dialog(self, 'Затваряне на програмата',
                          'Сигурни ли сте, че искате да затворите програмата?'):
            self.destroy()

    def _on_user_changed(self, changed_user_id, new_role, new_full_name):
        """Called by AdminPanel when a user is saved.
        If the changed user is the currently logged-in user,
        rebuild the entire UI immediately to reflect the new role/name.
        """
        if self._current_user and self._current_user['id'] == changed_user_id:
            # Update in-memory user record
            self._current_user['role'] = new_role
            self._current_user['full_name'] = new_full_name
            # Rebuild UI — this re-creates nav and all panels for the new role
            for w in self.winfo_children():
                w.destroy()
            self._panels = {}
            self._build_main_ui()

    def _change_password_dialog(self):
        from widgets import make_entry, show_message
        from db_config import check_password
        import dal

        dlg = tk.Toplevel(self)
        dlg.title('Смяна на парола')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        W, H = 360, 270
        px = self.winfo_x() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_y() + (self.winfo_height() - H) // 2)
        dlg.geometry(f'{W}x{H}+{px}+{py}')

        tk.Label(dlg, text='Смяна на парола', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(pady=(14, 8))

        # Buttons pinned to bottom
        btns = tk.Frame(dlg, bg=COLORS['bg_medium'])
        btns.pack(side='bottom', pady=10)
        from widgets import make_button as mb

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=24)
        form.pack(fill='x')

        for label, key, show in [
            ('Текуща парола', 'old', '•'),
            ('Нова парола', 'new', '•'),
            ('Повтори новата парола', 'rep', '•'),
        ]:
            tk.Label(form, text=label, bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
            v = tk.StringVar()
            make_entry(form, textvariable=v, width=36, show=show).pack(
                ipady=4, pady=(2, 8), fill='x')
            if key == 'old':
                old_var = v
            elif key == 'new':
                new_var = v
            else:
                rep_var = v

        def save():
            old_pw = old_var.get()
            new_pw = new_var.get()
            rep_pw = rep_var.get()
            if not old_pw or not new_pw or not rep_pw:
                show_message(dlg, 'Грешка', 'Попълнете всички полета!', 'error')
                return
            from db_config import get_connection
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT password_hash FROM users WHERE id=%s',
                        (self._current_user['id'],))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row or not check_password(old_pw, row['password_hash']):
                show_message(dlg, 'Грешка', 'Грешна текуща парола!', 'error')
                return
            if new_pw != rep_pw:
                show_message(dlg, 'Грешка', 'Новите пароли не съвпадат!', 'error')
                return
            if len(new_pw) < 6:
                show_message(dlg, 'Грешка', 'Паролата трябва да е поне 6 символа!', 'error')
                return
            dal.update_user(self._current_user['id'],
                            self._current_user['full_name'],
                            self._current_user['role'], new_pw)
            show_message(dlg, 'Успех', 'Паролата е сменена успешно!', 'success')
            dlg.destroy()

        mb(btns, 'Отказ', dlg.destroy, style='ghost').pack(side='left', padx=4)
        mb(btns, 'Запази', save, style='primary').pack(side='left', padx=4)


    def _open_db_settings_dialog(self):
        from db_settings import DBSettingsDialog
        DBSettingsDialog(self)

    def _about_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title('За програмата')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        W, H = 380, 260
        px = self.winfo_x() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_y() + (self.winfo_height() - H) // 2)
        dlg.geometry(f'{W}x{H}+{px}+{py}')

        tk.Frame(dlg, bg=COLORS['gold'], height=4).pack(fill='x')

        # Button pinned to bottom first
        make_button(dlg, 'Затвори', command=dlg.destroy,
                    style='primary').pack(side='bottom', pady=12)
        tk.Frame(dlg, height=1, bg=COLORS['border']).pack(side='bottom', fill='x', padx=30, pady=(0, 4))

        # Content
        tk.Label(dlg, text='✦', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=('Georgia', 28)).pack(pady=(14, 0))
        tk.Label(dlg, text='AQUA VITA', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=('Georgia', 16, 'bold')).pack()
        tk.Label(dlg, text='СПА & Уелнес система за управление',
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
                 font=FONTS['small']).pack(pady=(2, 8))

        tk.Frame(dlg, height=1, bg=COLORS['border']).pack(fill='x', padx=30, pady=(0, 8))

        info_frame = tk.Frame(dlg, bg=COLORS['bg_medium'])
        info_frame.pack()
        for label, value in [
            ('Версия:', '1.0.0'),
            ('Платформа:', 'Python + Tkinter + MySQL'),
            ('База данни:', 'XAMPP / MySQL 5.7+'),
        ]:
            row = tk.Frame(info_frame, bg=COLORS['bg_medium'])
            row.pack(fill='x', pady=2, padx=30)
            tk.Label(row, text=label, bg=COLORS['bg_medium'],
                     fg=COLORS['text_muted'], font=FONTS['small'],
                     width=12, anchor='w').pack(side='left')
            tk.Label(row, text=value, bg=COLORS['bg_medium'],
                     fg=COLORS['text_primary'], font=FONTS['small'],
                     anchor='w').pack(side='left')

# ─── ENTRY POINT ─────────────────────────────────────────────

def main():
    # Check DB connection first
    from db_config import test_connection
    ok, msg = test_connection()
    if not ok:
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror(
            'Грешка при свързване с база данни',
            f'{msg}\n\nМоля проверете:\n'
            '1. XAMPP стартиран и MySQL работи\n'
            '2. База данни "spa_system" е създадена\n'
            '3. SQL скриптът е изпълнен в phpMyAdmin\n\n'
            'Файл: database.sql'
        )
        root.destroy()
        return
    
    app = MainApp()
    app.mainloop()


if __name__ == '__main__':
    main()
