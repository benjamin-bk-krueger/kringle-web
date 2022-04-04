import psycopg2 
import json
import os
from psycopg2 import Error 
from flask import Flask, request, render_template, jsonify

gamedata = os.environ['HOME'] + "/.kringlecon"  # directory for game data

app = Flask(__name__)

# open a connection to PostgreSQL DB and return the connection
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

# fetch the configuration again from the default URL - HIDDEN "urlrefresh" command assigned
def refresh_data():
    counter_room = 1
    counter_item = 1
    counter_character = 1
    counter_objective = 1
    counter_loaded = 0
    f = open(gamedata + "/data.json")
    data = json.load(f)

    try:
        # Connect to an existing database
        connection = get_db_connection()

        # Create a cursor to perform database operations
        cursor = connection.cursor()
        # Executing a SQL query
        cursor.execute("SELECT version();")

        # purge the whole database
        delete_query = "DELETE FROM junction;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM person;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM objective;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM item;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM room;"
        cursor.execute(delete_query)
        connection.commit()

        # load all rooms
        for i in data["rooms"]:
            room_id = counter_room
            room_name = i["name"]
            room_desc = i["description"]

            insert_query = "INSERT INTO room (room_id, room_name, room_desc) VALUES (%s, %s, %s);"
            cursor.execute(insert_query, (room_id, room_name, room_desc))
            connection.commit()

            counter_room = counter_room + 1
            counter_loaded = counter_loaded + 1
            
            # load all items in the room
            if "items" in i:
                for j in i["items"]:
                    item_id = counter_item
                    item_name = j["name"]
                    item_desc = j["description"]

                    insert_query = "INSERT INTO item (item_id, room_name, item_name, item_desc) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (item_id, room_name, item_name, item_desc))
                    connection.commit()

                    counter_item = counter_item + 1
                    counter_loaded = counter_loaded + 1
                
            # load all characters in the room
            if "characters" in i:
                for j in i["characters"]:
                    person_id = counter_character
                    person_name = j["name"]
                    person_desc = j["description"]

                    insert_query = "INSERT INTO person (person_id, room_name, person_name, person_desc) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (person_id, room_name, person_name, person_desc))
                    connection.commit()

                    counter_character = counter_character + 1
                    counter_loaded = counter_loaded + 1

            # load all objectives in the room
            if "objectives" in i:
                for j in i["objectives"]:
                    objective_id = counter_objective
                    objective_name = j["name"]
                    objective_desc = j["description"]
                    difficulty = j["difficulty"]
                    objective_url = j["url"]
                    supported_by = j["supportedby"]
                    requires = j["requires"]

                    insert_query = "INSERT INTO objective (objective_id, room_name, objective_name, objective_desc, difficulty, objective_url, supported_by, requires) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (objective_id, room_name, objective_name, objective_desc, difficulty, objective_url, supported_by, requires))
                    connection.commit()

                    counter_objective = counter_objective + 1
                    counter_loaded = counter_loaded + 1

            # load all junctions in the room
            if "junctions" in i:
                for j in i["junctions"]:
                    destination = j["destination"]
                    junction_desc = j["description"]

                    insert_query = "INSERT INTO junction (destination, room_name, junction_desc) VALUES (%s, %s, %s);"
                    cursor.execute(insert_query, (destination, room_name, junction_desc))
                    connection.commit()

                    counter_loaded = counter_loaded + 1

    except (Exception, Error) as error:
        return 0
    finally:
        if (connection):
            cursor.close()
            connection.close()
    
    f.close()
    return(counter_loaded)

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
def set_world():
    auth = request.authorization
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            record = json.loads(request.data)
            with open(gamedata + "/data.json", 'w') as f:
                f.write(json.dumps(record, indent=4))
            i = refresh_data()
            return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
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
            with open(gamedata + "/data.json", 'r') as f:
                data = f.read()
                records = json.loads(data)
                return jsonify(records)
        else:
            return jsonify({'error': 'wrong credentials'})
    else:
        return jsonify({'error': 'no credentials'})


@app.route('/api/room/<int:num>', methods=['POST'])
def set_room():
    auth = request.authorization
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            record = json.loads(request.data)
            with open(gamedata + "/data.json", 'w') as f:
                f.write(json.dumps(record, indent=4))
            i = refresh_data()
            return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
        else:
            return jsonify({'error': 'wrong credentials'})
    else:
        return jsonify({'error': 'no credentials'})

@app.route('/api/room/<int:num>', methods=['GET'])
def get_room():
    # name = request.args.get('name')
    # print name
    auth = request.authorization
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(f'SELECT * FROM room where room_id = {num};')
            room = cur.fetchone()
            cur.close()
            conn.close()
            return jsonify({'name': room[1],  'description': room[2]})
        else:
            return jsonify({'error': 'wrong credentials'})
    else:
        return jsonify({'error': 'no credentials'})