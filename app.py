import json                     # for JSON file handling and parsing
import os                       # for direct file system and environment access
import markdown2                # for markdown parsing
import re                       # for regular expressions
import boto3                    # for S3 storage, see https://stackabuse.com/file-management-with-aws-s3-python-and-flask/
from flask import Flask, request, render_template, jsonify, send_file, escape, redirect, url_for # most important Flask modules
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user # to manage user sessions
from flask_sqlalchemy import SQLAlchemy # object-relational mapper (ORM)
from flask_sitemap import Sitemap # to generate sitemap.xml
from flask_restx import Resource, Api # to enable the REST API, see https://rahmanfadhil.com/flask-rest-api/
from flask_marshmallow import Marshmallow  # to marshall our objects
from werkzeug.security import generate_password_hash, check_password_hash # for password hashing
from werkzeug.utils import secure_filename # to prevent path traversal attacks

# the app configuration is done via environmental variables
POSTGRES_URL        = os.environ['POSTGRES_URL']           # DB connection data
POSTGRES_USER       = os.environ['POSTGRES_USER'] 
POSTGRES_PW         = os.environ['POSTGRES_PW'] 
POSTGRES_DB         = os.environ['POSTGRES_DB'] 
SECRET_KEY          = os.environ['SECRET_KEY']
S3_ENDPOINT         = os.environ['S3_ENDPOINT']             # where S3 buckets are located
BUCKET_PUBLIC       = os.environ['BUCKET_PUBLIC']
BUCKET_PRIVATE      = os.environ['BUCKET_PRIVATE']
UPLOAD_FOLDER       = os.environ['HOME'] + "/uploads"       # directory for game data
DOWNLOAD_FOLDER     = os.environ['HOME'] + "/downloads"
ALLOWED_EXTENSIONS  = {'png', 'jpg', 'jpeg', 'gif'}

# Flask app configuration containing static (css, img) path and template directory
app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')

# Limit file uploads to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# sitemap.xml configuration
ext = Sitemap(app=app)

# REST API configuration
api = Api(app)

# Marshall configuration
marsh = Marshmallow(app)

# DB configuration
db = SQLAlchemy()
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER,pw=POSTGRES_PW,url=POSTGRES_URL,db=POSTGRES_DB)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the deprecation warning
db.init_app(app)

# Login Manager configuration
# See https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login#step-2-creating-the-main-app-file
login_manager = LoginManager()
login_manager.login_view = 'get_login' # show this page if a login is required
login_manager.init_app(app)

@login_manager.user_loader
def load_user(creator_id):
    # since the creator_id is just the primary key of our user table, use it in the query for the user
    return Creator.query.get(int(creator_id))

# ORM model classes, Creator table is used for the Login Manager
# for each REST-enabled element, we add marshmallow schemas
# enable a REST API to modify the database contents
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
    
    def __repr__(self):
        return '<Creator %s>' % self.creator_name

class World(db.Model):
    __tablename__ = "world"
    world_id = db.Column (db.INTEGER, primary_key=True)
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    world_name = db.Column (db.VARCHAR(100), unique=True)
    world_desc = db.Column (db.VARCHAR(1024))
    world_url = db.Column (db.VARCHAR(256))
    world_img = db.Column (db.VARCHAR(384))
    visible = db.Column (db.INTEGER)

    def __repr__(self):
        return '<World %s>' % self.world_name

class WorldSchema(marsh.Schema):
    class Meta:
        fields = ("world_id", "creator_id", "world_name", "world_desc", "world_img")
        model = World

world_schema = WorldSchema()
worlds_schema = WorldSchema(many=True)

class WorldListResource(Resource):
    def get(self):
        worlds = World.query.all()
        return worlds_schema.dump(worlds)

    def post(self):
        if all(s in request.json for s in ('world_name', 'world_desc', 'world_img')):
            creator = Creator.query.filter_by(creator_name=request.authorization['username']).first()
            if (creator.creator_role == 'creator'):
                new_world = World(
                    creator_id=creator.creator_id,
                    world_name=escape(request.json['world_name']),
                    world_desc=escape(request.json['world_desc']),
                    world_img=clean_url(request.json['world_img'])
                )
                db.session.add(new_world)
                db.session.commit()
                return world_schema.dump(new_world)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class WorldResource(Resource):
    def get(self, world_id):
        world = World.query.get_or_404(world_id)
        return world_schema.dump(world)

    def patch(self, world_id):
        world = World.query.get_or_404(world_id)
        if all(s in request.json for s in ('world_name', 'world_desc', 'world_img')):
            if (AuthChecker().check(request.authorization, world.world_id)):
                world.world_name = escape(request.json['world_name'])
                world.world_desc = escape(request.json['world_desc'])
                world.world_img = clean_url(request.json['world_img'])
                db.session.commit()
                return world_schema.dump(world)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, world_id):
        world = World.query.get_or_404(world_id)
        if (AuthChecker().check(request.authorization, world.world_id)):
            db.session.delete(world)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

