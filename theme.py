"""
Theme & Style constants for SPA Management System
Luxury spa aesthetic: deep teal + warm gold + cream
"""

# ─── COLOR PALETTE ───────────────────────────────────────────
COLORS = {
    # Backgrounds
    'bg_dark':      '#0D1B2A',   # Very dark navy
    'bg_medium':    '#1B2E3F',   # Dark slate
    'bg_card':      '#1E3448',   # Card background
    'bg_input':     '#142231',   # Input fields

    # Accents
    'gold':         '#C9A84C',   # Warm gold (primary accent)
    'gold_light':   '#E2C272',   # Light gold
    'gold_dark':    '#9E7A2A',   # Dark gold
    'teal':         '#2A9D8F',   # Teal accent
    'teal_light':   '#3DBDAD',   # Light teal
    'teal_dark':    '#1E7268',   # Dark teal

    # Text
    'text_primary': '#F5ECD7',   # Warm cream white
    'text_secondary':'#A8B8C8',  # Muted blue-grey
    'text_muted':   '#5A7A94',   # Very muted

    # Status
    'success':      '#4CAF82',   # Green
    'warning':      '#E9A84C',   # Amber
    'danger':       '#E05A5A',   # Red
    'info':         '#5B9BD5',   # Blue

    # Borders
    'border':       '#2A4A6A',   # Subtle border
    'border_gold':  '#8A6A2A',   # Gold border
}

# ─── FONTS ──────────────────────────────────────────────────
FONTS = {
    'title':    ('Georgia', 22, 'bold'),
    'heading':  ('Georgia', 14, 'bold'),
    'subhead':  ('Georgia', 11, 'bold'),
    'body':     ('Calibri', 11),
    'body_bold':('Calibri', 11, 'bold'),
    'small':    ('Calibri', 9),
    'mono':     ('Consolas', 10),
    'btn':      ('Calibri', 10, 'bold'),
    'nav':      ('Calibri', 10, 'bold'),
    'stat':     ('Georgia', 28, 'bold'),
}

# ─── WIDGET STYLES ──────────────────────────────────────────
ENTRY_STYLE = {
    'bg': COLORS['bg_input'],
    'fg': COLORS['text_primary'],
    'insertbackground': COLORS['gold'],
    'relief': 'flat',
    'font': FONTS['body'],
    'highlightthickness': 1,
    'highlightcolor': COLORS['gold'],
    'highlightbackground': COLORS['border'],
}

LABEL_STYLE = {
    'bg': COLORS['bg_card'],
    'fg': COLORS['text_secondary'],
    'font': FONTS['small'],
}

LABEL_FORM = {
    'bg': COLORS['bg_medium'],
    'fg': COLORS['text_secondary'],
    'font': FONTS['body'],
}

# Status badge colors
STATUS_COLORS = {
    'active':    ('#4CAF82', '#0D2A1C'),
    'expired':   ('#E05A5A', '#2A0D0D'),
    'cancelled': ('#A8B8C8', '#1A2A3A'),
}
