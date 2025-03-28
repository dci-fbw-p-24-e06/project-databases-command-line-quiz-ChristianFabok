import psycopg2
import random
from psycopg2 import Error
from config import config


DB_CONFIG = {
    'dbname': 'quiz_db',
    'user': 'christian',
    'password': 'Chranton0708',
    'host': 'localhost',
    'port': '5432'
}

def connect_db():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def create_topic_table(topic):
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            table_name = topic.lower().replace(" ", "_")
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                module VARCHAR(100),
                submodule VARCHAR(100),
                difficulty_level INT CHECK (difficulty_level BETWEEN 1 AND 3),
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                wrong_answer1 TEXT NOT NULL,
                wrong_answer2 TEXT NOT NULL,
                wrong_answer3 TEXT,
                wrong_answer4 TEXT,
                wrong_answer5 TEXT
            );
            """
            cursor.execute(create_table_query)
            connection.commit()
            print(f"Table '{table_name}' created or already exists.")
        except Error as e:
            print(f"Error creating table: {e}")
        finally:
            cursor.close()
  