class WorldFullListResource(Resource):
    def post(self):
        if (request.args.get('world_name') is not None and request.args.get('world_desc') is not None and request.args.get('world_url') is not None and request.args.get('world_img') is not None):
            creator = Creator.query.filter_by(creator_name=request.authorization['username']).first()
            if (creator.creator_role == 'creator'):
                world_name = escape(request.args.get('world_name'))
                world_desc = escape(request.args.get('world_desc'))
                world_url = clean_url(request.args.get('world_url'))
                world_img = escape(request.args.get('world_img'))

                record = json.loads(request.data)
                inputfile = f"{UPLOAD_FOLDER}/{secure_filename(world_name)}.world"
                objectfile = f"world/{secure_filename(world_name)}.world"
                with open(inputfile, 'w') as f:
                    f.write(json.dumps(record, indent=4))
                upload_file(BUCKET_PRIVATE, objectfile, inputfile)
                i = init_world(inputfile, request.authorization['username'], world_name, world_desc, world_url, world_img)
                return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class WorldFullResource(Resource):
    def get(self, worldname):
        outputfile = f"{DOWNLOAD_FOLDER}/{secure_filename(worldname)}.world"
        objectfile = f"world/{secure_filename(worldname)}.world"
        output = download_file(BUCKET_PRIVATE, objectfile, outputfile)
        if (output):
            return send_file(output)
        else:
            return jsonify({'error': 'element not found'})

api.add_resource(WorldListResource, '/api/worlds')
api.add_resource(WorldResource, '/api/worlds/<int:world_id>')
api.add_resource(WorldFullListResource, '/api/fullworlds')
api.add_resource(WorldFullResource, '/api/fullworlds/<string:worldname>')

class Room(db.Model):
    __tablename__ = "room"
    room_id = db.Column (db.INTEGER, primary_key=True)
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    room_name = db.Column (db.VARCHAR(100))
    room_desc = db.Column (db.VARCHAR(1024))
    room_img = db.Column (db.VARCHAR(384))

    def __repr__(self):
        return '<Room %s>' % self.room_name

class RoomSchema(marsh.Schema):
    class Meta:
        fields = ("room_id", "world_id", "room_name", "room_desc", "room_img")
        model = Room

room_schema = RoomSchema()
rooms_schema = RoomSchema(many=True)

class RoomListResource(Resource):
    def get(self):
        rooms = Room.query.all()
        return rooms_schema.dump(rooms)

    def post(self):
        if all(s in request.json for s in ('world_id', 'room_name', 'room_desc', 'room_img')):
            if (AuthChecker().check(request.authorization, request.json['world_id'])):
                new_room = Room(
                    world_id=escape(request.json['world_id']),
                    room_name=escape(request.json['room_name']),
                    room_desc=escape(request.json['room_desc']),
                    room_img=clean_url(request.json['room_img'])
                )
                db.session.add(new_room)
                db.session.commit()
                return room_schema.dump(new_room)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class RoomResource(Resource):
    def get(self, room_id):
        room = Room.query.get_or_404(room_id)
        return room_schema.dump(room)

    def patch(self, room_id):
        room = Room.query.get_or_404(room_id)
        if all(s in request.json for s in ('world_id', 'room_name', 'room_desc', 'room_img')):
            if (AuthChecker().check(request.authorization, room.world_id)):
                room.world_id = escape(request.json['world_id'])
                room.room_name = escape(request.json['room_name'])
                room.room_desc = escape(request.json['room_desc'])
                room.room_img = clean_url(request.json['room_img'])
                db.session.commit()
                return room_schema.dump(room)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, room_id):
        room = Room.query.get_or_404(room_id)
        if (AuthChecker().check(request.authorization, room.world_id)):
            db.session.delete(room)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

api.add_resource(RoomListResource, '/api/rooms')
api.add_resource(RoomResource, '/api/rooms/<int:room_id>')

