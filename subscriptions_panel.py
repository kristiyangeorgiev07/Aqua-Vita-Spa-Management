"""
Subscriptions Panel — live search, exact date filters, calendar with year/month nav.
Status "Изтекъл" for both date-expired and visits-exhausted.
Prices shown in EUR (€).
"""
import calendar as _cal
import tkinter as tk
from tkinter import ttk
from datetime import date
import dal
from theme import COLORS, FONTS
from widgets import make_button, make_entry, StyledTreeview, show_message, confirm_dialog
from receipt import generate_receipt


# ── Calendar picker ───────────────────────────────────────────
class DatePicker(tk.Frame):
    """Read-only date entry + fixed-size popup calendar."""

    MONTHS = ['Януари','Февруари','Март','Април','Май','Юни',
               'Юли','Август','Септември','Октомври','Ноември','Декември']

    CELL_W = 32
    CELL_H = 26

    def __init__(self, parent, variable, bg=None, **kwargs):
        super().__init__(parent, bg=bg or COLORS['bg_card'])
        self._var   = variable
        self._bg    = bg or COLORS['bg_card']
        self._popup = None
        self._session = 0       # incremented each time popup opens; stale handlers bail out
        self._closed_at = 0.0   # timestamp of last _close(); prevents immediate reopen

        self._display = tk.StringVar(value=variable.get() or '')
        tk.Entry(self, textvariable=self._display, width=11,
                 bg=COLORS['bg_input'], fg=COLORS['text_primary'],
                 insertbackground=COLORS['gold'], relief='flat',
                 font=FONTS['body'], highlightthickness=1,
                 highlightcolor=COLORS['border'],
                 highlightbackground=COLORS['border'],
                 state='readonly',
                 readonlybackground=COLORS['bg_input']).pack(side='left', ipady=4)

        self._btn = tk.Button(self, text='📅', command=self._toggle,
                              bg=COLORS['bg_input'], fg=COLORS['gold'],
                              relief='flat', font=('Calibri', 10), cursor='hand2',
                              bd=0, padx=4, pady=3)
        self._btn.pack(side='left', padx=(2, 0))

        tk.Button(self, text='✕', command=self._clear,
                  bg=self._bg, fg=COLORS['text_muted'],
                  relief='flat', font=('Calibri', 9), cursor='hand2',
                  bd=0, padx=2).pack(side='left')

    def _clear(self):
        self._var.set('')
        self._display.set('')

    def _is_open(self):
        return self._popup is not None and self._popup.winfo_exists()

    def _close(self):
        """Close popup and invalidate session so stale handlers do nothing."""
        import time as _time
        self._session  += 1
        self._closed_at = _time.monotonic()
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None

    def _toggle(self):
        """Toggle popup open/closed. This is the button command.
        Guard: if popup was closed within 150 ms, skip open (same-click race).
        """
        import time as _time
        if self._is_open():
            self._close()
        elif _time.monotonic() - self._closed_at < 0.15:
            # Popup was just closed by _on_press on this same click — do nothing
            pass
        else:
            self._open_popup()

    def _open_popup(self):
        self._close()   # ensure clean state

        self.update_idletasks()
        ox = self.winfo_rootx()
        oy = self.winfo_rooty() + self.winfo_height() + 2

        try:
            cur = date.fromisoformat(self._var.get()) if self._var.get() else date.today()
        except ValueError:
            cur = date.today()

        state = {'year': cur.year, 'month': cur.month}

        popup = tk.Toplevel(self)
        self._popup  = popup
        my_session   = self._session   # capture session id for this popup lifetime

        popup.overrideredirect(True)
        popup.configure(bg=COLORS['border'])
        popup.resizable(False, False)

        inner = tk.Frame(popup, bg=COLORS['bg_medium'], padx=1, pady=1)
        inner.pack(fill='both', expand=True)

        HDR  = COLORS['bg_dark']
        CELL = COLORS['bg_card']

        # ── nav row ───────────────────────────────────────────
        nav = tk.Frame(inner, bg=HDR, pady=4)
        nav.pack(fill='x')

        # LEFT: ◀◀ year  ◀ month
        tk.Button(nav, text='◀◀', command=lambda: _shift_year(-1),
                  bg=HDR, fg=COLORS['text_muted'], relief='flat',
                  font=('Calibri', 8), cursor='hand2', bd=0, padx=6).pack(side='left')
        tk.Button(nav, text='◀', command=lambda: _shift_month(-1),
                  bg=HDR, fg=COLORS['gold'], relief='flat',
                  font=('Calibri', 11), cursor='hand2', bd=0, padx=8).pack(side='left')

        hdr_lbl = tk.Label(nav, text='', bg=HDR, fg=COLORS['gold'],
                           font=FONTS['body_bold'], width=14, anchor='center')
        hdr_lbl.pack(side='left', expand=True)

        # RIGHT: pack ▶▶ first (rightmost), then ▶ → displays as "▶ месец  ▶▶ година"
        tk.Button(nav, text='▶▶', command=lambda: _shift_year(1),
                  bg=HDR, fg=COLORS['text_muted'], relief='flat',
                  font=('Calibri', 8), cursor='hand2', bd=0, padx=6).pack(side='right')
        tk.Button(nav, text='▶', command=lambda: _shift_month(1),
                  bg=HDR, fg=COLORS['gold'], relief='flat',
                  font=('Calibri', 11), cursor='hand2', bd=0, padx=8).pack(side='right')

        # ── fixed canvas ──────────────────────────────────────
        COLS = 7
        ROWS = 7   # 1 header + 6 week rows max
        CW, CH = self.CELL_W, self.CELL_H
        canvas = tk.Canvas(inner,
                           width=COLS * CW,
                           height=ROWS * CH,
                           bg=COLORS['bg_medium'],
                           highlightthickness=0)
        canvas.pack(padx=4, pady=(0, 4))

        DAYS = ['Пн','Вт','Ср','Чт','Пт','Сб','Нд']
        _day_btns = []

        def _draw():
            for b in _day_btns:
                try: b.destroy()
                except Exception: pass
            _day_btns.clear()
            canvas.delete('all')

            y, m = state['year'], state['month']
            hdr_lbl.config(text=f"{self.MONTHS[m-1]}  {y}")

            for col, name in enumerate(DAYS):
                x = col * CW + CW // 2
                canvas.create_text(x, CH // 2, text=name,
                                   fill=COLORS['text_muted'],
                                   font=('Calibri', 8, 'bold'))

            first_wd = _cal.monthrange(y, m)[0]
            num_days = _cal.monthrange(y, m)[1]
            r, c = 1, first_wd
            for day in range(1, num_days + 1):
                d = date(y, m, day)
                is_today = (d == date.today())
                is_sel   = (self._var.get() == str(d))
                bg = COLORS['gold']      if is_sel  else \
                     COLORS['teal_dark'] if is_today else CELL
                fg = '#0D1B2A' if is_sel else COLORS['text_primary']

                def _pick(dt=d):
                    self._var.set(str(dt))
                    self._display.set(str(dt))
                    self._close()

                bx = c * CW + 1
                by = r * CH + 1
                btn = tk.Button(canvas, text=str(day), command=_pick,
                                bg=bg, fg=fg, relief='flat',
                                font=('Calibri', 9), cursor='hand2', bd=0,
                                activebackground=COLORS['gold'],
                                activeforeground='#0D1B2A')
                canvas.create_window(bx, by, anchor='nw',
                                     width=CW - 2, height=CH - 2, window=btn)
                _day_btns.append(btn)
                c += 1
                if c > 6:
                    c = 0
                    r += 1

            popup.geometry(f'+{ox}+{oy}')

        def _shift_month(delta):
            m = state['month'] + delta
            y = state['year']
            if m < 1:  m = 12; y -= 1
            elif m > 12: m = 1; y += 1
            state['month'] = m
            state['year']  = y
            _draw()

        def _shift_year(delta):
            state['year'] += delta
            _draw()

        _draw()

        # ── outside-click: bind to root, check session to avoid stale fires ──
        root = self.winfo_toplevel()

        def _on_press(e):
            # Stale handler from a previous popup — ignore
            if self._session != my_session:
                return
            if not self._is_open():
                return
            def _inside(w):
                try:
                    x0, y0 = w.winfo_rootx(), w.winfo_rooty()
                    x1, y1 = x0 + w.winfo_width(), y0 + w.winfo_height()
                    return x0 <= e.x_root <= x1 and y0 <= e.y_root <= y1
                except Exception:
                    return False
            if _inside(popup) or _inside(self._btn):
                return
            self._close()

        bid = root.bind('<Button-1>', _on_press, add='+')

        def _cleanup(e=None):
            try:
                root.unbind('<Button-1>', bid)
            except Exception:
                pass
        popup.bind('<Destroy>', _cleanup)


