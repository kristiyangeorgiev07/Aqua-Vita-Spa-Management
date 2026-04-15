"""
Reception Panel — Регистрация на клиенти ONLY.
"""
import re
import tkinter as tk
import dal
from theme import COLORS, FONTS
from widgets import make_button, make_entry, StyledTreeview, show_message, confirm_dialog


def _center(dlg, parent, w, h):
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = max(20, parent.winfo_rooty() + (parent.winfo_height() - h) // 2)
    dlg.geometry(f'{w}x{h}+{px}+{py}')


def _validate_phone(ph):
    """Return error string or empty string if OK."""
    if not ph:
        return ''
    if not re.fullmatch(r'[\d\s\+\-\(\)]{6,15}', ph):
        return 'Невалиден телефон! (6–15 цифри, +, -, интервал)'
    return ''


def _validate_email(em):
    """Return error string or empty string if OK."""
    if not em:
        return ''
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', em):
        return 'Невалиден email! (формат: name@domain.com)'
    return ''


class ReceptionPanel(tk.Frame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self._build()

    def _build(self):
        body = tk.Frame(self, bg=COLORS['bg_dark'], padx=24, pady=16)
        body.pack(fill='both', expand=True)

        # ── Left: new client form ─────────────────────────────
        left = tk.Frame(body, bg=COLORS['bg_card'], padx=24, pady=20)
        left.pack(side='left', fill='y', padx=(0, 16))

        tk.Label(left, text='Нов клиент', bg=COLORS['bg_card'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(anchor='w', pady=(0, 14))

        self._cl_vars = {}
        self._cl_entries = {}
        for label, key in [('Собствено име *', 'fn'), ('Фамилия *', 'ln'),
                            ('Телефон', 'ph'), ('Email', 'em')]:
            tk.Label(left, text=label, bg=COLORS['bg_card'],
                     fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
            v = tk.StringVar()
            self._cl_vars[key] = v
            e = make_entry(left, textvariable=v, width=30)
            e.pack(ipady=6, pady=(3, 10), fill='x')
            self._cl_entries[key] = e

        self._cl_error = tk.StringVar()
        tk.Label(left, textvariable=self._cl_error, bg=COLORS['bg_card'],
                 fg=COLORS['danger'], font=FONTS['small'],
                 wraplength=240).pack(anchor='w')
        make_button(left, '+ Запази клиент', command=self._save_client,
                    style='primary').pack(fill='x', ipady=6, pady=(6, 0))

        # ── Right: client list (no ID column) ─────────────────
        right = tk.Frame(body, bg=COLORS['bg_dark'])
        right.pack(side='left', fill='both', expand=True)

        sr = tk.Frame(right, bg=COLORS['bg_dark'])
        sr.pack(fill='x', pady=(0, 8))
        tk.Label(sr, text='Търсене:', bg=COLORS['bg_dark'],
                 fg=COLORS['text_secondary'], font=FONTS['body']).pack(side='left', padx=(0, 8))
        self._cl_search_var = tk.StringVar()
        self._cl_search_var.trace('w', lambda *_: self._load_clients())
        make_entry(sr, textvariable=self._cl_search_var, width=28).pack(side='left', ipady=5)

        self._cl_tree = StyledTreeview(
            right,
            columns=('id', 'name', 'phone', 'email', 'reg'),
            headings=('', 'Клиент', 'Телефон', 'Email', 'Дата на регистрация'),
            col_widths=[0, 210, 130, 200, 130],
            height=18,
        )
        self._cl_tree.tree.column('id', width=0, minwidth=0, stretch=False)
        self._cl_tree.tree.heading('id', text='')
        self._cl_tree.pack(fill='both', expand=True)

        act = tk.Frame(right, bg=COLORS['bg_dark'], pady=6)
        act.pack(fill='x')
        make_button(act, 'Редактирай', command=self._edit_client_dialog,
                    style='secondary').pack(side='left', padx=(0, 6), ipady=3)
        make_button(act, 'Изтрий', command=self._delete_client,
                    style='danger').pack(side='left', ipady=3)

        self._load_clients()

    # ── Data ─────────────────────────────────────────────────

    def _load_clients(self):
        self._cl_tree.clear()
        q = self._cl_search_var.get() if hasattr(self, '_cl_search_var') else ''
        for c in dal.search_clients(q):
            reg = str(c['created_at'])[:10] if c.get('created_at') else '—'
            self._cl_tree.insert((
                c['id'],
                f"{c['first_name']} {c['last_name']}",
                c['phone'] or '—',
                c['email'] or '—',
                reg,
            ))

    def _save_client(self):
        fn = self._cl_vars['fn'].get().strip()
        ln = self._cl_vars['ln'].get().strip()
        ph = self._cl_vars['ph'].get().strip()
        em = self._cl_vars['em'].get().strip()

        if not fn or not ln:
            self._cl_error.set('Собственото име и фамилията са задължителни!')
            return

        err = _validate_phone(ph)
        if err:
            self._cl_error.set(err)
            return

        err = _validate_email(em)
        if err:
            self._cl_error.set(err)
            return

        try:
            dal.create_client(fn, ln, ph, em)
            for v in self._cl_vars.values():
                v.set('')
            self._cl_error.set('')
            show_message(self, 'Успех', 'Клиентът е добавен успешно!', 'success')
            self._load_clients()
        except Exception as e:
            self._cl_error.set(str(e))

    def _edit_client_dialog(self):
        vals = self._cl_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете клиент от списъка', 'warning')
            return
        client = dal.get_client_by_id(vals[0])
        if not client:
            return
        dlg = tk.Toplevel(self)
        dlg.title('Редактиране на клиент')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        W, H = 420, 340
        px = self.winfo_rootx() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_rooty() + (self.winfo_height() - H) // 2)
        dlg.geometry(f'{W}x{H}+{px}+{py}')

        tk.Label(dlg, text='Редактиране на клиент', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(pady=(14, 6))

        # Buttons packed FIRST so side='bottom' works in Tkinter
        btns_frame = tk.Frame(dlg, bg=COLORS['bg_medium'])
        btns_frame.pack(side='bottom', pady=10)
        make_button(btns_frame, 'Отказ', dlg.destroy, style='ghost').pack(side='left', padx=4)

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=24)
        form.pack(fill='x')

        fdata = [('Собствено Име *', 'fn', client['first_name']),
                 ('Фамилия *', 'ln', client['last_name']),
                 ('Телефон', 'ph', client['phone'] or ''),
                 ('Email', 'em', client['email'] or '')]
        vars_ = {}
        for label, key, default in fdata:
            tk.Label(form, text=label, bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
            v = tk.StringVar(value=default)
            vars_[key] = v
            make_entry(form, textvariable=v, width=44).pack(ipady=4, pady=(2, 6), fill='x')

        err_var = tk.StringVar()
        tk.Label(form, textvariable=err_var, bg=COLORS['bg_medium'],
                 fg=COLORS['danger'], font=FONTS['small'],
                 wraplength=360).pack(anchor='w')

        def save():
            fn = vars_['fn'].get().strip()
            ln = vars_['ln'].get().strip()
            ph = vars_['ph'].get().strip()
            em = vars_['em'].get().strip()
            if not fn or not ln:
                err_var.set('Задължителните полета са празни!')
                return
            err = _validate_phone(ph)
            if err:
                err_var.set(err)
                return
            err = _validate_email(em)
            if err:
                err_var.set(err)
                return
            dal.update_client(client['id'], fn, ln, ph, em)
            show_message(dlg, 'Успех', 'Клиентът е обновен!', 'success')
            dlg.destroy()
            self._load_clients()

        make_button(btns_frame, 'Запази', save, style='primary').pack(side='left', padx=4)
    def _delete_client(self):
        vals = self._cl_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете клиент от списъка', 'warning')
            return
        if confirm_dialog(self, 'Изтриване', f'Изтриване на "{vals[1]}"?'):
            try:
                dal.delete_client(vals[0])
                self._load_clients()
            except Exception as e:
                show_message(self, 'Грешка', str(e), 'error')

    def refresh(self):
        self._load_clients()
