import os
import sqlite3
from flask import Flask, render_template_string, request, abort, redirect, url_for

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
    if not table.replace('_', '').isalnum():
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if table == 'logs':
        cursor.execute(f"SELECT * FROM `{table}` ORDER BY timestamp DESC")
    else:
        cursor.execute(f"SELECT * FROM `{table}`")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, rows

def get_table_schema(db_path, table):
    if not table.isalnum() and '_' not in table:
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info(`{table}`)")
    schema = cursor.fetchall()
    conn.close()
    return schema

def update_record(db_path, table, record_id, data):
    if not table.replace('_', '').isalnum():
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    valid_columns = [col[1] for col in get_table_schema(db_path, table)]
    filtered_data = {k: v for k, v in data.items() if k in valid_columns}
    
    if not filtered_data:
        conn.close()
        return
    
    set_clause = ', '.join([f"`{col}` = ?" for col in filtered_data.keys()])
    values = list(filtered_data.values()) + [record_id]
    cursor.execute(f"UPDATE `{table}` SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_record(db_path, table, record_id):
    if not table.replace('_', '').isalnum():
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM `{table}` WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def add_record(db_path, table, data):
    if not table.replace('_', '').isalnum():
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    valid_columns = [col[1] for col in get_table_schema(db_path, table)]
    filtered_data = {k: v for k, v in data.items() if k in valid_columns}
    
    if not filtered_data:
        conn.close()
        return
    
    columns = ', '.join([f"`{col}`" for col in filtered_data.keys()])
    placeholders = ', '.join(['?' for _ in filtered_data])
    cursor.execute(f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})", list(filtered_data.values()))
    conn.commit()
    conn.close()

