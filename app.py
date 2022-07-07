import json     # for JSON file handling and parsing
import os       # for direct file system and environment access
import re       # for regular expressions
import random   # for captcha random numbers
import logging  # enable logging

import boto3            # for S3 storage
import markdown2        # for markdown parsing
from flask import Flask, request, render_template, jsonify, send_file, escape, redirect, url_for, \
    session             # most important Flask modules
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, \
    current_user        # to manage user sessions
from flask_mail import Mail, Message        # to send mails
from flask_marshmallow import Marshmallow   # to marshall our objects
from flask_restx import Resource, Api       # to enable the REST API
from flask_sitemap import Sitemap           # to generate sitemap.xml
from flask_sqlalchemy import SQLAlchemy     # object-relational mapper (ORM)
from flask_wtf.csrf import CSRFProtect      # CSRF protection
from werkzeug.security import generate_password_hash, check_password_hash  # for password hashing
from werkzeug.utils import secure_filename  # to prevent path traversal attacks
from logging.handlers import SMTPHandler    # get crashes via mail

from forms import LoginForm, AccountForm, MailCreatorForm, PassCreatorForm, DelCreatorForm, \
    UploadForm, WorldForm, RoomForm, ItemForm, ObjectiveForm, ContactForm, PersonForm, \
    JunctionForm, QuestSolForm, FileForm    # Flask/Jinja template forms

# the app configuration is done via environmental variables
POSTGRES_URL = os.environ['POSTGRES_URL']           # DB connection data
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PW = os.environ['POSTGRES_PW']
POSTGRES_DB = os.environ['POSTGRES_DB']
SECRET_KEY = os.environ['SECRET_KEY']
MAIL_SERVER = os.environ['MAIL_SERVER']             # mail host
MAIL_SENDER = os.environ['MAIL_SENDER']
MAIL_ADMIN = os.environ['MAIL_ADMIN']
MAIL_ENABLE = int(os.environ['MAIL_ENABLE'])
S3_ENDPOINT = os.environ['S3_ENDPOINT']             # where S3 buckets are located
S3_QUOTA = os.environ['S3_QUOTA']
BUCKET_PUBLIC = os.environ['BUCKET_PUBLIC']
BUCKET_PRIVATE = os.environ['BUCKET_PRIVATE']
UPLOAD_FOLDER = os.environ['HOME'] + "/uploads"     # directory for game data
DOWNLOAD_FOLDER = os.environ['HOME'] + "/downloads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
APP_VERSION = os.environ['APP_VERSION']
APP_PREFIX = os.environ['APP_PREFIX']

# Flask app configuration containing static (css, img) path and template directory
app = Flask(__name__,
            static_url_path=APP_PREFIX + '/static',
            static_folder='static',
            template_folder='templates')


# enable global variables
@app.context_processor
def inject_version_and_prefix():
    return dict(version=APP_VERSION, prefix=APP_PREFIX)


# Enable logging and crashes via mail
if MAIL_ENABLE == 1:
    mail_handler = SMTPHandler(
        mailhost='127.0.0.1',
        fromaddr=MAIL_SENDER,
        toaddrs=[MAIL_ADMIN],
        subject='Kringle.info: Application Error'
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    if not app.debug:
        app.logger.addHandler(mail_handler)


# Enable CSRF protection for the app
csrf = CSRFProtect(app)

# Limit file uploads to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# sitemap.xml configuration
ext = Sitemap(app=app)

# REST API configuration
api = Api(app)

# Marshall configuration
marsh = Marshmallow(app)

# E-Mail configuration
mail = Mail(app)
app.config['MAIL_SERVER'] = MAIL_SERVER

# DB configuration
db = SQLAlchemy()
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
                                                               db=POSTGRES_DB)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # silence the deprecation warning
db.init_app(app)

# Login Manager configuration
login_manager = LoginManager()
login_manager.login_view = 'show_login'  # show this page if a login is required
login_manager.init_app(app)


# link the Login Manager to the correct user entry
@login_manager.user_loader
def load_user(creator_id):
    # since the creator_id is just the primary key of our user table, use it in the query for the user
    return Creator.query.get(int(creator_id))


# --------------------------------------------------------------
# ORM classes
# --------------------------------------------------------------

# ORM model classes, Creator table is used for the Login Manager
# for each REST-enabled element, we add marshmallow schemas
# enable a REST API to modify the database contents
class Creator(UserMixin, db.Model):
    __tablename__ = "creator"
    creator_id = db.Column(db.INTEGER, primary_key=True)
    creator_name = db.Column(db.VARCHAR(100), unique=True)
    creator_mail = db.Column(db.VARCHAR(100), unique=True)
    creator_desc = db.Column(db.VARCHAR(1024))
    creator_pass = db.Column(db.VARCHAR(256))
    creator_img = db.Column(db.VARCHAR(384))
    creator_role = db.Column(db.VARCHAR(20))

    # match the correct row for the Login Manager ID
    def get_id(self):
        return self.creator_id

    def __repr__(self):
        return '<Creator %s>' % self.creator_name


class World(db.Model):
    __tablename__ = "world"
    world_id = db.Column(db.INTEGER, primary_key=True)
    creator_id = db.Column(db.INTEGER, db.ForeignKey("creator.creator_id"))
    world_name = db.Column(db.VARCHAR(100), unique=True)
    world_desc = db.Column(db.VARCHAR(1024))
    world_url = db.Column(db.VARCHAR(256))
    world_img = db.Column(db.VARCHAR(384))
    visible = db.Column(db.INTEGER, default=0)
    reduced = db.Column(db.INTEGER, default=0)
    archived = db.Column(db.INTEGER, default=0)

    def __repr__(self):
        return '<World %s>' % self.world_name


class WorldSchema(marsh.Schema):
    class Meta:
        fields = ("world_id", "creator_id", "world_name", "world_desc", "world_img")
        model = World


world_schema = WorldSchema()
worlds_schema = WorldSchema(many=True)


class WorldListResource(Resource):
    @staticmethod
    def get():
        worlds = World.query.all()
        return worlds_schema.dump(worlds)

    @staticmethod
    def post():
        if all(s in request.json for s in ('world_name', 'world_desc', 'world_img')):
            creator = Creator.query.filter_by(creator_name=request.authorization['username']).first()
            if creator.creator_role == 'creator':
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
    @staticmethod
    def get(world_id):
        world = World.query.get_or_404(world_id)
        return world_schema.dump(world)

    @staticmethod
    def patch(world_id):
        world = World.query.get_or_404(world_id)
        if all(s in request.json for s in ('world_name', 'world_desc', 'world_img')):
            if AuthChecker().check(request.authorization, world.world_id):
                world.world_name = escape(request.json['world_name'])
                world.world_desc = escape(request.json['world_desc'])
                world.world_img = clean_url(request.json['world_img'])
                db.session.commit()
                return world_schema.dump(world)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    @staticmethod
    def delete(world_id):
        world = World.query.get_or_404(world_id)
        if AuthChecker().check(request.authorization, world.world_id):
            db.session.delete(world)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


class WorldFullListResource(Resource):
    @staticmethod
    def post():
        if (request.args.get('world_name') is not None and request.args.get(
                'world_desc') is not None and request.args.get('world_url') is not None and request.args.get(
                'world_img') is not None):
            creator = Creator.query.filter_by(creator_name=request.authorization['username']).first()
            if creator.creator_role == 'creator':
                world_name = escape(request.args.get('world_name'))
                world_desc = escape(request.args.get('world_desc'))
                world_url = clean_url(request.args.get('world_url'))
                world_img = escape(request.args.get('world_img'))

                record = json.loads(request.data)
                input_file = f"{UPLOAD_FOLDER}/{secure_filename(world_name)}.world"
                object_file = f"world/{secure_filename(world_name)}.world"
                with open(input_file, 'w') as f:
                    f.write(json.dumps(record, indent=4))
                upload_file(BUCKET_PRIVATE, object_file, input_file)
                i = init_world(input_file, request.authorization['username'], world_name, world_desc, world_url,
                               world_img)
                return jsonify({'success': 'world file stored containing ' + str(i) + ' elements.'})
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})


class WorldFullResource(Resource):
    @staticmethod
    def get(world_name):
        output_file = f"{DOWNLOAD_FOLDER}/{secure_filename(world_name)}.world"
        object_file = f"world/{secure_filename(world_name)}.world"
        output = download_file(BUCKET_PRIVATE, object_file, output_file)
        if output:
            return send_file(output)
        else:
            return jsonify({'error': 'element not found'})