# ── Main Panel ────────────────────────────────────────────────
class SubscriptionsPanel(tk.Frame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self._build()

    def _build(self):
        # Filters card — tighter padding on small screens
        _sh = self.winfo_screenheight()
        _fc_pady  = 6  if _sh <= 768 else 12
        _fc_outer = (6, 0) if _sh <= 768 else (12, 0)
        fc = tk.Frame(self, bg=COLORS['bg_card'], padx=16, pady=_fc_pady)
        fc.pack(fill='x', padx=16, pady=_fc_outer)

        row = tk.Frame(fc, bg=COLORS['bg_card'])
        row.pack(fill='x')

        # Client name — live
        f1 = tk.Frame(row, bg=COLORS['bg_card'])
        f1.pack(side='left', padx=(0, 16))
        tk.Label(f1, text='Клиент', bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        self.client_var = tk.StringVar()
        self.client_var.trace('w', lambda *_: self._search())
        make_entry(f1, textvariable=self.client_var, width=20).pack(ipady=5, pady=(2, 0))

        # Start date — exact
        f2 = tk.Frame(row, bg=COLORS['bg_card'])
        f2.pack(side='left', padx=(0, 16))
        tk.Label(f2, text='Начало (точна дата)', bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        self.start_var = tk.StringVar()
        self.start_var.trace('w', lambda *_: self._search())
        DatePicker(f2, self.start_var, bg=COLORS['bg_card']).pack(pady=(2, 0))

        # End date — exact
        f3 = tk.Frame(row, bg=COLORS['bg_card'])
        f3.pack(side='left', padx=(0, 16))
        tk.Label(f3, text='Край (точна дата)', bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        self.end_var = tk.StringVar()
        self.end_var.trace('w', lambda *_: self._search())
        DatePicker(f3, self.end_var, bg=COLORS['bg_card']).pack(pady=(2, 0))

        # Status
        f4 = tk.Frame(row, bg=COLORS['bg_card'])
        f4.pack(side='left', padx=(0, 16))
        tk.Label(f4, text='Статус', bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        self.status_var = tk.StringVar(value='Всички')
        status_cb = ttk.Combobox(f4, textvariable=self.status_var,
                                  values=['Всички', 'Активни', 'Изтекли', 'Отменени'],
                                  width=12, state='readonly')
        status_cb.pack(ipady=3, pady=(2, 0))
        self.status_var.trace('w', lambda *_: self._search())

        # Stats label
        self.stats_var = tk.StringVar(value='')
        _stats_pady = (4, 0) if _sh <= 768 else (8, 0)
        tk.Label(fc, textvariable=self.stats_var, bg=COLORS['bg_card'],
                 fg=COLORS['text_muted'], font=FONTS['small']).pack(anchor='w', pady=_stats_pady)

        # Treeview — height adapts to screen resolution
        screen_h = self.winfo_screenheight()
        if screen_h <= 768:
            tree_height = 10
            tree_pady   = 4
            ab_pady     = 4
        elif screen_h <= 900:
            tree_height = 13
            tree_pady   = 6
            ab_pady     = 6
        else:
            tree_height = 18
            tree_pady   = 10
            ab_pady     = 8

        tf = tk.Frame(self, bg=COLORS['bg_dark'], padx=16, pady=tree_pady)
        tf.pack(fill='both', expand=True)
        self.sub_tree = StyledTreeview(
            tf,
            columns=('id', 'client', 'phone', 'plan', 'start', 'end',
                     'days_left', 'visits', 'status', 'sold_by'),
            headings=('ID', 'Клиент', 'Телефон', 'Абонамент', 'Начало', 'Изтичане',
                      'Оставащи дни', 'Посещения', 'Статус', 'Продал'),
            col_widths=[48, 155, 110, 140, 95, 95, 95, 80, 85, 120],
            height=tree_height,
        )
        self.sub_tree.pack(fill='both', expand=True)
        self.sub_tree.tree.bind('<Double-1>', lambda e: self._print_receipt())

        # Action bar
        ab = tk.Frame(self, bg=COLORS['bg_dark'], padx=16, pady=ab_pady)
        ab.pack(fill='x')
        if self.current_user['role'] == 'admin':
            make_button(ab, 'Отмени абонамент', command=self._cancel_sub,
                        style='danger').pack(side='right', padx=4, ipady=3)
            make_button(ab, '+ Нов абонамент', command=self._new_sub_dialog,
                        style='primary').pack(side='right', padx=4, ipady=3)
        make_button(ab, 'Квитанция', command=self._print_receipt,
                    style='ghost').pack(side='right', padx=4, ipady=3)

        self._search()

    _STATUS_MAP = {'Всички': 'all', 'Активни': 'active',
                   'Изтекли': 'expired', 'Отменени': 'cancelled'}

    @staticmethod
    def _resolve_status(s):
        exhausted = (s['status'] == 'active'
                     and s.get('visits_limit')
                     and s['visits_used'] >= s['visits_limit'])
        days = s['days_left']
        if s['status'] == 'cancelled':
            return 'Отменен', 'odd'
        if exhausted or s['status'] == 'expired' or (days is not None and days < 0):
            return 'Изтекъл', 'expired'
        if days is not None and days <= 7:
            return 'Активен', 'expiring'
        return 'Активен', 'active'

    def _search(self):
        client_name = self.client_var.get().strip()
        start = self.start_var.get().strip() or None
        end   = self.end_var.get().strip() or None
        status = self._STATUS_MAP.get(self.status_var.get(), 'all')

        for val in [start, end]:
            if val:
                try:
                    date.fromisoformat(val)
                except ValueError:
                    return

        try:
            subs = dal.get_subscriptions(
                client_name=client_name,
                start_exact=start,
                end_exact=end,
                status_filter=status,
            )
            self.sub_tree.clear()
            for s in subs:
                status_lbl, tag = self._resolve_status(s)
                days = s['days_left']
                days_str = (f'{days} дни' if isinstance(days, int) and days >= 0
                            else 'Изтекъл')
                if status_lbl == 'Изтекъл':
                    days_str = 'Изтекъл'
                visits_str = (f"{s['visits_used']}/{s['visits_limit']}"
                              if s['visits_limit'] else f"{s['visits_used']}/∞")
                self.sub_tree.insert((
                    s['id'],
                    f"{s['first_name']} {s['last_name']}",
                    s['phone'] or '—',
                    s['plan_name'],
                    str(s['start_date']),
                    str(s['end_date']),
                    days_str,
                    visits_str,
                    status_lbl,
                    s['sold_by_name'] or '—',
                ), tags=(tag,))
            self.stats_var.set(f'Намерени: {len(subs)} записа')
        except Exception as e:
            show_message(self, 'Грешка', str(e), 'error')

    def _clear_filters(self):
        self.client_var.set('')
        self.start_var.set('')
        self.end_var.set('')
        self.status_var.set('Всички')

    def _cancel_sub(self):
        vals = self.sub_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете абонамент от списъка', 'warning')
            return
        if vals[8] != 'Активен':
            show_message(self, 'Внимание', 'Може да отмените само активни абонаменти!', 'warning')
            return
        if confirm_dialog(self, 'Отмяна', f'Отмяна на абонамент #{vals[0]}?'):
            try:
                dal.cancel_subscription(vals[0])
                show_message(self, 'Успех', 'Абонаментът е отменен', 'success')
                self._search()
            except Exception as e:
                show_message(self, 'Грешка', str(e), 'error')

    def _print_receipt(self):
        vals = self.sub_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете абонамент от списъка', 'warning')
            return
        try:
            full = dal.get_subscription_by_id(vals[0])
            if not full:
                return
            client = {'first_name': full['first_name'], 'last_name': full['last_name'],
                      'phone': full['phone'], 'email': full.get('email', '')}
            plan = {'name': full['plan_name'], 'price': full['price'],
                    'duration_days': full['duration_days'], 'visits_limit': full['visits_limit']}
            generate_receipt(client, full, plan, full.get('sold_by_name') or '')
        except Exception as e:
            show_message(self, 'Грешка', str(e), 'error')

    def _new_sub_dialog(self):
        plans = dal.get_all_plans(active_only=True)
        if not plans:
            show_message(self, 'Грешка', 'Няма активни планове!', 'error')
            return

        dlg = tk.Toplevel(self)
        dlg.title('Нов абонамент')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        W, H = 500, 500
        px = self.winfo_rootx() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_rooty() + (self.winfo_height() - H) // 2)
        dlg.geometry(f'{W}x{H}+{px}+{py}')

        tk.Label(dlg, text='Нов абонамент', bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(pady=(12, 0))

        # Buttons pinned to bottom
        btns = tk.Frame(dlg, bg=COLORS['bg_medium'])
        btns.pack(side='bottom', pady=10)
        make_button(btns, 'Отказ', dlg.destroy, style='ghost').pack(side='left', padx=4)

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=24)
        form.pack(fill='x', pady=8)

        tk.Label(form, text='Клиент *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        search_var = tk.StringVar()
        make_entry(form, textvariable=search_var, width=44).pack(fill='x', ipady=4, pady=(2, 4))

        lb_f = tk.Frame(form, bg=COLORS['bg_card'])
        lb_f.pack(fill='x', pady=(0, 8))
        lb = tk.Listbox(lb_f, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                        selectbackground=COLORS['teal_dark'], height=5,
                        relief='flat', highlightthickness=0, activestyle='none',
                        font=FONTS['body'])
        lbs = tk.Scrollbar(lb_f, orient='vertical', command=lb.yview)
        lb.configure(yscrollcommand=lbs.set)
        lb.pack(side='left', fill='both', expand=True)
        lbs.pack(side='right', fill='y')

        all_clients = dal.search_clients('')
        filtered = [all_clients[:]]
        sel_client = [None]

        def populate(q=''):
            fc = [c for c in all_clients
                  if q.lower() in f"{c['first_name']} {c['last_name']} {c['phone'] or ''} {c['email'] or ''}".lower()]
            filtered[0] = fc
            lb.delete(0, 'end')
            for c in fc:
                lb.insert('end', f"{c['first_name']} {c['last_name']}  ·  {c['phone'] or '—'}")

        search_var.trace('w', lambda *_: populate(search_var.get()))
        populate()

        sel_lbl = tk.Label(form, text='Не е избран клиент', bg=COLORS['bg_medium'],
                           fg=COLORS['text_muted'], font=FONTS['small'])
        sel_lbl.pack(anchor='w', pady=(0, 8))

        def on_sel(_e=None):
            s = lb.curselection()
            if s:
                sel_client[0] = filtered[0][s[0]]
                c = sel_client[0]
                sel_lbl.config(text=f"Избран: {c['first_name']} {c['last_name']}",
                               fg=COLORS['success'])

        lb.bind('<<ListboxSelect>>', on_sel)

        tk.Label(form, text='Абонаментен план *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        plan_var = tk.StringVar()
        plan_labels = [f"{p['name']}  —  {p['price']:.2f} €" for p in plans]
        plan_var.set(plan_labels[0])
        pm = tk.OptionMenu(form, plan_var, *plan_labels)
        pm.configure(bg=COLORS['bg_input'], fg=COLORS['text_primary'], relief='flat',
                     font=FONTS['body'], highlightthickness=0,
                     activebackground=COLORS['bg_card'])
        pm['menu'].configure(bg=COLORS['bg_input'], fg=COLORS['text_primary'])
        pm.pack(fill='x', pady=(2, 4))

        info_lbl = tk.Label(form, text='', bg=COLORS['bg_medium'],
                            fg=COLORS['teal_light'], font=FONTS['small'])
        info_lbl.pack(anchor='w', pady=(0, 8))

        def upd(*_):
            p = next((p for p in plans if plan_var.get().startswith(p['name'])), None)
            if p:
                vis = f"{p['visits_limit']} посещения" if p.get('visits_limit') else 'неограничени'
                info_lbl.config(text=f"{p['duration_days']} дни  ·  {vis}")

        plan_var.trace('w', upd); upd()

        tk.Label(form, text='Начална дата *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        date_var = tk.StringVar(value=str(date.today()))
        make_entry(form, textvariable=date_var, width=44).pack(ipady=5, pady=(2, 2), fill='x')
        tk.Label(form, text='Формат: ГГГГ-ММ-ДД', bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted'], font=('Calibri', 8)).pack(anchor='w')

        def save():
            if not sel_client[0]:
                show_message(dlg, 'Грешка', 'Изберете клиент!', 'error'); return
            p = next((p for p in plans if plan_var.get().startswith(p['name'])), None)
            if not p:
                show_message(dlg, 'Грешка', 'Изберете план!', 'error'); return
            try:
                sub_id, end_date = dal.create_subscription(
                    sel_client[0]['id'], p['id'], date_var.get(), self.current_user['id'])
                show_message(dlg, 'Успех', f"Добавено!\nВалиден до: {end_date}", 'success')
                dlg.destroy()
                self._search()
            except Exception as e:
                show_message(dlg, 'Грешка', str(e), 'error')

        make_button(btns, 'Добави', save, style='primary').pack(side='left', padx=4)

    def refresh(self):
        self._search()