class Item(db.Model):
    __tablename__ = "item"
    item_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    item_name = db.Column (db.VARCHAR(100))
    item_desc = db.Column (db.VARCHAR(1024))
    item_img = db.Column (db.VARCHAR(384))

    def __repr__(self):
        return '<Item %s>' % self.item_name

class ItemSchema(marsh.Schema):
    class Meta:
        fields = ("item_id", "room_id", "world_id", "item_name", "item_desc", "item_img")
        model = Item

item_schema = ItemSchema()
items_schema = ItemSchema(many=True)

class ItemListResource(Resource):
    def get(self):
        items = Item.query.all()
        return items_schema.dump(items)

    def post(self):
        if all(s in request.json for s in ('room_id', 'world_id', 'item_name', 'item_desc', 'item_img')):
            if (AuthChecker().check(request.authorization, request.json['world_id'])):
                new_item = Item(
                    room_id=escape(request.json['room_id']),
                    world_id=escape(request.json['world_id']),
                    item_name=escape(request.json['item_name']),
                    item_desc=escape(request.json['item_desc']),
                    item_img=clean_url(request.json['item_img'])
                )
                db.session.add(new_item)
                db.session.commit()
                return item_schema.dump(new_item)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class ItemResource(Resource):
    def get(self, item_id):
        item = Item.query.get_or_404(item_id)
        return item_schema.dump(item)

    def patch(self, item_id):
        item = Item.query.get_or_404(item_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'item_name', 'item_desc', 'item_img')):
            if (AuthChecker().check(request.authorization, item.world_id)):
                item.room_id = escape(request.json['room_id'])
                item.world_id = escape(request.json['world_id'])
                item.item_name = escape(request.json['item_name'])
                item.item_desc = escape(request.json['item_desc'])
                item.item_img = clean_url(request.json['item_img'])
                db.session.commit()
                return item_schema.dump(item)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, item_id):
        item = Item.query.get_or_404(item_id)
        if (AuthChecker().check(request.authorization, item.world_id)):
            db.session.delete(item)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

api.add_resource(ItemListResource, '/api/items')
api.add_resource(ItemResource, '/api/items/<int:item_id>')

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

    def __repr__(self):
        return '<Objective %s>' % self.objective_name

class ObjectiveSchema(marsh.Schema):
    class Meta:
        fields = ("objective_id", "room_id", "world_id", "objective_name", "objective_desc", "difficulty", "objective_url", "supported_by", "requires", "objective_img")
        model = Objective

objective_schema = ObjectiveSchema()
objectives_schema = ObjectiveSchema(many=True)

class ObjectiveListResource(Resource):
    def get(self):
        objectives = Objective.query.all()
        return objectives_schema.dump(objectives)

    def post(self):
        if all(s in request.json for s in ('room_id', 'world_id', 'objective_name', 'objective_desc', 'difficulty', 'objective_url', 'supported_by', 'requires', 'objective_img')):
            if (AuthChecker().check(request.authorization, request.json['world_id'])):
                new_objective = Objective(
                    room_id=escape(request.json['room_id']),
                    world_id=escape(request.json['world_id']),
                    objective_name=escape(request.json['objective_name']),
                    objective_desc=escape(request.json['objective_desc']),
                    difficulty=escape(request.json['difficulty']),
                    objective_url=clean_url(request.json['objective_url']),
                    supported_by=escape(request.json['supported_by']),
                    requires=escape(request.json['requires']),
                    objective_img=clean_url(request.json['objective_img'])
                )
                db.session.add(new_objective)
                db.session.commit()
                return objective_schema.dump(new_objective)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class ObjectiveResource(Resource):
    def get(self, objective_id):
        objective = Objective.query.get_or_404(objective_id)
        return objective_schema.dump(objective)

    def patch(self, objective_id):
        objective = Objective.query.get_or_404(objective_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'objective_name', 'objective_desc', 'difficulty', 'objective_url', 'supported_by', 'requires', 'objective_img')):
            if (AuthChecker().check(request.authorization, objective.world_id)):
                objective.room_id=escape(request.json['room_id']),
                objective.world_id=escape(request.json['world_id']),
                objective.objective_name=escape(request.json['objective_name']),
                objective.objective_desc=escape(request.json['objective_desc']),
                objective.difficulty=escape(request.json['difficulty']),
                objective.objective_url=clean_url(request.json['objective_url']),
                objective.supported_by=escape(request.json['supported_by']),
                objective.requires=escape(request.json['requires']),
                objective.objective_img=clean_url(request.json['objective_img'])
                db.session.commit()
                return objective_schema.dump(objective)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, objective_id):
        objective = Objective.query.get_or_404(objective_id)
        if (AuthChecker().check(request.authorization, objective.world_id)):
            db.session.delete(objective)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