api.add_resource(WorldListResource, APP_PREFIX + '/api/worlds')
api.add_resource(WorldResource, APP_PREFIX + '/api/worlds/<int:world_id>')
api.add_resource(WorldFullListResource, APP_PREFIX + '/api/full_worlds')
api.add_resource(WorldFullResource, APP_PREFIX + '/api/full_worlds/<string:world_name>')


class Room(db.Model):
    __tablename__ = "room"
    room_id = db.Column(db.INTEGER, primary_key=True)
    world_id = db.Column(db.INTEGER, db.ForeignKey("world.world_id"))
    room_name = db.Column(db.VARCHAR(100))
    room_desc = db.Column(db.VARCHAR(1024))
    room_img = db.Column(db.VARCHAR(384))

    def __repr__(self):
        return '<Room %s>' % self.room_name


class RoomSchema(marsh.Schema):
    class Meta:
        fields = ("room_id", "world_id", "room_name", "room_desc", "room_img")
        model = Room


room_schema = RoomSchema()
rooms_schema = RoomSchema(many=True)


class RoomListResource(Resource):
    @staticmethod
    def get():
        rooms = Room.query.all()
        return rooms_schema.dump(rooms)

    @staticmethod
    def post():
        if all(s in request.json for s in ('world_id', 'room_name', 'room_desc', 'room_img')):
            if AuthChecker().check(request.authorization, request.json['world_id']):
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
    @staticmethod
    def get(room_id):
        room = Room.query.get_or_404(room_id)
        return room_schema.dump(room)

    @staticmethod
    def patch(room_id):
        room = Room.query.get_or_404(room_id)
        if all(s in request.json for s in ('world_id', 'room_name', 'room_desc', 'room_img')):
            if AuthChecker().check(request.authorization, room.world_id):
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

    @staticmethod
    def delete(room_id):
        room = Room.query.get_or_404(room_id)
        if AuthChecker().check(request.authorization, room.world_id):
            db.session.delete(room)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


api.add_resource(RoomListResource, APP_PREFIX + '/api/rooms')
api.add_resource(RoomResource, APP_PREFIX + '/api/rooms/<int:room_id>')


class Item(db.Model):
    __tablename__ = "item"
    item_id = db.Column(db.INTEGER, primary_key=True)
    room_id = db.Column(db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column(db.INTEGER, db.ForeignKey("world.world_id"))
    item_name = db.Column(db.VARCHAR(100))
    item_desc = db.Column(db.VARCHAR(1024))
    item_img = db.Column(db.VARCHAR(384))

    def __repr__(self):
        return '<Item %s>' % self.item_name


class ItemSchema(marsh.Schema):
    class Meta:
        fields = ("item_id", "room_id", "world_id", "item_name", "item_desc", "item_img")
        model = Item


item_schema = ItemSchema()
items_schema = ItemSchema(many=True)


class ItemListResource(Resource):
    @staticmethod
    def get():
        items = Item.query.all()
        return items_schema.dump(items)

    @staticmethod
    def post():
        if all(s in request.json for s in ('room_id', 'world_id', 'item_name', 'item_desc', 'item_img')):
            if AuthChecker().check(request.authorization, request.json['world_id']):
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
    @staticmethod
    def get(item_id):
        item = Item.query.get_or_404(item_id)
        return item_schema.dump(item)

    @staticmethod
    def patch(item_id):
        item = Item.query.get_or_404(item_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'item_name', 'item_desc', 'item_img')):
            if AuthChecker().check(request.authorization, item.world_id):
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

    @staticmethod
    def delete(item_id):
        item = Item.query.get_or_404(item_id)
        if AuthChecker().check(request.authorization, item.world_id):
            db.session.delete(item)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


api.add_resource(ItemListResource, APP_PREFIX + '/api/items')
api.add_resource(ItemResource, APP_PREFIX + '/api/items/<int:item_id>')


class Objective(db.Model):
    __tablename__ = "objective"
    objective_id = db.Column(db.INTEGER, primary_key=True)
    room_id = db.Column(db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column(db.INTEGER, db.ForeignKey("world.world_id"))
    objective_name = db.Column(db.VARCHAR(100))
    objective_title = db.Column(db.VARCHAR(100))
    objective_desc = db.Column(db.VARCHAR(1024))
    difficulty = db.Column(db.INTEGER)
    objective_url = db.Column(db.VARCHAR(256))
    supported_by = db.Column(db.VARCHAR(100))
    requires = db.Column(db.VARCHAR(100))
    objective_img = db.Column(db.VARCHAR(384))
    quest = db.Column(db.LargeBinary)

    def __repr__(self):
        return '<Objective %s>' % self.objective_name


class ObjectiveSchema(marsh.Schema):
    class Meta:
        fields = (
            "objective_id", "room_id", "world_id", "objective_name", "objective_title", "objective_desc", "difficulty",
            "objective_url", "supported_by", "requires", "objective_img")
        model = Objective


objective_schema = ObjectiveSchema()
objectives_schema = ObjectiveSchema(many=True)


class ObjectiveListResource(Resource):
    @staticmethod
    def get():
        objectives = Objective.query.all()
        return objectives_schema.dump(objectives)

    @staticmethod
    def post():
        if all(s in request.json for s in (
                'room_id', 'world_id', 'objective_name', 'objective_title', 'objective_desc', 'difficulty',
                'objective_url',
                'supported_by', 'requires', 'objective_img')):
            if AuthChecker().check(request.authorization, request.json['world_id']):
                new_objective = Objective(
                    room_id=escape(request.json['room_id']),
                    world_id=escape(request.json['world_id']),
                    objective_name=escape(request.json['objective_name']),
                    objective_title=escape(request.json['objective_title']),
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
    @staticmethod
    def get(objective_id):
        objective = Objective.query.get_or_404(objective_id)
        return objective_schema.dump(objective)

    @staticmethod
    def patch(objective_id):
        objective = Objective.query.get_or_404(objective_id)
        if all(s in request.json for s in (
                'room_id', 'world_id', 'objective_name', 'objective_title', 'objective_desc', 'difficulty',
                'objective_url',
                'supported_by', 'requires', 'objective_img')):
            if AuthChecker().check(request.authorization, objective.world_id):
                objective.room_id = escape(request.json['room_id']),
                objective.world_id = escape(request.json['world_id']),
                objective.objective_name = escape(request.json['objective_name']),
                objective.objective_title = escape(request.json['objective_title']),
                objective.objective_desc = escape(request.json['objective_desc']),
                objective.difficulty = escape(request.json['difficulty']),
                objective.objective_url = clean_url(request.json['objective_url']),
                objective.supported_by = escape(request.json['supported_by']),
                objective.requires = escape(request.json['requires']),
                objective.objective_img = clean_url(request.json['objective_img'])
                db.session.commit()
                return objective_schema.dump(objective)
            else:
                return jsonify({'error': 'wrong credentials or permissions'})
        else:
            return jsonify({'error': 'wrong JSON format'})

    @staticmethod
    def delete(objective_id):
        objective = Objective.query.get_or_404(objective_id)
        if AuthChecker().check(request.authorization, objective.world_id):
            db.session.delete(objective)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


api.add_resource(ObjectiveListResource, APP_PREFIX + '/api/objectives')
api.add_resource(ObjectiveResource, APP_PREFIX + '/api/objectives/<int:objective_id>')


class Person(db.Model):
    __tablename__ = "person"
    person_id = db.Column(db.INTEGER, primary_key=True)
    room_id = db.Column(db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column(db.INTEGER, db.ForeignKey("world.world_id"))
    person_name = db.Column(db.VARCHAR(100))
    person_desc = db.Column(db.VARCHAR(1024))
    person_img = db.Column(db.VARCHAR(384))

    def __repr__(self):
        return '<Person %s>' % self.person_name


class PersonSchema(marsh.Schema):
    class Meta:
        fields = ("person_id", "room_id", "world_id", "person_name", "person_desc", "person_img")
        model = Person


person_schema = PersonSchema()
persons_schema = PersonSchema(many=True)


class PersonListResource(Resource):
    @staticmethod
    def get():
        persons = Person.query.all()
        return persons_schema.dump(persons)

    @staticmethod
    def post():
        if all(s in request.json for s in ('room_id', 'world_id', 'person_name', 'person_desc', 'person_img')):
            if AuthChecker().check(request.authorization, request.json['world_id']):
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
    @staticmethod
    def get(person_id):
        person = Person.query.get_or_404(person_id)
        return person_schema.dump(person)

    @staticmethod
    def patch(person_id):
        person = Person.query.get_or_404(person_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'person_name', 'person_desc', 'person_img')):
            if AuthChecker().check(request.authorization, person.world_id):
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

    @staticmethod
    def delete(person_id):
        person = Person.query.get_or_404(person_id)
        if AuthChecker().check(request.authorization, person.world_id):
            db.session.delete(person)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


api.add_resource(PersonListResource, APP_PREFIX + '/api/persons')
api.add_resource(PersonResource, APP_PREFIX + '/api/persons/<int:person_id>')


class Junction(db.Model):
    __tablename__ = "junction"
    junction_id = db.Column(db.INTEGER, primary_key=True)
    room_id = db.Column(db.INTEGER, db.ForeignKey("room.room_id"))
    world_id = db.Column(db.INTEGER, db.ForeignKey("world.world_id"))
    dest_id = db.Column(db.INTEGER, db.ForeignKey("room.room_id"))
    junction_desc = db.Column(db.VARCHAR(1024))

    def __repr__(self):
        return '<Junction %s>' % self.junction_id


class JunctionSchema(marsh.Schema):
    class Meta:
        fields = ("junction_id", "room_id", "world_id", "dest_id", "junction_desc")
        model = Junction


junction_schema = JunctionSchema()
junctions_schema = JunctionSchema(many=True)


class JunctionListResource(Resource):
    @staticmethod
    def get():
        junctions = Junction.query.all()
        return junctions_schema.dump(junctions)

    @staticmethod
    def post():
        if all(s in request.json for s in ('room_id', 'world_id', 'dest_id', 'junction_desc')):
            if AuthChecker().check(request.authorization, request.json['world_id']):
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
    @staticmethod
    def get(junction_id):
        junction = Junction.query.get_or_404(junction_id)
        return junction_schema.dump(junction)

    @staticmethod
    def patch(junction_id):
        junction = Junction.query.get_or_404(junction_id)
        if all(s in request.json for s in ('room_id', 'world_id', 'dest_id', 'junction_desc')):
            if AuthChecker().check(request.authorization, junction.world_id):
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

    @staticmethod
    def delete(junction_id):
        junction = Junction.query.get_or_404(junction_id)
        if AuthChecker().check(request.authorization, junction.world_id):
            db.session.delete(junction)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'wrong credentials or permissions'})


