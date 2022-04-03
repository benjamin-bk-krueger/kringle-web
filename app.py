import psycopg2 
from psycopg2 import Error 
from flask import Flask, render_template

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

@app.route('/flask/room'), methods = ['GET'])
def get_all_rooms():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM room;')
    rooms = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('room.html', rooms=rooms)

@app.route('/flask/room/<int:num>', methods = ['GET'])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM room where room_id = {num};')
    rooms = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('room.html', rooms=rooms)