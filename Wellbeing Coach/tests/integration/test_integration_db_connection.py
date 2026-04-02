import pytest 
from app.db.db_connection import create_tables

@pytest.mark.integration
def test_creating_tables(db_connection):
    create_tables()
    
    cursor = db_connection.cursor()
    
    #check for mood analysis table
    cursor.execute("""
                    SELECT EXISTS (
                       SELECT FROM information_schema.tables
                       WHERE table_name = 'mood_analysis'
                    );
    """)
    
    assert cursor.fetchone()[0] is True
    
    #check for activities table
    cursor.execute("""
                    SELECT EXISTS (
                       SELECT FROM information_schema.tables
                       WHERE table_name = 'activities'
                    );
    """)
    
    assert cursor.fetchone()[0] is True
    
    #check for feedback table
    cursor.execute("""
                    SELECT EXISTS (
                       SELECT FROM information_schema.tables
                       WHERE table_name = 'feedback'
                    );
    """)
    
    assert cursor.fetchone()[0] is True
    
    cursor.close()