api.add_resource(JunctionListResource, APP_PREFIX + '/api/junctions')
api.add_resource(JunctionResource, APP_PREFIX + '/api/junctions/<int:junction_id>')


class Solution(db.Model):
    __tablename__ = "solution"
    solution_id = db.Column(db.INTEGER, primary_key=True)
    objective_id = db.Column(db.INTEGER, db.ForeignKey("objective.objective_id"))
    creator_id = db.Column(db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_text = db.Column(db.LargeBinary)
    visible = db.Column(db.INTEGER, default=0)

    def __repr__(self):
        return '<Solution %s>' % self.solution_id


class Invitation(db.Model):
    __tablename__ = "invitation"
    invitation_id = db.Column(db.INTEGER, primary_key=True)
    invitation_code = db.Column(db.VARCHAR(20))
    invitation_role = db.Column(db.VARCHAR(20))
    invitation_forever = db.Column(db.INTEGER, default=0)
    invitation_taken = db.Column(db.INTEGER, default=0)

    def __repr__(self):
        return '<Invitation %s>' % self.invitation_id


class Voting(db.Model):
    __tablename__ = "voting"
    voting_id = db.Column(db.INTEGER, primary_key=True)
    creator_id = db.Column(db.INTEGER, db.ForeignKey("creator.creator_id"))
    solution_id = db.Column(db.INTEGER, db.ForeignKey("solution.solution_id"))
    rating = db.Column(db.INTEGER, default=1)

    def __repr__(self):
        return '<Voting %s>' % self.voting_id


# --------------------------------------------------------------
# Internal functions
# --------------------------------------------------------------

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


def rename_file(bucket, object_name_new, object_name_old):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    s3.Object(bucket, object_name_new).copy_from(CopySource=f"{bucket}/{object_name_old}")
    s3.Object(bucket, object_name_old).delete()


def list_files(bucket, creator_name):
    s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    contents = []
    for item in s3.list_objects(Bucket=bucket)['Contents']:
        if item['Key'].startswith(creator_name):
            contents.append(item)
    return contents


def get_size(bucket, path):
    s3 = boto3.resource('s3', endpoint_url=S3_ENDPOINT)
    my_bucket = s3.Bucket(bucket)
    total_size = 0

    for obj in my_bucket.objects.filter(Prefix=path):
        total_size = total_size + obj.size

    return total_size


def get_all_size(bucket):
    s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    top_level_folders = dict()
    for key in s3.list_objects(Bucket=bucket)['Contents']:
        folder = key['Key'].split('/')[0]
        if folder in top_level_folders:
            top_level_folders[folder] += key['Size']
        else:
            top_level_folders[folder] = key['Size']

    return top_level_folders


# initialize a completely new world using a world template supplied as JSON
def init_world(world_file, creator_name, world_name, world_desc, world_url, world_img):
    counter_loaded = 0  # count each single element

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
    world = World.query.filter_by(world_name=world_name).first()

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
                objective.objective_title = escape(j["title"])
                objective.objective_desc = escape(j["description"])
                objective.difficulty = escape(j["difficulty"])
                objective.objective_url = clean_url(j["url"])
                objective.supported_by = escape(j["supported_by"])
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

                dest_room = Room.query.filter_by(world_id=world.world_id).filter_by(room_name=j["destination"]).first()
                junction.dest_id = dest_room.room_id
                junction.junction_desc = escape(j["description"])
                db.session.add(junction)
                db.session.commit()
                counter_loaded = counter_loaded + 1
    f.close()
    return counter_loaded


# URL sanitization
def clean_url(url):
    return re.sub('[^-A-Za-z0-9+&@#/%?=~_|!:,.;()]', '', url)


# Path traversal prevention
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# check if the basic authentication is valid, used for API calls
class AuthChecker:
    @staticmethod
    def check(auth, world_id):
        if auth:
            creator_name = auth['username']
            creator_pass = auth['password']
            creator = Creator.query.filter_by(creator_name=creator_name).first()
            world = World.query.filter_by(world_id=world_id).first()

            if (creator and world and check_password_hash(creator.creator_pass,
                                                          creator_pass) and creator.creator_id == world.creator_id):
                return True
        return False


# Sitemap page
@ext.register_generator
def index():
    # Not needed if you set SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS=True
    yield 'show_index', {}
    yield 'show_creators', {}
    yield 'show_worlds', {}


# Send an e-mail
def send_mail(recipients, mail_header, mail_body):
    if MAIL_ENABLE == 1:
        msg = Message(mail_header,
                      sender=MAIL_SENDER,
                      recipients=recipients)
        msg.body = mail_body
        mail.send(msg)


# Internal helpers - return choices list used in HTML select elements
def get_rooms_choices(rooms):
    rooms_choices = list()
    for room in rooms:
        rooms_choices.append((room.room_id, room.room_name))
    return rooms_choices


def get_objectives_choices(objectives):
    objectives_choices = list()
    objectives_choices.append("none")
    for objective in objectives:
        objectives_choices.append(objective.objective_name)
    return objectives_choices


def get_items_choices(items):
    items_choices = list()
    items_choices.append("none")
    for item in items:
        items_choices.append(item.item_name)
    return items_choices


# Internal helpers - persist selected world in the session to improve navigation and remember selected world
def update_session(world):
    session['world_id'] = world.world_id
    session['world_name'] = world.world_name
    session['reduced'] = world.reduced


# --------------------------------------------------------------
# Flask entry pages
# --------------------------------------------------------------

# Show site index containing a list of all active and available worlds
@app.route(APP_PREFIX + '/web/', methods=['GET'])
def show_index():
    worlds = World.query.filter_by(archived=0).order_by(World.world_name.asc())
    return render_template('index.html', worlds=worlds)


# Show error page  - for all "hard" crashes a mail is sent to the site admin
@app.route(APP_PREFIX + '/web/error', methods=['GET'])
def show_error():
    return render_template('error.html')


# Force user log-in and return to the site index afterwards
@app.route(APP_PREFIX + '/web/logged', methods=['GET'])
@login_required
def show_logged():
    return redirect(url_for('show_index'))


# Show user log-in page
@app.route(APP_PREFIX + '/web/login', methods=['GET', 'POST'])
def show_login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        creator_name = request.form["creator"]
        creator_pass = request.form["password"]
        remember = True if request.form.get('remember') else False
        creator = Creator.query.filter_by(creator_name=creator_name).first()

        if not creator or not check_password_hash(creator.creator_pass, creator_pass):
            return redirect(url_for('show_login'))
        else:
            login_user(creator, remember=remember)
            return redirect(url_for('show_index'))
    else:
        return render_template('login.html', form=form)


# Log out user and return to the site index afterwards
@app.route(APP_PREFIX + '/web/logout', methods=['GET'])
def show_logout():
    logout_user()
    return redirect(url_for('show_index'))


# --------------------------------------------------------------
# S3 storage pages
# --------------------------------------------------------------

# Show list of all uploaded filed and upload form
@app.route(APP_PREFIX + "/web/storage", methods=['GET', 'POST'])
@login_required
def show_storage():
    form = UploadForm()
    form2 = FileForm()
    space_used_in_mb = round((get_size(BUCKET_PUBLIC, f"{current_user.creator_name}/") / 1024 / 1024), 2)
    space_used = int(space_used_in_mb / int(S3_QUOTA) * 100)

    if request.method == 'POST' and form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)

        if allowed_file(filename) and space_used < 100:
            folder_name = f"{UPLOAD_FOLDER}/{current_user.creator_name}"
            local_file = os.path.join(folder_name, filename)
            remote_file = f"{current_user.creator_name}/{filename}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            form.file.data.save(local_file)
            upload_file(BUCKET_PUBLIC, remote_file, local_file)
        return redirect(url_for('show_storage'))
    else:
        contents = list_files(BUCKET_PUBLIC, current_user.creator_name)
        return render_template('storage.html', contents=contents, creator_name=current_user.creator_name,
                               space_used_in_mb=space_used_in_mb, space_used=space_used, form=form, form2=form2)


