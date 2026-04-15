"""
Reusable custom widgets for SPA Management System
"""
import tkinter as tk
from tkinter import ttk
from theme import COLORS, FONTS


def make_button(parent, text, command=None, style='primary', width=None, **kwargs):
    """Create a styled button."""
    styles = {
        'primary': {'bg': COLORS['gold'], 'fg': '#0D1B2A', 'activebackground': COLORS['gold_light']},
        'secondary': {'bg': COLORS['teal'], 'fg': COLORS['text_primary'], 'activebackground': COLORS['teal_light']},
        'danger': {'bg': COLORS['danger'], 'fg': COLORS['text_primary'], 'activebackground': '#FF7070'},
        'ghost': {'bg': COLORS['bg_card'], 'fg': COLORS['text_secondary'], 'activebackground': COLORS['bg_medium']},
        'success': {'bg': COLORS['success'], 'fg': '#0D2A1C', 'activebackground': '#5DC990'},
    }
    s = styles.get(style, styles['primary'])
    btn_kwargs = {
        'text': text,
        'command': command,
        'bg': s['bg'],
        'fg': s['fg'],
        'activebackground': s['activebackground'],
        'activeforeground': s['fg'],
        'relief': 'flat',
        'font': FONTS['btn'],
        'cursor': 'hand2',
        'padx': 14,
        'pady': 7,
        'bd': 0,
    }
    if width:
        btn_kwargs['width'] = width
    btn_kwargs.update(kwargs)
    return tk.Button(parent, **btn_kwargs)


def make_label(parent, text, style='body', color=None, **kwargs):
    """Create a styled label."""
    font_map = {'title': FONTS['title'], 'heading': FONTS['heading'], 'body': FONTS['body'],
                'small': FONTS['small'], 'subhead': FONTS['subhead']}
    lbl_kwargs = {
        'text': text,
        'bg': kwargs.pop('bg', COLORS['bg_card']),
        'fg': color or COLORS['text_primary'],
        'font': font_map.get(style, FONTS['body']),
    }
    lbl_kwargs.update(kwargs)
    return tk.Label(parent, **lbl_kwargs)


def make_entry(parent, textvariable=None, placeholder='', width=30, show=None, **kwargs):
    """Create a styled entry field."""
    entry = tk.Entry(
        parent,
        textvariable=textvariable,
        bg=COLORS['bg_input'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['gold'],
        relief='flat',
        font=FONTS['body'],
        highlightthickness=1,
        highlightcolor=COLORS['gold'],
        highlightbackground=COLORS['border'],
        width=width,
        show=show or '',
        **kwargs
    )
    if placeholder and textvariable is None:
        entry.insert(0, placeholder)
        entry.config(fg=COLORS['text_muted'])
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
                entry.config(fg=COLORS['text_primary'])
        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=COLORS['text_muted'])
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
    return entry


def make_combobox(parent, values, textvariable=None, width=27, state='readonly', **kwargs):
    """Create a styled combobox."""
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Spa.TCombobox',
        fieldbackground=COLORS['bg_input'],
        background=COLORS['bg_medium'],
        foreground=COLORS['text_primary'],
        arrowcolor=COLORS['gold'],
        bordercolor=COLORS['border'],
        lightcolor=COLORS['border'],
        darkcolor=COLORS['border'],
        selectbackground=COLORS['gold_dark'],
        selectforeground=COLORS['text_primary'],
    )
    cb = ttk.Combobox(parent, values=values, textvariable=textvariable,
                      width=width, state=state, style='Spa.TCombobox', **kwargs)
    return cb


def make_separator(parent, orient='horizontal', **kwargs):
    color = kwargs.pop('color', COLORS['border'])
    if orient == 'horizontal':
        f = tk.Frame(parent, height=1, bg=color, **kwargs)
    else:
        f = tk.Frame(parent, width=1, bg=color, **kwargs)
    return f


