"""
Reports Panel - Statistics, charts and CSV export
"""
import tkinter as tk
from tkinter import filedialog
import csv
import os
from datetime import date, timedelta
import dal
from theme import COLORS, FONTS
from widgets import make_button, StyledTreeview, show_message


class ReportsPanel(tk.Frame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self._build()

    def _build(self):
        # Tab bar
        tab_bar = tk.Frame(self, bg=COLORS['bg_dark'], padx=16, pady=10)
        tab_bar.pack(fill='x')
        self._tabs = {}
        self._tab_frames = {}

        tab_defs = [
            ('revenue',  'Приходи по план'),
            ('monthly',  'Месечна активност'),
            ('export',   'Експорт на данни'),
        ]
        for key, label in tab_defs:
            btn = tk.Button(tab_bar, text=label,
                            command=lambda k=key: self._switch_tab(k),
                            bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                            relief='flat', font=FONTS['btn'], cursor='hand2',
                            padx=14, pady=7, bd=0)
            btn.pack(side='left', padx=(0, 2))
            self._tabs[key] = btn

        self.content = tk.Frame(self, bg=COLORS['bg_dark'])
        self.content.pack(fill='both', expand=True, padx=16, pady=0)

        self._build_revenue_tab()
        self._build_monthly_tab()
        self._build_export_tab()
        self._revenue_loaded = False
        self._monthly_loaded = False
        self._switch_tab('revenue')

    # ─── TAB SWITCHING ───────────────────────────────────────

    def _switch_tab(self, key):
        for k, f in self._tab_frames.items():
            f.pack_forget()
        for k, btn in self._tabs.items():
            btn.config(bg=COLORS['gold_dark'] if k == key else COLORS['bg_card'],
                       fg=COLORS['gold_light'] if k == key else COLORS['text_secondary'])
        self._tab_frames[key].pack(fill='both', expand=True)
        # Load data on first visit to each tab
        if key == 'revenue' and not self._revenue_loaded:
            self._load_revenue()
            self._revenue_loaded = True
        elif key == 'monthly' and not self._monthly_loaded:
            self._load_monthly()
            self._monthly_loaded = True

    def refresh(self):
        """Called by F5 or admin tab switch — force reload current tab."""
        self._revenue_loaded = False
        self._monthly_loaded = False
        # Find current active tab and reload it
        for key, frame in self._tab_frames.items():
            try:
                if frame.winfo_ismapped():
                    if key == 'revenue':
                        self._load_revenue()
                        self._revenue_loaded = True
                    elif key == 'monthly':
                        self._load_monthly()
                        self._monthly_loaded = True
                    break
            except Exception:
                pass

    # ─── REVENUE TAB ─────────────────────────────────────────

    def _build_revenue_tab(self):
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['revenue'] = frame

        tk.Label(frame, text='Приходи по абонаментен план', bg=COLORS['bg_dark'],
                 fg=COLORS['text_secondary'], font=FONTS['subhead']).pack(anchor='w', pady=(12, 8))

        self.revenue_tree = StyledTreeview(
            frame,
            columns=('plan', 'count', 'revenue'),
            headings=('Абонаментен план', 'Продадени', 'Общо приходи (€)'),
            col_widths=[280, 120, 160],
            height=10,
        )
        self.revenue_tree.pack(fill='x')

        # Summary labels
        self.total_rev_var = tk.StringVar(value='')
        tk.Label(frame, textvariable=self.total_rev_var, bg=COLORS['bg_dark'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(anchor='e', pady=(8, 0))

        # Mini bar chart canvas
        tk.Label(frame, text='ВИЗУАЛИЗАЦИЯ', bg=COLORS['bg_dark'],
                 fg=COLORS['text_muted'], font=('Calibri', 8, 'bold')).pack(anchor='w', pady=(16, 4))
        self.chart_canvas = tk.Canvas(frame, bg=COLORS['bg_card'], height=160,
                                      highlightthickness=0)
        self.chart_canvas.pack(fill='x')
        self._chart_data = []
        self.chart_canvas.bind('<Configure>', lambda e: self._draw_bar_chart())

        make_button(frame, '↻  Обнови', command=lambda: (self._load_revenue(), setattr(self, '_revenue_loaded', True)),
                    style='ghost').pack(anchor='e', pady=8)

    def _load_revenue(self):
        self.revenue_tree.clear()
        data = dal.get_revenue_by_plan()
        self._chart_data = data
        total = 0
        for row in data:
            rev = float(row['revenue']) if row['revenue'] else 0
            total += rev
            self.revenue_tree.insert((
                row['name'],
                row['count'],
                f"{rev:,.2f}",
            ))
        self.total_rev_var.set(f"Общо: {total:,.2f} €")
        self._draw_bar_chart()

    def _draw_bar_chart(self):
        canvas = self.chart_canvas
        canvas.delete('all')
        data = self._chart_data
        if not data:
            return

        W = canvas.winfo_width() or 600
        H = 160
        pad_l, pad_r, pad_t, pad_b = 10, 10, 16, 30

        max_rev = max((float(r['revenue']) for r in data if r['revenue']), default=1)
        n = len(data)
        bar_w = max(10, (W - pad_l - pad_r) // n - 6)
        colors_cycle = [COLORS['gold'], COLORS['teal'], COLORS['success'],
                        COLORS['warning'], COLORS['info'], COLORS['gold_light']]

        for i, row in enumerate(data):
            rev = float(row['revenue']) if row['revenue'] else 0
            ratio = rev / max_rev
            bh = int((H - pad_t - pad_b) * ratio)
            x0 = pad_l + i * ((W - pad_l - pad_r) // n)
            x1 = x0 + bar_w
            y1 = H - pad_b
            y0 = y1 - bh
            color = colors_cycle[i % len(colors_cycle)]
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='', width=0)
            # Value label on top
            canvas.create_text((x0+x1)//2, y0 - 4, text=f"{rev:,.0f}",
                                fill=COLORS['text_secondary'],
                                font=('Calibri', 7), anchor='s')
            # Name label bottom
            name = row['name'][:10] + '…' if len(row['name']) > 10 else row['name']
            canvas.create_text((x0+x1)//2, H - pad_b + 4, text=name,
                                fill=COLORS['text_muted'], font=('Calibri', 7), anchor='n')

    # ─── MONTHLY TAB ─────────────────────────────────────────

    def _build_monthly_tab(self):
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['monthly'] = frame

        tk.Label(frame, text='Посещения по месец (последните 12 месеца)',
                 bg=COLORS['bg_dark'], fg=COLORS['text_secondary'],
                 font=FONTS['subhead']).pack(anchor='w', pady=(12, 8))

        self.monthly_tree = StyledTreeview(
            frame,
            columns=('month', 'visits'),
            headings=('Месец', 'Брой посещения'),
            col_widths=[180, 160],
            height=12,
        )
        self.monthly_tree.pack(anchor='w')

        # Line chart canvas
        tk.Label(frame, text='ТРЕНД', bg=COLORS['bg_dark'],
                 fg=COLORS['text_muted'], font=('Calibri', 8, 'bold')).pack(anchor='w', pady=(16, 4))
        self.line_canvas = tk.Canvas(frame, bg=COLORS['bg_card'], height=160,
                                     highlightthickness=0)
        self.line_canvas.pack(fill='x')
        self._monthly_data = []
        self.line_canvas.bind('<Configure>', lambda e: self._draw_line_chart())

        make_button(frame, '↻  Обнови', command=lambda: (self._load_monthly(), setattr(self, '_monthly_loaded', True)),
                    style='ghost').pack(anchor='e', pady=8)

    def _load_monthly(self):
        self.monthly_tree.clear()
        data = dal.get_monthly_visits_stats()
        self._monthly_data = data
        for row in data:
            self.monthly_tree.insert((row['month'], row['visits']))
        self._draw_line_chart()

    def _draw_line_chart(self):
        canvas = self.line_canvas
        canvas.delete('all')
        data = self._monthly_data
        if not data:
            return

        W = canvas.winfo_width() or 600
        H = 160
        pad_l, pad_r, pad_t, pad_b = 14, 14, 20, 28

        max_v = max((r['visits'] for r in data), default=1)
        n = len(data)
        step = (W - pad_l - pad_r) / max(n - 1, 1)

        points = []
        for i, row in enumerate(data):
            x = pad_l + i * step
            y = H - pad_b - int((H - pad_t - pad_b) * row['visits'] / max_v)
            points.append((x, y))

        # Grid lines
        for pct in [0.25, 0.5, 0.75, 1.0]:
            yg = H - pad_b - int((H - pad_t - pad_b) * pct)
            canvas.create_line(pad_l, yg, W - pad_r, yg,
                               fill=COLORS['border'], dash=(3, 4))

        # Fill area under line
        if len(points) >= 2:
            poly = list(points) + [(points[-1][0], H - pad_b), (points[0][0], H - pad_b)]
            flat = [c for pt in poly for c in pt]
            canvas.create_polygon(flat, fill=COLORS['teal_dark'], outline='', stipple='')

        # Line
        if len(points) >= 2:
            flat_pts = [c for pt in points for c in pt]
            canvas.create_line(flat_pts, fill=COLORS['teal_light'], width=2, smooth=True)

        # Dots + labels
        for i, (x, y) in enumerate(points):
            canvas.create_oval(x-4, y-4, x+4, y+4,
                               fill=COLORS['teal'], outline=COLORS['bg_card'], width=2)
            canvas.create_text(x, H - pad_b + 4,
                               text=data[i]['month'][5:],  # MM only
                               fill=COLORS['text_muted'], font=('Calibri', 7), anchor='n')
            canvas.create_text(x, y - 8,
                               text=str(data[i]['visits']),
                               fill=COLORS['text_secondary'], font=('Calibri', 7), anchor='s')

    # ─── EXPORT TAB ──────────────────────────────────────────

    def _build_export_tab(self):
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['export'] = frame

        tk.Frame(frame, height=20, bg=COLORS['bg_dark']).pack()

        # Export cards
        exports = [
            ('Пълен регистър на абонаменти',
             'Всички абонаменти с детайли за клиент, план, дати и статус.',
             self._export_subscriptions),
            ('Списък с клиенти',
             'Всички регистрирани клиенти с контактна информация.',
             self._export_clients),
            ('История на посещенията',
             'Всички регистрирани посещения с дата, час и абонамент.',
             self._export_visits),
        ]

        for title, desc, cmd in exports:
            card = tk.Frame(frame, bg=COLORS['bg_card'], padx=20, pady=16)
            card.pack(fill='x', pady=(0, 10))

            left_card = tk.Frame(card, bg=COLORS['bg_card'])
            left_card.pack(side='left', fill='both', expand=True)
            tk.Label(left_card, text=title, bg=COLORS['bg_card'],
                     fg=COLORS['text_primary'], font=FONTS['body_bold']).pack(anchor='w')
            tk.Label(left_card, text=desc, bg=COLORS['bg_card'],
                     fg=COLORS['text_muted'], font=FONTS['small']).pack(anchor='w', pady=(3, 0))

            make_button(card, 'CSV', command=cmd,
                        style='secondary').pack(side='right', padx=(16, 0), ipady=4)

        # Note
        tk.Label(frame, text='Файловете се записват в CSV формат (UTF-8), съвместим с Excel.',
                 bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
                 font=('Calibri', 9)).pack(anchor='w', pady=(10, 0))

    def _export_subscriptions(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV файлове', '*.csv'), ('Всички файлове', '*.*')],
            initialfile=f'абонаменти_{date.today()}.csv',
            title='Запази регистър на абонаменти',
        )
        if not path:
            return
        try:
            data = dal.get_all_subscriptions_export()
            headers = ['ID', 'Собствено Иmе', 'Фамилия', 'Телефон', 'Email',
                       'План', 'Цена', 'Начало', 'Изтичане',
                       'Посещения', 'Статус', 'Продал', 'Дата на закупуване']
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                for row in data:
                    writer.writerow([
                        row['id'], row['first_name'], row['last_name'],
                        row['phone'] or '', row['email'] or '',
                        row['plan_name'], row['price'],
                        row['start_date'], row['end_date'],
                        row['visits_used'], row['status'],
                        row['sold_by_name'] or '',
                        str(row['created_at'])[:19],
                    ])
            show_message(self, 'Успех', f'Файлът е записан:\n{os.path.basename(path)}', 'success')
        except Exception as e:
            show_message(self, 'Грешка', str(e), 'error')

    def _export_clients(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV файлове', '*.csv'), ('Всички файлове', '*.*')],
            initialfile=f'клиенти_{date.today()}.csv',
            title='Запази списък с клиенти',
        )
        if not path:
            return
        try:
            clients = dal.search_clients('')
            headers = ['ID', 'Собствено Иmе', 'Фамилия', 'Телефон', 'Email', 'Регистриран на']
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                for c in clients:
                    writer.writerow([
                        c['id'], c['first_name'], c['last_name'],
                        c['phone'] or '', c['email'] or '',
                        str(c['created_at'])[:10],
                    ])
            show_message(self, 'Успех', f'Файлът е записан:\n{os.path.basename(path)}', 'success')
        except Exception as e:
            show_message(self, 'Грешка', str(e), 'error')

    def _export_visits(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV файлове', '*.csv'), ('Всички файлове', '*.*')],
            initialfile=f'посещения_{date.today()}.csv',
            title='Запази история на посещенията',
        )
        if not path:
            return
        try:
            visits = dal.get_recent_visits(limit=99999)
            headers = ['Дата и час', 'Клиент', 'Абонамент', 'Регистрирал']
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                for v in visits:
                    writer.writerow([
                        v['visit_date'].strftime('%Y-%m-%d %H:%M'),
                        f"{v['first_name']} {v['last_name']}",
                        v['plan_name'],
                        v.get('registered_by_name') or '',
                    ])
            show_message(self, 'Успех', f'Файлът е записан:\n{os.path.basename(path)}', 'success')
        except Exception as e:
            show_message(self, 'Грешка', str(e), 'error')