# Change a filename
@app.route(APP_PREFIX + "/web/rename", methods=['POST'])
@login_required
def do_rename():
    form = FileForm()
    filename_new = escape(request.form["filename_new"])
    filename_old = escape(request.form["filename_old"])

    remote_file_new = f"{current_user.creator_name}/{secure_filename(filename_new)}"
    remote_file_old = f"{current_user.creator_name}/{secure_filename(filename_old)}"

    if remote_file_new != remote_file_old and allowed_file(remote_file_new):
        rename_file(BUCKET_PUBLIC, remote_file_new, remote_file_old)

    return redirect(url_for('show_storage'))


# Download a specific file from S3 storage
@app.route(APP_PREFIX + "/web/download/<string:filename>", methods=['GET'])
@login_required
def do_download(filename):
    folder_name = f"{DOWNLOAD_FOLDER}/{current_user.creator_name}"
    local_file = os.path.join(folder_name, secure_filename(filename))
    remote_file = f"{current_user.creator_name}/{secure_filename(filename)}"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    output = download_file(BUCKET_PUBLIC, remote_file, local_file)
    # return send_from_directory(app.config["UPLOAD_FOLDER"], name)
    return send_file(output, as_attachment=True)


# Remove a specific file from S3 storage
@app.route(APP_PREFIX + "/web/delete/<string:filename>", methods=['GET'])
@login_required
def do_delete(filename):
    remote_file = f"{current_user.creator_name}/{secure_filename(filename)}"
    delete_file(BUCKET_PUBLIC, remote_file)
    return redirect(url_for('show_storage'))


# --------------------------------------------------------------
# Flask HTML views to read and modify the database contents
# --------------------------------------------------------------

# Show statistics regarding available elements stored in the database and on S3 storage
@app.route(APP_PREFIX + '/web/stats', methods=['GET'])
def show_stats():
    counts = dict()
    counts['creator'] = Creator.query.count()
    counts['world'] = World.query.count()
    counts['room'] = Room.query.count()
    counts['item'] = Item.query.count()
    counts['person'] = Person.query.count()
    counts['objective'] = Objective.query.count()
    counts['junction'] = Junction.query.count()
    counts['solution'] = Solution.query.count()

    # bucket = dict()
    # bucket['world'] = round((get_size(BUCKET_PUBLIC, "world/") / 1024 / 1024), 2)

    bucket_all = get_all_size(BUCKET_PUBLIC)

    return render_template('stats.html', counts=counts, bucket_all=bucket_all)


# Show information about all major releases
@app.route(APP_PREFIX + '/web/release', methods=['GET'])
def show_release():
    return render_template('release.html')


# Displays an image file stored on S3 storage
@app.route(APP_PREFIX + '/web/image/<string:filename>', methods=['GET'])
@login_required
def show_image(filename):
    return render_template('image.html', creator_name=current_user.creator_name, filename=filename)


# Displays a form to send a message to the site admin - implements a simple captcha as well
@app.route(APP_PREFIX + '/web/contact', methods=['GET', 'POST'])
def show_contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            contact_name = escape(request.form["contact_name"])
            email = escape(request.form["email"])
            message = escape(request.form["message"])

            send_mail([MAIL_ADMIN], f"{contact_name} - {email}",
                      f"{message}")

            return redirect(url_for('show_index'))
        else:
            form.contact_name.default = escape(request.form["contact_name"])
            form.email.default = escape(request.form["email"])
            form.message.default = escape(request.form["message"])

            random1 = random.randint(1, 10)
            random2 = random.randint(1, 10)
            check_captcha = random1 + random2

            form.check_captcha.default = check_captcha
            form.process()

            return render_template('contact.html', form=form, random1=random1, random2=random2,
                                   check_captcha=check_captcha)
    else:
        random1 = random.randint(1, 10)
        random2 = random.randint(1, 10)
        check_captcha = random1 + random2

        form.check_captcha.default = check_captcha
        form.process()

        return render_template('contact.html', form=form, random1=random1, random2=random2, check_captcha=check_captcha)


# Displays all available creators
@app.route(APP_PREFIX + '/web/creators', methods=['GET'])
def show_creators():
    creators = Creator.query.order_by(Creator.creator_name.asc())
    return render_template('creator.html', creators=creators)


# Shows information about a specific creator
@app.route(APP_PREFIX + '/web/creator/<int:creator_id>', methods=['GET'])
def show_creator(creator_id):
    creator = Creator.query.filter_by(creator_id=creator_id).first()
    if creator:
        return render_template('creator_detail.html', creator=creator)
    else:
        return render_template('error.html')


# Displays a form to create a new user (aka creator)
@app.route(APP_PREFIX + '/web/new_creator', methods=['GET', 'POST'])
def show_new_creator():
    form = AccountForm()
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form["invitation"]
        invitation = Invitation.query.filter_by(invitation_code=code).first()

        if invitation:
            if invitation.invitation_forever == 1 or invitation.invitation_taken == 0:
                creator = Creator()
                creator.creator_name = escape(request.form["creator"])
                creator.creator_mail = escape(request.form["email"])
                creator.creator_desc = ""
                creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256',
                                                              salt_length=16)
                creator.creator_role = invitation.invitation_role
                creator.creator_img = ""
                db.session.add(creator)
                db.session.commit()

                invitation.invitation_taken = 1
                db.session.commit()
        return redirect(url_for('show_creators'))
    else:
        return render_template('account.html', form=form)


# Displays various forms to change the currently logged-in user
@app.route(APP_PREFIX + '/web/my_creator', methods=['GET'])
@login_required
def show_my_creator():
    form1 = MailCreatorForm()
    form2 = PassCreatorForm()
    form3 = DelCreatorForm()
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()

    form1.email.default = creator.creator_mail
    form1.description.default = creator.creator_desc
    form1.url.default = creator.creator_img
    form1.process()
    return render_template('account_detail.html', creator=creator, form1=form1, form2=form2, form3=form3)


# Post a change of user data or display error message if some data was not entered correctly
@app.route(APP_PREFIX + '/web/my_mail_creator', methods=['POST'])
@login_required
def show_my_mail_creator():
    form1 = MailCreatorForm()
    form2 = PassCreatorForm()
    form3 = DelCreatorForm()
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()

    if creator:
        if form1.validate_on_submit():
            old_mail = creator.creator_mail
            creator.creator_mail = escape(request.form["email"])
            creator.creator_desc = escape(request.form["description"])
            creator.creator_img = clean_url(request.form["url"])
            db.session.commit()

            send_mail([creator.creator_mail], "Notification: E-Mail changed",
                      f"You have changed you e-mail address from {old_mail} to {creator.creator_mail}.")

            return redirect(url_for('show_my_creator'))
        else:
            form1.email.default = creator.creator_mail
            form1.description.default = creator.creator_desc
            form1.url.default = creator.creator_img
            form1.process()
            return render_template('account_detail.html', creator=creator, form1=form1, form2=form2, form3=form3)
    else:
        return render_template('error.html')


