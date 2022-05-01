import json                     # for JSON file handling and parsing
import os                       # for direct file system and environment access
import markdown2                # for markdown parsing
from flask import Flask, request, render_template, jsonify, send_file # most important Flask modules
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user # to manage user sessions
from flask_sqlalchemy import SQLAlchemy # object-relational mapper (ORM)
from werkzeug.security import generate_password_hash, check_password_hash # password hashing

gamedata = os.environ['HOME'] + "/.kringlecon"  # directory for game data
#POSTGRES_URL = get_env_variable("POSTGRES_URL")
#POSTGRES_USER = get_env_variable("POSTGRES_USER")
#POSTGRES_PW = get_env_variable("POSTGRES_PW")
#POSTGRES_DB = get_env_variable("POSTGRES_DB")
POSTGRES_URL = "kringle_database:5432"
POSTGRES_USER = "postgres"
POSTGRES_PW = "postgres"
POSTGRES_DB = "postgres"

app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')

# DB configuration
db = SQLAlchemy()
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER,pw=POSTGRES_PW,url=POSTGRES_URL,db=POSTGRES_DB)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the deprecation warning
db.init_app(app)

# Login Manager configuration
login_manager = LoginManager()
login_manager.login_view = 'get_login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(creator_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Creator.query.get(int(creator_id))

# ORM model classes
class Creator(UserMixin, db.Model):
    __tablename__ = "creator"
    creator_id = db.Column (db.INTEGER, primary_key=True)
    creator_name = db.Column (db.VARCHAR(100), unique=True)
    creator_pass = db.Column (db.VARCHAR(256))
    creator_role = db.Column (db.VARCHAR(10))
    creator_img = db.Column (db.VARCHAR(384))

    def get_id(self):
           return (self.creator_id)

class World(db.Model):
    __tablename__ = "world"
    world_id = db.Column (db.INTEGER, primary_key=True)
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    world_name = db.Column (db.VARCHAR(100), unique=True)
    world_desc = db.Column (db.VARCHAR(1024))
    world_url = db.Column (db.VARCHAR(256))
    world_img = db.Column (db.VARCHAR(384))

class Room(db.Model):
    __tablename__ = "room"
    room_id = db.Column (db.INTEGER, primary_key=True)
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    room_name = db.Column (db.VARCHAR(100))
    room_desc = db.Column (db.VARCHAR(1024))
    room_img = db.Column (db.VARCHAR(384))

class Item(db.Model):
    __tablename__ = "item"
    item_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    item_name = db.Column (db.VARCHAR(100))
    item_desc = db.Column (db.VARCHAR(1024))
    item_img = db.Column (db.VARCHAR(384))

class Objective(db.Model):
    __tablename__ = "objective"
    objective_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    objective_name = db.Column (db.VARCHAR(100))
    objective_desc = db.Column (db.VARCHAR(1024))
    difficulty = db.Column (db.INTEGER)
    objective_url = db.Column (db.VARCHAR(256))
    supported_by = db.Column (db.VARCHAR(100))
    requires = db.Column (db.VARCHAR(100))
    objective_img = db.Column (db.VARCHAR(384))
    quest = db.Column (db.LargeBinary)
    solution = db.Column (db.LargeBinary)

class Person(db.Model):
    __tablename__ = "person"
    person_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    person_name =  db.Column (db.VARCHAR(100))
    person_desc = db.Column (db.VARCHAR(1024))
    person_img = db.Column (db.VARCHAR(384))

class Junction(db.Model):
    __tablename__ = "junction"
    junction_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    dest_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    junction_desc = db.Column (db.VARCHAR(1024))

class Solution(db.Model):
    __tablename__ = "solution"
    solution_id = db.Column (db.INTEGER, primary_key=True)
    objective_id = db.Column (db.INTEGER, db.ForeignKey("objective.objective_id"))
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_text = db.Column (db.LargeBinary)

# initialize a completely new world using a world template suplied as JSON
def init_world(worldfile, creator_name, world_name, world_desc, world_url, world_img):
    counter_loaded = 0

    f = open(worldfile)
    data = json.load(f)

    # Connect to an existing database and ceate a cursor to perform database operations
    creator = Creator.query.filter_by(creator_name=creator_name).first()

    world = World()
    world.creator_id = creator.creator_id
    world.world_name = world_name
    world.world_desc = world_desc
    world.world_url = world_url
    world.world_img = world_img
    db.session.add(world)
    db.session.commit()
    counter_loaded = counter_loaded + 1

    world =  World.query.filter_by(world_name=world_name).first()

    # load all rooms before to enable foreign key relationship
    for i in data["rooms"]:
        room = Room()
        room.world_id = world.world_id
        room.room_name = i["name"]
        room.room_desc = i["description"]
        room.room_img = i["image"]
        db.session.add(room)
        db.session.commit()
        counter_loaded = counter_loaded + 1

    # load all other elements and check foreign key relationship
    for i in data["rooms"]:
        room_name = i["name"]
        room = Room.query.filter_by(room_name=room_name).filter_by(world_id=world.world_id).first()

        # load all items in the room
        if "items" in i:
            for j in i["items"]:
                item = Item()
                item.room_id = room.room_id
                item.world_id = world.world_id
                item.item_name = j["name"]
                item.item_desc = j["description"]
                item.item_img = j["image"]
                db.session.add(item)
                db.session.commit()
                counter_loaded = counter_loaded + 1
        
        # load all characters in the room
        if "characters" in i:
            for j in i["characters"]:
                person = Person()
                person.room_id = room.room_id
                person.world_id = world.world_id
                person.person_name = j["name"]
                person.person_desc = j["description"]
                person.person_img = j["image"]
                db.session.add(person)
                db.session.commit()
                counter_loaded = counter_loaded + 1
        
        # load all objectives in the room
        if "objectives" in i:
            for j in i["objectives"]:
                objective = Objective()
                objective.room_id = room.room_id
                objective.world_id = world.world_id
                objective.objective_name = j["name"]
                objective.objective_desc = j["description"]
                objective.difficulty = j["difficulty"]
                objective.objective_url = j["url"]
                objective.supported_by = j["supportedby"]
                objective.requires = j["requires"]
                objective.objective_img = j["image"]
                db.session.add(objective)
                db.session.commit()
                counter_loaded = counter_loaded + 1
        
        # load all junctions in the room
        if "junctions" in i:
            for j in i["junctions"]:
                junction = Junction()
                junction.room_id = room.room_id
                junction.world_id = world.world_id

                destroom = Room.query.filter_by(world_id=world.world_id).filter_by(room_name=j["destination"]).first()
                junction.dest_id = destroom.room_id
                junction.junction_desc = j["description"]
                db.session.add(junction)
                db.session.commit()
                counter_loaded = counter_loaded + 1
    
    f.close()
    return(counter_loaded)

# check if the basic authentication is valid
def is_authenticated(auth, admin):
    users = dict()
    if (admin):
        creators = Creator.query.filter_by(creator_role="admin").order_by(Creator.creator_id.asc())
    else:
        creators = Creator.query.order_by(Creator.creator_id.asc())
    for i in creators:
        users[i.creator_name] = i.creator_pass

    if auth:
        if auth['username'] in users and check_password_hash(users.get(auth['username']), auth['password']):
            return True
    return False

# entry pages
@app.route('/', methods = ['GET'])
def get_index():
    return render_template('index.html')

@app.route('/login', methods = ['GET'])
def get_login():
    return render_template('login.html')

@app.route('/login', methods = ['POST'])
def post_login():
    creator_name = request.form["creator"]
    creator_pass = request.form["password"]
    remember = True if request.form.get('remember') else False
    creator = Creator.query.filter_by(creator_name=creator_name).first()

    if not creator or not check_password_hash(creator.creator_pass, creator_pass):
        return render_template('login.html')
    login_user(creator, remember=remember)
    return render_template('index.html')

@app.route('/logout', methods = ['GET'])
@login_required
def get_logout():
    logout_user()
    return render_template('index.html')

# enable a HTML view to read the database contents
@app.route('/creators', methods = ['GET'])
def get_creators():
    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('creator.html', creators=creators)

@app.route('/creator/<int:num>', methods = ['GET'])
def get_creator(num):
    creator = Creator.query.filter_by(creator_id=num).first()
    return render_template('creator_detail.html', creator=creator)

@app.route('/newcreator', methods=['GET'])
def get_newcreator():
    return render_template('creator_new.html')

@app.route('/newcreator', methods=['POST'])
def post_newcreator():
    creator = Creator()
    creator.creator_name = request.form["creator"]
    creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)
    creator.creator_role = "user"
    db.session.add(creator)
    db.session.commit()

    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('creator.html', creators=creators)

@app.route('/worlds', methods = ['GET'])
def get_worlds():
    worlds = World.query.order_by(World.world_id.asc())
    return render_template('world.html', worlds=worlds)

@app.route('/world/<int:num>', methods = ['GET'])
def get_world(num):
    world = World.query.filter_by(world_id=num).first()
    return render_template('world_detail.html', world=world)

@app.route('/rooms/<int:num>', methods = ['GET'])
def get_rooms(num):
    rooms = Room.query.filter_by(world_id=num).order_by(Room.room_id.asc())
    return render_template('room.html', rooms=rooms, world_id=num)

@app.route('/room/<int:num>', methods = ['GET'])
def get_room(num):
    room = Room.query.filter_by(room_id=num).first()
    return render_template('room_detail.html', room=room)

@app.route('/items/<int:num>', methods = ['GET'])
def get_items(num):
    items = Item.query.filter_by(world_id=num).order_by(Item.item_id.asc())
    return render_template('item.html', items=items, world_id=num)

@app.route('/item/<int:num>', methods = ['GET'])
def get_item(num):
    item = Item.query.filter_by(item_id=num).first()
    return render_template('item_detail.html', item=item)

@app.route('/persons/<int:num>', methods = ['GET'])
def get_persons(num):
    persons = Person.query.filter_by(world_id=num).order_by(Person.person_id.asc())
    return render_template('person.html', persons=persons, world_id=num)

@app.route('/person/<int:num>', methods = ['GET'])
def get_person(num):
    person = Person.query.filter_by(person_id=num).first()
    return render_template('person_detail.html', person=person)

@app.route('/objectives/<int:num>', methods = ['GET'])
def get_objectives(num):
    objectives = Objective.query.filter_by(world_id=num).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=num)