api.add_resource(ObjectiveListResource, '/api/objectives')
api.add_resource(ObjectiveResource, '/api/objectives/<int:objective_id>')

class Person(db.Model):
    __tablename__ = "person"
    person_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    person_name =  db.Column (db.VARCHAR(100))
    person_desc = db.Column (db.VARCHAR(1024))
    person_img = db.Column (db.VARCHAR(384))

    def __repr__(self):
        return '<Person %s>' % self.person_name

class PersonSchema(marsh.Schema):
    class Meta:
        fields = ("person_id", "room_id", "world_id", "person_name", "person_desc", "person_img")
        model = Person

person_schema = PersonSchema()
persons_schema = PersonSchema(many=True)

class PersonListResource(Resource):
    def get(self):
        persons = Person.query.all()
        return persons_schema.dump(persons)

    def post(self):
        if all(s in request.json for s in ('room_id', 'world_id', 'person_name', 'person_desc', 'person_img')):
            if (AuthChecker().check(request.authorization, request.json['world_id'])):
                new_person = Person(
                    room_id=escape(request.json['room_id']),
                    world_id=escape(request.json['world_id']),
                    person_name=escape(request.json['person_name']),
                    person_desc=escape(request.json['person_desc']),
                    person_img=clean_url(request.json['person_img'])
                )
                db.session.add(new_person)
                db.session.commit()
                return person_schema.dump(new_person)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class PersonResource(Resource):
    def get(self, person_id):
        person = Person.query.get_or_404(person_id)
        return person_schema.dump(person)

    def patch(self, person_id):
        person = Person.query.get_or_404(person_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'person_name', 'person_desc', 'person_img')):
            if (AuthChecker().check(request.authorization, person.world_id)):
                person.room_id = escape(request.json['room_id'])
                person.world_id = escape(request.json['world_id'])
                person.person_name = escape(request.json['person_name'])
                person.person_desc = escape(request.json['person_desc'])
                person.person_img = clean_url(request.json['person_img'])
                db.session.commit()
                return person_schema.dump(person)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, person_id):
        person = Person.query.get_or_404(person_id)
        if (AuthChecker().check(request.authorization, person.world_id)):
            db.session.delete(person)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

api.add_resource(PersonListResource, '/api/persons')
api.add_resource(PersonResource, '/api/persons/<int:person_id>')

class Junction(db.Model):
    __tablename__ = "junction"
    junction_id = db.Column (db.INTEGER, primary_key=True)
    room_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column (db.INTEGER, db.ForeignKey("world.world_id"))
    dest_id = db.Column (db.INTEGER, db.ForeignKey("room.room_id"))
    junction_desc = db.Column (db.VARCHAR(1024))

    def __repr__(self):
        return '<Junction %s>' % self.junction_id

class JunctionSchema(marsh.Schema):
    class Meta:
        fields = ("junction_id", "room_id", "world_id", "dest_id", "junction_desc")
        model = Junction

junction_schema = JunctionSchema()
junctions_schema = JunctionSchema(many=True)

class JunctionListResource(Resource):
    def get(self):
        junctions = Junction.query.all()
        return junctions_schema.dump(junctions)

    def post(self):
        if all(s in request.json for s in ('room_id', 'world_id', 'dest_id', 'junction_desc')):
            if (AuthChecker().check(request.authorization, request.json['world_id'])):
                new_junction = Junction(
                    room_id=escape(request.json['room_id']),
                    world_id=escape(request.json['world_id']),
                    dest_id=escape(request.json['dest_id']),
                    junction_desc=escape(request.json['junction_desc'])
                )
                db.session.add(new_junction)
                db.session.commit()
                return junction_schema.dump(new_junction)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

class JunctionResource(Resource):
    def get(self, junction_id):
        junction = Junction.query.get_or_404(junction_id)
        return junction_schema.dump(junction)

    def patch(self, junction_id):
        junction = Junction.query.get_or_404(junction_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'dest_id', 'junction_desc')):
            if (AuthChecker().check(request.authorization, junction.world_id)):
                junction.room_id = escape(request.json['room_id'])
                junction.world_id = escape(request.json['world_id'])
                junction.dest_id = escape(request.json['dest_id'])
                junction.junction_desc = escape(request.json['junction_desc'])
                db.session.commit()
                return junction_schema.dump(junction)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    def delete(self, junction_id):
        junction = Junction.query.get_or_404(junction_id)
        if (AuthChecker().check(request.authorization, junction.world_id)):
            db.session.delete(junction)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})

