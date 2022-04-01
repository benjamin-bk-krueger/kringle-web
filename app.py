import psycopg2 
from psycopg2 import Error 
from flask import Flask

app = Flask(__name__)

@app.route('/flask/hello')
def hello():
    content = '<h1>Hello, World!</h1><br><br>\n'
    try:
        # Connect to an existing database
        connection = psycopg2.connect(user="postgres",
                                    password="postgres",
                                    host="kringle_database",
                                    port="5432",
                                    database="postgres")

        # Create a cursor to perform database operations
        cursor = connection.cursor()
        # Executing a SQL query
        cursor.execute("SELECT version();")
        # Fetch result
        record = cursor.fetchone()
        content = content + "You are connected to - " + record + "<br>\n"

    except (Exception, Error) as error:
        return ("Error while connecting to PostgreSQL " + error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            content = content + "PostgreSQL connection is closed<br>\n"

    return content

