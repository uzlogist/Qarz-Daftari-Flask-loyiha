from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import pandas as pd
import io
import sqlite3

app = Flask(__name__)

# SQLite ma'lumotlar bazasini sozlash
def init_db():
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS debtors (
            name TEXT PRIMARY KEY,
            debt INTEGER NOT NULL,
            paid INTEGER NOT NULL
        )''')
        conn.commit()

init_db()

@app.route('/')
def index():
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, debt, paid FROM debtors")
        debtors = {row[0]: {"debt": row[1], "paid": row[2]} for row in cursor.fetchall()}

    total_debt = sum(info['debt'] for info in debtors.values())
    total_paid = sum(info['paid'] for info in debtors.values())
    return render_template('index.html', debtors=debtors, total_debt=total_debt, total_paid=total_paid)

@app.route('/add_debtor', methods=['POST'])
def add_debtor():
    name = request.form['name']
    debt = int(request.form['debt'])
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT debt, paid FROM debtors WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE debtors SET debt = debt + ? WHERE name = ?", (debt, name))
        else:
            cursor.execute("INSERT INTO debtors (name, debt, paid) VALUES (?, ?, 0)", (name, debt))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/reduce_debt', methods=['POST'])
def reduce_debt():
    name = request.form['name']
    payment = int(request.form['payment'])
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT debt, paid FROM debtors WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            new_debt = row[0] - payment
            new_paid = row[1] + payment
            if new_debt <= 0:
                cursor.execute("DELETE FROM debtors WHERE name = ?", (name,))
            else:
                cursor.execute("UPDATE debtors SET debt = ?, paid = ? WHERE name = ?", (new_debt, new_paid, name))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, debt, paid FROM debtors WHERE lower(name) LIKE ?", (f"%{query}%",))
        results = {row[0]: {"debt": row[1], "paid": row[2]} for row in cursor.fetchall()}
    return jsonify(results)

@app.route('/export')
def export():
    with sqlite3.connect('debtors.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, debt, paid FROM debtors")
        data = [{"Ism": row[0], "Qarzi": row[1], "To'lagani": row[2]} for row in cursor.fetchall()]

    df = pd.DataFrame(data)

    total_debt = df["Qarzi"].sum() if not df.empty else 0
    total_paid = df["To'lagani"].sum() if not df.empty else 0

    summary = pd.DataFrame([
        {"Ism": "Jami", "Qarzi": total_debt, "To'lagani": total_paid}
    ])

    df = pd.concat([df, summary], ignore_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Qarzdorlar')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="qarzdorlar.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)