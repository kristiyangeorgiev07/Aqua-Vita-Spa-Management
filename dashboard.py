"""
Dashboard - Statistics and overview
"""
import tkinter as tk
from datetime import date, timedelta
import dal
from theme import COLORS, FONTS
from widgets import make_button, StyledTreeview


class Dashboard(tk.Frame):
    def __init__(self, parent, current_user, on_navigate=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self.on_navigate = on_navigate
        self._refresh_job = None
        self._build()
        # Defer first refresh so the window is fully drawn
        self.after(100, self.refresh)

    def _build(self):
        # Stat cards row
        stats_frame = tk.Frame(self, bg=COLORS['bg_dark'], padx=20, pady=16)
        stats_frame.pack(fill='x')

        self.stat_cards = {}
        card_defs = [
            ('total_clients', '👤', 'Клиенти', COLORS['teal']),
            ('active_subs', '✓', 'Активни карти', COLORS['success']),
            ('today_visits', '⟡', 'Посещения днес', COLORS['gold']),
            ('expiring_soon', '⚠', 'Изтичат скоро', COLORS['warning']),
        ]

        for i, (key, icon, label, color) in enumerate(card_defs):
            is_last = (i == len(card_defs) - 1)
            card = tk.Frame(stats_frame, bg=COLORS['bg_card'], padx=20, pady=18)
            card.pack(side='left', fill='both', expand=True,
                      padx=(0, 0 if is_last else 10))

            # Left color bar
            tk.Frame(card, bg=color, width=4).pack(side='left', fill='y', padx=(0,14))
            
            inner = tk.Frame(card, bg=COLORS['bg_card'])
            inner.pack(side='left', fill='both', expand=True)

            num_lbl = tk.Label(inner, text='—', bg=COLORS['bg_card'],
                               fg=color, font=FONTS['stat'])
            num_lbl.pack(anchor='w')
            tk.Label(inner, text=label, bg=COLORS['bg_card'],
                     fg=COLORS['text_muted'], font=FONTS['small']).pack(anchor='w')
            
            self.stat_cards[key] = num_lbl

        # Content row
        content = tk.Frame(self, bg=COLORS['bg_dark'], padx=20, pady=0)
        content.pack(fill='both', expand=True)

        # Recent visits
        left = tk.Frame(content, bg=COLORS['bg_dark'])
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))

        header2 = tk.Frame(left, bg=COLORS['bg_dark'])
        header2.pack(fill='x', pady=8)
        tk.Label(header2, text='ПОСЛЕДНИ ПОСЕЩЕНИЯ', bg=COLORS['bg_dark'],
                 fg=COLORS['text_muted'], font=('Calibri', 8, 'bold')).pack(side='left')
        if self.on_navigate:
            make_button(header2, 'Виж всички →',
                        command=lambda: self.on_navigate('visits'),
                        style='ghost').pack(side='right')

        self.visits_tree = StyledTreeview(
            left,
            columns=('datetime', 'client', 'plan', 'registered_by'),
            headings=('Дата и час', 'Клиент', 'Абонамент', 'Регистрирал'),
            col_widths=[130, 180, 150, 130],
            height=10,
        )

        self.visits_tree = StyledTreeview(
            left,
            columns=('datetime', 'client', 'plan', 'registered_by'),
            headings=('Дата и час', 'Клиент', 'Абонамент', 'Регистрирал'),
            col_widths=[130, 180, 150, 130],
            height=10,
        )

        self.visits_tree.pack(fill='both', expand=True)

        # Right: expiring subs
        right = tk.Frame(content, bg=COLORS['bg_dark'], width=320)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)

        tk.Label(right, text='ИЗТИЧАЩИ В 7 ДНИ', bg=COLORS['bg_dark'],
                 fg=COLORS['warning'], font=('Calibri', 8, 'bold')).pack(anchor='w', pady=(0,8))

        self.expiring_tree = StyledTreeview(
            right,
            columns=('client', 'plan', 'end_date', 'days'),
            headings=('Клиент', 'Абонамент', 'Изтича', 'Дни'),
            col_widths=[130, 100, 90, 50],
            height=10,
        )
        self.expiring_tree.pack(fill='both', expand=True)

        # Refresh button
        btn_row = tk.Frame(self, bg=COLORS['bg_dark'], padx=20, pady=10)
        btn_row.pack(fill='x')
        make_button(btn_row, '↻  Опресни', command=self.refresh, style='ghost').pack(side='right')

    def refresh(self):
        try:
            # Auto-mark expired subscriptions first
            dal.mark_expired_subscriptions()

            stats = dal.get_stats()
            for key, lbl in self.stat_cards.items():
                lbl.config(text=str(stats.get(key, '—')))

            # Recent visits
            self.visits_tree.clear()
            visits = dal.get_recent_visits(30)
            for v in visits:
                dt = v['visit_date'].strftime('%d.%m %H:%M')
                self.visits_tree.insert((
                    dt,
                    f"{v['first_name']} {v['last_name']}",
                    v['plan_name'],
                    v.get('registered_by_name') or '-',
                ))

            # Expiring subscriptions — within next 7 days, not exhausted
            self.expiring_tree.clear()
            cutoff = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
            today_str = date.today().strftime('%Y-%m-%d')
            subs_expiring = dal.get_subscriptions(
                end_from=today_str,
                end_to=cutoff,
                status_filter='active',
            )
            for s in subs_expiring:
                # Skip visit-exhausted cards
                if s.get('visits_limit') and s['visits_used'] >= s['visits_limit']:
                    continue
                days = s['days_left'] if s['days_left'] is not None else 0
                tag = 'expiring' if days <= 3 else 'odd'
                self.expiring_tree.insert((
                    f"{s['first_name']} {s['last_name']}",
                    s['plan_name'],
                    str(s['end_date']),
                    f"{days}д",
                ), tags=(tag,))

        except Exception:
            pass
        finally:
            # Always reschedule next auto-refresh (cancellable)
            if self._refresh_job:
                self.after_cancel(self._refresh_job)
            self._refresh_job = self.after(300_000, self.refresh)
