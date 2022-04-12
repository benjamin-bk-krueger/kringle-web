import psycopg2 
import json
import base64
import os
from psycopg2 import Error 
from flask import Flask, request, render_template, jsonify

gamedata = os.environ['HOME'] + "/.kringlecon"  # directory for game data

creator_name = 'Ben Krueger'

world_name = 'KringleCon2021'
world_desc = 'A shiny new world'
world_url = 'None URL yet'

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

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

# remove everything in the DB
def purge_db():
    try:
        # Connect to an existing database and ceate a cursor to perform database operations
        connection = get_db_connection()
        cursor = connection.cursor()

        # purge the whole database
        delete_query = "DELETE FROM solution;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM quest;"
        cursor.execute(delete_query)
        connection.commit()
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
        delete_query = "DELETE FROM world;"
        cursor.execute(delete_query)
        connection.commit()
        delete_query = "DELETE FROM creator;"
        cursor.execute(delete_query)
        connection.commit()

    except (Exception, Error) as error:
        return 0
    finally:
        if (connection):
            cursor.close()
            connection.close()

# initialize a completely new world using a world template suplied as JSON
def init_world(worldfile):
    counter_loaded = 0

    f = open(worldfile)
    data = json.load(f)

    try:
        # Connect to an existing database and ceate a cursor to perform database operations
        connection = get_db_connection()
        cursor = connection.cursor()

        insert_query = "INSERT INTO creator (creator_name) VALUES (%s);"
        cursor.execute(insert_query, (creator_name,))
        connection.commit()
        counter_loaded = counter_loaded + 1

        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]

        insert_query = "INSERT INTO world (creator_id, world_name, world_desc, world_url) VALUES (%s, %s, %s, %s);"
        cursor.execute(insert_query, (creator_id, world_name, world_desc, world_url))
        connection.commit()
        counter_loaded = counter_loaded + 1

        world = fetch_one_from_db(f'SELECT * FROM world where world_name = \'{world_name}\';')
        world_id = world[0]

        # load all rooms before to enable foreign key relationship
        for i in data["rooms"]:
            room_name = i["name"]
            room_desc = i["description"]

            insert_query = "INSERT INTO room (world_id, room_name, room_desc) VALUES (%s, %s, %s);"
            cursor.execute(insert_query, (world_id, room_name, room_desc))
            connection.commit()
            counter_loaded = counter_loaded + 1

        # load all other elements and check foreign key relationship
        for i in data["rooms"]:
            room_name = i["name"]
            room = fetch_one_from_db(f'SELECT * FROM room where room_name = \'{room_name}\' and world_id = {world_id};')
            room_id = room[0]

            # load all items in the room
            if "items" in i:
                for j in i["items"]:
                    item_name = j["name"]
                    item_desc = j["description"]

                    insert_query = "INSERT INTO item (room_id, world_id, item_name, item_desc) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, item_name, item_desc))
                    connection.commit()
                    counter_loaded = counter_loaded + 1
            
            # load all characters in the room
            if "characters" in i:
                for j in i["characters"]:
                    person_name = j["name"]
                    person_desc = j["description"]

                    insert_query = "INSERT INTO person (room_id, world_id, person_name, person_desc) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, person_name, person_desc))
                    connection.commit()
                    counter_loaded = counter_loaded + 1
            
            # load all objectives in the room
            if "objectives" in i:
                for j in i["objectives"]:
                    objective_name = j["name"]
                    objective_desc = j["description"]
                    difficulty = j["difficulty"]
                    objective_url = j["url"]
                    supported_by = j["supportedby"]
                    requires = j["requires"]

                    insert_query = "INSERT INTO objective (room_id, world_id, objective_name, objective_desc, difficulty, objective_url, supported_by, requires) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, objective_name, objective_desc, difficulty, objective_url, supported_by, requires))
                    connection.commit()
                    counter_loaded = counter_loaded + 1
            
            # load all junctions in the room
            if "junctions" in i:
                for j in i["junctions"]:
                    destination = j["destination"]
                    junction_desc = j["description"]

                    dest = fetch_one_from_db(f'SELECT * FROM room where room_name = \'{destination}\' and world_id = {world_id};')
                    dest_id = dest[0]

                    insert_query = "INSERT INTO junction (room_id, world_id, dest_id, junction_desc) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, dest_id, junction_desc))
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

@app.route('/flask/index', methods = ['GET'])
def get_my_index():
    return render_template('index.html')

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

@app.route('/flask/junction/<int:num>', methods = ['GET'])
def get_single_junction(num):
    junctions = fetch_all_from_db(f'SELECT * FROM junction where junction_id = {num};')
    return render_template('junction.html', junctions=junctions)

