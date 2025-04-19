"""
Database utility functions for the Old Pension Adapter.
"""
import pymysql
from app.core.config import DB_CONFIG

def get_db_connection():
    """
    Get a database connection to the Old Pension System.
    Returns a PyMySQL connection.
    """
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise