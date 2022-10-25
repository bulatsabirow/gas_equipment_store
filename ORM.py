from flask_login import UserMixin
import psycopg2
CON = psycopg2.connect(user='postgres',
                       password='postgres',
                       dbname='gas_equipment',
                       host='localhost',
                       port=5432)
CURSOR = CON.cursor()


class BaseInterface:
    @staticmethod
    def select(query):
        CURSOR.execute(query)
        return CURSOR.fetchall()

    @staticmethod
    def insert(query):
        CURSOR.execute(query)
        CON.commit()


class UserInterface(BaseInterface):
    def insert(self):
        return super(UserInterface, self).insert(f'INSERT INTO "user"("name","password",email,is_admin)' +
                                                 f' VALUES (\'{self.name}\',\'{self.password}\',' +
                                                 f'\'{self.email}\',false)')

    @staticmethod
    def select(email):
        response = BaseInterface.select(f'SELECT "name", email, "password", is_admin FROM "user"'
                                        f' WHERE email = \'{email}\'')
        if not response:
            return None
        response = response[0]
        return UserModel(*response)


class GoodsInterface(BaseInterface):
    def insert(self):
        category = 'null' if self.category is None else f'{self.category}'
        brand = 'null' if self.brand is None else f'{self.brand}'
        return super(GoodsInterface, self).insert(f'INSERT INTO goods(title, description, price, image,'
                                                  f' category, brand) VALUES (\'{self.title}\','
                                                  f'\'{self.description}\',{self.price},\'{self.image}\','
                                                  f' {category}, {brand});')

    @staticmethod
    def select(goods_id):
        return BaseInterface.select(f'SELECT title, description, price, image, category, brand'
                                    f' FROM goods WHERE id = {goods_id};')

    @staticmethod
    def all():
        return (GoodsModel(*item) for item in BaseInterface.select(f'SELECT title, description, price, image,'
                                                                   f' category, brand'
                                                                   f' FROM goods;'))


class BaseObjectModel:
    def __repr__(self):
        return str(tuple(self.__dict__.values()))


class UserModel(BaseObjectModel, UserMixin, UserInterface):
    def __init__(self, name, email, password, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def get_id(self):
        return self.email

    @staticmethod
    def find_user(email):
        response = UserModel.select(email)
        print(response)
        if not response:
            return None
        return response


class GoodsModel(BaseObjectModel, GoodsInterface):
    def __init__(self, title, description, price, image, category=None, brand=None):
        self.title = title
        self.description = description
        self.price = price
        self.image = image
        self.category = category
        self.brand = brand








