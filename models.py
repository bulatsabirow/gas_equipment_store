import psycopg2


class BaseSelector:
    @staticmethod
    def select(cursor, query):
        cursor.execute(query)
        return cursor.fetchall()


class Selector(BaseSelector):
    def user_select(self, cursor):
        return super().select(cursor, f'SELECT "name", email, is_admin FROM "user"')


class DataBase:
    def __init__(self):
        self.con = psycopg2.connect(user='postgres',
                                    password='postgres',
                                    dbname='gas_equipment',
                                    host='localhost',
                                    port=5432)
        self.cur = self.con.cursor()
        self.selector = Selector()
        self.user = self.selector.user_select(self.cur)













