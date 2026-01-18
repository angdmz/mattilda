#!/usr/bin/env python3
"""Initialize test database before running tests."""
import os
import time
import psycopg2
from psycopg2 import sql


def main():
    user = os.environ['DB_USERNAME']
    password = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOSTNAME']
    port = int(os.environ['DB_PORT'])
    test_db = os.environ['DB_NAME']
    
    for i in range(30):
        try:
            conn = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                dbname='postgres'
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (test_db,))
            exists = cur.fetchone() is not None
            
            if not exists:
                cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(test_db)))
                print(f"Created database: {test_db}")
            else:
                print(f"Database already exists: {test_db}")
            
            cur.close()
            conn.close()
            return
        except Exception as e:
            if i == 29:
                raise RuntimeError(f"Database not ready after 30 attempts: {e}")
            time.sleep(1)


if __name__ == '__main__':
    main()