@app.route('/flask/quest/<int:num>', methods=['POST'])
def set_single_quest(num):
    if (is_authenticated(request.authorization) or True):
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]
        id = "quest"
        
        update_one_in_db(f'DELETE FROM quest WHERE objective_id = {num} and creator_id = {creator_id};')
        update_one_in_db(f'INSERT INTO quest (objective_id, creator_id, quest_text) VALUES ({num}, {creator_id}, {psycopg2.Binary(request.form[id].encode())});')
        return "ok"
    else:
        return "wrong credentials"

@app.route('/flask/quest/<int:num>', methods=['GET'])
def get_single_quest(num):
    if (is_authenticated(request.authorization) or True):
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]

        quest = fetch_one_from_db(f'SELECT * FROM quest where objective_id = {num} and creator_id = {creator_id};')
        if (quest != None):
            return render_template('quest.html', quest=str(bytes(quest[3]), 'utf-8'), number=num)
        else:
            return render_template('quest.html', quest="", number=num)
    else:
        return "wrong credentials"

@app.route('/flask/solution/<int:num>', methods=['POST'])
def set_single_solution(num):
    if (is_authenticated(request.authorization) or True):
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]
        id = "solution"
        
        update_one_in_db(f'DELETE FROM solution WHERE objective_id = {num} and creator_id = {creator_id};')
        update_one_in_db(f'INSERT INTO solution (objective_id, creator_id, solution_text) VALUES ({num}, {creator_id}, {psycopg2.Binary(request.form[id].encode())});')
        return "ok"
    else:
        return "wrong credentials"

@app.route('/flask/solution/<int:num>', methods=['GET'])
def get_single_solution(num):
    if (is_authenticated(request.authorization) or True):
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]

        solution = fetch_one_from_db(f'SELECT * FROM solution where objective_id = {num} and creator_id = {creator_id};')
        if (solution != None):
            return render_template('solution.html', solution=str(bytes(solution[3]), 'utf-8'), number=num)
        else:
            return render_template('solution.html', solution="", number=num)
    else:
        return "wrong credentials"

# enable a REST API to modify the database contents
@app.route('/api/world', methods=['POST'])
def set_world():
    if (is_authenticated(request.authorization)):
        record = json.loads(request.data)
        with open(gamedata + "/data.json", 'w') as f:
            f.write(json.dumps(record, indent=4))
        purge_db()
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
        return jsonify({'name': room[2],  'description': room[3]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['POST'])
def set_item(num):
    if (is_authenticated(request.authorization)):
        item = json.loads(request.data)
        update_one_in_db(f'UPDATE item SET item_name = \'{item["name"]}\', item_desc = \'{item["description"]}\' where item_id = {num};')
        return jsonify({'success': f'item {item["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['GET'])
def get_item(num):
    if (is_authenticated(request.authorization)):
        item = fetch_one_from_db(f'SELECT * FROM item where item_id = {num};')
        return jsonify({'name': item[3],  'description': item[4]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['POST'])
def set_person(num):
    if (is_authenticated(request.authorization)):
        person = json.loads(request.data)
        update_one_in_db(f'UPDATE person SET person_name = \'{person["name"]}\', person_desc = \'{person["description"]}\' where person_id = {num};')
        return jsonify({'success': f'person {person["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['GET'])
def get_person(num):
    if (is_authenticated(request.authorization)):
        person = fetch_one_from_db(f'SELECT * FROM person where person_id = {num};')
        return jsonify({'name': person[3],  'description': person[4]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['POST'])
def set_objective(num):
    if (is_authenticated(request.authorization)):
        objective = json.loads(request.data)
        update_one_in_db(f'UPDATE objective SET objective_name = \'{objective["name"]}\', objective_desc = \'{objective["description"]}\', difficulty = \'{objective["difficulty"]}\', objective_url = \'{objective["url"]}\', supported_by = \'{objective["supportedby"]}\', requires = \'{objective["requires"]}\' where objective_id = {num};')
        return jsonify({'success': f'objective {objective["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['GET'])
def get_objective(num):
    if (is_authenticated(request.authorization)):
        objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
        return jsonify({'name': objective[3],  'description': objective[4],  'difficulty': objective[5],  'url': objective[6],  'supportedby': objective[7],  'requires': objective[8]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['POST'])
def set_junction(num):
    if (is_authenticated(request.authorization)):
        junction = json.loads(request.data)
        update_one_in_db(f'UPDATE junction SET dest_id = \'{junction["destination"]}\', junction_desc = \'{junction["description"]}\' where junction_id = {num};')
        return jsonify({'success': f'junction {junction["destination"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['GET'])
def get_junction(num):
    if (is_authenticated(request.authorization)):
        junction = fetch_one_from_db(f'SELECT * FROM junction where junction_id = {num};')
        return jsonify({'destination': junction[3],  'description': junction[4]})
    else:
        return jsonify({'error': 'wrong credentials'})
