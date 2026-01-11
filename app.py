import os
import datetime
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random

app = Flask(__name__)
DB_NAME = "incidents.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incident (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER UNIQUE,
                title TEXT NOT NULL,
                service TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_to TEXT
            )
        ''')
        # Check if we have any data, if not seed some
        cursor.execute('SELECT count(*) FROM incident')
        if cursor.fetchone()[0] == 0:
            seed_data = [
                (32521, 'Slow performance on Web Server', 'New Relic', 'Acknowledged', 'Dave'),
                (32519, 'Low Appdex on DB Server', 'New Relic', 'Triggered', '--'),
                (32518, 'A triggered incident', 'Enterprise performance', 'Triggered', '--'),
                (32517, 'A triggered incident', 'Enterprise performance', 'Triggered', '--'),
                (32514, 'Slow performance on Web Server', 'New Relic', 'Triggered', '--'),
                (32512, 'Low Appdex on Web Server', 'New Relic', 'Triggered', '--'),
                (32511, 'High Load on Web Server', 'New Relic', 'Triggered', '--'),
                (32510, 'A triggered incident', 'logic monitor stuff', 'Triggered', '--'),
                (32509, 'A triggered incident', 'Nagios', 'Triggered', '--')
            ]
            # We need to insert created_at as well, let's just use current time for simplicity or fake it
            # For simplicity in this demo, we'll let the DB handle created_at or pass it if needed.
            # But the schema has a default. Let's just insert the other fields.
            cursor.executemany('''
                INSERT INTO incident (number, title, service, status, assigned_to)
                VALUES (?, ?, ?, ?, ?)
            ''', seed_data)
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect(url_for('incidents'))

@app.route('/incidents')
def incidents():
    status_filter = request.args.get('status')
    assigned_to_filter = request.args.get('assigned_to')
    
    conn = get_db_connection()
    
    query = 'SELECT * FROM incident'
    params = []
    conditions = []
    
    if status_filter:
        if status_filter == 'Open':
            conditions.append("status IN ('Triggered', 'Acknowledged')")
        elif status_filter == 'Any':
            pass # No filter
        else:
            conditions.append("status = ?")
            params.append(status_filter)
            
    if assigned_to_filter == 'me':
        conditions.append("assigned_to = ?")
        params.append('Dave') # Mocking 'me' as Dave
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
        
    query += ' ORDER BY number DESC'
    
    incidents = conn.execute(query, params).fetchall()
    
    # Calculate counts for the dashboard summary (always based on all incidents)
    all_incidents = conn.execute('SELECT * FROM incident').fetchall()
    conn.close()
    
    open_count = 0
    triggered_count = 0
    acknowledged_count = 0
    resolved_count = 0
    
    for inc in all_incidents:
        if inc['status'] == 'Triggered':
            triggered_count += 1
            open_count += 1
        elif inc['status'] == 'Acknowledged':
            acknowledged_count += 1
            open_count += 1
        elif inc['status'] == 'Resolved':
            resolved_count += 1
            
    return render_template('dashboard.html', 
                           incidents=incidents, 
                           open_count=open_count,
                           triggered_count=triggered_count,
                           acknowledged_count=acknowledged_count,
                           resolved_count=resolved_count,
                           current_status=status_filter,
                           current_assigned_to=assigned_to_filter)

@app.route('/incidents/<int:incident_number>')
def incident_detail(incident_number):
    conn = get_db_connection()
    incident = conn.execute('SELECT * FROM incident WHERE number = ?', (incident_number,)).fetchone()
    conn.close()
    if incident is None:
        return "Incident not found", 404
    return render_template('incident_detail.html', incident=incident)

@app.route('/api/incidents/bulk_update', methods=['POST'])
def bulk_update():
    data = request.get_json()
    incident_ids = data.get('incident_ids', [])
    action = data.get('action')
    assignee = data.get('assignee')
    
    if not incident_ids or not action:
        return {"error": "Missing incident_ids or action"}, 400
        
    conn = get_db_connection()
    placeholders = ','.join('?' * len(incident_ids))
    
    if action == 'resolve':
        query = f'UPDATE incident SET status = ? WHERE number IN ({placeholders})'
        conn.execute(query, ['Resolved'] + incident_ids)
    elif action == 'acknowledge':
        query = f'UPDATE incident SET status = ? WHERE number IN ({placeholders})'
        conn.execute(query, ['Acknowledged'] + incident_ids)
    elif action == 'reassign':
        if not assignee:
             return {"error": "Missing assignee for reassign action"}, 400
        query = f'UPDATE incident SET assigned_to = ? WHERE number IN ({placeholders})'
        conn.execute(query, [assignee] + incident_ids)
    else:
        return {"error": "Invalid action"}, 400
        
    conn.commit()
    conn.close()
    
    return {"success": True}

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    conn = get_db_connection()
    incidents = conn.execute('SELECT * FROM incident').fetchall()
    conn.close()
    
    incidents_list = [dict(ix) for ix in incidents]
    return {"incidents": incidents_list}

@app.route('/api/incidents/generate', methods=['POST'])
def generate_incidents():
    count = request.args.get('count', default=1, type=int)
    conn = get_db_connection()
    
    services = ['New Relic', 'Datadog', 'Nagios', 'AWS CloudWatch', 'Azure Monitor']
    statuses = ['Triggered', 'Acknowledged']
    titles = ['High CPU Usage', 'Memory Leak Detected', 'Disk Space Low', 'API Latency High', 'Service Unreachable']
    
    new_incidents = []
    
    # Get last number to increment
    cursor = conn.execute('SELECT MAX(number) FROM incident')
    max_num = cursor.fetchone()[0] or 30000
    
    for i in range(count):
        new_num = max_num + 1 + i
        title = random.choice(titles)
        service = random.choice(services)
        status = random.choice(statuses)
        
        conn.execute('INSERT INTO incident (number, title, service, status, assigned_to) VALUES (?, ?, ?, ?, ?)',
                     (new_num, title, service, status, '--'))
        new_incidents.append(new_num)
        
    conn.commit()
    conn.close()
    
    return {"message": f"Generated {count} incidents", "ids": new_incidents}


@app.route('/configuration')
def configuration():
    return render_template('base.html', content="Configuration Page Placeholder")

@app.route('/analytics')
def analytics():
    return render_template('base.html', content="Analytics Page Placeholder")

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5001)
