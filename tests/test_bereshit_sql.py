import pytest
import os
from bereshit.bereshit_sql import BereshitSQL

# Mock config for testing (replace with real config for integration)
db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'test_user',
    'password': 'test_pass',
    'dbname': 'test_db'
}

SQL_DIR = os.path.join(os.path.dirname(__file__), '../src/bereshit/sql')

@pytest.fixture
def bereshit():
    return BereshitSQL(db_config, db_type='postgresql', sql_dir=SQL_DIR)

def test_connect_and_close(bereshit):
    try:
        bereshit.connect()
        assert bereshit.conn is not None
    finally:
        bereshit.close()
        assert bereshit.conn is None or bereshit.conn.closed

def test_execute_sql(bereshit):
    bereshit.connect()
    try:
        # Simple test: create and drop a temp table
        bereshit.execute_sql('CREATE TEMP TABLE test_table (id INT);')
        bereshit.execute_sql('DROP TABLE test_table;')
    finally:
        bereshit.close()

def test_fetch_dataframe(bereshit):
    bereshit.connect()
    try:
        bereshit.execute_sql('CREATE TEMP TABLE test_table (id INT);')
        bereshit.execute_sql('INSERT INTO test_table (id) VALUES (1), (2), (3);')
        df = bereshit.fetch_dataframe('SELECT * FROM test_table;')
        assert df.shape[0] == 3
        bereshit.execute_sql('DROP TABLE test_table;')
    finally:
        bereshit.close()

def test_bootstrap_runs_without_error(bereshit):
    # This will run all bootstrap scripts in the SQL_DIR
    try:
        bereshit.bootstrap()
    except Exception as e:
        pytest.fail(f"Bootstrap failed: {e}")
