import os
import sqlite3
from flask import Flask, render_template_string, request, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'host/db')

def safe_db_path(db_name):
    if '/' in db_name or '\\' in db_name or not db_name.endswith('.db'):
        abort(400, "Invalid database name")
    db_path = os.path.abspath(os.path.join(DB_DIR, db_name))
    if not db_path.startswith(os.path.abspath(DB_DIR)):
        abort(400, "Invalid database path")
    return db_path

def get_db_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(db_path, table):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if table == 'logs':
        cursor.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC")
    else:
        cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, rows

@app.route('/')
def index():
    db_files = [f for f in os.listdir(DB_DIR) if f.endswith('.db')]
    return render_template_string('''
        <h2>Available Databases</h2>
        <ul>
        {% for db in db_files %}
            <li><a href="{{ url_for('view_db', db_name=db) }}">{{ db }}</a></li>
        {% endfor %}
        </ul>
    ''', db_files=db_files)

@app.route('/db/<db_name>')
def view_db(db_name):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    tables = get_db_tables(db_path)
    return render_template_string('''
        <h2>Tables in {{ db_name }}</h2>
        <ul>
        {% for table in tables %}
            <li><a href="{{ url_for('view_table', db_name=db_name, table=table) }}">{{ table }}</a></li>
        {% endfor %}
        </ul>
        <a href="{{ url_for('index') }}">Back</a>
    ''', db_name=db_name, tables=tables)

@app.route('/db/<db_name>/<table>')
def view_table(db_name, table):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    try:
        columns, rows = get_table_data(db_path, table)
    except Exception as e:
        return f"Error: {e}", 500
    return render_template_string('''
        <html>
        <head>
        <title>{{ table }} ({{ db_name }})</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #f6f8fa;
                color: #222;
                margin: 0;
                padding: 0 0 40px 0;
            }
            h2 {
                margin-top: 32px;
                text-align: center;
                color: #2d3748;
            }
            table {
                border-collapse: collapse;
                margin: 30px auto 20px auto;
                min-width: 60vw;
                background: #fff;
                box-shadow: 0 2px 8px #0001;
            }
            th, td {
                padding: 8px 16px;
                border: 1px solid #e2e8f0;
                text-align: left;
            }
            th {
                background: #edf2fa;
                color: #2b6cb0;
                font-weight: 600;
            }
            tr:nth-child(even) td {
                background: #f7fafc;
            }
            tr:hover td {
                background: #e6f7ff;
            }
            a {
                display: inline-block;
                margin: 18px auto 0 auto;
                padding: 8px 18px;
                background: #3182ce;
                color: #fff;
                border-radius: 5px;
                text-decoration: none;
                font-weight: 500;
                transition: background 0.2s;
            }
            a:hover {
                background: #225ea8;
            }
            ul {
                list-style: none;
                padding: 0;
                margin: 30px auto 0 auto;
                max-width: 400px;
            }
            ul li {
                margin: 10px 0;
            }
            ul li a {
                background: #e2e8f0;
                color: #2d3748;
                padding: 8px 14px;
                border-radius: 4px;
                text-decoration: none;
                display: block;
                transition: background 0.2s;
            }
            ul li a:hover {
                background: #cbd5e1;
                color: #1a202c;
            }
        </style>
        </head>
        <body>
        <h2>{{ table }} ({{ db_name }})</h2>
        <table>
            <tr>
            {% for col in columns %}
                <th>{{ col }}</th>
            {% endfor %}
            </tr>
            {% for row in rows %}
            <tr>
                {% for cell in row %}
                <td>{{ cell }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
        <a href="{{ url_for('view_db', db_name=db_name) }}">Back</a>
        </body>
        </html>
    ''', db_name=db_name, table=table, columns=columns, rows=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6970, debug=True)

