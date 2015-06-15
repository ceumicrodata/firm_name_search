# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sqlite3


class SqliteConstantMap(object):

    # Directly using dbapi, as an sqlalchemy experiment failed miserably.
    # SA was uncomparably slower when millions of key-values are stored.
    # autocommit was slow (not surprising, as it writes a lot).
    # Using batches of updates in a transaction was faster, but still too slow
    # compared to direct SQL.

    def __init__(self, database, tablename):
        self.TABLE = tablename
        self.db = sqlite3.connect(database)
        self.cursor = self.db.cursor()
        self.exists = bool(
            list(self.fetchall(self.sql_table_exists, tablename=self.TABLE)))
        if not self.exists:
            self.db.execute(self.sql_create)

    def add(self, key, value):
        assert not self.exists
        self.db.execute(self.sql_insert, dict(key=key, value=value))

    def create_index(self):
        assert not self.exists
        self.db.execute(self.sql_create_index)
        self.db.commit()
        self.exists = True

    def __getitem__(self, key):
        value_tuples = self.fetchall(self.sql_select, key=key)
        return set(value for value, in value_tuples)

    def fetchall(self, sql, **params):
        return self.cursor.execute(sql, params).fetchall()

    def drop(self):
        self.db.execute(self.sql_drop)
        self.exists = False

    # SQLs

    @property
    def sql_drop(self):
        return '''\
            DROP TABLE {};
        '''.format(self.TABLE)

    @property
    def sql_table_exists(self):
        return '''\
            SELECT name FROM sqlite_master WHERE type='table' AND name='{}';
        '''.format(self.TABLE)

    @property
    def sql_create(self):
        return '''
            CREATE TABLE IF NOT EXISTS {} (key varchar, value varchar);
        '''.format(self.TABLE)

    @property
    def sql_insert(self):
        return '''
            INSERT INTO {}(key, value) VALUES (:key, :value);
        '''.format(self.TABLE)

    @property
    def sql_select(self):
        return '''
            SELECT value FROM {} WHERE key = :key;
        '''.format(self.TABLE)

    @property
    def sql_create_index(self):
        return '''
            CREATE INDEX IF NOT EXISTS ix_{} ON {}(key);
        '''.format(self.TABLE, self.TABLE)
