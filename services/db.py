# Author: Yash Srivastava 
# File: services/db.py 
# Purpose: The only place SQL Server is touched (coding standard Section 6). 

import os 
import threading 
import pymssql 
from contextlib import contextmanager 
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "env", override=False)

_SERVER = os.getenv("DB_SERVER")       
_DATABASE = os.getenv("DB_NAME")      
_UID = os.getenv("DB_USER") 
_PWD = os.getenv("DB_PASSWORD") 
_PORT = os.getenv("DB_PORT", "1433") 

# Thread-local, NOT a shared global -- Flask's dev server (flask run) and any 
# real WSGI server handle requests on multiple threads. A single shared 
# pymssql connection object used concurrently by two threads corrupts the 
# TDS protocol stream and surfaces as a random 'OperationalError: Unknown 
# error' on whichever query loses the race (this is what was happening across 
# the Logs/Dashboard ajax calls firing in parallel on page load). Each thread 
# now gets its own connection, so concurrent requests can't collide. 
_local = threading.local() 

def _connect(): 
    conn = pymssql.connect( 
        server=_SERVER, 
        user=_UID, 
        password=_PWD, 
        database=_DATABASE, 
        port=int(_PORT),
        autocommit=True, 
        as_dict=True, 
        appname="",   
        charset="UTF-8",         
        tds_version="7.4",       
    ) 
    _local.conn = conn 
    return conn 

def _get_conn(force_new=False): 
    missing = [ 
        name for name, val in [ 
            ("DB_SERVER", _SERVER), 
            ("DB_NAME", _DATABASE), 
            ("DB_USER", _UID), 
            ("DB_PASSWORD", _PWD), 
        ] if not val 
    ] 
    if missing: 
        raise RuntimeError( 
            f"Missing required .env value(s): {', '.join(missing)}. " 
            f"Check that .env exists in the project root (next to app.py) " 
            f"and that load_dotenv() actually found it." 
        ) 
    if force_new or getattr(_local, "conn", None) is None: 
        return _connect() 
    return _local.conn 

def _run(op): 
    """Run op(conn) with one automatic reconnect-and-retry if the cached 
    connection turned out to be dead.""" 
    try: 
        return op(_get_conn()) 
    except (pymssql.OperationalError, pymssql.InterfaceError): 
        return op(_get_conn(force_new=True)) 

def query(sql, params=None): 
    """Execute any statement; returns cursor.rowcount. Use for statements with no result set.""" 
    def op(conn): 
        cur = conn.cursor() 
        cur.execute(sql, params or ()) 
        rc = cur.rowcount 
        cur.close() 
        return rc 
    return _run(op) 

def select(sql, params=None): 
    """Returns list[dict] for a SELECT.""" 
    def op(conn): 
        cur = conn.cursor(as_dict=True) 
        cur.execute(sql, params or ()) 
        rows = cur.fetchall() 
        cur.close() 
        return rows 
    return _run(op) 

def select_one(sql, params=None): 
    """Returns a single dict or None.""" 
    rows = select(sql, params) 
    return rows[0] if rows else None 

def insert(table, data: dict): 
    """data = {column: value}. Returns the inserted row via OUTPUT INSERTED.*.""" 
    def op(conn): 
        cols = ", ".join(data.keys()) 
        placeholders = ", ".join("%s" for _ in data) 
        sql = f"INSERT INTO {table} ({cols}) OUTPUT INSERTED.* VALUES ({placeholders})" 
        cur = conn.cursor(as_dict=True) 
        cur.execute(sql, tuple(data.values())) 
        row = cur.fetchone() 
        cur.close() 
        return row 
    return _run(op) 

def update(table, data: dict, where: str, where_params=None): 
    """data = {column: value}. `where` is a raw SQL fragment with %s placeholders.""" 
    set_clause = ", ".join(f"{k} = %s" for k in data) 
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}" 
    params = tuple(data.values()) + tuple(where_params or ()) 
    return query(sql, params) 

def delete(table, where: str, where_params=None): 
    sql = f"DELETE FROM {table} WHERE {where}" 
    return query(sql, tuple(where_params or ())) 

@contextmanager 
def begin_transaction(): 
    """Usage: with begin_transaction() as cur: cur.execute(...); cur.execute(...)""" 
    conn = _get_conn() 
    conn.autocommit(False) 
    cur = conn.cursor(as_dict=True) 
    try: 
        yield cur 
        conn.commit() 
    except Exception: 
        conn.rollback() 
        raise 
    finally: 
        cur.close() 
        conn.autocommit(True) 

def commit(): 
    _get_conn().commit() 

def rollback(): 
    _get_conn().rollback()
