"""
Data Access Layer for SPA Management System
All database queries are centralised here.
"""
from db_config import get_connection, hash_password
from datetime import date, timedelta


# ══════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════

def get_all_users():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def create_user(username, password, full_name, role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (%s,%s,%s,%s)",
        (username, hash_password(password), full_name, role))
    cur.close(); conn.close()


def update_user(user_id, full_name, role, password=None):
    conn = get_connection()
    cur = conn.cursor()
    if password:
        cur.execute(
            "UPDATE users SET full_name=%s, role=%s, password_hash=%s WHERE id=%s",
            (full_name, role, hash_password(password), user_id))
    else:
        cur.execute(
            "UPDATE users SET full_name=%s, role=%s WHERE id=%s",
            (full_name, role, user_id))
    cur.close(); conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  PLANS
# ══════════════════════════════════════════════════════════════

def get_all_plans(active_only=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if active_only:
        cur.execute("SELECT * FROM plans WHERE is_active=1 ORDER BY price")
    else:
        cur.execute("SELECT * FROM plans ORDER BY is_active DESC, price")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def create_plan(name, description, duration_days, price, visits_limit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO plans (name, description, duration_days, price, visits_limit) VALUES (%s,%s,%s,%s,%s)",
        (name, description, duration_days, price, visits_limit))
    cur.close(); conn.close()


def update_plan(plan_id, name, description, duration_days, price, visits_limit, is_active):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE plans SET name=%s, description=%s, duration_days=%s,
           price=%s, visits_limit=%s, is_active=%s WHERE id=%s""",
        (name, description, duration_days, price, visits_limit, is_active, plan_id))
    cur.close(); conn.close()


def delete_plan(plan_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM plans WHERE id=%s", (plan_id,))
    cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  CLIENTS
# ══════════════════════════════════════════════════════════════

def search_clients(query=""):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    like = f"%{query}%"
    cur.execute(
        """SELECT c.*,
           (SELECT COUNT(*)
            FROM subscriptions s JOIN plans p ON s.plan_id=p.id
            WHERE s.client_id=c.id AND s.status='active'
              AND s.end_date >= CURDATE()
              AND (p.visits_limit IS NULL OR s.visits_used < p.visits_limit)
           ) as active_subs
           FROM clients c
           WHERE c.first_name LIKE %s OR c.last_name LIKE %s
              OR c.phone LIKE %s OR c.email LIKE %s
           ORDER BY c.last_name, c.first_name""",
        (like, like, like, like))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_client_by_id(client_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM clients WHERE id=%s", (client_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def create_client(first_name, last_name, phone, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clients (first_name, last_name, phone, email) VALUES (%s,%s,%s,%s)",
        (first_name, last_name, phone, email))
    new_id = cur.lastrowid
    cur.close(); conn.close()
    return new_id


def update_client(client_id, first_name, last_name, phone, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE clients SET first_name=%s, last_name=%s, phone=%s, email=%s WHERE id=%s",
        (first_name, last_name, phone, email, client_id))
    cur.close(); conn.close()


def delete_client(client_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id=%s", (client_id,))
    cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  SUBSCRIPTIONS
# ══════════════════════════════════════════════════════════════

def get_subscriptions(client_name="", start_from=None, start_to=None,
                      end_from=None, end_to=None, status_filter="all",
                      start_exact=None, end_exact=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT s.*,
               c.first_name, c.last_name, c.phone,
               p.name as plan_name, p.visits_limit,
               u.full_name as sold_by_name,
               DATEDIFF(s.end_date, CURDATE()) as days_left
        FROM subscriptions s
        JOIN clients c ON s.client_id = c.id
        JOIN plans p ON s.plan_id = p.id
        LEFT JOIN users u ON s.sold_by = u.id
        WHERE 1=1
    """
    params = []

    if client_name:
        query += " AND (c.first_name LIKE %s OR c.last_name LIKE %s)"
        like = f"%{client_name}%"
        params += [like, like]

    # Exact date filters take priority over range filters
    if start_exact:
        query += " AND s.start_date = %s"
        params.append(start_exact)
    else:
        if start_from:
            query += " AND s.start_date >= %s"
            params.append(start_from)
        if start_to:
            query += " AND s.start_date <= %s"
            params.append(start_to)

    if end_exact:
        query += " AND s.end_date = %s"
        params.append(end_exact)
    else:
        if end_from:
            query += " AND s.end_date >= %s"
            params.append(end_from)
        if end_to:
            query += " AND s.end_date <= %s"
            params.append(end_to)

    if status_filter != "all":
        query += " AND s.status = %s"
        params.append(status_filter)

    query += " ORDER BY s.created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def create_subscription(client_id, plan_id, start_date, sold_by):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT duration_days FROM plans WHERE id=%s", (plan_id,))
    plan = cur.fetchone()
    if not plan:
        cur.close(); conn.close()
        raise ValueError("Планът не е намерен")

    if isinstance(start_date, str):
        from datetime import datetime as _dt
        try:
            start_date = _dt.strptime(start_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            cur.close(); conn.close()
            raise ValueError(f"Невалиден формат на дата: '{start_date}'. Използвайте ГГГГ-ММ-ДД")

    end_date = start_date + timedelta(days=plan['duration_days'] - 1)

    cur.close()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO subscriptions (client_id, plan_id, start_date, end_date, sold_by, status)
           VALUES (%s,%s,%s,%s,%s,'active')""",
        (client_id, plan_id, start_date, end_date, sold_by))
    new_id = cur.lastrowid
    cur.close(); conn.close()
    return new_id, end_date


def get_subscription_by_id(sub_id):
    """Fetch a single subscription with all join data."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT s.*,
                  c.first_name, c.last_name, c.phone, c.email,
                  p.name as plan_name, p.price, p.duration_days, p.visits_limit,
                  u.full_name as sold_by_name,
                  DATEDIFF(s.end_date, CURDATE()) as days_left
           FROM subscriptions s
           JOIN clients c ON s.client_id = c.id
           JOIN plans p ON s.plan_id = p.id
           LEFT JOIN users u ON s.sold_by = u.id
           WHERE s.id = %s""",
        (sub_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def cancel_subscription(sub_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE subscriptions SET status='cancelled' WHERE id=%s", (sub_id,))
    cur.close(); conn.close()


def mark_expired_subscriptions():
    """Mark date-expired subscriptions as 'expired'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE subscriptions SET status='expired' WHERE status='active' AND end_date < CURDATE()")
    cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  VISITS
# ══════════════════════════════════════════════════════════════

def register_visit(subscription_id, client_id, registered_by, notes=""):
    """Register a visit. Returns (success, message)."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        """SELECT s.*, p.visits_limit FROM subscriptions s
           JOIN plans p ON s.plan_id=p.id
           WHERE s.id=%s AND s.status='active' AND s.end_date >= CURDATE()""",
        (subscription_id,))
    sub = cur.fetchone()
    if not sub:
        cur.close(); conn.close()
        return False, "Абонаментът е изтекъл или невалиден!"

    if sub['visits_limit'] is not None and sub['visits_used'] >= sub['visits_limit']:
        cur.close(); conn.close()
        return False, f"Посещенията по тази карта са изчерпани ({sub['visits_used']}/{sub['visits_limit']})!"

    cur.close()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO visits (subscription_id, client_id, registered_by, notes) VALUES (%s,%s,%s,%s)",
        (subscription_id, client_id, registered_by, notes))
    cur.execute(
        "UPDATE subscriptions SET visits_used = visits_used + 1 WHERE id=%s",
        (subscription_id,))
    cur.close(); conn.close()
    return True, "Посещението е регистрирано успешно!"


def get_recent_visits(limit=50):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT v.*, c.first_name, c.last_name, p.name as plan_name,
                  u.full_name as registered_by_name
           FROM visits v
           JOIN clients c ON v.client_id=c.id
           JOIN subscriptions s ON v.subscription_id=s.id
           JOIN plans p ON s.plan_id=p.id
           LEFT JOIN users u ON v.registered_by=u.id
           ORDER BY v.visit_date DESC LIMIT %s""",
        (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_stats():
    """Dashboard statistics."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) as total FROM clients")
    total_clients = cur.fetchone()['total']

    # Active = not date-expired AND not visits-exhausted
    cur.execute("""
        SELECT COUNT(*) as total
        FROM subscriptions s JOIN plans p ON s.plan_id = p.id
        WHERE s.status='active' AND s.end_date >= CURDATE()
          AND (p.visits_limit IS NULL OR s.visits_used < p.visits_limit)""")
    active_subs = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as total FROM visits WHERE DATE(visit_date)=CURDATE()")
    today_visits = cur.fetchone()['total']

    cur.execute("""
        SELECT COUNT(*) as total
        FROM subscriptions s JOIN plans p ON s.plan_id = p.id
        WHERE s.end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
          AND s.status='active'
          AND (p.visits_limit IS NULL OR s.visits_used < p.visits_limit)""")
    expiring_soon = cur.fetchone()['total']

    cur.close(); conn.close()
    return {
        'total_clients': total_clients,
        'active_subs': active_subs,
        'today_visits': today_visits,
        'expiring_soon': expiring_soon,
    }


# ══════════════════════════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════════════════════════

def get_revenue_by_plan():
    """Revenue breakdown by plan (excluding cancelled)."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT p.name, COUNT(s.id) as count, SUM(p.price) as revenue
           FROM subscriptions s JOIN plans p ON s.plan_id = p.id
           WHERE s.status != 'cancelled'
           GROUP BY p.id, p.name
           ORDER BY revenue DESC""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_monthly_visits_stats():
    """Visits per month for the last 12 months."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT DATE_FORMAT(visit_date, '%Y-%m') as month, COUNT(*) as visits
           FROM visits
           WHERE visit_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
           GROUP BY month ORDER BY month""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_all_subscriptions_export():
    """Full subscription list for CSV export."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT s.id, c.first_name, c.last_name, c.phone, c.email,
                  p.name as plan_name, p.price,
                  s.start_date, s.end_date, s.visits_used, s.status,
                  u.full_name as sold_by_name, s.created_at
           FROM subscriptions s
           JOIN clients c ON s.client_id = c.id
           JOIN plans p ON s.plan_id = p.id
           LEFT JOIN users u ON s.sold_by = u.id
           ORDER BY s.created_at DESC""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows
