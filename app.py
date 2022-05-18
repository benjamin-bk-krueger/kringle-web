import json                     # for JSON file handling and parsing
import os                       # for direct file system and environment access
import markdown2                # for markdown parsing
import boto3                    # for S3 storage, see https://stackabuse.com/file-management-with-aws-s3-python-and-flask/
from flask import Flask, request, render_template, jsonify, send_file # most important Flask modules
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user # to manage user sessions
from flask_sqlalchemy import SQLAlchemy # object-relational mapper (ORM)
from flask_sitemap import Sitemap # sitemap.xml
from werkzeug.security import generate_password_hash, check_password_hash # password hashing
from werkzeug.utils import secure_filename

GAME_DATA = os.environ['HOME'] + "/.kringlecon"     # directory for game data
POSTGRES_URL = os.environ['POSTGRES_URL']           # DB connection data
POSTGRES_USER = os.environ['POSTGRES_USER'] 
POSTGRES_PW = os.environ['POSTGRES_PW'] 
POSTGRES_DB = os.environ['POSTGRES_DB'] 
SECRET_KEY = os.environ['SECRET_KEY']
S3_ENDPOINT = os.environ['S3_ENDPOINT']
UPLOAD_FOLDER = os.environ['HOME'] + "/uploads"
DOWNLOAD_FOLDER = os.environ['HOME'] + "/downloads"
BUCKET_PUBLIC = os.environ['BUCKET_PUBLIC']
BUCKET_PRIVATE = os.environ['BUCKET_PRIVATE']

# Flask app configuration containing static (css, img) path and template directory
app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')

# sitemap.xml configuration
ext = Sitemap(app=app)

# DB configuration
db = SQLAlchemy()
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER,pw=POSTGRES_PW,url=POSTGRES_URL,db=POSTGRES_DB)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the deprecation warning
db.init_app(app)

# Login Manager configuration
# See https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login#step-2-creating-the-main-app-file
# See https://www.educba.com/flask-authentication/?source=leftnav
login_manager = LoginManager()
login_manager.login_view = 'get_login' # show this page if a login is required
login_manager.init_app(app)

@login_manager.user_loader
def load_user(creator_id):
    # since the creator_id is just the primary key of our user table, use it in the query for the user
    return Creator.query.get(int(creator_id))

# ORM model classes, Creator table is used for the Login Manager
class Creator(UserMixin, db.Model):
    __tablename__ = "creator"
    creator_id = db.Column (db.INTEGER, primary_key=True)
    creator_name = db.Column (db.VARCHAR(100), unique=True)
    creator_mail = db.Column (db.VARCHAR(100), unique=True)
    creator_pass = db.Column (db.VARCHAR(256))
    creator_img = db.Column (db.VARCHAR(384))
    creator_role = db.Column (db.VARCHAR(20))

    # match the correct row for the Login Manager ID
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
    visible = db.Column (db.INTEGER)

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
    visible = db.Column (db.INTEGER)

class Invitation(db.Model):
    __tablename__ = "invitation"
    invitation_id = db.Column (db.INTEGER, primary_key=True)
    invitation_code = db.Column (db.VARCHAR(20))
    invitation_role = db.Column (db.VARCHAR(20))
    invitation_forever = db.Column (db.INTEGER)
    invitation_taken = db.Column (db.INTEGER)

class Voting(db.Model):
    __tablename__ = "voting"
    voting_id = db.Column (db.INTEGER, primary_key=True)
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_id = db.Column (db.INTEGER, db.ForeignKey("solution.solution_id"))
    rating = db.Column (db.INTEGER)

# S3 helper functions
def upload_file(creator_name, file_name, bucket, object_name):
    s3_client = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    response = s3_client.upload_file(file_name, bucket, creator_name + "/" + object_name)

    return response

def download_file(creator_name, file_name, bucket):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    output = f"{DOWNLOAD_FOLDER}/{file_name}"
    s3.Bucket(bucket).download_file(creator_name + "/" + file_name, output)

    return output

def delete_file(creator_name, file_name, bucket):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    s3.Object(bucket, creator_name + "/" + file_name).delete()

def list_files(creator_name, bucket):
    s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    contents = []
    for item in s3.list_objects(Bucket=bucket)['Contents']:
        if (item['Key'].startswith(creator_name)):
            contents.append(item)

    return contents

# initialize a completely new world using a world template suplied as JSON
def init_world(worldfile, creator_name, world_name, world_desc, world_url, world_img):
    counter_loaded = 0 # count each single element

    f = open(worldfile)
    data = json.load(f)

    # each world is linked to it's creator
    creator = Creator.query.filter_by(creator_name=creator_name).first()

    # create a new ORM object for each ORM type and feed the JSON values into it
    world = World()
    world.creator_id = creator.creator_id
    world.world_name = world_name
    world.world_desc = world_desc
    world.world_url = world_url
    world.world_img = world_img
    db.session.add(world)
    db.session.commit()
    counter_loaded = counter_loaded + 1

    # each world element is linked to it's world
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

# check if the basic authentication is valid, used for API calls
def is_authenticated(auth):
    creator_name = auth['username']
    creator_pass = auth['password']
    creator = Creator.query.filter_by(creator_name=creator_name).first()

    if not creator or not check_password_hash(creator.creator_pass, creator_pass):
        return -1
    else:
        return creator.creator_id

# Sitemap page
@ext.register_generator
def index():
    # Not needed if you set SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS=True
    yield 'get_index', {}
    yield 'get_creators', {}
    yield 'get_worlds', {}

# Flask entry pages
@app.route('/web/', methods = ['GET'])
def get_index():
    return render_template('index.html')

@app.route('/web/logged', methods = ['GET'])
@login_required
def get_logged():
    return render_template('index.html')

@app.route('/web/login', methods = ['GET'])
def get_login():
    return render_template('login.html')

@app.route('/web/login', methods = ['POST'])
def post_login():
    creator_name = request.form["creator"]
    creator_pass = request.form["password"]
    remember = True if request.form.get('remember') else False
    creator = Creator.query.filter_by(creator_name=creator_name).first()

    if not creator or not check_password_hash(creator.creator_pass, creator_pass):
        return render_template('login.html')
    else:
        login_user(creator, remember=remember)
        return render_template('index.html')

@app.route('/web/logout', methods = ['GET'])
@login_required
def get_logout():
    logout_user()
    return render_template('index.html')

# S3 storage pages
@app.route("/web/storage", methods=['GET'])
@login_required
def get_storage():
    contents = list_files(current_user.creator_name, BUCKET_PUBLIC)
    return render_template('storage.html', contents=contents)

@app.route("/web/upload", methods=['POST'])
@login_required
def post_upload():
    f = request.files['file']
    f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
    upload_file(current_user.creator_name, f"{UPLOAD_FOLDER}/{f.filename}", BUCKET_PUBLIC, f.filename)

    contents = list_files(current_user.creator_name, BUCKET_PUBLIC)
    return render_template('storage.html', contents=contents)

@app.route("/web/download/<creator_name>/<filename>", methods=['GET'])
@login_required
def get_download(creator_name, filename):
    output = download_file(creator_name, secure_filename(filename), BUCKET_PUBLIC)

    return send_file(output, as_attachment=True)

@app.route("/web/delete/<creator_name>/<filename>", methods=['GET'])
@login_required
def get_delete(creator_name, filename):
    delete_file(creator_name, filename, BUCKET_PUBLIC)

    contents = list_files(current_user.creator_name, BUCKET_PUBLIC)
    return render_template('storage.html', contents=contents)

# Flask HTML views to read and modify the database contents
@app.route('/web/stats', methods = ['GET'])
def get_stats():
    creatorcount = Creator.query.count()
    worldcount = World.query.count()
    roomcount = Room.query.count()
    itemcount = Item.query.count()
    personcount = Person.query.count()
    objectivecount = Objective.query.count()
    junctioncount = Junction.query.count()

    return render_template('stats.html', creatorcount=creatorcount, worldcount=worldcount, roomcount=roomcount, itemcount=itemcount, personcount=personcount, objectivecount=objectivecount, junctioncount=junctioncount)

@app.route('/web/creators', methods = ['GET'])
def get_creators():
    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('creator.html', creators=creators)

@app.route('/web/creator/<int:num>', methods = ['GET'])
def get_creator(num):
    creator = Creator.query.filter_by(creator_id=num).first()
    return render_template('creator_detail.html', creator=creator)

@app.route('/web/newcreator', methods = ['GET'])
def get_newcreator():
    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('account.html', creators=creators)

@app.route('/web/newcreator', methods=['POST'])
def post_newcreator():
    code = request.form["invitation"]
    invitation  = Invitation.query.filter_by(invitation_code=code).first()

    if (invitation):
        if (invitation.invitation_forever == 1 or invitation.invitation_taken == 0):
            creator = Creator()
            creator.creator_name = request.form["creator"]
            creator.creator_mail = request.form["mail"]
            creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)
            creator.creator_role = invitation.invitation_role
            creator.creator_img = ""
            db.session.add(creator)
            db.session.commit()

            invitation.invitation_taken = 1
            db.session.commit()

    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('creator.html', creators=creators)

@app.route('/web/mycreator', methods = ['GET'])
@login_required
def get_mycreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('account_detail.html', creator=creator, creators=creators)

@app.route('/web/mailcreator', methods=['POST'])
@login_required
def post_mailcreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    creators = Creator.query.order_by(Creator.creator_id.asc())
    creator.creator_mail = request.form["mail"]
    creator.creator_img = request.form["image"]
    db.session.commit()

    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('account_detail.html', creator=creator, creators=creators)

@app.route('/web/passcreator', methods=['POST'])
@login_required
def post_passcreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    creators = Creator.query.order_by(Creator.creator_id.asc())
    creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)
    db.session.commit()

    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('account_detail.html', creator=creator, creators=creators)

@app.route('/web/delcreator', methods=['POST'])
@login_required
def post_delcreator():
    confirmation = request.form["confirm"]
    if (confirmation == "delete"):
        Creator.query.filter_by(creator_id=current_user.creator_id).delete()
        db.session.commit()
        logout_user()
    return render_template('index.html')

@app.route('/web/worlds', methods = ['GET'])
def get_worlds():
    worlds = World.query.order_by(World.world_id.asc())
    return render_template('world.html', worlds=worlds)

@app.route('/web/world/<int:num>', methods = ['GET'])
def get_world(num):
    world = World.query.filter_by(world_id=num).first()
    return render_template('world_detail.html', world=world)

@app.route('/web/delworld/<int:num>', methods=['GET'])
@login_required
def get_delworld(num):
    World.query.filter_by(world_id=num).filter_by(creator_id=current_user.creator_id).delete()
    db.session.commit()

    worlds = World.query.order_by(World.world_id.asc())
    return render_template('world.html', worlds=worlds)

@app.route('/web/switchworld/<int:num>', methods=['GET'])
@login_required
def get_switchworld(num):
    world = World.query.filter_by(world_id=num).filter_by(creator_id=current_user.creator_id).first()
    if (world):
        if (world.visible == 0):
            world.visible = 1
        else:
            world.visible = 0
        db.session.commit()

    worlds = World.query.order_by(World.world_id.asc())
    return render_template('world.html', worlds=worlds)

@app.route('/web/rooms/<int:num>', methods = ['GET'])
def get_rooms(num):
    rooms = Room.query.filter_by(world_id=num).order_by(Room.room_id.asc())
    return render_template('room.html', rooms=rooms, world_id=num)

