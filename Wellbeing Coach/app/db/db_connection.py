import psycopg2
import os
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        raise Exception(e)

def create_tables():
    try:
        connection = get_connection()
        curr = connection.cursor()
        
        curr.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """)
        
        curr.execute("""
        CREATE TABLE IF NOT EXISTS mood_analysis (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_input TEXT NOT NULL,
            mood VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        curr.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            mood VARCHAR(50),
            instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        curr.execute("""
        CREATE TABLE IF NOT EXISTS feedback(
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            activity_id UUID,
            rating INT,
            effective BOOLEAN,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities(activity_id)
        );
        """)
        
    except Exception as e:
        raise Exception(e)
    
    connection.commit()
    
    curr.close()
    connection.close()