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

# fetch all rows from a query
def fetch_all_from_db(query):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

# fetch only a single row from a query
def fetch_one_from_db(query):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

# update one row from a query
def update_one_in_db(query):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    conn.commit()
    conn.close()

# check if the basic authentication is valid
def is_authenticated(auth):
    if auth and auth.get('username') and auth.get('password'):
        if (auth['username'] == "kringle" and auth['password'] == "kringle"):
            return True
        else:
            return False
    else:
        return False

# initialize a completely new world using a world template suplied as JSON
def init_world(world):
    counter_room = 1
    counter_item = 1
    counter_character = 1
    counter_objective = 1
    counter_loaded = 0

    f = open(world)
    data = json.load(f)

    try:
        # Connect to an existing database and ceate a cursor to perform database operations
        connection = get_db_connection()
        cursor = connection.cursor()

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

# enable a HTML view to read the database contents
@app.route('/flask/room', methods = ['GET'])
def get_all_rooms():
    rooms = fetch_all_from_db('SELECT * FROM room;')
    return render_template('room.html', rooms=rooms)

@app.route('/flask/room/<int:num>', methods = ['GET'])
def get_single_room(num):
    rooms = fetch_all_from_db(f'SELECT * FROM room where room_id = {num};')
    return render_template('room.html', rooms=rooms)

@app.route('/flask/item', methods = ['GET'])
def get_all_items():
    items = fetch_all_from_db('SELECT * FROM item;')
    return render_template('item.html', items=items)

@app.route('/flask/item/<int:num>', methods = ['GET'])
def get_single_item(num):
    items = fetch_all_from_db(f'SELECT * FROM item where item_id = {num};')
    return render_template('item.html', items=items)

@app.route('/flask/person', methods = ['GET'])
def get_all_persons():
    persons = fetch_all_from_db('SELECT * FROM person;')
    return render_template('person.html', persons=persons)

@app.route('/flask/person/<int:num>', methods = ['GET'])
def get_single_person(num):
    persons = fetch_all_from_db(f'SELECT * FROM person where person_id = {num};')
    return render_template('person.html', persons=persons)

@app.route('/flask/objective', methods = ['GET'])
def get_all_objectives():
    objectives = fetch_all_from_db('SELECT * FROM objective;')
    return render_template('objective.html', objectives=objectives)

@app.route('/flask/objective/<int:num>', methods = ['GET'])
def get_single_objective(num):
    objectives = fetch_all_from_db(f'SELECT * FROM objective where objective_id = {num};')
    return render_template('objective.html', objectives=objectives)

@app.route('/flask/junction', methods = ['GET'])
def get_all_junctions():
    junctions = fetch_all_from_db('SELECT * FROM junction;')
    return render_template('junction.html', junctions=junctions)

# enable a REST API to modify the database contents
@app.route('/api/world', methods=['POST'])
def set_world():
    if (is_authenticated(request.authorization)):
        record = json.loads(request.data)
        with open(gamedata + "/data.json", 'w') as f:
            f.write(json.dumps(record, indent=4))
        i = init_world(gamedata + "/data.json")
        return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/world', methods=['GET'])
def get_world():
    # name = request.args.get('name')
    if (is_authenticated(request.authorization)):
        with open(gamedata + "/data.json", 'r') as f:
            data = f.read()
            records = json.loads(data)
            return jsonify(records)
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['POST'])
def set_room(num):
    if (is_authenticated(request.authorization)):
        room = json.loads(request.data)
        update_one_in_db(f'UPDATE room SET room_name = \'{room["name"]}\', room_desc = \'{room["description"]}\' where room_id = {num};')
        return jsonify({'success': f'room {room["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['GET'])
def get_room(num):
    if (is_authenticated(request.authorization)):
        room = fetch_one_from_db(f'SELECT * FROM room where room_id = {num};')
        return jsonify({'name': room[1],  'description': room[2]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['POST'])
def set_item(num):
    if (is_authenticated(request.authorization)):
        item = json.loads(request.data)
        update_one_in_db(f'UPDATE item SET item_name = \'{item["name"]}\', room_desc = \'{item["description"]}\' where item_id = {num};')
        return jsonify({'success': f'item {item["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['GET'])
def get_item(num):
    if (is_authenticated(request.authorization)):
        item = fetch_one_from_db(f'SELECT * FROM item where item_id = {num};')
        return jsonify({'name': item[1],  'description': item[2]})
    else:
        return jsonify({'error': 'wrong credentials'})