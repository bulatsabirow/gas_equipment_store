# import psycopg2
# from ORM import User
#
#
# class BaseSelector:
#     @staticmethod
#     def beautify(cls, iterator):
#         return (cls(*item) for item in iterator)
#
#     @staticmethod
#     def select(cursor, query):
#         cursor.execute(query)
#         return cursor.fetchall()
#
#     @staticmethod
#     def insert(cursor, query, con):
#         cursor.execute(query)
#         con.commit()
#
#     find = select
#
#
# class UserSelector(BaseSelector):
#     def select(self, cursor):
#         # return [User(*item) for
#         #         item in super().select(cursor, f'SELECT id,"name", email,password, is_admin FROM "user"')]
#         return self.beautify(User,  super().select(cursor, f'SELECT id,"name", email,password, is_admin FROM "user"'))
#
#     def insert(self, cursor, con, password, *args):
#         super().insert(cursor, f'INSERT INTO "user"("name", email, password) VALUES' + f'{args}'[:-1]
#                        + f', MD5(\'{password}\'));', con)
#
#     def find_user_by_email(self, cursor, user_email: str):
#         # return self.find(cursor, f'SELECT id,"name",email,password,is_admin FROM "user"'
#         #                          f' WHERE id = {user_id}')
#         return self.beautify(User, super().select(cursor, f'SELECT id,"name",email,password,is_admin FROM "user"'
#                                                           f' WHERE email = \'{user_email}\''))
#
#
# class DataBase:
#     def __init__(self):
#         self.con = psycopg2.connect(user='postgres',
#                                     password='postgres',
#                                     dbname='gas_equipment',
#                                     host='localhost',
#                                     port=5432)
#         self.cur = self.con.cursor()
#         self.selector = UserSelector()
#
#     @property
#     def user(self):
#         return self.selector.select(self.cur)
#
#     def user_insert(self, password, *args):
#         return self.selector.insert(self.cur, self.con, password, *args)
#
#     def find_user_by_email(self, email):
#         return self.selector.find_user_by_email(self.cur, email)

















