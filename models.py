import psycopg2


class BaseSelector:
    @staticmethod
    def select(cursor, query):
        cursor.execute(query)
        return cursor.fetchall()

    @staticmethod
    def insert(cursor, query, con):
        cursor.execute(query)
        con.commit()


class Selector(BaseSelector):
    def select(self, cursor):
        return super().select(cursor, f'SELECT "name", email, is_admin FROM "user"')

    def insert(self, cursor, con, password, *args, is_admin=False):
        print(f'INSERT INTO "user"("name", email, password) VALUES' + f'{args}'[:-1]
                       + f', MD5(\'{password}\'));')
        super().insert(cursor, f'INSERT INTO "user"("name", email, password) VALUES' + f'{args}'[:-1]
                       + f', MD5(\'{password}\'));', con)


class DataBase:
    def __init__(self):
        self.con = psycopg2.connect(user='postgres',
                                    password='postgres',
                                    dbname='gas_equipment',
                                    host='localhost',
                                    port=5432)
        self.cur = self.con.cursor()
        self.selector = Selector()

    @property
    def user(self):
        return self.selector.select(self.cur)

    def user_insert(self, password, *args):
        return self.selector.insert(self.cur, self.con, password, *args)














