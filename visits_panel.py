"""
Visits Panel — standalone check-in by Subscription ID.
"""
import tkinter as tk
from datetime import date
import dal
from theme import COLORS, FONTS
from widgets import make_button, make_entry, StyledTreeview, show_message


class VisitsPanel(tk.Frame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self._selected_sub = [None]
        self._build()

    def _build(self):
        body = tk.Frame(self, bg=COLORS['bg_dark'], padx=24, pady=16)
        body.pack(fill='both', expand=True)

        # ── Left: check-in form ──────────────────────────────
        left = tk.Frame(body, bg=COLORS['bg_card'], padx=24, pady=22)
        left.pack(side='left', fill='y', padx=(0, 16))

        tk.Label(left, text='Регистрация на посещение',
                 bg=COLORS['bg_card'], fg=COLORS['gold'],
                 font=FONTS['heading']).pack(anchor='w', pady=(0, 18))

        tk.Label(left, text='Номер на абонамент (ID) *',
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                 font=FONTS['small']).pack(anchor='w')

        self._id_var = tk.StringVar()
        self._id_entry = make_entry(left, textvariable=self._id_var, width=14)
        self._id_entry.pack(ipady=8, pady=(3, 10), anchor='w')
        self._id_entry.bind('<KeyRelease>', lambda e: self._lookup())
        # Enter key triggers registration if a valid subscription is loaded
        self._id_entry.bind('<Return>', lambda e: self._do_register())

        # Info card
        self._info_frame = tk.Frame(left, bg=COLORS['bg_medium'], padx=14, pady=12)
        self._info_frame.pack(fill='x', pady=(0, 14))
        tk.Label(self._info_frame, text='Въведете ID на абонамент',
                 bg=COLORS['bg_medium'], fg=COLORS['text_muted'],
                 font=FONTS['small']).pack(anchor='w')

        tk.Label(left, text='Бележка (незадължително)',
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                 font=FONTS['small']).pack(anchor='w')
        self._notes_var = tk.StringVar()
        make_entry(left, textvariable=self._notes_var, width=30,
                   placeholder='напр. процедура, зала...').pack(ipady=5, pady=(3, 12), fill='x')

        self._error_var = tk.StringVar()
        tk.Label(left, textvariable=self._error_var,
                 bg=COLORS['bg_card'], fg=COLORS['danger'],
                 font=FONTS['small'], wraplength=260).pack(anchor='w')

        self._btn = make_button(left, 'Регистрирай посещение',
                                command=self._do_register, style='success')
        self._btn.pack(fill='x', ipady=8, pady=(6, 0))
        self._btn.config(state='disabled', bg=COLORS['bg_medium'])

        # ── Right: today's visits log ─────────────────────────
        right = tk.Frame(body, bg=COLORS['bg_dark'])
        right.pack(side='left', fill='both', expand=True)

        hdr = tk.Frame(right, bg=COLORS['bg_dark'])
        hdr.pack(fill='x', pady=(0, 6))
        tk.Label(hdr, text='ПОСЕЩЕНИЯ ДНЕС', bg=COLORS['bg_dark'],
                 fg=COLORS['text_muted'],
                 font=('Calibri', 8, 'bold')).pack(side='left')
        self._count_lbl = tk.Label(hdr, text='', bg=COLORS['bg_dark'],
                                    fg=COLORS['gold'], font=FONTS['body_bold'])
        self._count_lbl.pack(side='right')

        self._tree = StyledTreeview(
            right,
            columns=('time', 'sub_id', 'client', 'plan', 'notes', 'by'),
            headings=('Час', 'Абон. #', 'Клиент', 'Абонамент', 'Бележка', 'Регистрирал'),
            col_widths=[65, 75, 165, 145, 130, 120],
            height=20,
        )
        self._tree.pack(fill='both', expand=True)

        self._load_today()

    # ── Lookup ────────────────────────────────────────────────
    def _lookup(self):
        id_str = self._id_var.get().strip()
        for w in self._info_frame.winfo_children():
            w.destroy()
        self._selected_sub[0] = None
        self._btn.config(state='disabled', bg=COLORS['bg_medium'],
                         text='Регистрирай посещение')
        self._error_var.set('')

        if not id_str:
            tk.Label(self._info_frame, text='Въведете ID на абонамент',
                     bg=COLORS['bg_medium'], fg=COLORS['text_muted'],
                     font=FONTS['small']).pack(anchor='w')
            return
        if not id_str.isdigit():
            return

        try:
            sub = dal.get_subscription_by_id(int(id_str))
        except Exception:
            sub = None

        if not sub:
            tk.Label(self._info_frame,
                     text=f'Абонамент #{id_str} не е намерен',
                     bg=COLORS['bg_medium'], fg=COLORS['danger'],
                     font=FONTS['body_bold']).pack(anchor='w')
            return

        days = sub['days_left'] if sub['days_left'] is not None else -1
        exhausted = bool(sub.get('visits_limit') and sub['visits_used'] >= sub['visits_limit'])
        can_enter = (sub['status'] == 'active' and days >= 0 and not exhausted)
        color = COLORS['success'] if can_enter else COLORS['danger']

        name = f"{sub['first_name']} {sub['last_name']}"
        tk.Label(self._info_frame, text=name,
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                 font=FONTS['body_bold']).pack(anchor='w')
        tk.Label(self._info_frame, text=sub['plan_name'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
                 font=FONTS['small']).pack(anchor='w')

        if sub['status'] == 'cancelled':
            tk.Label(self._info_frame, text='Статус: Отменен',
                     bg=COLORS['bg_medium'], fg=COLORS['danger'],
                     font=FONTS['small']).pack(anchor='w')
        elif sub['status'] == 'expired' or days < 0:
            tk.Label(self._info_frame, text='Абонаментът е изтекъл',
                     bg=COLORS['bg_medium'], fg=COLORS['danger'],
                     font=FONTS['small']).pack(anchor='w')
        elif exhausted:
            tk.Label(self._info_frame, text='Посещенията са изчерпани',
                     bg=COLORS['bg_medium'], fg=COLORS['danger'],
                     font=FONTS['small']).pack(anchor='w')
        else:
            tk.Label(self._info_frame,
                     text=f'Валиден до: {sub["end_date"]}  ·  {days} дни',
                     bg=COLORS['bg_medium'], fg=color,
                     font=FONTS['small']).pack(anchor='w')
            if sub.get('visits_limit'):
                remaining = sub['visits_limit'] - sub['visits_used']
                tk.Label(self._info_frame,
                         text=f'Оставащи посещения: {remaining}',
                         bg=COLORS['bg_medium'], fg=color,
                         font=FONTS['small']).pack(anchor='w')

        if can_enter:
            self._selected_sub[0] = sub
            self._btn.config(state='normal', bg=COLORS['success'],
                             text=f'Регистрирай посещение  (#{id_str})')

    # ── Register ──────────────────────────────────────────────
    def _do_register(self):
        sub = self._selected_sub[0]
        if not sub:
            self._error_var.set('Изберете валиден абонамент!')
            return
        try:
            ok, msg = dal.register_visit(
                sub['id'], sub['client_id'],
                self.current_user['id'],
                self._notes_var.get().strip())
            if ok:
                self._error_var.set('')
                self._notes_var.set('')
                self._id_var.set('')
                for w in self._info_frame.winfo_children():
                    w.destroy()
                tk.Label(self._info_frame, text='Въведете ID на абонамент',
                         bg=COLORS['bg_medium'], fg=COLORS['text_muted'],
                         font=FONTS['small']).pack(anchor='w')
                self._btn.config(state='disabled', bg=COLORS['bg_medium'],
                                 text='Регистрирай посещение')
                self._selected_sub[0] = None
                self._load_today()
                show_message(self, 'Успех', msg, 'success')
            else:
                self._error_var.set(msg)
        except Exception as e:
            self._error_var.set(str(e))

    # ── Today log ─────────────────────────────────────────────
    def _load_today(self):
        self._tree.clear()
        today = date.today()
        count = 0
        for v in dal.get_recent_visits(300):
            if v['visit_date'].date() == today:
                self._tree.insert((
                    v['visit_date'].strftime('%H:%M'),
                    f"#{v['subscription_id']}",
                    f"{v['first_name']} {v['last_name']}",
                    v['plan_name'],
                    v.get('notes') or '—',
                    v.get('registered_by_name') or '—'))
                count += 1
        self._count_lbl.config(text=f'{count} посещения')

    def refresh(self):
        self._load_today()
        # Focus ID field when panel becomes visible (deferred so widget is ready)
        self.after(50, self._focus_id_entry)

    def _focus_id_entry(self):
        try:
            if self._id_entry.winfo_exists():
                self._id_entry.focus()
        except Exception:
            pass
