"""
Database initialization script for CraveBites.
Executes schema, seeds, procedures, triggers, and views safely into any local or cloud MySQL database.
Usage:
    python init_db.py
"""

import os
import re
import sys
from db import get_connection, DB_NAME, DB_HOST

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'database'))

def clean_sql(sql_text):
    """Remove CREATE DATABASE and USE statements to target current active database."""
    lines = []
    for line in sql_text.splitlines():
        trimmed = line.strip()
        if trimmed.upper().startswith('CREATE DATABASE'):
            continue
        if trimmed.upper().startswith('USE ') and ';' in trimmed:
            continue
        lines.append(line)
    return '\n'.join(lines)

def split_statements(sql_text):
    """
    Split SQL script into executable statements, properly respecting DELIMITER blocks.
    """
    delimiter = ';'
    statements = []
    current_statement = []
    
    for line in sql_text.splitlines():
        trimmed = line.strip()
        
        # Check for DELIMITER change
        if trimmed.upper().startswith('DELIMITER'):
            parts = trimmed.split()
            if len(parts) >= 2:
                delimiter = parts[1]
            continue
            
        if not trimmed or trimmed.startswith('--') or trimmed.startswith('/*'):
            continue
            
        current_statement.append(line)
        
        # Check if line ends with current delimiter
        if trimmed.endswith(delimiter):
            stmt = '\n'.join(current_statement)
            # Strip trailing delimiter
            if delimiter != ';':
                stmt = stmt[:stmt.rfind(delimiter)].strip()
            else:
                stmt = stmt.rstrip(';').strip()
                
            if stmt:
                statements.append(stmt)
            current_statement = []
            
    if current_statement:
        stmt = '\n'.join(current_statement).strip().rstrip(';')
        if stmt:
            statements.append(stmt)
            
    return statements

def run_script(conn, filename):
    filepath = os.path.join(DB_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[-] File not found: {filepath}")
        return False
        
    print(f"[*] Executing {filename}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    cleaned = clean_sql(content)
    statements = split_statements(cleaned)
    cursor = conn.cursor()
    
    success = 0
    errors = 0
    
    for i, stmt in enumerate(statements, 1):
        try:
            cursor.execute(stmt)
            success += 1
        except Exception as e:
            err_msg = str(e)
            # Ignore duplicate key or already exists errors gracefully
            if "already exists" in err_msg or "Duplicate" in err_msg:
                success += 1
            else:
                print(f"    [!] Error in statement {i}: {e}")
                errors += 1
                
    conn.commit()
    cursor.close()
    print(f"[+] Completed {filename}: {success} statements executed ({errors} errors).")
    return errors == 0

def main():
    print("=" * 60)
    print(f"  🍱 CraveBites Database Initializer")
    print(f"  Target Host: {DB_HOST} | Database: {DB_NAME}")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("[+] Successfully connected to MySQL database!")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        sys.exit(1)
        
    try:
        # Run schema, seeds, procedures/triggers, views
        run_script(conn, 'schema.sql')
        run_script(conn, 'seed.sql')
        run_script(conn, 'triggers_procedures.sql')
        run_script(conn, 'views.sql')
        print("\n" + "=" * 60)
        print("  🎉 DATABASE FULLY INITIALIZED AND READY!")
        print("=" * 60)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
