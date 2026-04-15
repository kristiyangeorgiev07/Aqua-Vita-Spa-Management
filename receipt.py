"""
Receipt generator for SPA Management System.
Generates a styled HTML receipt that opens in the default browser for printing.
"""
import os
import tempfile
import webbrowser
from datetime import datetime


def generate_receipt(client, subscription, plan, sold_by_name=''):
    """
    Generate and open an HTML receipt for a subscription.

    Args:
        client       – dict with first_name, last_name, phone, email
        subscription – dict with id, start_date, end_date, visits_used
        plan         – dict with name, price, duration_days, visits_limit
        sold_by_name – str full name of the user who sold
    """
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    client_name = f"{client['first_name']} {client['last_name']}"
    phone = client.get('phone') or '—'
    email = client.get('email') or '—'
    visits_str = str(plan['visits_limit']) if plan.get('visits_limit') else 'Неограничени'

    html = f"""<!DOCTYPE html>
<html lang="bg">
<head>
  <meta charset="UTF-8">
  <title>Квитанция — {client_name}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Lato:wght@300;400;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Lato', sans-serif;
      background: #f5f0e8;
      display: flex;
      justify-content: center;
      padding: 40px 20px;
    }}
    .card {{
      background: #fff;
      width: 480px;
      border-top: 6px solid #C9A84C;
      box-shadow: 0 4px 24px rgba(0,0,0,0.12);
      padding: 0;
      page-break-inside: avoid;
    }}
    .header {{
      background: #0D1B2A;
      color: #C9A84C;
      text-align: center;
      padding: 28px 24px 20px;
    }}
    .header .brand {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 4px;
    }}
    .header .sub {{
      font-size: 10px;
      letter-spacing: 3px;
      color: #8A7A5A;
      margin-top: 4px;
      text-transform: uppercase;
    }}
    .divider {{
      height: 1px;
      background: linear-gradient(to right, transparent, #C9A84C, transparent);
      margin: 0 24px;
    }}
    .section {{
      padding: 18px 28px;
    }}
    .section-title {{
      font-size: 9px;
      letter-spacing: 2px;
      color: #9A8A6A;
      text-transform: uppercase;
      margin-bottom: 12px;
      font-weight: 700;
    }}
    .row {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
    }}
    .row .label {{
      font-size: 11px;
      color: #888;
      min-width: 140px;
    }}
    .row .value {{
      font-size: 12px;
      color: #1B2E3F;
      font-weight: 600;
      text-align: right;
    }}
    .plan-box {{
      background: #0D1B2A;
      color: #C9A84C;
      border-radius: 4px;
      padding: 14px 20px;
      margin: 0 28px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .plan-box .plan-name {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 18px;
      font-weight: 600;
    }}
    .plan-box .plan-price {{
      font-size: 22px;
      font-weight: 700;
    }}
    .plan-box .price-label {{
      font-size: 9px;
      color: #8A7A5A;
      display: block;
      text-align: right;
    }}
    .validity-bar {{
      background: #f0f8f4;
      border-left: 4px solid #4CAF82;
      margin: 0 28px 16px;
      padding: 10px 16px;
    }}
    .validity-bar .valid-label {{
      font-size: 10px;
      color: #4CAF82;
      font-weight: 700;
      letter-spacing: 1px;
    }}
    .validity-bar .valid-dates {{
      font-size: 13px;
      color: #1B2E3F;
      font-weight: 600;
      margin-top: 2px;
    }}
    .footer {{
      background: #f9f5ec;
      border-top: 1px solid #e8e0d0;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .footer .receipt-num {{
      font-size: 10px;
      color: #aaa;
    }}
    .footer .issued {{
      font-size: 10px;
      color: #aaa;
      text-align: right;
    }}
    .print-btn {{
      display: block;
      width: 480px;
      margin: 16px auto 0;
      padding: 12px;
      background: #C9A84C;
      color: #0D1B2A;
      border: none;
      font-family: 'Lato', sans-serif;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 2px;
      cursor: pointer;
      text-transform: uppercase;
    }}
    .print-btn:hover {{ background: #E2C272; }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .card {{ box-shadow: none; width: 100%; }}
      .print-btn {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div>
    <div class="card">
      <div class="header">
        <div class="brand">✦ AQUA VITA</div>
        <div class="sub">СПА &amp; Уелнес Център</div>
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="section-title">Данни за клиент</div>
        <div class="row">
          <span class="label">Клиент</span>
          <span class="value">{client_name}</span>
        </div>
        <div class="row">
          <span class="label">Телефон</span>
          <span class="value">{phone}</span>
        </div>
        <div class="row">
          <span class="label">Email</span>
          <span class="value">{email}</span>
        </div>
      </div>

      <div class="divider"></div>

      <div class="section" style="padding-bottom:8px;">
        <div class="section-title">Абонаментен план</div>
      </div>

      <div class="plan-box">
        <span class="plan-name">{plan['name']}</span>
        <div>
          <span class="plan-price">{float(plan['price']):.2f} €</span>
          <span class="price-label">еднократно</span>
        </div>
      </div>

      <div class="validity-bar">
        <div class="valid-label">✓ ВАЛИДЕН АБОНАМЕНТ</div>
        <div class="valid-dates">{subscription['start_date']}  →  {subscription['end_date']}</div>
      </div>

      <div class="section">
        <div class="row">
          <span class="label">Продължителност</span>
          <span class="value">{plan['duration_days']} дни</span>
        </div>
        <div class="row">
          <span class="label">Лимит посещения</span>
          <span class="value">{visits_str}</span>
        </div>
        <div class="row">
          <span class="label">Абонамент №</span>
          <span class="value">#{subscription['id']:05d}</span>
        </div>
        {f'<div class="row"><span class="label">Продал</span><span class="value">{sold_by_name}</span></div>' if sold_by_name else ''}
      </div>

      <div class="footer">
        <div class="receipt-num">Квитанция #{subscription['id']:08d}</div>
        <div class="issued">Издадена: {now}</div>
      </div>
    </div>

    <button class="print-btn" onclick="window.print()">🖨  Разпечатай / Запази PDF</button>
  </div>
</body>
</html>"""

    # Write to temp file and open in browser
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.html', delete=False,
        encoding='utf-8', prefix='aquavita_receipt_'
    )
    tmp.write(html)
    tmp.close()
    webbrowser.open(f'file://{tmp.name}')

    # Schedule cleanup after 60 seconds (browser has had time to load)
    import threading
    def _cleanup():
        import time
        time.sleep(60)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    threading.Thread(target=_cleanup, daemon=True).start()

    return tmp.name
