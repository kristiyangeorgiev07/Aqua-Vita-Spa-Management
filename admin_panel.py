"""
Admin Panel - Plans and Users management + embedded Reports
"""
import tkinter as tk
from tkinter import ttk
import dal
from theme import COLORS, FONTS
from widgets import make_button, make_entry, StyledTreeview, show_message, confirm_dialog


class AdminPanel(tk.Frame):
    def __init__(self, parent, current_user, on_user_changed=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_dark'], **kwargs)
        self.current_user = current_user
        self._on_user_changed = on_user_changed
        self._build()

    def _build(self):
        # Tab bar
        tab_bar = tk.Frame(self, bg=COLORS['bg_dark'], pady=0)
        tab_bar.pack(fill='x', padx=16, pady=(14, 0))

        self._tabs = {}
        self._tab_frames = {}

        tab_defs = [
            ('plans',   'Абонаментни планове'),
            ('users',   'Потребители'),
            ('reports', 'Справки'),
        ]

        for key, label in tab_defs:
            btn = tk.Button(
                tab_bar, text=label,
                command=lambda k=key: self._switch_tab(k),
                bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                relief='flat', font=FONTS['btn'], cursor='hand2',
                padx=16, pady=8, bd=0,
            )
            btn.pack(side='left', padx=(0, 2))
            self._tabs[key] = btn

        # Content area
        self.content = tk.Frame(self, bg=COLORS['bg_dark'])
        self.content.pack(fill='both', expand=True, padx=16, pady=12)

        self._build_plans_tab()
        self._build_users_tab()
        self._build_reports_tab()

        self._switch_tab('plans')

    def _switch_tab(self, tab_key):
        for key, frame in self._tab_frames.items():
            frame.pack_forget()

        for key, btn in self._tabs.items():
            if key == tab_key:
                btn.config(bg=COLORS['gold'], fg='#0D1B2A')
            else:
                btn.config(bg=COLORS['bg_card'], fg=COLORS['text_secondary'])

        self._tab_frames[tab_key].pack(fill='both', expand=True)

        if tab_key == 'plans':
            self._load_plans()
        elif tab_key == 'users':
            self._load_users()
        elif tab_key == 'reports':
            if hasattr(self._reports_panel, 'refresh'):
                self._reports_panel.refresh()

    # ──────────────── PLANS TAB ────────────────────────────────

    def _build_plans_tab(self):
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['plans'] = frame

        # Treeview
        self.plans_tree = StyledTreeview(
            frame,
            columns=('id', 'name', 'duration', 'price', 'visits', 'active'),
            headings=('ID', 'Наименование', 'Дни', 'Цена (€)', 'Лимит посещения', 'Активен'),
            col_widths=[50, 200, 80, 100, 130, 80],
            height=14,
        )
        self.plans_tree.pack(fill='both', expand=True)

        btn_bar = tk.Frame(frame, bg=COLORS['bg_dark'], pady=8)
        btn_bar.pack(fill='x')
        make_button(btn_bar, '+ Нов план', command=self._plan_dialog, style='primary').pack(side='left', padx=(0,6), ipady=3)
        make_button(btn_bar, '✎ Редактирай', command=self._edit_plan_dialog, style='secondary').pack(side='left', padx=(0,6), ipady=3)
        make_button(btn_bar, '✗ Изтрий', command=self._delete_plan, style='danger').pack(side='left', ipady=3)

    def _load_plans(self):
        self.plans_tree.clear()
        plans = dal.get_all_plans()
        for p in plans:
            visits = str(p['visits_limit']) if p['visits_limit'] else 'Неограничени'
            active = '✓ Да' if p['is_active'] else '✗ Не'
            self.plans_tree.insert((p['id'], p['name'], p['duration_days'],
                                    f"{p['price']:.2f}", visits, active))

    def _plan_dialog(self, plan=None):
        """Add or edit plan dialog — compact for small screens."""
        dlg = tk.Toplevel(self)
        dlg.title('Нов план' if not plan else 'Редактиране на план')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        # Use resizable height, keep width fixed
        W = 440
        dlg.geometry(f'{W}x420')
        px = self.winfo_rootx() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_rooty() + (self.winfo_height() - 420) // 2)
        dlg.geometry(f'{W}x420+{px}+{py}')

        title = 'Нов абонаментен план' if not plan else f'Редактиране: {plan["name"]}'
        tk.Label(dlg, text=title, bg=COLORS['bg_medium'],
                 fg=COLORS['gold'], font=FONTS['heading']).pack(pady=(12, 8))

        # Buttons pinned to bottom FIRST so they're always visible
        btns = tk.Frame(dlg, bg=COLORS['bg_medium'])
        btns.pack(side='bottom', pady=10)
        make_button(btns, 'Отказ', dlg.destroy, style='ghost').pack(side='left', padx=4)

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=24)
        form.pack(fill='x')

        fields = [
            ('Наименование *', 'name', plan['name'] if plan else ''),
            ('Описание', 'desc', plan['description'] if plan else ''),
            ('Продължителност (дни) *', 'days', str(plan['duration_days']) if plan else '30'),
            ('Цена (€) *', 'price', str(plan['price']) if plan else ''),
            ('Лимит посещения (празно = неограничени)', 'visits',
             str(plan['visits_limit']) if plan and plan['visits_limit'] else ''),
        ]

        vars_ = {}
        for label, key, default in fields:
            row = tk.Frame(form, bg=COLORS['bg_medium'])
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary'], font=FONTS['small'],
                     anchor='w').pack(anchor='w')
            v = tk.StringVar(value=default)
            vars_[key] = v
            make_entry(row, textvariable=v, width=44).pack(ipady=4, fill='x')

        # Active checkbox (edit only)
        active_var = tk.BooleanVar(value=plan['is_active'] if plan else True)
        if plan:
            tk.Checkbutton(form, text='Активен', variable=active_var,
                           bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                           selectcolor=COLORS['bg_input'],
                           activebackground=COLORS['bg_medium'],
                           font=FONTS['body']).pack(anchor='w', pady=(4, 0))

        def save():
            name = vars_['name'].get().strip()
            if not name:
                show_message(dlg, 'Грешка', 'Наименованието е задължително!', 'error')
                return
            try:
                days  = int(vars_['days'].get())
                price = float(vars_['price'].get())
                visits = int(vars_['visits'].get()) if vars_['visits'].get().strip() else None
            except ValueError:
                show_message(dlg, 'Грешка', 'Дните и цената трябва да са числа!', 'error')
                return
            try:
                if plan:
                    dal.update_plan(plan['id'], name, vars_['desc'].get().strip(),
                                    days, price, visits, active_var.get())
                    show_message(dlg, 'Успех', 'Планът е обновен успешно!', 'success')
                else:
                    dal.create_plan(name, vars_['desc'].get().strip(), days, price, visits)
                    show_message(dlg, 'Успех', 'Планът е добавен успешно!', 'success')
                dlg.destroy()
                self._load_plans()
            except Exception as e:
                show_message(dlg, 'Грешка', str(e), 'error')

        make_button(btns, 'Запази', save, style='primary').pack(side='left', padx=4)

    def _edit_plan_dialog(self):
        vals = self.plans_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете план от списъка', 'warning')
            return
        plan_id = vals[0]
        plans = dal.get_all_plans()
        plan = next((p for p in plans if p['id'] == plan_id), None)
        if plan:
            self._plan_dialog(plan)

    def _delete_plan(self):
        vals = self.plans_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете план от списъка', 'warning')
            return
        if confirm_dialog(self, 'Изтриване на план',
                          f'Сигурни ли сте, че искате да изтриете план "{vals[1]}"?\nТова действие е необратимо!'):
            try:
                dal.delete_plan(vals[0])
                show_message(self, 'Успех', 'Планът е изтрит успешно', 'success')
                self._load_plans()
            except Exception as e:
                show_message(self, 'Грешка', f'Грешка при изтриване: {e}', 'error')

    # ──────────────── USERS TAB ────────────────────────────────

    def _build_users_tab(self):
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['users'] = frame

        self.users_tree = StyledTreeview(
            frame,
            columns=('id', 'username', 'full_name', 'role', 'created'),
            headings=('ID', 'Потребителско Иmе', 'Пълно Иmе', 'Роля', 'Регистриран'),
            col_widths=[50, 160, 180, 120, 120],
            height=13,
        )
        self.users_tree.pack(fill='both', expand=True)

        btn_bar = tk.Frame(frame, bg=COLORS['bg_dark'], pady=8)
        btn_bar.pack(fill='x')
        make_button(btn_bar, '+ Нов потребител', command=self._user_dialog, style='primary').pack(side='left', padx=(0,6), ipady=3)
        make_button(btn_bar, '✎ Редактирай', command=self._edit_user_dialog, style='secondary').pack(side='left', padx=(0,6), ipady=3)
        make_button(btn_bar, '✗ Изтрий', command=self._delete_user, style='danger').pack(side='left', ipady=3)

    def _load_users(self):
        self.users_tree.clear()
        users = dal.get_all_users()
        role_labels = {'admin': '⟡ Администратор', 'receptionist': '◇ Рецепционист'}
        for u in users:
            reg = str(u['created_at'])[:10] if u.get('created_at') else '-'
            self.users_tree.insert((
                u['id'], u['username'], u['full_name'],
                role_labels.get(u['role'], u['role']), reg
            ))

    def _user_dialog(self, user=None):
        dlg = tk.Toplevel(self)
        dlg.title('Нов потребител' if not user else 'Редактиране')
        dlg.configure(bg=COLORS['bg_medium'])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.overrideredirect(True)
        W, H = 420, 380
        px = self.winfo_rootx() + (self.winfo_width() - W) // 2
        py = max(20, self.winfo_rooty() + (self.winfo_height() - H) // 2)
        dlg.geometry(f'{W}x{H}+{px}+{py}')

        tk.Label(dlg, text='Нов потребител' if not user else 'Редактиране на потребител',
                 bg=COLORS['bg_medium'], fg=COLORS['gold'],
                 font=FONTS['heading']).pack(pady=(12, 8))

        # Buttons pinned to bottom
        btns = tk.Frame(dlg, bg=COLORS['bg_medium'])
        btns.pack(side='bottom', pady=10)
        make_button(btns, 'Отказ', dlg.destroy, style='ghost').pack(side='left', padx=4)

        form = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=24)
        form.pack(fill='x')

        # Username
        tk.Label(form, text='Потребителско Име *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        username_var = tk.StringVar(value=user['username'] if user else '')
        u_entry = make_entry(form, textvariable=username_var, width=44)
        u_entry.pack(ipady=4, pady=(2, 6), fill='x')
        if user:
            u_entry.config(state='disabled')

        # Full name
        tk.Label(form, text='Пълно Име *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        name_var = tk.StringVar(value=user['full_name'] if user else '')
        make_entry(form, textvariable=name_var, width=44).pack(ipady=4, pady=(2, 6), fill='x')

        # Role
        tk.Label(form, text='Роля *', bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        role_var = tk.StringVar(value=user['role'] if user else 'receptionist')
        role_frame = tk.Frame(form, bg=COLORS['bg_medium'])
        role_frame.pack(anchor='w', pady=(2, 6))
        for val, label in [('admin', 'Администратор'), ('receptionist', 'Рецепционист')]:
            tk.Radiobutton(role_frame, text=label, variable=role_var, value=val,
                           bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                           selectcolor=COLORS['bg_input'],
                           activebackground=COLORS['bg_medium'],
                           font=FONTS['body']).pack(side='left', padx=(0, 16))

        # Password
        pw_label = 'Нова парола (празно = без промяна)' if user else 'Парола *'
        tk.Label(form, text=pw_label, bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary'], font=FONTS['small']).pack(anchor='w')
        pw_var = tk.StringVar()
        make_entry(form, textvariable=pw_var, width=44, show='•').pack(ipady=4, pady=(2, 6), fill='x')

        def save():
            uname = username_var.get().strip()
            fname = name_var.get().strip()
            pwd = pw_var.get()
            if not uname or not fname:
                show_message(dlg, 'Грешка',
                             'Потребителското име и пълното име са задължителни!', 'error')
                return
            if not user and not pwd:
                show_message(dlg, 'Грешка',
                             'Паролата е задължителна за нов потребител!', 'error')
                return
            try:
                if user:
                    dal.update_user(user['id'], fname, role_var.get(), pwd or None)
                    show_message(dlg, 'Успех', 'Потребителят е обновен успешно!', 'success')
                    if self._on_user_changed:
                        self._on_user_changed(user['id'], role_var.get(), fname)
                else:
                    dal.create_user(uname, pwd, fname, role_var.get())
                    show_message(dlg, 'Успех', 'Потребителят е добавен успешно!', 'success')
                dlg.destroy()
                self._load_users()
            except Exception as e:
                show_message(dlg, 'Грешка', str(e), 'error')

        make_button(btns, 'Запази', save, style='primary').pack(side='left', padx=4)

    def _edit_user_dialog(self):
        vals = self.users_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете потребител от списъка', 'warning')
            return
        users = dal.get_all_users()
        user = next((u for u in users if u['id'] == vals[0]), None)
        if user:
            self._user_dialog(user)

    def _delete_user(self):
        vals = self.users_tree.get_selected_values()
        if not vals:
            show_message(self, 'Внимание', 'Изберете потребител от списъка', 'warning')
            return
        if vals[0] == self.current_user['id']:
            show_message(self, 'Грешка', 'Не може да изтриете собствения си акаунт!', 'error')
            return
        if confirm_dialog(self, 'Изтриване на потребител',
                          f'Сигурни ли сте, че искате да изтриете "{vals[2]}"?'):
            try:
                dal.delete_user(vals[0])
                show_message(self, 'Успех', 'Потребителят е изтрит успешно', 'success')
                self._load_users()
            except Exception as e:
                show_message(self, 'Грешка', str(e), 'error')

    def _build_reports_tab(self):
        """Embed the full ReportsPanel inside the admin panel."""
        from reports_panel import ReportsPanel
        frame = tk.Frame(self.content, bg=COLORS['bg_dark'])
        self._tab_frames['reports'] = frame
        self._reports_panel = ReportsPanel(frame, self.current_user)
        self._reports_panel.pack(fill='both', expand=True)

    def refresh(self):
        pass