@app.route('/objective/<int:num>', methods = ['GET'])
def get_objective(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    if (objective.quest != None):
        mdquest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdquest = ""
    if (objective.solution != None):
        mdsolution = markdown2.markdown(str(bytes(objective.solution), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdsolution = ""

    return render_template('objective_detail.html', objective=objective, mdquest=mdquest, mdsolution=mdsolution)

@app.route('/junctions/<int:num>', methods = ['GET'])
def get_junctions(num):
    junctions = Junction.query.filter_by(world_id=num).order_by(Junction.junction_id.asc())
    return render_template('junction.html', junctions=junctions, world_id=num)

@app.route('/junction/<int:num>', methods = ['GET'])
def get_junction(num):
    junction = Junction.query.filter_by(junction_id=num).first()
    return render_template('junction_detail.html', junction=junction)

@app.route('/quest/<int:num>', methods=['POST'])
@login_required
def post_quest(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    id = "quest"

    objective.quest = request.form[id].encode()
    db.session.commit()
    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/quest/<int:num>', methods=['GET'])
@login_required
def get_quest(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    if (objective.quest != None):
        return render_template('quest_detail.html', quest=str(bytes(objective.quest), 'utf-8'), number=num, world_id=objective.world_id)
    else:
        return render_template('quest_detail.html', quest="", number=num, world_id=objective.world_id)

@app.route('/solution/<int:num>', methods=['POST'])
@login_required
def post_solution(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    id = "solution"

    objective.solution = request.form[id].encode()
    db.session.commit()
    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/solution/<int:num>', methods=['GET'])
@login_required
def get_solution(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    if (objective.solution != None):
        return render_template('solution_detail.html', solution=str(bytes(objective.solution), 'utf-8'), number=num, world_id=objective.world_id)
    else:
        return render_template('solution_detail.html', solution="", number=num, world_id=objective.world_id)

@app.route('/mysolution/<int:num>', methods=['POST'])
@login_required
def post_mysolution(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    id = "solution"
    
    solution = Solution.query.filter_by(objective_id=num).filter_by(creator_id=current_user.creator_id).first()
    if solution is not None:
        db.session.delete(solution)
        db.session.commit()

    solution_new = Solution()
    solution_new.objective_id = num
    solution_new.creator_id = current_user.creator_id
    solution_new.solution_text = request.form[id].encode()
    db.session.add(solution_new)
    db.session.commit()

    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/mysolution/<int:num>', methods=['GET'])
@login_required
def get_mysolution(num):
    objective = Objective.query.filter_by(objective_id=num).first()

    solution = Solution.query.filter_by(objective_id=num).filter_by(creator_id=current_user.creator_id).first()
    if (solution != None):
        return render_template('solution_my_detail.html', solution=str(bytes(solution.solution_text), 'utf-8'), number=num, world_id=objective.world_id)
    else:
        return render_template('solution_my_detail.html', solution="", number=num, world_id=objective.world_id)

@app.route('/mywalkthrough/<int:num>', methods=['GET'])
@login_required
def get_mywalkthrough(num):
    objective = Objective.query.filter_by(objective_id=num).first()

    with open(gamedata + "/walkthrough.md", 'w') as f:
        f.write("Markdown")

    # return send_file(gamedata + "/walkthrough.md", attachment_filename='walkthrough.md',  as_attachment=True)
    return send_file(gamedata + "/walkthrough.md", attachment_filename='walkthrough.md')

# enable a REST API to modify the database contents
@app.route('/api/world', methods=['POST'])
def api_post_world():
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
def api_get_world():
    if (is_authenticated(request.authorization, False)):
        with open(gamedata + "/data.json", 'r') as f:
            data = f.read()
            records = json.loads(data)
            return jsonify(records)
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['POST'])
def api_post_room(num):
    if (is_authenticated(request.authorization, True)):
        data = json.loads(request.data)
        room = Room.query.filter_by(room_id=num).first()
        room.room_name = data["name"]
        room.room_desc = data["description"]
        room.room_img = data["image"]
        db.session.commit()
        return jsonify({'success': f'room {data["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['GET'])
def api_get_room(num):
    if (is_authenticated(request.authorization, False)):
        room = Room.query.filter_by(room_id=num).first()
        return jsonify({'name': room.room_name,  'description': room.room_desc,  'image': room.room_img})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['POST'])
def api_post_item(num):
    if (is_authenticated(request.authorization, True)):
        data = json.loads(request.data)
        item = Item.query.filter_by(item_id=num).first()
        item.item_name = data["name"]
        item.item_desc = data["description"]
        item.item_img = data["image"]
        db.session.commit()
        return jsonify({'success': f'item {data["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['GET'])
def api_get_item(num):
    if (is_authenticated(request.authorization, False)):
        item = Item.query.filter_by(item_id=num).first()
        return jsonify({'name': item.item_name,  'description': item.item_desc,  'image': item.item_img})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['POST'])
def api_post_person(num):
    if (is_authenticated(request.authorization, True)):
        data = json.loads(request.data)
        person = Person.query.filter_by(person_id=num).first()
        person.person_name = data["name"]
        person.person_desc = data["description"]
        person.person_img = data["image"]
        db.session.commit()
        return jsonify({'success': f'person {data["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['GET'])
def api_get_person(num):
    if (is_authenticated(request.authorization, False)):
        person = Person.query.filter_by(person_id=num).first()
        return jsonify({'name': person.person_name,  'description': person.person_desc,  'image': person.person_img})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['POST'])
def api_post_objective(num):
    if (is_authenticated(request.authorization, True)):
        data = json.loads(request.data)
        objective = Objective.query.filter_by(objective_id=num).first()
        objective.objective_name = data["name"]
        objective.objective_desc = data["description"]
        objective.difficulty = data["difficulty"]
        objective.objective_url = data["url"]
        objective.supported_by = data["supportedby"]
        objective.requires = data["requires"]
        objective.objective_img = data["image"]
        db.session.commit()
        return jsonify({'success': f'objective {data["name"]} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['GET'])
def api_get_objective(num):
    if (is_authenticated(request.authorization, False)):
        objective = Objective.query.filter_by(objective_id=num).first()
        return jsonify({'name': objective.objective_name,  'description': objective.objective_desc,  'difficulty': objective.difficulty,  'url': objective.objective_url,  'supportedby': objective.supported_by,  'requires': objective.requires,  'image': objective.objective_img})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['POST'])
def api_post_junction(num):
    if (is_authenticated(request.authorization, True)):
        data = json.loads(request.data)
        junction = Junction.query.filter_by(junction_id=num).first()
        junction.dest_id = data["destination"]
        junction.junction_desc = data["description"]
        db.session.commit()
        return jsonify({'success': f'junction {num} updated'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['GET'])
def api_get_junction(num):
    if (is_authenticated(request.authorization, False)):
        junction = Junction.query.filter_by(junction_id=num).first()
        return jsonify({'destination': junction.dest_id,  'description': junction.junction_desc})
    else:
        return jsonify({'error': 'wrong credentials'})