# Post a user's password change or display error message if some data was not entered correctly
@app.route(APP_PREFIX + '/web/my_pass_creator', methods=['POST'])
@login_required
def show_my_pass_creator():
    form1 = MailCreatorForm()
    form2 = PassCreatorForm()
    form3 = DelCreatorForm()
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()

    if creator:
        if form2.validate_on_submit():
            creator.creator_pass = generate_password_hash(request.form["password"], method='pbkdf2:sha256',
                                                          salt_length=16)
            db.session.commit()
            return redirect(url_for('show_my_creator'))
        else:
            form1.email.default = creator.creator_mail
            form1.description.default = creator.creator_desc
            form1.url.default = creator.creator_img
            form1.process()
            return render_template('account_detail.html', creator=creator, form1=form1, form2=form2, form3=form3)
    else:
        return render_template('error.html')


# Delete a user and return to the site index afterwards
@app.route(APP_PREFIX + '/web/my_del_creator', methods=['POST'])
@login_required
def show_my_del_creator():
    form1 = MailCreatorForm()
    form2 = PassCreatorForm()
    form3 = DelCreatorForm()
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()

    if creator:
        if form3.validate_on_submit():
            Creator.query.filter_by(creator_id=current_user.creator_id).delete()
            db.session.commit()
            logout_user()
            return redirect(url_for('show_index'))
        else:
            form1.email.default = creator.creator_mail
            form1.description.default = creator.creator_desc
            form1.url.default = creator.creator_img
            form1.process()
            return render_template('account_detail.html', creator=creator, form1=form1, form2=form2, form3=form3)
    else:
        return render_template('error.html')


# Displays all available worlds
@app.route(APP_PREFIX + '/web/worlds', methods=['GET'])
def show_worlds():
    form = WorldForm()
    worlds_active = World.query.filter_by(archived=0).order_by(World.world_name.asc())
    worlds_archived = World.query.filter_by(archived=1).order_by(World.world_name.asc())
    return render_template('world.html', worlds_active=worlds_active, worlds_archived=worlds_archived, form=form)


# Post a new world - if it doesn't already exist
@app.route(APP_PREFIX + '/web/worlds', methods=['POST'])
@login_required
def show_worlds_p():
    if current_user.creator_id and current_user.creator_role == "creator":
        world_name = escape(request.form["name"])
        world = World.query.filter_by(world_name=world_name).first()

        if not world:
            world = World()
            world.world_name = world_name
            world.world_url = clean_url(request.form["url"])
            world.world_desc = escape(request.form["description"])
            world.world_img = clean_url(request.form["image"])
            world.creator_id = current_user.creator_id
            db.session.add(world)
            db.session.commit()
        return redirect(url_for('show_worlds'))
    else:
        return render_template('error.html')


# Shows information about a specific world
@app.route(APP_PREFIX + '/web/world/<int:world_id>', methods=['GET'])
def show_world(world_id):
    form = WorldForm()
    world = World.query.filter_by(world_id=world_id).first()
    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_name.asc())

        form.name.default = world.world_name
        form.url.default = world.world_url
        form.description.default = world.world_desc
        form.image.default = world.world_img
        form.process()
        return render_template('world_detail.html', world=world, creator=creator, rooms=rooms, form=form)
    else:
        return render_template('error.html')


# Post a change in a world's data
@app.route(APP_PREFIX + '/web/world/<int:world_id>', methods=['POST'])
@login_required
def show_world_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        world.world_name = clean_url(request.form["name"])
        world.world_url = clean_url(request.form["url"])
        world.world_desc = escape(request.form["description"])
        world.world_img = clean_url(request.form["image"])
        db.session.commit()
        return redirect(url_for('show_world', world_id=world.world_id))
    else:
        return render_template('error.html')


# Delete a specific world - and all included elements!!!
@app.route(APP_PREFIX + '/web/deleted_world/<int:world_id>', methods=['GET'])
@login_required
def show_deleted_world(world_id):
    World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).delete()
    db.session.commit()
    return redirect(url_for('show_worlds'))


# Switch the world's visibility - it may be open (solutions can be seen) or closed (no solutions can be seen)
@app.route(APP_PREFIX + '/web/switched_world/<int:world_id>', methods=['GET'])
@login_required
def show_switched_world(world_id):
    world = World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).first()
    if world:
        if world.visible == 1:
            world.visible = 0
        else:
            world.visible = 1
        db.session.commit()

        return redirect(url_for('show_world', world_id=world.world_id))
    else:
        return render_template('error.html')


# Archive a specific world - archived worlds are not shown on the site index page
@app.route(APP_PREFIX + '/web/archived_world/<int:world_id>', methods=['GET'])
@login_required
def show_archived_world(world_id):
    world = World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).first()
    if world:
        if world.archived == 1:
            world.archived = 0
        else:
            world.archived = 1
        db.session.commit()

        return redirect(url_for('show_world', world_id=world.world_id))
    else:
        return render_template('error.html')


# Switch the world's mode - it may be Kringle (containing additional elements) or Standard (missing items, persons, etc)
@app.route(APP_PREFIX + '/web/reduced_world/<int:world_id>', methods=['GET'])
@login_required
def show_reduced_world(world_id):
    world = World.query.filter_by(world_id=world_id).filter_by(creator_id=current_user.creator_id).first()
    if world:
        if world.reduced == 1:
            world.reduced = 0
        else:
            world.reduced = 1
        db.session.commit()

        if 'world_id' in session and session['world_id'] == world_id:
            session['reduced'] = world.reduced

        return redirect(url_for('show_world', world_id=world.world_id))
    else:
        return render_template('error.html')


