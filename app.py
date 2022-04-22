import psycopg2 
import json
import base64
import os
import markdown2
from psycopg2 import Error 
from flask import Flask, request, render_template, jsonify
from flask_httpauth import HTTPBasicAuth # https://flask-httpauth.readthedocs.io/en/latest/
from werkzeug.security import generate_password_hash, check_password_hash

gamedata = os.environ['HOME'] + "/.kringlecon"  # directory for game data

app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')
auth = HTTPBasicAuth()

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
def init_world(worldfile, creator_name, world_name, world_desc, world_url, world_img):
    counter_loaded = 0

    f = open(worldfile)
    data = json.load(f)

    try:
        # Connect to an existing database and ceate a cursor to perform database operations
        connection = get_db_connection()
        cursor = connection.cursor()

        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]

        insert_query = "INSERT INTO world (creator_id, world_name, world_desc, world_url, world_img) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(insert_query, (creator_id, world_name, world_desc, world_url, world_img))
        connection.commit()
        counter_loaded = counter_loaded + 1

        world = fetch_one_from_db(f'SELECT * FROM world where world_name = \'{world_name}\';')
        world_id = world[0]

        # load all rooms before to enable foreign key relationship
        for i in data["rooms"]:
            room_name = i["name"]
            room_desc = i["description"]
            room_img = i["image"]

            insert_query = "INSERT INTO room (world_id, room_name, room_desc, room_img) VALUES (%s, %s, %s, %s);"
            cursor.execute(insert_query, (world_id, room_name, room_desc, room_img))
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
                    item_img = j["image"]

                    insert_query = "INSERT INTO item (room_id, world_id, item_name, item_desc, item_img) VALUES (%s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, item_name, item_desc, item_img))
                    connection.commit()
                    counter_loaded = counter_loaded + 1
            
            # load all characters in the room
            if "characters" in i:
                for j in i["characters"]:
                    person_name = j["name"]
                    person_desc = j["description"]
                    person_img = j["image"]

                    insert_query = "INSERT INTO person (room_id, world_id, person_name, person_desc, person_img) VALUES (%s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, person_name, person_desc, person_img))
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
                    objective_img = j["image"]

                    insert_query = "INSERT INTO objective (room_id, world_id, objective_name, objective_desc, difficulty, objective_url, supported_by, requires, objective_img) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (room_id, world_id, objective_name, objective_desc, difficulty, objective_url, supported_by, requires, objective_img))
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

# check if the basic authentication is valid
def is_authenticated(auth, admin):
    users = dict()
    if (admin):
        creator = fetch_all_from_db(f'SELECT creator_name, creator_pass FROM creator WHERE creator_role = \'admin\';')
    else:
        creator = fetch_all_from_db(f'SELECT creator_name, creator_pass FROM creator;')
    for i in creator:
        users[i[0]] = i[1]

    if auth:
        if auth['username'] in users and check_password_hash(users.get(auth['username']), auth['password']):
            return True
    return False

@auth.verify_password
def verify_password(username, password):
    users = dict()
    creator = fetch_all_from_db(f'SELECT creator_name, creator_pass FROM creator;')
    for i in creator:
        users[i[0]] = i[1]

    if username in users and \
            check_password_hash(users.get(username), password):
        return username

# entry pages
@app.route('/flask/login', methods = ['GET'])
@auth.login_required
def get_my_login():
    return render_template('index.html')

@app.route('/flask/index', methods = ['GET'])
def get_my_index():
    return render_template('index.html')

# enable a HTML view to read the database contents
@app.route('/flask/creators', methods = ['GET'])
def get_all_creators():
    creators = fetch_all_from_db('SELECT * FROM creator ORDER BY creator_id ASC;')
    return render_template('creator.html', creators=creators)

@app.route('/flask/creator/<int:num>', methods = ['GET'])
def get_single_creator(num):
    creator = fetch_one_from_db(f'SELECT * FROM creator where creator_id = {num};')
    return render_template('creator_detail.html', creator=creator)

@app.route('/flask/newcreator', methods=['GET'])
def get_new_creator():
    return render_template('creator_new.html')

@app.route('/flask/newcreator', methods=['POST'])
def post_new_creator():
    creator_name = request.form["creator"]
    creator_pass = request.form["password"]
    creator_hash = generate_password_hash(creator_pass, method='pbkdf2:sha256', salt_length=16)
    update_one_in_db(f'INSERT INTO creator (creator_name, creator_pass, creator_role) VALUES (\'{creator_name}\', \'{creator_hash}\', \'user\');')
    
    creators = fetch_all_from_db('SELECT * FROM creator ORDER BY creator_id ASC;')
    return render_template('creator.html', creators=creators)

@app.route('/flask/worlds', methods = ['GET'])
def get_all_worlds():
    worlds = fetch_all_from_db('SELECT * FROM world ORDER BY world_id ASC;')
    return render_template('world.html', worlds=worlds)

@app.route('/flask/world/<int:num>', methods = ['GET'])
def get_single_world(num):
    world = fetch_one_from_db(f'SELECT * FROM world where world_id = {num};')
    return render_template('world_detail.html', world=world)