api.add_resource(JunctionListResource, '/api/junctions')
api.add_resource(JunctionResource, '/api/junctions/<int:junction_id>')

class Solution(db.Model):
    __tablename__ = "solution"
    solution_id = db.Column (db.INTEGER, primary_key=True)
    objective_id = db.Column (db.INTEGER, db.ForeignKey("objective.objective_id"))
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_text = db.Column (db.LargeBinary)
    visible = db.Column (db.INTEGER)

    def __repr__(self):
        return '<Solution %s>' % self.solution_id

class Invitation(db.Model):
    __tablename__ = "invitation"
    invitation_id = db.Column (db.INTEGER, primary_key=True)
    invitation_code = db.Column (db.VARCHAR(20))
    invitation_role = db.Column (db.VARCHAR(20))
    invitation_forever = db.Column (db.INTEGER)
    invitation_taken = db.Column (db.INTEGER)

    def __repr__(self):
        return '<Invitation %s>' % self.invitation_id

class Voting(db.Model):
    __tablename__ = "voting"
    voting_id = db.Column (db.INTEGER, primary_key=True)
    creator_id = db.Column (db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_id = db.Column (db.INTEGER, db.ForeignKey("solution.solution_id"))
    rating = db.Column (db.INTEGER)

    def __repr__(self):
        return '<Voting %s>' % self.voting_id

# S3 storage helper functions
def upload_file(bucket, object_name, file_name):
    s3_client = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    response = s3_client.upload_file(file_name, bucket, object_name)
    return response

def download_file(bucket, object_name, file_name):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    s3.Bucket(bucket).download_file(object_name, file_name)
    return file_name

def delete_file(bucket, object_name):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    s3.Object(bucket, object_name).delete()

def list_files(bucket, creator_name):
    s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    contents = []
    for item in s3.list_objects(Bucket=bucket)['Contents']:
        if (item['Key'].startswith(creator_name)):
            contents.append(item)
    return contents

# initialize a completely new world using a world template suplied as JSON
def init_world(world_file, creator_name, world_name, world_desc, world_url, world_img):
    counter_loaded = 0 # count each single element

    f = open(world_file)
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
        room.room_name = escape(i["name"])
        room.room_desc = escape(i["description"])
        room.room_img = clean_url(i["image"])
        db.session.add(room)
        db.session.commit()
        counter_loaded = counter_loaded + 1

    # load all other elements and check foreign key relationship
    for i in data["rooms"]:
        room_name = escape(i["name"])
        room = Room.query.filter_by(room_name=room_name).filter_by(world_id=world.world_id).first()

        # load all items in the room
        if "items" in i:
            for j in i["items"]:
                item = Item()
                item.room_id = room.room_id
                item.world_id = world.world_id
                item.item_name = escape(j["name"])
                item.item_desc = escape(j["description"])
                item.item_img = clean_url(j["image"])
                db.session.add(item)
                db.session.commit()
                counter_loaded = counter_loaded + 1
        
        # load all characters in the room
        if "characters" in i:
            for j in i["characters"]:
                person = Person()
                person.room_id = room.room_id
                person.world_id = world.world_id
                person.person_name = escape(j["name"])
                person.person_desc = escape(j["description"])
                person.person_img = clean_url(j["image"])
                db.session.add(person)
                db.session.commit()
                counter_loaded = counter_loaded + 1
        
        # load all objectives in the room
        if "objectives" in i:
            for j in i["objectives"]:
                objective = Objective()
                objective.room_id = room.room_id
                objective.world_id = world.world_id
                objective.objective_name = escape(j["name"])
                objective.objective_desc = escape(j["description"])
                objective.difficulty = escape(j["difficulty"])
                objective.objective_url = clean_url(j["url"])
                objective.supported_by = escape(j["supportedby"])
                objective.requires = escape(j["requires"])
                objective.objective_img = clean_url(j["image"])
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
                junction.junction_desc = escape(j["description"])
                db.session.add(junction)
                db.session.commit()
                counter_loaded = counter_loaded + 1
    f.close()
    return(counter_loaded)

# URL sanitization
def clean_url(url):
    return (re.sub('[^-A-Za-z0-9+&@#/%?=~_|!:,.;\(\)]', '', url))

# Path traversal prevention
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# check if the basic authentication is valid, used for API calls
class AuthChecker():
    def check(self, auth, world_id):
        if (auth):
            creator_name = auth['username']
            creator_pass = auth['password']
            creator = Creator.query.filter_by(creator_name=creator_name).first()
            world = World.query.filter_by(world_id=world_id).first()

            if (creator and world and check_password_hash(creator.creator_pass, creator_pass) and creator.creator_id == world.creator_id):
                return True
        return False

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

@app.route('/web/error', methods = ['GET'])
def get_error():
    return render_template('error.html')

@app.route('/web/logged', methods = ['GET'])
@login_required
def get_logged():
    return redirect(url_for('get_index'))

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
        return redirect(url_for('get_login'))
    else:
        login_user(creator, remember=remember)

        return redirect(url_for('get_index'))

@app.route('/web/logout', methods = ['GET'])
def get_logout():
    logout_user()
    return redirect(url_for('get_index'))

# S3 storage pages
@app.route("/web/storage", methods=['GET'])
@login_required
def get_storage():
    contents = list_files(BUCKET_PUBLIC, current_user.creator_name)
    return render_template('storage.html', contents=contents)

@app.route("/web/upload", methods=['POST'])
@login_required
def post_upload():
    # check if the post request has the file part
    if 'file' not in request.files:
        # flash('No file part')
        return render_template('error.html')
    file = request.files['file']

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        # flash('No selected file')
        return render_template('error.html')

    if file and allowed_file(file.filename):
        folder_name = f"{UPLOAD_FOLDER}/{current_user.creator_name}"
        local_file = os.path.join(folder_name, secure_filename(file.filename))
        remote_file = f"{current_user.creator_name}/{secure_filename(file.filename)}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        file.save(local_file)
        upload_file(BUCKET_PUBLIC, remote_file, local_file)
    return redirect(url_for('get_storage'))

@app.route("/web/download/<string:creatorname>/<string:filename>", methods=['GET'])
@login_required
def get_download(creatorname, filename):
    folder_name = f"{DOWNLOAD_FOLDER}/{current_user.creator_name}"
    local_file = os.path.join(folder_name, secure_filename(filename))
    remote_file = f"{current_user.creator_name}/{secure_filename(filename)}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    output = download_file(BUCKET_PUBLIC, remote_file, local_file)
    # return send_from_directory(app.config["UPLOAD_FOLDER"], name)
    return send_file(output, as_attachment=True)

@app.route("/web/delete/<string:creatorname>/<string:filename>", methods=['GET'])
@login_required
def get_delete(creatorname, filename):
    remote_file = f"{current_user.creator_name}/{secure_filename(filename)}"
    delete_file(BUCKET_PUBLIC, remote_file)
    return redirect(url_for('get_storage'))

# Flask HTML views to read and modify the database contents
@app.route('/web/stats', methods = ['GET'])
def get_stats():
    counts = dict()
    counts['creator'] = Creator.query.count()
    counts['world'] = World.query.count()
    counts['room'] = Room.query.count()
    counts['item'] = Item.query.count()
    counts['person'] = Person.query.count()
    counts['objective'] = Objective.query.count()
    counts['junction'] = Junction.query.count()
    counts['solution'] = Solution.query.count()
    
    return render_template('stats.html', counts=counts)

@app.route('/web/creators', methods = ['GET'])
def get_creators():
    creators = Creator.query.order_by(Creator.creator_id.asc())
    return render_template('creator.html', creators=creators)

@app.route('/web/creator/<int:creator_id>', methods = ['GET'])
def get_creator(creator_id):
    creator = Creator.query.filter_by(creator_id=creator_id).first()
    if (creator):
        return render_template('creator_detail.html', creator=creator)
    else:
        return render_template('error.html')

@app.route('/web/newcreator', methods = ['GET'])
def get_newcreator():
    return render_template('account.html')

@app.route('/web/newcreator', methods=['POST'])
def post_newcreator():
    code = request.form["invitation"]
    invitation  = Invitation.query.filter_by(invitation_code=code).first()

    if (invitation):
        if (invitation.invitation_forever == 1 or invitation.invitation_taken == 0):
            creator = Creator()
            creator.creator_name = escape(request.form["creator"])
            creator.creator_mail = escape(request.form["mail"])
            creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)
            creator.creator_role = invitation.invitation_role
            creator.creator_img = ""
            db.session.add(creator)
            db.session.commit()

            invitation.invitation_taken = 1
            db.session.commit()
    return redirect(url_for('get_creators'))