def delete_all_records(db_path, table):
    if not table.replace('_', '').isalnum():
        raise ValueError("Invalid table name")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM `{table}`")
    conn.commit()
    conn.close()

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
            <th>Actions</th>
            </tr>
            {% for row in rows %}
            <tr>
                {% for cell in row %}
                <td>{{ cell }}</td>
                {% endfor %}
                <td>
                    <a href="{{ url_for('edit_record', db_name=db_name, table=table, record_id=row[0]) }}" style="background:#28a745;margin:2px;">Edit</a>
                    <a href="{{ url_for('delete_record_confirm', db_name=db_name, table=table, record_id=row[0]) }}" style="background:#dc3545;margin:2px;">Delete</a>
                </td>
            </tr>
            {% endfor %}
        </table>
        <div style="text-align:center;margin:20px;">
            <a href="{{ url_for('add_record_form', db_name=db_name, table=table) }}" style="background:#007bff;">Add New Record</a>
            <a href="{{ url_for('delete_all_confirm', db_name=db_name, table=table) }}" style="background:#dc3545;margin-left:10px;">Delete All Records</a>
        </div>
        <a href="{{ url_for('view_db', db_name=db_name) }}">Back</a>
        </body>
        </html>
    ''', db_name=db_name, table=table, columns=columns, rows=rows)

@app.route('/db/<db_name>/<table>/edit/<int:record_id>')
def edit_record(db_name, table, record_id):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        schema = get_table_schema(db_path, table)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{table}` WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            return "Record not found", 404
            
    except Exception as e:
        return f"Error: {e}", 500
    
    return render_template_string('''
        <html>
        <head>
        <title>Edit Record - {{ table }} ({{ db_name }})</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f6f8fa; color: #222; margin: 0; padding: 40px; }
            h2 { text-align: center; color: #2d3748; }
            form { max-width: 600px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #0001; }
            label { display: block; margin: 15px 0 5px 0; font-weight: 600; color: #2d3748; }
            input[type="text"], input[type="email"], input[type="number"], textarea { width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
            input[readonly] { background: #f7fafc; color: #718096; }
            .button-group { text-align: center; margin-top: 25px; }
            button, .btn { display: inline-block; margin: 8px; padding: 10px 20px; background: #3182ce; color: #fff; border: none; border-radius: 5px; text-decoration: none; font-weight: 500; cursor: pointer; transition: background 0.2s; }
            button:hover, .btn:hover { background: #225ea8; }
            .btn-cancel { background: #718096; }
            .btn-cancel:hover { background: #4a5568; }
        </style>
        </head>
        <body>
        <h2>Edit Record - {{ table }} ({{ db_name }})</h2>
        <form method="POST" action="{{ url_for('update_record_route', db_name=db_name, table=table, record_id=record_id) }}">
            {% for i in range(schema|length) %}
                <label for="{{ schema[i][1] }}">{{ schema[i][1] }}{% if schema[i][3] %} (Required){% endif %}:</label>
                {% if schema[i][1] == 'id' %}
                    <input type="text" id="{{ schema[i][1] }}" name="{{ schema[i][1] }}" value="{{ record[i] }}" readonly>
                {% else %}
                    <input type="text" id="{{ schema[i][1] }}" name="{{ schema[i][1] }}" value="{{ record[i] if record[i] else '' }}" {% if schema[i][3] %}required{% endif %}>
                {% endif %}
            {% endfor %}
            <div class="button-group">
                <button type="submit">Update Record</button>
                <a href="{{ url_for('view_table', db_name=db_name, table=table) }}" class="btn btn-cancel">Cancel</a>
            </div>
        </form>
        </body>
        </html>
    ''', db_name=db_name, table=table, record_id=record_id, schema=schema, record=record)

@app.route('/db/<db_name>/<table>/update/<int:record_id>', methods=['POST'])
def update_record_route(db_name, table, record_id):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        data = {}
        for key, value in request.form.items():
            if key != 'id':
                data[key] = value if value.strip() else None
        
        update_record(db_path, table, record_id, data)
        return redirect(url_for('view_table', db_name=db_name, table=table))
    except Exception as e:
        return f"Error updating record: {e}", 500

@app.route('/db/<db_name>/<table>/delete/<int:record_id>')
def delete_record_confirm(db_name, table, record_id):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{table}` WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            return "Record not found", 404
            
    except Exception as e:
        return f"Error: {e}", 500
    
    return render_template_string('''
        <html>
        <head>
        <title>Delete Record - {{ table }} ({{ db_name }})</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f6f8fa; color: #222; margin: 0; padding: 40px; text-align: center; }
            h2 { color: #2d3748; }
            .warning { background: #fff; max-width: 500px; margin: 30px auto; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #0001; border-left: 4px solid #dc3545; }
            .record-info { background: #f7fafc; padding: 15px; border-radius: 4px; margin: 20px 0; font-family: monospace; }
            .button-group { margin-top: 25px; }
            .btn { display: inline-block; margin: 8px; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: 500; transition: background 0.2s; }
            .btn-delete { background: #dc3545; color: #fff; }
            .btn-delete:hover { background: #c82333; }
            .btn-cancel { background: #6c757d; color: #fff; }
            .btn-cancel:hover { background: #545b62; }
        </style>
        </head>
        <body>
        <div class="warning">
            <h2>Confirm Delete</h2>
            <p>Are you sure you want to delete this record from <strong>{{ table }}</strong>?</p>
            <div class="record-info">
                Record ID: {{ record_id }}<br>
                {% if record %}
                    Preview: {{ record[:3]|join(', ') }}{% if record|length > 3 %}...{% endif %}
                {% endif %}
            </div>
            <div class="button-group">
                <a href="{{ url_for('delete_record_execute', db_name=db_name, table=table, record_id=record_id) }}" class="btn btn-delete">Yes, Delete</a>
                <a href="{{ url_for('view_table', db_name=db_name, table=table) }}" class="btn btn-cancel">Cancel</a>
            </div>
        </div>
        </body>
        </html>
    ''', db_name=db_name, table=table, record_id=record_id, record=record)

@app.route('/db/<db_name>/<table>/delete/<int:record_id>/execute')
def delete_record_execute(db_name, table, record_id):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        delete_record(db_path, table, record_id)
        return redirect(url_for('view_table', db_name=db_name, table=table))
    except Exception as e:
        return f"Error deleting record: {e}", 500

@app.route('/db/<db_name>/<table>/add')
def add_record_form(db_name, table):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        schema = get_table_schema(db_path, table)
    except Exception as e:
        return f"Error: {e}", 500
    
    return render_template_string('''
        <html>
        <head>
        <title>Add Record - {{ table }} ({{ db_name }})</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f6f8fa; color: #222; margin: 0; padding: 40px; }
            h2 { text-align: center; color: #2d3748; }
            form { max-width: 600px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #0001; }
            label { display: block; margin: 15px 0 5px 0; font-weight: 600; color: #2d3748; }
            input[type="text"], input[type="email"], input[type="number"], textarea { width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
            .button-group { text-align: center; margin-top: 25px; }
            button, .btn { display: inline-block; margin: 8px; padding: 10px 20px; background: #3182ce; color: #fff; border: none; border-radius: 5px; text-decoration: none; font-weight: 500; cursor: pointer; transition: background 0.2s; }
            button:hover, .btn:hover { background: #225ea8; }
            .btn-cancel { background: #718096; }
            .btn-cancel:hover { background: #4a5568; }
            .note { font-size: 12px; color: #718096; margin-top: 5px; }
        </style>
        </head>
        <body>
        <h2>Add New Record - {{ table }} ({{ db_name }})</h2>
        <form method="POST" action="{{ url_for('add_record_submit', db_name=db_name, table=table) }}">
            {% for col in schema %}
                {% if col[1] != 'id' or not col[5] %}
                    <label for="{{ col[1] }}">{{ col[1] }}{% if col[3] %} (Required){% endif %}:</label>
                    <input type="text" id="{{ col[1] }}" name="{{ col[1] }}" {% if col[3] %}required{% endif %}>
                    {% if col[1] == 'id' %}
                        <div class="note">Leave empty for auto-increment</div>
                    {% endif %}
                {% endif %}
            {% endfor %}
            <div class="button-group">
                <button type="submit">Add Record</button>
                <a href="{{ url_for('view_table', db_name=db_name, table=table) }}" class="btn btn-cancel">Cancel</a>
            </div>
        </form>
        </body>
        </html>
    ''', db_name=db_name, table=table, schema=schema)

@app.route('/db/<db_name>/<table>/add', methods=['POST'])
def add_record_submit(db_name, table):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        data = {}
        for key, value in request.form.items():
            if value.strip():
                data[key] = value
        
        add_record(db_path, table, data)
        return redirect(url_for('view_table', db_name=db_name, table=table))
    except Exception as e:
        return f"Error adding record: {e}", 500

@app.route('/db/<db_name>/<table>/delete_all')
def delete_all_confirm(db_name, table):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        return f"Error: {e}", 500
    
    return render_template_string('''
        <html>
        <head>
        <title>Delete All Records - {{ table }} ({{ db_name }})</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f6f8fa; color: #222; margin: 0; padding: 40px; text-align: center; }
            h2 { color: #2d3748; }
            .warning { background: #fff; max-width: 600px; margin: 30px auto; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px #0001; border-left: 6px solid #dc3545; }
            .count-info { background: #fff3cd; padding: 20px; border-radius: 4px; margin: 20px 0; font-size: 18px; font-weight: 600; color: #856404; border: 1px solid #ffeaa7; }
            .danger-text { color: #dc3545; font-weight: 700; font-size: 20px; margin: 20px 0; }
            .button-group { margin-top: 30px; }
            .btn { display: inline-block; margin: 10px; padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: 600; transition: background 0.2s; }
            .btn-delete { background: #dc3545; color: #fff; }
            .btn-delete:hover { background: #c82333; }
            .btn-cancel { background: #6c757d; color: #fff; }
            .btn-cancel:hover { background: #545b62; }
        </style>
        </head>
        <body>
        <div class="warning">
            <h2>⚠️ Confirm Delete All Records</h2>
            <div class="danger-text">This action cannot be undone!</div>
            <p>Are you sure you want to delete <strong>ALL</strong> records from table <strong>{{ table }}</strong>?</p>
            <div class="count-info">
                {{ count }} record(s) will be permanently deleted
            </div>
            <p>This will completely empty the table but keep its structure intact.</p>
            <div class="button-group">
                <a href="{{ url_for('delete_all_execute', db_name=db_name, table=table) }}" class="btn btn-delete">Yes, Delete All {{ count }} Records</a>
                <a href="{{ url_for('view_table', db_name=db_name, table=table) }}" class="btn btn-cancel">Cancel</a>
            </div>
        </div>
        </body>
        </html>
    ''', db_name=db_name, table=table, count=count)

@app.route('/db/<db_name>/<table>/delete_all/execute')
def delete_all_execute(db_name, table):
    db_path = safe_db_path(db_name)
    if not os.path.exists(db_path):
        return "Database not found", 404
    
    try:
        delete_all_records(db_path, table)
        return redirect(url_for('view_table', db_name=db_name, table=table))
    except Exception as e:
        return f"Error deleting all records: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6970, debug=True)