# Displays all available rooms
@app.route(APP_PREFIX + '/web/rooms/<int:world_id>', methods=['GET'])
def show_rooms(world_id):
    form = RoomForm()
    world = World.query.filter_by(world_id=world_id).first()

    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_name.asc())
        return render_template('room.html', rooms=rooms, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a new room - if it doesn't already exist
@app.route(APP_PREFIX + '/web/rooms/<int:world_id>', methods=['POST'])
@login_required
def show_rooms_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        room_name = escape(request.form["name"])
        room = Room.query.filter_by(room_name=room_name).filter_by(world_id=world_id).first()

        if not room:
            room = Room()
            room.room_name = room_name
            room.room_desc = escape(request.form["description"])
            room.room_img = clean_url(request.form["image"])
            room.world_id = world_id
            db.session.add(room)
            db.session.commit()
        return redirect(url_for('show_rooms', world_id=world.world_id))
    else:
        return render_template('error.html')


# Shows information about a specific room - and links to all attached elements
@app.route(APP_PREFIX + '/web/room/<int:room_id>', methods=['GET'])
def show_room(room_id):
    form = RoomForm()
    room = Room.query.filter_by(room_id=room_id).first()

    if room:
        world = World.query.filter_by(world_id=room.world_id).first()
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        objectives = Objective.query.filter_by(world_id=world.world_id).filter_by(room_id=room.room_id).order_by(
                Objective.objective_title.asc())
        items = Item.query.filter_by(world_id=world.world_id).filter_by(room_id=room.room_id).order_by(
                Item.item_name.asc())
        persons = Person.query.filter_by(world_id=world.world_id).filter_by(room_id=room.room_id).order_by(
                Person.person_name.asc())
        junctions = Junction.query.filter_by(world_id=world.world_id).filter_by(room_id=room.room_id).order_by(
                Junction.junction_id.asc())

        form.name.default = room.room_name
        form.description.default = room.room_desc
        form.image.default = room.room_img
        form.process()
        return render_template('room_detail.html', room=room, world=world, creator=creator, objectives=objectives,
                               items=items, persons=persons, junctions=junctions, form=form)
    else:
        return render_template('error.html')


# Post a change in a room's data
@app.route(APP_PREFIX + '/web/room/<int:room_id>', methods=['POST'])
@login_required
def show_room_p(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    world = World.query.filter_by(world_id=room.world_id).first()

    if room and current_user.creator_id and current_user.creator_id == world.creator_id:
        room.room_name = escape(request.form["name"])
        room.room_desc = escape(request.form["description"])
        room.room_img = clean_url(request.form["image"])
        db.session.commit()
        return redirect(url_for('show_room', room_id=room.room_id))
    else:
        return render_template('error.html')


# Delete a specific room - and all included elements!!!
@app.route(APP_PREFIX + '/web/deleted_room/<int:room_id>', methods=['GET'])
@login_required
def show_deleted_room(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    world = World.query.filter_by(world_id=room.world_id).first()

    if room and current_user.creator_id and current_user.creator_id == world.creator_id:
        Room.query.filter_by(room_id=room_id).delete()
        db.session.commit()

        return redirect(url_for('show_rooms', world_id=session['world_id']))
    else:
        return render_template('error.html')


# Displays all available items
@app.route(APP_PREFIX + '/web/items/<int:world_id>', methods=['GET'])
def show_items(world_id):
    form = ItemForm()
    world = World.query.filter_by(world_id=world_id).first()

    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
        items = Item.query.filter_by(world_id=world_id).order_by(Item.item_name.asc())

        form.room.choices = get_rooms_choices(rooms)

        return render_template('item.html', items=items, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a new item - if it doesn't already exist
@app.route(APP_PREFIX + '/web/items/<int:world_id>', methods=['POST'])
@login_required
def show_items_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        item_name = escape(request.form["name"])
        item = Item.query.filter_by(item_name=item_name).filter_by(world_id=world_id).first()

        if not item:
            item = Item()
            item.item_name = item_name
            item.item_desc = escape(request.form["description"])
            item.item_img = clean_url(request.form["image"])
            item.world_id = world_id
            item.room_id = escape(request.form["room"])
            db.session.add(item)
            db.session.commit()
        return redirect(url_for('show_items', world_id=world.world_id))
    else:
        return render_template('error.html')


# Shows information about a specific item
@app.route(APP_PREFIX + '/web/item/<int:item_id>', methods=['GET'])
def show_item(item_id):
    form = ItemForm()
    item = Item.query.filter_by(item_id=item_id).first()

    if item:
        room = Room.query.filter_by(room_id=item.room_id).first()
        world = World.query.filter_by(world_id=item.world_id).first()
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()

        rooms = Room.query.filter_by(world_id=world.world_id).order_by(Room.room_id.asc())

        form.name.default = item.item_name
        form.description.default = item.item_desc
        form.image.default = item.item_img
        form.room.choices = get_rooms_choices(rooms)
        form.room.default = item.room_id
        form.process()

        return render_template('item_detail.html', item=item, room=room, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a change in am item's data
@app.route(APP_PREFIX + '/web/item/<int:item_id>', methods=['POST'])
@login_required
def show_item_p(item_id):
    item = Item.query.filter_by(item_id=item_id).first()
    world = World.query.filter_by(world_id=item.world_id).first()

    if item and current_user.creator_id and current_user.creator_id == world.creator_id:
        item.item_name = escape(request.form["name"])
        item.item_desc = escape(request.form["description"])
        item.item_img = clean_url(request.form["image"])
        item.room_id = escape(request.form["room"])
        db.session.commit()

        return redirect(url_for('show_item', item_id=item.item_id))
    else:
        return render_template('error.html')


# Delete a specific item
@app.route(APP_PREFIX + '/web/deleted_item/<int:item_id>', methods=['GET'])
@login_required
def show_deleted_item(item_id):
    item = Item.query.filter_by(item_id=item_id).first()
    world = World.query.filter_by(world_id=item.world_id).first()

    if item and current_user.creator_id and current_user.creator_id == world.creator_id:
        Item.query.filter_by(item_id=item_id).delete()
        db.session.commit()

        return redirect(url_for('show_items', world_id=session['world_id']))
    else:
        return render_template('error.html')


# Displays all available persons
@app.route(APP_PREFIX + '/web/persons/<int:world_id>', methods=['GET'])
def show_persons(world_id):
    form = PersonForm()
    world = World.query.filter_by(world_id=world_id).first()

    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
        persons = Person.query.filter_by(world_id=world_id).order_by(Person.person_name.asc())

        form.room.choices = get_rooms_choices(rooms)

        return render_template('person.html', persons=persons, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a new person - if it doesn't already exist
@app.route(APP_PREFIX + '/web/persons/<int:world_id>', methods=['POST'])
@login_required
def show_persons_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        person_name = escape(request.form["name"])
        person = Person.query.filter_by(person_name=person_name).filter_by(world_id=world_id).first()

        if not person:
            person = Person()
            person.person_name = person_name
            person.person_desc = escape(request.form["description"])
            person.person_img = clean_url(request.form["image"])
            person.world_id = world_id
            person.room_id = escape(request.form["room"])
            db.session.add(person)
            db.session.commit()
        return redirect(url_for('show_persons', world_id=world.world_id))
    else:
        return render_template('error.html')


# Shows information about a specific person
@app.route(APP_PREFIX + '/web/person/<int:person_id>', methods=['GET'])
def show_person(person_id):
    form = PersonForm()
    person = Person.query.filter_by(person_id=person_id).first()

    if person:
        room = Room.query.filter_by(room_id=person.room_id).first()
        world = World.query.filter_by(world_id=person.world_id).first()
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()

        rooms = Room.query.filter_by(world_id=world.world_id).order_by(Room.room_id.asc())

        form.name.default = person.person_name
        form.description.default = person.person_desc
        form.image.default = person.person_img
        form.room.choices = get_rooms_choices(rooms)
        form.room.default = person.room_id
        form.process()

        return render_template('person_detail.html', person=person, room=room, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a change in a person's data
@app.route(APP_PREFIX + '/web/person/<int:person_id>', methods=['POST'])
@login_required
def show_person_p(person_id):
    person = Person.query.filter_by(person_id=person_id).first()
    world = World.query.filter_by(world_id=person.world_id).first()

    if person and current_user.creator_id and current_user.creator_id == world.creator_id:
        person.person_name = escape(request.form["name"])
        person.person_desc = escape(request.form["description"])
        person.person_img = clean_url(request.form["image"])
        person.room_id = escape(request.form["room"])
        db.session.commit()

        return redirect(url_for('show_person', person_id=person.person_id))
    else:
        return render_template('error.html')


# Delete a specific person
@app.route(APP_PREFIX + '/web/deleted_person/<int:person_id>', methods=['GET'])
@login_required
def show_deleted_person(person_id):
    person = Person.query.filter_by(person_id=person_id).first()
    world = World.query.filter_by(world_id=person.world_id).first()

    if person and current_user.creator_id and current_user.creator_id == world.creator_id:
        Person.query.filter_by(person_id=person_id).delete()
        db.session.commit()

        return redirect(url_for('show_persons', world_id=session['world_id']))
    else:
        return render_template('error.html')


# Displays all available objectives
@app.route(APP_PREFIX + '/web/objectives/<int:world_id>', methods=['GET'])
def show_objectives(world_id):
    form = ObjectiveForm()
    world = World.query.filter_by(world_id=world_id).first()

    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
        objectives = Objective.query.filter_by(world_id=world_id).order_by(Objective.objective_title.asc())
        items = Item.query.filter_by(world_id=world_id).order_by(Item.item_name.asc())

        solved_solutions = dict()
        solved_percentage = "0"
        if current_user.is_authenticated:
            solutions = Solution.query.filter_by(creator_id=current_user.creator_id).order_by(Solution.solution_id.asc())
            counter_solved = 0
            for objective in objectives:
                for solution in solutions:
                    if objective.objective_id == solution.objective_id:
                        solved_solutions[objective.objective_id] = 1
                        counter_solved = counter_solved + 1
            solved_percentage = str(int((counter_solved / objectives.count()) * 100))

        form.room.choices = get_rooms_choices(rooms)
        if world.reduced == 0:
            form.supported.choices = get_objectives_choices(objectives)
            form.requires.choices = get_items_choices(items)
        else:
            form.supported.choices = ["none"]
            form.requires.choices = ["none"]

        return render_template('objective.html', objectives=objectives, world=world, creator=creator,
                               solved_solutions=solved_solutions, solved_percentage=solved_percentage, form=form)


# Post a new objective - if it doesn't already exist
@app.route(APP_PREFIX + '/web/objectives/<int:world_id>', methods=['POST'])
@login_required
def show_objectives_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        objective_name = escape(request.form["name"])
        objective = Objective.query.filter_by(objective_name=objective_name).filter_by(world_id=world_id).first()

        if not objective:
            objective = Objective()
            objective.objective_name = objective_name
            objective.objective_title = escape(request.form["title"])
            objective.difficulty = escape(request.form["difficulty"])
            objective.objective_url = clean_url(request.form["url"])
            objective.supported_by = escape(request.form["supported"])
            objective.requires = escape(request.form["requires"])
            objective.objective_desc = escape(request.form["description"])
            objective.objective_img = clean_url(request.form["image"])
            objective.world_id = world_id
            objective.room_id = escape(request.form["room"])
            db.session.add(objective)
            db.session.commit()
        return redirect(url_for('show_objectives', world_id=world.world_id))
    else:
        return render_template('error.html')


# Shows information about a specific objective - including its quest and solutions
@app.route(APP_PREFIX + '/web/objective/<int:objective_id>', methods=['GET'])
def show_objective(objective_id):
    form = ObjectiveForm()
    objective = Objective.query.filter_by(objective_id=objective_id).first()

    if objective:
        room = Room.query.filter_by(room_id=objective.room_id).first()
        solutions = Solution.query.filter_by(objective_id=objective_id).filter_by(visible=1).order_by(
            Solution.solution_id.asc())
        world = World.query.filter_by(world_id=room.world_id).first()
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()

        rooms = Room.query.filter_by(world_id=world.world_id).order_by(Room.room_id.asc())
        objectives = Objective.query.filter_by(world_id=world.world_id).order_by(Objective.objective_title.asc())
        items = Item.query.filter_by(world_id=world.world_id).order_by(Item.item_name.asc())

        solved_solution = 0
        if current_user.is_authenticated:
            my_solutions = Solution.query.filter_by(creator_id=current_user.creator_id).order_by(Solution.solution_id.asc())
            for my_solution in my_solutions:
                if objective.objective_id == my_solution.objective_id:
                    solved_solution = 1

        voting_all = dict()
        creator_all = dict()
        for solution in solutions:
            voting_count = Voting.query.filter_by(solution_id=solution.solution_id).filter_by(rating=1).count()
            creator_name = Creator.query.filter_by(creator_id=solution.creator_id).first().creator_name
            voting_all[solution.solution_id] = voting_count
            creator_all[solution.solution_id] = creator_name

        if objective.quest is not None:
            md_quest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
            md_quest = md_quest.replace("<img src=", "<img class=\"img-fluid\" src=")
        else:
            md_quest = ""

        form.name.default = objective.objective_name
        form.title.default = objective.objective_title
        form.difficulty.default = objective.difficulty
        form.url.default = objective.objective_url
        form.supported.choices = get_objectives_choices(objectives)
        form.supported.default = objective.supported_by
        form.supported.default = objective.supported_by
        form.requires.choices = get_items_choices(items)
        form.requires.default = objective.requires
        form.requires.default = objective.requires
        form.description.default = objective.objective_desc
        form.image.default = objective.objective_img
        form.room.choices = get_rooms_choices(rooms)
        form.room.default = objective.room_id
        form.process()

        return render_template('objective_detail.html', objective=objective, md_quest=md_quest, solutions=solutions,
                               world=world, voting_all=voting_all, creator_all=creator_all, room=room, creator=creator,
                               solved_solution=solved_solution, form=form)
    else:
        return render_template('error.html')


# Post a change in an objective's data
@app.route(APP_PREFIX + '/web/objective/<int:objective_id>', methods=['POST'])
@login_required
def show_objective_p(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    world = World.query.filter_by(world_id=objective.world_id).first()

    if objective and current_user.creator_id and current_user.creator_id == world.creator_id:
        objective.objective_name = escape(request.form["name"])
        objective.objective_title = escape(request.form["title"])
        objective.difficulty = escape(request.form["difficulty"])
        objective.objective_url = clean_url(request.form["url"])
        objective.supported_by = escape(request.form["supported"])
        objective.requires = escape(request.form["requires"])
        objective.objective_desc = escape(request.form["description"])
        objective.objective_img = clean_url(request.form["image"])
        objective.room_id = escape(request.form["room"])
        db.session.commit()
        return redirect(url_for('show_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')


# Delete a specific objective - and all included elements!!!
@app.route(APP_PREFIX + '/web/deleted_objective/<int:objective_id>', methods=['GET'])
@login_required
def show_deleted_objective(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    world = World.query.filter_by(world_id=objective.world_id).first()

    if objective and current_user.creator_id and current_user.creator_id == world.creator_id:
        Objective.query.filter_by(objective_id=objective_id).delete()
        db.session.commit()

        return redirect(url_for('show_objectives', world_id=session['world_id']))
    else:
        return render_template('error.html')


# Displays all available junctions
@app.route(APP_PREFIX + '/web/junctions/<int:world_id>', methods=['GET'])
def show_junctions(world_id):
    form = JunctionForm()
    world = World.query.filter_by(world_id=world_id).first()

    if world:
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()
        rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
        junctions = Junction.query.filter_by(world_id=world_id).order_by(Junction.junction_id.asc())

        form.room.choices = get_rooms_choices(rooms)
        form.room_dest.choices = get_rooms_choices(rooms)

        return render_template('junction.html', junctions=junctions, world=world, creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a new junction - if it doesn't already exist
@app.route(APP_PREFIX + '/web/junctions/<int:world_id>', methods=['POST'])
@login_required
def show_junctions_p(world_id):
    world = World.query.filter_by(world_id=world_id).first()

    if world and current_user.creator_id and current_user.creator_id == world.creator_id:
        junction_room = escape(request.form["room"])
        junction_room_dest = escape(request.form["room_dest"])

        junction = Junction.query.filter_by(room_id=junction_room).filter_by(dest_id=junction_room_dest).filter_by(
                world_id=world_id).first()

        if not junction:
            junction = Junction()
            junction.junction_desc = escape(request.form["description"])
            junction.world_id = world_id
            junction.room_id = escape(request.form["room"])
            junction.dest_id = escape(request.form["room_dest"])
            db.session.add(junction)
            db.session.commit()
        return redirect(url_for('show_junctions', world_id=world.world_id))
    else:
        return render_template('error.html')


# Shows information about a specific junction
@app.route(APP_PREFIX + '/web/junction/<int:junction_id>', methods=['GET'])
def show_junction(junction_id):
    form = JunctionForm()
    junction = Junction.query.filter_by(junction_id=junction_id).first()

    if junction:
        room = Room.query.filter_by(room_id=junction.room_id).first()
        room_dest = Room.query.filter_by(room_id=junction.dest_id).first()
        world = World.query.filter_by(world_id=junction.world_id).first()
        update_session(world)
        creator = Creator.query.filter_by(creator_id=world.creator_id).first()

        rooms = Room.query.filter_by(world_id=world.world_id).order_by(Room.room_id.asc())

        form.description.default = junction.junction_desc
        form.room.choices = get_rooms_choices(rooms)
        form.room_dest.choices = get_rooms_choices(rooms)
        form.room.default = junction.room_id
        form.room_dest.default = junction.dest_id
        form.process()

        return render_template('junction_detail.html', junction=junction, room=room, room_dest=room_dest, world=world,
                               creator=creator, form=form)
    else:
        return render_template('error.html')


# Post a change in a junction's data
@app.route(APP_PREFIX + '/web/junction/<int:junction_id>', methods=['POST'])
@login_required
def show_junction_p(junction_id):
    junction = Junction.query.filter_by(junction_id=junction_id).first()
    world = World.query.filter_by(world_id=junction.world_id).first()

    if junction and current_user.creator_id and current_user.creator_id == world.creator_id:
        junction.junction_desc = escape(request.form["description"])
        junction.room_id = escape(request.form["room"])
        junction.dest_id = escape(request.form["room_dest"])
        db.session.commit()

        return redirect(url_for('show_junction', junction_id=junction.junction_id))
    else:
        return render_template('error.html')


# Delete a specific junction
@app.route(APP_PREFIX + '/web/deleted_junction/<int:junction_id>', methods=['GET'])
@login_required
def show_deleted_junction(junction_id):
    junction = Junction.query.filter_by(junction_id=junction_id).first()
    world = World.query.filter_by(world_id=junction.world_id).first()

    if junction and current_user.creator_id and current_user.creator_id == world.creator_id:
        Junction.query.filter_by(junction_id=junction_id).delete()
        db.session.commit()

        return redirect(url_for('show_junctions', world_id=session['world_id']))
    else:
        return render_template('error.html')


# Shows or posts an objective's challenge to be solved (aka quest)
@app.route(APP_PREFIX + '/web/quest/<int:objective_id>', methods=['GET', 'POST'])
@login_required
def show_quest(objective_id):
    form = QuestSolForm()
    if request.method == 'POST':
        objective = Objective.query.filter_by(objective_id=objective_id).first()
        if objective:
            room = Room.query.filter_by(room_id=objective.room_id).first()
            world = World.query.filter_by(world_id=room.world_id).first()
            update_session(world)

            if world.creator_id == current_user.creator_id:
                objective.quest = request.form["quest"].encode()
                db.session.commit()
            return redirect(url_for('show_objective', objective_id=objective.objective_id))
        else:
            return render_template('error.html')
    else:
        objective = Objective.query.filter_by(objective_id=objective_id).first()
        contents = list_files(BUCKET_PUBLIC, current_user.creator_name)
        if objective:
            room = Room.query.filter_by(room_id=objective.room_id).first()
            world = World.query.filter_by(world_id=room.world_id).first()

            if world.creator_id == current_user.creator_id:
                if objective.quest is not None:
                    return render_template('quest_detail.html', quest=str(bytes(objective.quest), 'utf-8'),
                                           objective_id=objective_id, world_id=objective.world_id, contents=contents,
                                           form=form)
                else:
                    return render_template('quest_detail.html', quest="", objective_id=objective_id,
                                           world_id=objective.world_id, contents=contents, form=form)
            else:
                return redirect(url_for('show_objective', objective_id=objective.objective_id))
        else:
            return render_template('error.html')


# Shows other users' solutions - if the solution and world is open/public
@app.route(APP_PREFIX + '/web/solution/<int:solution_id>', methods=['GET'])
def show_solution(solution_id):
    solution = Solution.query.filter_by(solution_id=solution_id).first()
    if solution:
        objective = Objective.query.filter_by(objective_id=solution.objective_id).first()
        world = World.query.filter_by(world_id=objective.world_id).first()
        update_session(world)

        if solution.visible == 1 and world.visible == 1:
            if solution.solution_text is not None:
                md_solution = markdown2.markdown(str(bytes(solution.solution_text), 'utf-8'),
                                                 extras=['fenced-code-blocks'])
                md_solution = md_solution.replace("<img src=", "<img class=\"img-fluid\" src=")

                return render_template('solution_detail.html', md_solution=md_solution, solution=solution,
                                       objective=objective)
            else:
                return render_template('solution_detail.html', md_solution="", solution=solution, objective=objective)
        else:
            return redirect(url_for('show_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')


# Like/Unlike other users' solutions and return to its objective page afterwards
@app.route(APP_PREFIX + '/web/liked_solution/<int:solution_id>', methods=['GET'])
@login_required
def show_liked_solution(solution_id):
    voting = Voting.query.filter_by(solution_id=solution_id).filter_by(creator_id=current_user.creator_id).first()
    solution = Solution.query.filter_by(solution_id=solution_id).first()
    if solution:
        objective = Objective.query.filter_by(objective_id=solution.objective_id).first()
        if voting:
            if voting.rating == 0:
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

        return redirect(url_for('show_objective', objective_id=objective.objective_id))
    else:
        return render_template('error.html')


# Shows or posts an objective's solution
@app.route(APP_PREFIX + '/web/my_solution/<int:objective_id>', methods=['GET', 'POST'])
@login_required
def show_my_solution(objective_id):
    form = QuestSolForm()
    if request.method == 'POST':
        objective = Objective.query.filter_by(objective_id=objective_id).first()
        if objective:
            solution = Solution.query.filter_by(objective_id=objective_id).filter_by(
                creator_id=current_user.creator_id).first()
            if solution is not None:
                db.session.delete(solution)
                db.session.commit()

            solution_new = Solution()
            solution_new.objective_id = objective_id
            solution_new.creator_id = current_user.creator_id
            solution_new.solution_text = request.form["solution"].encode()
            if 'visible' in request.form:
                solution_new.visible = 1
            db.session.add(solution_new)
            db.session.commit()

            return redirect(url_for('show_objective', objective_id=objective.objective_id))
        else:
            return render_template('error.html')
    else:
        objective = Objective.query.filter_by(objective_id=objective_id).first()
        contents = list_files(BUCKET_PUBLIC, current_user.creator_name)
        if objective:
            world = World.query.filter_by(world_id=objective.world_id).first()
            creator = Creator.query.filter_by(creator_id=world.creator_id).first()
            if objective.quest is not None:
                md_quest = markdown2.markdown(str(bytes(objective.quest), 'utf-8'), extras=['fenced-code-blocks'])
                md_quest = md_quest.replace("<img src=", "<img class=\"img-fluid\" src=")
            else:
                md_quest = ""

            solution = Solution.query.filter_by(objective_id=objective_id).filter_by(
                creator_id=current_user.creator_id).first()
            if solution is not None:
                return render_template('solution_my_detail.html', solution=str(bytes(solution.solution_text), 'utf-8'),
                                       visible=solution.visible, md_quest=md_quest, objective_id=objective_id,
                                       world_id=objective.world_id, creator=creator, contents=contents, form=form)
            else:
                return render_template('solution_my_detail.html', solution="", visible=0, md_quest=md_quest,
                                       objective_id=objective_id, world_id=objective.world_id, creator=creator,
                                       contents=contents, form=form)
        else:
            return render_template('error.html')


# Delete a specific solution
@app.route(APP_PREFIX + '/web/my_deleted_solution/<int:objective_id>', methods=['GET'])
@login_required
def show_deleted_solution(objective_id):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if objective:
        solution = Solution.query.filter_by(objective_id=objective_id).filter_by(
            creator_id=current_user.creator_id).first()
        if solution is not None:
            db.session.delete(solution)
            db.session.commit()

        return redirect(url_for('show_objective', objective_id=objective_id))
    else:
        return render_template('error.html')


# Shows a full report containing information about the world, its objectives and solutions in different formats
@app.route(APP_PREFIX + '/web/report/<string:format_type>/<int:world_id>', methods=['GET'])
@login_required
def show_report(world_id, format_type):
    world = World.query.filter_by(world_id=world_id).first()
    creator = Creator.query.filter_by(creator_id=current_user.creator_id).first()
    rooms = Room.query.filter_by(world_id=world_id).order_by(Room.room_id.asc())
    objectives = Objective.query.filter_by(world_id=world_id).order_by(Objective.objective_id.asc())
    items = Item.query.filter_by(world_id=world_id).order_by(Item.item_id.asc())
    md_quests = dict()
    md_solutions = dict()
    for objective in objectives:
        if objective.quest is not None:
            md_quests[objective.objective_id] = str(bytes(objective.quest), 'utf-8')
        else:
            md_quests[objective.objective_id] = ""

        solution = Solution.query.filter_by(objective_id=objective.objective_id).filter_by(
            creator_id=current_user.creator_id).first()
        if solution is not None:
            md_solutions[objective.objective_id] = str(bytes(solution.solution_text), 'utf-8')
        else:
            md_solutions[objective.objective_id] = ""

    folder_name = f"{DOWNLOAD_FOLDER}/{current_user.creator_name}"

    if world.reduced == 0:
        template_file = "report_kringle.md"
    else:
        template_file = "report_standard.md"

    if format_type == "markdown":
        local_file = os.path.join(folder_name, template_file)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        with open(local_file, 'w') as f:
            f.write(render_template(template_file, world=world, rooms=rooms, objectives=objectives, items=items,
                                    md_quests=md_quests, md_solutions=md_solutions, creator=creator))
        return send_file(local_file, attachment_filename=template_file, as_attachment=True)
    else:
        md_report = markdown2.markdown(
            render_template(template_file, world=world, rooms=rooms, objectives=objectives, items=items,
                            md_quests=md_quests, md_solutions=md_solutions, creator=creator),
            extras=['fenced-code-blocks'])

        md_report = re.sub('<h2>(.*?)</h2>', '<h2 id="\\1">\\1</h2>',
                           re.sub('<h1>(.*?)</h1>', '<h1 id="\\1">\\1</h1>', md_report))

        md_report = md_report.replace("<img src=", "<img class=\"img-fluid\" src=")

        return render_template('report.html', md_report=md_report)


# Show a report containing information about a specific objective and its solution in different formats
@app.route(APP_PREFIX + '/web/report_single/<string:format_type>/<int:objective_id>', methods=['GET'])
@login_required
def show_report_single(objective_id, format_type):
    objective = Objective.query.filter_by(objective_id=objective_id).first()
    if objective:
        if objective.quest is not None:
            md_quest = str(bytes(objective.quest), 'utf-8')
        else:
            md_quest = ""

        solution = Solution.query.filter_by(objective_id=objective.objective_id).filter_by(
            creator_id=current_user.creator_id).first()
        if solution is not None:
            md_solution = str(bytes(solution.solution_text), 'utf-8')
        else:
            md_solution = ""

        folder_name = f"{DOWNLOAD_FOLDER}/{current_user.creator_name}"

        template_file = "report_single.md"

        if format_type == "markdown":
            local_file = os.path.join(folder_name, template_file)
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            with open(local_file, 'w') as f:
                f.write(render_template(template_file, objective=objective, md_quest=md_quest,
                                        md_solution=md_solution))
            return send_file(local_file, attachment_filename=template_file, as_attachment=True)
        else:
            md_report = markdown2.markdown(
                render_template(template_file, objective=objective, md_quest=md_quest,
                                md_solution=md_solution),
                extras=['fenced-code-blocks'])

            md_report = re.sub('<h2>(.*?)</h2>', '<h2 id="\\1">\\1</h2>',
                               re.sub('<h1>(.*?)</h1>', '<h1 id="\\1">\\1</h1>', md_report))

            md_report = md_report.replace("<img src=", "<img class=\"img-fluid\" src=")

            return render_template('report.html', md_report=md_report)