@app.route('/web/mycreator', methods = ['GET'])
@login_required
def get_mycreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    if (creator):
        return render_template('account_detail.html', creator=creator)
    else:
        return render_template('error.html')

@app.route('/web/mailcreator', methods=['POST'])
@login_required
def post_mailcreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    if (creator):
        creator.creator_mail = escape(request.form["mail"])
        creator.creator_img = clean_url(request.form["image"])
        db.session.commit()
        
        return redirect(url_for('get_mycreator'))
    else:
        return render_template('error.html')

@app.route('/web/passcreator', methods=['POST'])
@login_required
def post_passcreator():
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    if (creator):
        creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)
        db.session.commit()

        return redirect(url_for('get_mycreator'))
    else:
        return render_template('error.html')

@app.route('/web/delcreator', methods=['POST'])
@login_required
def post_delcreator():
    confirmation = request.form["confirm"]
    if (confirmation == "delete"):
        Creator.query.filter_by(creator_id=current_user.creator_id).delete()
        db.session.commit()
        logout_user()
    return redirect(url_for('get_index'))

@app.route('/web/worlds', methods = ['GET'])
def get_worlds():
    worlds = World.query.order_by(World.world_id.asc())
    return render_template('world.html', worlds=worlds)

@app.route('/web/world/<int:world_id>', methods = ['GET'])
def get_world(world_id):
    world = World.query.filter_by(world_id=world_id).first()
    if (world):
        return render_template('world_detail.html', world=world)
    else:
        return render_template('error.html')

