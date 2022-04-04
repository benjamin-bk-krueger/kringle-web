import psycopg2 
import json
from psycopg2 import Error 
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(user="postgres",
                                    password="postgres",
                                    host="kringle_database",
                                    port="5432",
                                    database="postgres")
        return conn
    except (Exception, Error) as error:
        return None

@app.route('/flask/room', methods = ['GET'])
def get_all_rooms():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM room;')
    rooms = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('room.html', rooms=rooms)

@app.route('/flask/room/<int:num>', methods = ['GET'])
def get_single_room(num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM room where room_id = {num};')
    rooms = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('room.html', rooms=rooms)

@app.route('/flask/item', methods = ['GET'])
def get_all_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM item;')
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('item.html', items=items)

@app.route('/flask/item/<int:num>', methods = ['GET'])
def get_single_item(num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM item where item_id = {num};')
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('item.html', items=items)

@app.route('/flask/person', methods = ['GET'])
def get_all_persons():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM person;')
    persons = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('person.html', persons=persons)

@app.route('/flask/person/<int:num>', methods = ['GET'])
def get_single_person(num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM person where person_id = {num};')
    persons = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('person.html', persons=persons)

@app.route('/flask/objective', methods = ['GET'])
def get_all_objectives():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM objective;')
    objectives = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('objective.html', objectives=objectives)

@app.route('/flask/objective/<int:num>', methods = ['GET'])
def get_single_objective(num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM objective where objective_id = {num};')
    objectives = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('objective.html', objectives=objectives)

@app.route('/flask/junction', methods = ['GET'])
def get_all_junctions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM junction;')
    junctions = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('junction.html', junctions=junctions)


@app.route('/api/world', methods=['POST'])
def create_world():
    auth = request.authorization
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            record = json.loads(request.data)
            with open('/tmp/world.json', 'w') as f:
                f.write(json.dumps(record, indent=4))
            return jsonify({'success': 'world file stored'})
        else:
            return jsonify({'error': 'wrong credentials'})
    else:
        return jsonify({'error': 'no credentials'})

@app.route('/api/world', methods=['GET'])
def get_world():
    # name = request.args.get('name')
    # print name
    auth = request.authorization
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            with open('/tmp/world.json', 'r') as f:
                data = f.read()
                records = json.loads(data)
                return jsonify(records)
        else:
            return jsonify({'error': 'wrong credentials'})
    else:
        return jsonify({'error': 'no credentials'})
