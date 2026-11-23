"""
Database connection and execution helpers using mysql-connector-python.
All queries strictly use parameterized queries (%s) to prevent SQL injection.
Supports local MySQL, Railway, Render, TiDB Serverless, Aiven, and URL connection strings.
"""

import os
import urllib.parse
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for connection URLs first (common on Railway, Render, TiDB, etc.)
db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL') or os.getenv('MYSQL_PUBLIC_URL')

if db_url:
    try:
        parsed = urllib.parse.urlparse(db_url)
        DB_HOST = parsed.hostname
        DB_PORT = parsed.port or 3306
        DB_USER = parsed.username
        DB_PASSWORD = parsed.password
        DB_NAME = parsed.path.lstrip('/')
    except Exception:
        DB_HOST = '127.0.0.1'
        DB_PORT = 3306
        DB_USER = 'root'
        DB_PASSWORD = ''
        DB_NAME = 'dabba_db'
else:
    DB_HOST = os.getenv('DB_HOST') or os.getenv('MYSQLHOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT') or os.getenv('MYSQLPORT', '3306'))
    DB_USER = os.getenv('DB_USER') or os.getenv('MYSQLUSER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD', '')
    DB_NAME = os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE', 'dabba_db')

DB_SSL_DISABLED = os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true'

def get_connection():
    """Establish and return a new MySQL database connection."""
    kwargs = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME,
        'autocommit': False,
        'charset': 'utf8mb4'
    }
    if DB_SSL_DISABLED:
        kwargs['ssl_disabled'] = True
    elif DB_HOST not in ('127.0.0.1', 'localhost'):
        # For cloud MySQL like TiDB, Aiven, or Railway public, enable TLS/SSL
        kwargs['ssl_verify_cert'] = False
        kwargs['ssl_verify_identity'] = False
        
    return mysql.connector.connect(**kwargs)

def query_db(query, params=(), one=False, commit=False):
    """
    Execute a parameterized SQL query safely.
    :param query: SQL string containing %s placeholders
    :param params: tuple or list of parameters
    :param one: if True, returns a single dictionary row or None
    :param commit: if True, commits transaction and returns lastrowid / affected_rows
    :return: list of dicts, single dict, or dict with metadata if commit
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            cursor.close()
            return {'lastrowid': last_id, 'rowcount': affected}
        
        result = cursor.fetchall()
        cursor.close()
        return (result[0] if result else None) if one else result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def call_procedure(proc_name, args=()):
    """
    Call a MySQL stored procedure safely using parameterized arguments.
    :param proc_name: Stored procedure name
    :param args: list/tuple of IN, OUT parameters
    :return: dict of procedure return values
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        result = cursor.callproc(proc_name, args)
        conn.commit()
        cursor.close()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
