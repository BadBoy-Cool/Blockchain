import sqlite3

def oracle_fetch_data(employee_id, month):
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()
    c.execute("SELECT SUM(hours_worked), SUM(overtime_hours) FROM attendance WHERE employee_id = ? AND strftime('%Y-%m', date) = ?", (employee_id, month))
    work_hours, overtime_hours = c.fetchone()
    c.execute("SELECT AVG(kpi_score) FROM kpi WHERE employee_id = ? AND strftime('%Y-%m', date) = ?", (employee_id, month))
    kpi_score = c.fetchone()[0]
    conn.close()
    return work_hours or 0, overtime_hours or 0, kpi_score or 0