from os import getenv

import mysql.connector
from dotenv import load_dotenv

load_dotenv("password.env")

USER = getenv("USER_DATABASE")
PASSWORD = getenv("PASSWORD")
HOST = getenv("HOST")
DATABASE = getenv("DATABASE")


class MySQLWrapper:
    """
    Small wrapper for mysql.connector, so I can use magic with statement. Because readibility counts!
    """

    def __init__(self, **credentials):
        if not credentials:
            self.credentials = {"user": USER, "password": PASSWORD, "host": HOST, "database": DATABASE}
        else:
            self.credentials = credentials
        self.database = None
        self.cursor = None

    def __enter__(self):
        self.database = mysql.connector.connect(**self.credentials)
        self.cursor = self.database.cursor()
        return self

    def __exit__(self, exception_type, exception_val, trace):
        try:
            self.cursor.close()
            self.database.close()

        except AttributeError:
            print('Not closable.')
            return True

    def query(self, query: str, val=None):
        """
        Query of database. Returns list tuples from database.
        :param query: str
        :param val: Optional
        :return: list of tuples
        """
        self.cursor.execute(query, val or ())
        return self.cursor.fetchall()

    def execute(self, query, val=None, commit=False):
        """
        Execute your values and commit them. Or not. Your decision.
        :param query: str
        :param val: Optional
        :param commit: bool
        :return: None
        """
        self.cursor.execute(query, val or ())
        if commit:
            self.database.commit()
