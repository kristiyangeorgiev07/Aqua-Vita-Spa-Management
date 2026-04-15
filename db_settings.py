"""
Database Connection Settings Dialog
Saves config to a local settings.ini file so users don't edit source code.
"""
import tkinter as tk
import configparser
import os
from theme import COLORS, FONTS
from widgets import make_button, make_entry, show_message

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.ini')


def load_db_settings():
    """Load DB settings from settings.ini, with XAMPP defaults."""
    cfg = configparser.ConfigParser()
    cfg.read(SETTINGS_FILE, encoding='utf-8')
    return {
        'host':     cfg.get('database', 'host',     fallback='localhost'),
        'port':     cfg.get('database', 'port',     fallback='3306'),
        'user':     cfg.get('database', 'user',     fallback='root'),
        'password': cfg.get('database', 'password', fallback=''),
        'database': cfg.get('database', 'database', fallback='spa_system'),
    }


def save_db_settings(host, port, user, password, database):
    """Persist DB settings to settings.ini."""
    cfg = configparser.ConfigParser()
    cfg['database'] = {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database,
    }
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        cfg.write(f)


def apply_settings_to_db_config():
    """Push loaded settings into db_config.DB_CONFIG at runtime."""
    import db_config
    s = load_db_settings()
    db_config.DB_CONFIG.update({
        'host':     s['host'],
        'port':     int(s['port']),
        'user':     s['user'],
        'password': s['password'],
        'database': s['database'],
    })


class DBSettingsDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        self._build()

    def _build(self):
        dlg = tk.Toplevel(self.parent)
        dlg.title('Настройки на база данни')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        dlg.geometry('420x400')

        px = self.parent.winfo_rootx() + (self.parent.winfo_width() - 420) // 2
        py = max(20, self.parent.winfo_rooty() + (self.parent.winfo_height() - 400) // 2)
        dlg.geometry(f'420x400+{px}+{py}')
        self._dlg = dlg

        # Header bar
        hbar = tk.Frame(dlg, bg=COLORS['gold_dark'], height=4)
        hbar.pack(fill='x')

        tk.Label(dlg, text='⚙  Настройки на връзката', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(pady=(18, 4))
        tk.Label(dlg, text='Конфигурация на MySQL / XAMPP връзката',
                 bg=COLORS['bg_medium'], fg=COLORS['text_muted'],
                 font=FONTS['small']).pack()

        tk.Frame(dlg, height=1, bg=COLORS['border']).pack(fill='x', padx=20, pady=12)

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=28)
        form.pack(fill='x')

        current = load_db_settings()
        fields = [
            ('Хост (Host)',          'host',     current['host']),
            ('Порт (Port)',           'port',     current['port']),
            ('Потребител (User)',     'user',     current['user']),
            ('Парола (Password)',     'password', current['password']),
            ('База данни (Database)', 'database', current['database']),
        ]
        self._vars = {}
        for label, key, default in fields:
            row = tk.Frame(form, bg=COLORS['bg_medium'])
            row.pack(fill='x', pady=4)
            tk.Label(row, text=label, bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary'], font=FONTS['small'],
                     width=22, anchor='w').pack(side='left')
            v = tk.StringVar(value=default)
            self._vars[key] = v
            show_char = '•' if key == 'password' else ''
            e = make_entry(row, textvariable=v, width=20, show=show_char)
            e.pack(side='left', ipady=4)

        tk.Frame(dlg, height=1, bg=COLORS['border']).pack(fill='x', padx=20, pady=12)

        # Test + Save buttons
        btn_frame = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=28)
        btn_frame.pack(side='bottom', fill='x', pady=10)

        self._status_var = tk.StringVar()
        tk.Label(btn_frame, textvariable=self._status_var, bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted'], font=FONTS['small'],
                 wraplength=360).pack(anchor='w', pady=(0, 8))

        btns = tk.Frame(btn_frame, bg=COLORS['bg_medium'])
        btns.pack(fill='x')
        make_button(btns, 'Тест на връзката', command=self._test,
                    style='secondary').pack(side='left', padx=(0, 8), ipady=3)
        make_button(btns, 'Отказ', command=dlg.destroy,
                    style='ghost').pack(side='right', padx=(8, 0), ipady=3)
        make_button(btns, 'Запази', command=self._save,
                    style='primary').pack(side='right', ipady=3)

    def _get_values(self):
        return {k: v.get().strip() for k, v in self._vars.items()}

    def _test(self):
        vals = self._get_values()
        self._status_var.set('⏳ Свързване...')
        self._dlg.update()
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=vals['host'], port=int(vals['port']),
                user=vals['user'], password=vals['password'],
                database=vals['database'], connection_timeout=5,
            )
            conn.close()
            self._status_var.set('✓ Връзката е успешна!')
        except Exception as e:
            self._status_var.set(f'✗ Грешка: {e}')

    def _save(self):
        vals = self._get_values()
        if not vals['host'] or not vals['database']:
            show_message(self._dlg, 'Грешка', 'Хостът и базата данни са задължителни!', 'error')
            return
        save_db_settings(**vals)
        apply_settings_to_db_config()
        show_message(self._dlg, 'Успех',
                     'Настройките са запазени!\nПромените влизат в сила при следващото стартиране.',
                     'success')
        self.result = True
        self._dlg.destroy()