@app.route('/flask/rooms/<int:num>', methods = ['GET'])
def get_all_rooms(num):
    rooms = fetch_all_from_db(f'SELECT * FROM room where world_id = {num} ORDER BY room_id ASC;')
    return render_template('room.html', rooms=rooms, world_id=num)

@app.route('/flask/room/<int:num>', methods = ['GET'])
def get_single_room(num):
    room = fetch_one_from_db(f'SELECT * FROM room where room_id = {num};')
    return render_template('room_detail.html', room=room)

@app.route('/flask/items/<int:num>', methods = ['GET'])
def get_all_items(num):
    items = fetch_all_from_db(f'SELECT * FROM item where world_id = {num} ORDER BY item_id ASC;')
    return render_template('item.html', items=items, world_id=num)

@app.route('/flask/item/<int:num>', methods = ['GET'])
def get_single_item(num):
    item = fetch_one_from_db(f'SELECT * FROM item where item_id = {num};')
    return render_template('item_detail.html', item=item)

@app.route('/flask/persons/<int:num>', methods = ['GET'])
def get_all_persons(num):
    persons = fetch_all_from_db(f'SELECT * FROM person where world_id = {num} ORDER BY person_id ASC;')
    return render_template('person.html', persons=persons, world_id=num)

@app.route('/flask/person/<int:num>', methods = ['GET'])
def get_single_person(num):
    person = fetch_one_from_db(f'SELECT * FROM person where person_id = {num};')
    return render_template('person_detail.html', person=person)

@app.route('/flask/objectives/<int:num>', methods = ['GET'])
def get_all_objectives(num):
    objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {num} ORDER BY objective_id ASC;')
    return render_template('objective.html', objectives=objectives, world_id=num)

@app.route('/flask/objective/<int:num>', methods = ['GET'])
def get_single_objective(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (objective[10] != None):
        mdquest = markdown2.markdown(str(bytes(objective[10]), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdquest = ""
    if (objective[11] != None):
        mdsolution = markdown2.markdown(str(bytes(objective[11]), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdsolution = ""

    return render_template('objective_detail.html', objective=objective, mdquest=mdquest, mdsolution=mdsolution)

@app.route('/flask/junctions/<int:num>', methods = ['GET'])
def get_all_junctions(num):
    junctions = fetch_all_from_db(f'SELECT * FROM junction where world_id = {num} ORDER BY junction_id ASC;')
    return render_template('junction.html', junctions=junctions, world_id=num)

@app.route('/flask/junction/<int:num>', methods = ['GET'])
def get_single_junction(num):
    junction = fetch_one_from_db(f'SELECT * FROM junction where junction_id = {num};')
    return render_template('junction_detail.html', junction=junction)

@app.route('/flask/quest/<int:num>', methods=['POST'])
def set_single_quest(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, True)):
        id = "quest"

        update_one_in_db(f'UPDATE objective set quest={psycopg2.Binary(request.form[id].encode())} WHERE objective_id = {num};')
    objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
    return render_template('objective.html', objectives=objectives, world_id=objective[2])

@app.route('/flask/quest/<int:num>', methods=['GET'])
def get_single_quest(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, True)):
        if (objective[10] != None):
            return render_template('quest_detail.html', quest=str(bytes(objective[10]), 'utf-8'), number=num, world_id=objective[2])
        else:
            return render_template('quest_detail.html', quest="", number=num, world_id=objective[2])
    else:
        objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
        return render_template('objective.html', objectives=objectives, world_id=objective[2])

@app.route('/flask/solution/<int:num>', methods=['POST'])
def set_single_solution(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, True)):
        id = "solution"

        update_one_in_db(f'UPDATE objective set solution={psycopg2.Binary(request.form[id].encode())} WHERE objective_id = {num};')
    objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
    return render_template('objective.html', objectives=objectives, world_id=objective[2])

@app.route('/flask/solution/<int:num>', methods=['GET'])
def get_single_solution(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, True)):
        if (objective[11] != None):
            return render_template('solution_detail.html', solution=str(bytes(objective[11]), 'utf-8'), number=num, world_id=objective[2])
        else:
            return render_template('solution_detail.html', solution="", number=num, world_id=objective[2])
    else:
        objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
        return render_template('objective.html', objectives=objectives, world_id=objective[2])

@app.route('/flask/mysolution/<int:num>', methods=['POST'])
def set_my_solution(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, False)):
        creator_name = request.authorization['username']
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]
        id = "solution"
        
        update_one_in_db(f'DELETE FROM solution WHERE objective_id = {num} and creator_id = {creator_id};')
        update_one_in_db(f'INSERT INTO solution (objective_id, creator_id, solution_text) VALUES ({num}, {creator_id}, {psycopg2.Binary(request.form[id].encode())});')        
    objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
    return render_template('objective.html', objectives=objectives, world_id=objective[2])