@app.route('/web/delworld/<int:world_id>', methods=['GET'])
@login_required
def get_delworld(world_id):
    World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).delete()
    db.session.commit()
    return redirect(url_for('get_worlds'))

@app.route('/web/switchworld/<int:world_id>', methods=['GET'])
@login_required
def get_switchworld(world_id):
    world = World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).first()
    if (world):
        if (world.visible == 1):
            world.visible = 0
        else:
            world.visible = 1
        db.session.commit()
        
        return redirect(url_for('get_world', world_id=world_id))
    else:
        return render_template('error.html')

@app.route('/web/rooms/<int:world_id>', methods = ['GET'])
def get_rooms(world_id):
    rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
    return render_template('room.html', rooms=rooms, world_id=world_id)

@app.route('/web/room/<int:room_id>', methods = ['GET'])
def get_room(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    if (room):
        return render_template('room_detail.html', room=room)
    else:
        return render_template('error.html')

@app.route('/web/items/<int:world_id>', methods = ['GET'])
def get_items(world_id):
    items = Item.query.filter_by(world_id=world_id).order_by(Item.item_id.asc())
    return render_template('item.html', items=items, world_id=world_id)

@app.route('/web/item/<int:item_id>', methods = ['GET'])
def get_item(item_id):
    item = Item.query.filter_by(item_id=item_id).first()
    if (item):
        return render_template('item_detail.html', item=item)
    else:
        return render_template('error.html')

@app.route('/web/persons/<int:world_id>', methods = ['GET'])
def get_persons(world_id):
    persons = Person.query.filter_by(world_id=world_id).order_by(Person.person_id.asc())
    return render_template('person.html', persons=persons, world_id=world_id)

@app.route('/web/person/<int:person_id>', methods = ['GET'])
def get_person(person_id):
    person = Person.query.filter_by(person_id=person_id).first()
    if (person):
        return render_template('person_detail.html', person=person)
    else:
        return render_template('error.html')

@app.route('/web/objectives/<int:world_id>', methods = ['GET'])
def get_objectives(world_id):
    objectives = Objective.query.filter_by(world_id=world_id).order_by(Objective.objective_id.asc())
    return render_template('objective.html', objectives=objectives, world_id=world_id)

@app.route('/web/objective/<int:objective_id>', methods = ['GET'])
def get_objective(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if (objective):
        solutions = Solution.query.filter_by(objective_id=objective_id).filter_by(visible=1).order_by(Solution.solution_id.asc())
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
    else:
        return render_template('error.html')

@app.route('/web/junctions/<int:world_id>', methods = ['GET'])
def get_junctions(world_id):
    junctions = Junction.query.filter_by(world_id=world_id).order_by(Junction.junction_id.asc())
    return render_template('junction.html', junctions=junctions, world_id=world_id)

@app.route('/web/junction/<int:junction_id>', methods = ['GET'])
def get_junction(junction_id):
    junction = Junction.query.filter_by(junction_id=junction_id).first()
    if (junction):
        return render_template('junction_detail.html', junction=junction)
    else:
        return render_template('error.html')

@app.route('/web/quest/<int:objective_id>', methods=['POST'])
@login_required
def post_quest(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if (objective):
        room = Room.query.filter_by(room_id=objective.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()

        if (world.creator_id == current_user.creator_id):
            objective.quest = request.form["quest"].encode()
            db.session.commit()
        return redirect(url_for('get_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')

@app.route('/web/quest/<int:objective_id>', methods=['GET'])
@login_required
def get_quest(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if (objective):
        room = Room.query.filter_by(room_id=objective.room_id).first()
        world = World.query.filter_by(world_id=room.world_id).first()

        if (world.creator_id == current_user.creator_id):
            if (objective.quest != None):
                return render_template('quest_detail.html', quest=str(bytes(objective.quest), 'utf-8'), objective_id=objective_id, world_id=objective.world_id)
            else:
                return render_template('quest_detail.html', quest="", objective_id=objective_id, world_id=objective.world_id)
        else:
            return redirect(url_for('get_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')

@app.route('/web/solution/<int:solution_id>', methods=['GET'])
@login_required
def get_solution(solution_id):
    solution = Solution.query.filter_by(solution_id=solution_id).first()
    if (solution):
        objective = Objective.query.filter_by(objective_id=solution.objective_id).first()
        world = World.query.filter_by(world_id=objective.world_id).first()

        if (solution.visible == 1 and world.visible == 1):
            if (solution.solution_text != None):
                mdsolution = markdown2.markdown(str(bytes(solution.solution_text), 'utf-8'), extras=['fenced-code-blocks'])

                return render_template('solution_detail.html', mdsolution=mdsolution, solution_id=solution_id, world_id=objective.world_id)
            else:
                return render_template('solution_detail.html', mdsolution="", solution_id=solution_id, world_id=objective.world_id)
        else:
            return redirect(url_for('get_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')

@app.route('/web/likesolution/<int:solution_id>', methods=['GET'])
@login_required
def get_likesolution(solution_id):
    voting = Voting.query.filter_by(solution_id=solution_id).filter_by(creator_id=current_user.creator_id).first()
    solution = Solution.query.filter_by(solution_id=solution_id).first()
    if (solution):
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
            voting.solution_id = solution_id
            voting.rating = 1
            db.session.add(voting)
            db.session.commit()

        return redirect(url_for('get_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')

@app.route('/web/mysolution/<int:objective_id>', methods=['POST'])
@login_required
def post_mysolution(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if (objective):
        solution = Solution.query.filter_by(objective_id=objective_id).filter_by(creator_id=current_user.creator_id).first()
        if solution is not None:
            db.session.delete(solution)
            db.session.commit()

        solution_new = Solution()
        solution_new.objective_id = objective_id
        solution_new.creator_id = current_user.creator_id
        solution_new.solution_text = request.form["solution"].encode()
        if ('visible' in request.form):
            solution_new.visible = 1
        db.session.add(solution_new)
        db.session.commit()

        return redirect(url_for('get_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')

@app.route('/web/mysolution/<int:objective_id>', methods=['GET'])
@login_required
def get_mysolution(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if (objective):
        if (objective.quest != None):
            mdquest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
        else:
            mdquest = ""

        solution = Solution.query.filter_by(objective_id=objective_id).filter_by(creator_id=current_user.creator_id).first()
        if (solution != None):
            return render_template('solution_my_detail.html', solution=str(bytes(solution.solution_text), 'utf-8'), visible=solution.visible, mdquest=mdquest, objective_id=objective_id, world_id=objective.world_id)
        else:
            return render_template('solution_my_detail.html', solution="", visible=0, mdquest=mdquest, objective_id=objective_id, world_id=objective.world_id)
    else:
        return render_template('error.html')

@app.route('/web/mywalkthrough/<int:world_id>', methods=['GET'])
@login_required
def get_mywalkthrough(world_id):
    # objective = Objective.query.filter_by(objective_id=objective_id).first()

    with open(DOWNLOAD_FOLDER + "/walkthrough.md", 'w') as f:
        f.write("Markdown")

    # return send_file(DOWNLOAD_FOLDER + "/walkthrough.md", attachment_filename='walkthrough.md',  as_attachment=True)
    return send_file(DOWNLOAD_FOLDER + "/walkthrough.md", attachment_filename='walkthrough.md')
