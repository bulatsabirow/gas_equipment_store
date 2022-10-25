from flask_bcrypt import check_password_hash
from flask_login import UserMixin
import psycopg2
CON = psycopg2.connect(user='postgres',
                       password='postgres',
                       dbname='gas_equipment',
                       host='localhost',
                       port=5432)
CURSOR = CON.cursor()


class BaseSelector:
    @staticmethod
    def select(query):
        CURSOR.execute(query)
        return CURSOR.fetchall()

    @staticmethod
    def insert(query):
        CURSOR.execute(query)
        CON.commit()


class UserSelector(BaseSelector):
    def insert(self):
        return super(UserSelector, self).insert(f'INSERT INTO "user"("name","password",email,is_admin)' +
                                                f' VALUES (\'{self.name}\',\'{self.password}\',' +
                                                f'\'{self.email}\',false)')

    @staticmethod
    def select(email):
        response = BaseSelector.select(f'SELECT "name", email, "password", is_admin FROM "user"'
                                       f' WHERE email = \'{email}\'')
        if not response:
            return None
        response = response[0]
        return UserModel(response[0], response[2], response[1], response[3])


class BaseObjectModel:
    def __repr__(self):
        return str(tuple(self.__dict__.values()))


class UserModel(BaseObjectModel, UserMixin, UserSelector):
    def __init__(self, name, email, password, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def get_id(self):
        return self.email

    @staticmethod
    def find_user(email, password):
        response = UserModel.select(email)
        print(response)
        print(check_password_hash(password, response.password))
        if not response or not check_password_hash(password, response.password):
            return None
        return response