@app.route('/web/room/<int:num>', methods = ['GET'])
def get_room(num):
    room = Room.query.filter_by(room_id=num).first()
    return render_template('room_detail.html', room=room)

@app.route('/web/items/<int:num>', methods = ['GET'])
def get_items(num):
    items = Item.query.filter_by(world_id=num).order_by(Item.item_id.asc())
    return render_template('item.html', items=items, world_id=num)

@app.route('/web/item/<int:num>', methods = ['GET'])
def get_item(num):
    item = Item.query.filter_by(item_id=num).first()
    return render_template('item_detail.html', item=item)

@app.route('/web/persons/<int:num>', methods = ['GET'])
def get_persons(num):
    persons = Person.query.filter_by(world_id=num).order_by(Person.person_id.asc())
    return render_template('person.html', persons=persons, world_id=num)

@app.route('/web/person/<int:num>', methods = ['GET'])
def get_person(num):
    person = Person.query.filter_by(person_id=num).first()
    return render_template('person_detail.html', person=person)

@app.route('/web/objectives/<int:num>', methods = ['GET'])
def get_objectives(num):
    objectives = Objective.query.filter_by(world_id=num).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=num)

@app.route('/web/objective/<int:num>', methods = ['GET'])
def get_objective(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    solutions = Solution.query.filter_by(objective_id=num).filter_by(visible=1).order_by(Solution.solution_id.asc())
    world = World.query.filter_by(world_id=objective.world_id).first()
    
    votingall = dict()
    creatorall = dict()
    for solution in solutions:
        votingcount = Voting.query.filter_by(solution_id=solution.solution_id).filter_by(rating=1).count()
        creatorname = Creator.query.filter_by(creator_id=solution.creator_id).first().creator_name
        votingall[solution.solution_id]=votingcount
        creatorall[solution.solution_id]=creatorname


    if (objective.quest != None):
        mdquest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdquest = ""

    return render_template('objective_detail.html', objective=objective, mdquest=mdquest, solutions=solutions, world=world, votingall=votingall, creatorall=creatorall)

@app.route('/web/junctions/<int:num>', methods = ['GET'])
def get_junctions(num):
    junctions = Junction.query.filter_by(world_id=num).order_by(Junction.junction_id.asc())
    return render_template('junction.html', junctions=junctions, world_id=num)

@app.route('/web/junction/<int:num>', methods = ['GET'])
def get_junction(num):
    junction = Junction.query.filter_by(junction_id=num).first()
    return render_template('junction_detail.html', junction=junction)

@app.route('/web/quest/<int:num>', methods=['POST'])
@login_required
def post_quest(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    room = Room.query.filter_by(room_id=objective.room_id).first()
    world = World.query.filter_by(world_id=room.world_id).first()
    id = "quest"

    if (world.creator_id == current_user.creator_id):
        objective.quest = request.form[id].encode()
        db.session.commit()
    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/web/quest/<int:num>', methods=['GET'])
@login_required
def get_quest(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    room = Room.query.filter_by(room_id=objective.room_id).first()
    world = World.query.filter_by(world_id=room.world_id).first()

    if (world.creator_id == current_user.creator_id):
        if (objective.quest != None):
            return render_template('quest_detail.html', quest=str(bytes(objective.quest), 'utf-8'), number=num, world_id=objective.world_id)
        else:
            return render_template('quest_detail.html', quest="", number=num, world_id=objective.world_id)
    else:
        objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
        return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/web/solution/<int:num>', methods=['GET'])
@login_required
def get_solution(num):
    solution = Solution.query.filter_by(solution_id=num).first()
    objective = Objective.query.filter_by(objective_id=solution.objective_id).first()
    world = World.query.filter_by(world_id=objective.world_id).first()

    if (solution.visible == 1 and world.visible == 1):
        if (solution.solution_text != None):
            mdsolution = markdown2.markdown(str(bytes(solution.solution_text), 'utf-8'), extras=['fenced-code-blocks'])

            return render_template('solution_detail.html', mdsolution=mdsolution, number=num, world_id=objective.world_id)
        else:
            return render_template('solution_detail.html', mdsolution="", number=num, world_id=objective.world_id)
    else:
        objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
        return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/web/likesolution/<int:num>', methods=['GET'])
@login_required
def get_likesolution(num):
    voting = Voting.query.filter_by(solution_id=num).filter_by(creator_id=current_user.creator_id).first()
    solution = Solution.query.filter_by(solution_id=num).first()
    objective = Objective.query.filter_by(objective_id=solution.objective_id).first()
    if (voting):
        if (voting.rating == 0):
            voting.rating = 1
        else:
            voting.rating = 0
        db.session.commit()
    else:
        voting = Voting()
        voting.creator_id = current_user.creator_id
        voting.solution_id = num
        voting.rating = 1
        db.session.add(voting)
        db.session.commit()

    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/web/mysolution/<int:num>', methods=['POST'])
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
    if ('visible' in request.form):
        solution_new.visible = 1
    db.session.add(solution_new)
    db.session.commit()

    objectives = Objective.query.filter_by(world_id=objective.world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=objective.world_id)

@app.route('/web/mysolution/<int:num>', methods=['GET'])
@login_required
def get_mysolution(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    if (objective.quest != None):
        mdquest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
    else:
        mdquest = ""

    solution = Solution.query.filter_by(objective_id=num).filter_by(creator_id=current_user.creator_id).first()
    if (solution != None):
        return render_template('solution_my_detail.html', solution=str(bytes(solution.solution_text), 'utf-8'), visible=solution.visible, mdquest=mdquest, number=num, world_id=objective.world_id)
    else:
        return render_template('solution_my_detail.html', solution="", visible=0, mdquest=mdquest, number=num, world_id=objective.world_id)

@app.route('/web/mywalkthrough/<int:num>', methods=['GET'])
@login_required
def get_mywalkthrough(num):
    # objective = Objective.query.filter_by(objective_id=num).first()

    with open(GAME_DATA + "/walkthrough.md", 'w') as f:
        f.write("Markdown")

    # return send_file(GAME_DATA + "/walkthrough.md", attachment_filename='walkthrough.md',  as_attachment=True)
    return send_file(GAME_DATA + "/walkthrough.md", attachment_filename='walkthrough.md')

# enable a REST API to modify the database contents
@app.route('/api/world/<worldname>', methods=['POST'])
def api_post_world(worldname):
    if (is_authenticated(request.authorization)):
        creator = Creator.query.filter_by(creator_name=request.authorization['username']).first()
        if (creator.creator_role == 'creator'):
            world_desc = request.args.get('worlddesc') 
            world_url = request.args.get('worldurl') 
            world_img = request.args.get('worldimg')

            record = json.loads(request.data)
            with open(GAME_DATA + "/data.json", 'w') as f:
                f.write(json.dumps(record, indent=4))
            # purge_db()
            upload_file("world", GAME_DATA + "/data.json", BUCKET_PRIVATE, worldname + ".world")
            i = init_world(GAME_DATA + "/data.json", request.authorization['username'], worldname, world_desc, world_url, world_img)
            return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
        else:
            return jsonify({'error': 'insufficient permissions'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/world/<worldname>', methods=['GET'])
def api_get_world(worldname):
    output = download_file("world", secure_filename(worldname) + ".world", BUCKET_PRIVATE)
    return send_file(output)

@app.route('/api/room/<int:num>', methods=['POST'])
def api_post_room(num):
    creator_id = is_authenticated(request.authorization)
    if (creator_id > 0):
        data = json.loads(request.data)
        room = Room.query.filter_by(room_id=num).first()
        world = World.query.filter_by(world_id=room.world_id).first()
        if (creator_id == world.creator_id):
            room.room_name = data["name"]
            room.room_desc = data["description"]
            room.room_img = data["image"]
            db.session.commit()
            return jsonify({'success': f'room {data["name"]} updated'})
        else:
            return jsonify({'error': 'not authorized for object'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/room/<int:num>', methods=['GET'])
def api_get_room(num):
    room = Room.query.filter_by(room_id=num).first()
    return jsonify({'name': room.room_name,  'description': room.room_desc,  'image': room.room_img})

@app.route('/api/item/<int:num>', methods=['POST'])
def api_post_item(num):
    creator_id = is_authenticated(request.authorization)
    if (creator_id > 0):
        data = json.loads(request.data)
        item = Item.query.filter_by(item_id=num).first()
        room = Room.query.filter_by(room_id=item.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()
        if (creator_id == world.creator_id):
            item.item_name = data["name"]
            item.item_desc = data["description"]
            item.item_img = data["image"]
            db.session.commit()
            return jsonify({'success': f'item {data["name"]} updated'})
        else:
            return jsonify({'error': 'not authorized for object'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/item/<int:num>', methods=['GET'])
def api_get_item(num):
    item = Item.query.filter_by(item_id=num).first()
    return jsonify({'name': item.item_name,  'description': item.item_desc,  'image': item.item_img})

@app.route('/api/person/<int:num>', methods=['POST'])
def api_post_person(num):
    creator_id = is_authenticated(request.authorization)
    if (creator_id > 0):
        data = json.loads(request.data)
        person = Person.query.filter_by(person_id=num).first()
        room = Room.query.filter_by(room_id=person.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()
        if (creator_id == world.creator_id):
            person.person_name = data["name"]
            person.person_desc = data["description"]
            person.person_img = data["image"]
            db.session.commit()
            return jsonify({'success': f'person {data["name"]} updated'})
        else:
            return jsonify({'error': 'not authorized for object'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/person/<int:num>', methods=['GET'])
def api_get_person(num):
    person = Person.query.filter_by(person_id=num).first()
    return jsonify({'name': person.person_name,  'description': person.person_desc,  'image': person.person_img})

@app.route('/api/objective/<int:num>', methods=['POST'])
def api_post_objective(num):
    creator_id = is_authenticated(request.authorization)
    if (creator_id > 0):
        data = json.loads(request.data)
        objective = Objective.query.filter_by(objective_id=num).first()
        room = Room.query.filter_by(room_id=objective.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()
        if (creator_id == world.creator_id):
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
            return jsonify({'error': 'not authorized for object'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/objective/<int:num>', methods=['GET'])
def api_get_objective(num):
    objective = Objective.query.filter_by(objective_id=num).first()
    return jsonify({'name': objective.objective_name,  'description': objective.objective_desc,  'difficulty': objective.difficulty,  'url': objective.objective_url,  'supportedby': objective.supported_by,  'requires': objective.requires,  'image': objective.objective_img})

@app.route('/api/junction/<int:num>', methods=['POST'])
def api_post_junction(num):
    creator_id = is_authenticated(request.authorization)
    if (creator_id > 0):
        data = json.loads(request.data)
        junction = Junction.query.filter_by(junction_id=num).first()
        room = Room.query.filter_by(room_id=junction.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()
        if (creator_id == world.creator_id):
            junction.dest_id = data["destination"]
            junction.junction_desc = data["description"]
            db.session.commit()
            return jsonify({'success': f'junction {num} updated'})
        else:
            return jsonify({'error': 'not authorized for object'})
    else:
        return jsonify({'error': 'wrong credentials'})

@app.route('/api/junction/<int:num>', methods=['GET'])
def api_get_junction(num):
    junction = Junction.query.filter_by(junction_id=num).first()
    return jsonify({'destination': junction.dest_id,  'description': junction.junction_desc})