class ScrollableFrame(tk.Frame):
    """A scrollable frame container."""
    def __init__(self, parent, bg=None, **kwargs):
        super().__init__(parent, bg=bg or COLORS['bg_dark'], **kwargs)
        canvas = tk.Canvas(self, bg=bg or COLORS['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg or COLORS['bg_dark'])
        self.inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(-1*(e.delta//120), 'units'))


class StyledTreeview(tk.Frame):
    """A styled treeview with scrollbars."""
    _style_configured = False  # configure ttk style only once

    def __init__(self, parent, columns, headings, col_widths=None, height=15, **kwargs):
        bg = kwargs.pop('bg', COLORS['bg_card'])
        super().__init__(parent, bg=bg)

        if not StyledTreeview._style_configured:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Spa.Treeview',
                background=COLORS['bg_card'],
                foreground=COLORS['text_primary'],
                rowheight=28,
                fieldbackground=COLORS['bg_card'],
                borderwidth=0,
                font=FONTS['body'],
            )
            style.configure('Spa.Treeview.Heading',
                background=COLORS['bg_medium'],
                foreground=COLORS['gold'],
                relief='flat',
                font=FONTS['body_bold'],
                padding=(8, 6),
            )
            style.map('Spa.Treeview',
                background=[('selected', COLORS['teal_dark'])],
                foreground=[('selected', COLORS['text_primary'])],
            )
            style.map('Spa.Treeview.Heading',
                background=[('active', COLORS['bg_card'])],
            )
            StyledTreeview._style_configured = True
        
        self.tree = ttk.Treeview(self, columns=columns, show='headings',
                                  height=height, style='Spa.Treeview')
        
        for i, (col, head) in enumerate(zip(columns, headings)):
            w = col_widths[i] if col_widths else 120
            self.tree.heading(col, text=head, anchor='center')
            self.tree.column(col, width=w, minwidth=50, anchor='w')
        
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Alternating row colors
        self.tree.tag_configure('odd', background=COLORS['bg_card'])
        self.tree.tag_configure('even', background=COLORS['bg_medium'])
        self.tree.tag_configure('active', background='#1A3A28')
        self.tree.tag_configure('expired', background='#2A1A1A')
        self.tree.tag_configure('expiring', background='#2A2010')
    
    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def insert(self, values, tags=()):
        idx = len(self.tree.get_children())
        row_tag = 'even' if idx % 2 == 0 else 'odd'
        all_tags = (row_tag,) + tuple(tags)
        return self.tree.insert('', 'end', values=values, tags=all_tags)
    
    def get_selected_values(self):
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0])['values']
        return None


def show_message(parent, title, message, msg_type='info'):
    """Show a styled message dialog."""
    colors = {
        'info': COLORS['info'],
        'success': COLORS['success'],
        'error': COLORS['danger'],
        'warning': COLORS['warning'],
    }
    icons = {'info': 'ℹ', 'success': '✓', 'error': '✗', 'warning': '⚠'}
    
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=COLORS['bg_medium'])
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.overrideredirect(True)
    
    w, h = 380, 180
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = max(20, parent.winfo_rooty() + (parent.winfo_height() - h) // 2)
    dlg.geometry(f"{w}x{h}+{px}+{py}")
    
    # Icon
    accent = colors.get(msg_type, COLORS['info'])
    icon_frame = tk.Frame(dlg, bg=accent, width=6)
    icon_frame.pack(side='left', fill='y')
    
    content = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=20, pady=20)
    content.pack(side='left', fill='both', expand=True)
    
    tk.Label(content, text=f"{icons.get(msg_type,'')} {title}",
             bg=COLORS['bg_medium'], fg=accent, font=FONTS['subhead']).pack(anchor='w')
    tk.Frame(content, height=8, bg=COLORS['bg_medium']).pack()
    tk.Label(content, text=message, bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
             font=FONTS['body'], wraplength=300, justify='left').pack(anchor='w')
    tk.Frame(content, height=12, bg=COLORS['bg_medium']).pack()
    make_button(content, 'OK', command=dlg.destroy, style='primary').pack(anchor='e')


def confirm_dialog(parent, title, message):
    """Show a confirmation dialog. Returns True if confirmed."""
    result = [False]
    
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=COLORS['bg_medium'])
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.overrideredirect(True)
    
    w, h = 380, 180
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = max(20, parent.winfo_rooty() + (parent.winfo_height() - h) // 2)
    dlg.geometry(f"{w}x{h}+{px}+{py}")
    
    accent_frame = tk.Frame(dlg, bg=COLORS['warning'], width=6)
    accent_frame.pack(side='left', fill='y')
    
    content = tk.Frame(dlg, bg=COLORS['bg_medium'], padx=20, pady=20)
    content.pack(side='left', fill='both', expand=True)
    
    tk.Label(content, text=f"⚠ {title}", bg=COLORS['bg_medium'],
             fg=COLORS['warning'], font=FONTS['subhead']).pack(anchor='w')
    tk.Frame(content, height=8, bg=COLORS['bg_medium']).pack()
    tk.Label(content, text=message, bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
             font=FONTS['body'], wraplength=300, justify='left').pack(anchor='w')
    tk.Frame(content, height=12, bg=COLORS['bg_medium']).pack()
    
    btn_frame = tk.Frame(content, bg=COLORS['bg_medium'])
    btn_frame.pack(anchor='e')
    
    def on_yes():
        result[0] = True
        dlg.destroy()
    
    make_button(btn_frame, 'Отказ', command=dlg.destroy, style='ghost').pack(side='left', padx=(0, 8))
    make_button(btn_frame, 'Потвърди', command=on_yes, style='danger').pack(side='left')
    
    dlg.wait_window()
    return result[0]