@app.route('/flask/mysolution/<int:num>', methods=['GET'])
def get_my_solution(num):
    objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
    if (is_authenticated(request.authorization, False)):
        creator_name = request.authorization['username']
        creator = fetch_one_from_db(f'SELECT * FROM creator where creator_name = \'{creator_name}\';')
        creator_id = creator[0]

        solution = fetch_one_from_db(f'SELECT * FROM solution where objective_id = {num} and creator_id = {creator_id};')
        if (solution != None):
            return render_template('solution_my_detail.html', solution=str(bytes(solution[3]), 'utf-8'), number=num, world_id=objective[2])
        else:
            return render_template('solution_my_detail.html', solution="", number=num, world_id=objective[2])
    else:
        objectives = fetch_all_from_db(f'SELECT * FROM objective where world_id = {objective[2]} ORDER BY objective_id ASC;')
        return render_template('objective.html', objectives=objectives, world_id=objective[2])

# enable a REST API to modify the database contents
@app.route('/api/world', methods=['POST'])
def set_world():
    if (is_authenticated(request.authorization, True)):
        world_name = request.args.get('worldname') 
        world_desc = request.args.get('worlddesc') 
        world_url = request.args.get('worldurl') 
        world_img = request.args.get('worldimg')

        record = json.loads(request.data)
        with open(gamedata + "/data.json", 'w') as f:
            f.write(json.dumps(record, indent=4))
        # purge_db()
        i = init_world(gamedata + "/data.json", request.authorization['username'], world_name, world_desc, world_url, world_img)
        return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/world', methods=['GET'])
def get_world():
    if (is_authenticated(request.authorization, False)):
        with open(gamedata + "/data.json", 'r') as f:
            data = f.read()
            records = json.loads(data)
            return jsonify(records)
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['POST'])
def set_room(num):
    if (is_authenticated(request.authorization, True)):
        room = json.loads(request.data)
        update_one_in_db(f'UPDATE room SET room_name = \'{room["name"]}\', room_desc = \'{room["description"]}\', room_img = \'{room["image"]}\' where room_id = {num};')
        return jsonify({'success': f'room {room["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['GET'])
def get_room(num):
    if (is_authenticated(request.authorization, False)):
        room = fetch_one_from_db(f'SELECT * FROM room where room_id = {num};')
        return jsonify({'name': room[2],  'description': room[3],  'image': room[4]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['POST'])
def set_item(num):
    if (is_authenticated(request.authorization, True)):
        item = json.loads(request.data)
        update_one_in_db(f'UPDATE item SET item_name = \'{item["name"]}\', item_desc = \'{item["description"]}\', item_img = \'{item["image"]}\' where item_id = {num};')
        return jsonify({'success': f'item {item["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['GET'])
def get_item(num):
    if (is_authenticated(request.authorization, False)):
        item = fetch_one_from_db(f'SELECT * FROM item where item_id = {num};')
        return jsonify({'name': item[3],  'description': item[4],  'image': item[5]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['POST'])
def set_person(num):
    if (is_authenticated(request.authorization, True)):
        person = json.loads(request.data)
        update_one_in_db(f'UPDATE person SET person_name = \'{person["name"]}\', person_desc = \'{person["description"]}\', person_img = \'{person["image"]}\' where person_id = {num};')
        return jsonify({'success': f'person {person["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['GET'])
def get_person(num):
    if (is_authenticated(request.authorization, False)):
        person = fetch_one_from_db(f'SELECT * FROM person where person_id = {num};')
        return jsonify({'name': person[3],  'description': person[4],  'image': person[5]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['POST'])
def set_objective(num):
    if (is_authenticated(request.authorization, True)):
        objective = json.loads(request.data)
        update_one_in_db(f'UPDATE objective SET objective_name = \'{objective["name"]}\', objective_desc = \'{objective["description"]}\', difficulty = \'{objective["difficulty"]}\', objective_url = \'{objective["url"]}\', supported_by = \'{objective["supportedby"]}\', requires = \'{objective["requires"]}\', objective_img = \'{objective["image"]}\'  where objective_id = {num};')
        return jsonify({'success': f'objective {objective["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['GET'])
def get_objective(num):
    if (is_authenticated(request.authorization, False)):
        objective = fetch_one_from_db(f'SELECT * FROM objective where objective_id = {num};')
        return jsonify({'name': objective[3],  'description': objective[4],  'difficulty': objective[5],  'url': objective[6],  'supportedby': objective[7],  'requires': objective[8],  'image': objective[9]})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['POST'])
def set_junction(num):
    if (is_authenticated(request.authorization, True)):
        junction = json.loads(request.data)
        update_one_in_db(f'UPDATE junction SET dest_id = \'{junction["destination"]}\', junction_desc = \'{junction["description"]}\' where junction_id = {num};')
        return jsonify({'success': f'junction {junction["destination"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['GET'])
def get_junction(num):
    if (is_authenticated(request.authorization, False)):
        junction = fetch_one_from_db(f'SELECT * FROM junction where junction_id = {num};')
        return jsonify({'destination': junction[3],  'description': junction[4]})
    else:
        return jsonify({'error': 'wrong credentials'})
