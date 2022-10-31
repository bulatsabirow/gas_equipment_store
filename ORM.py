from abc import ABC
from typing import Iterator

CATEGORY_CHOICES = {'gas stoves', 'geysers', 'gas meter', 'kitchen hoods'}
BRAND_CHOICES = {'Atlan', 'Graude', 'De Luxe', 'Gefest', 'Oasis', 'Beko'}


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


class GoodsInterface(BaseInterface, ABC):
    def insert(self):
        category = 'null' if self.category is None else f'{self.category}'
        brand = 'null' if self.brand is None else f'{self.brand}'
        return super(GoodsInterface, self).insert(f'INSERT INTO goods(title, description, price, image,'
                                                  f' category, brand, count) VALUES (\'{self.title}\','
                                                  f'\'{self.description}\',{self.price},\'{self.image}\','
                                                  f' {category}, {brand}, {self.count};')

    @staticmethod
    def select(goods_id):
        response = BaseInterface.select(f'SELECT id, title, description, price, image, category, brand, count'
                                        f' FROM goods WHERE id = {goods_id};')[0]
        return GoodsModel(*response)

    @staticmethod
    def all():
        x = [GoodsModel(*item) for item in BaseInterface.select(f'SELECT id, title, description, price, image,'
                                                                f' category, brand, count'
                                                                f' FROM goods;')]
        print(x)
        return x

    @staticmethod
    def find_all(goods_id: Iterator):
        return [GoodsModel(*item) for item in BaseInterface.select(f'SELECT id, title, description, price, image,'
                                                                   f' category, brand, count'
                                                                   f' FROM goods WHERE id'
                                                                   f' IN ({", ".join(goods_id)});')]
    @staticmethod
    def filter(text: str = '', brand=None, category=None):
        if text is None:
            text = ''
        if brand is None:
            brand = ' (brand IS NOT NULL OR NULL)'
        else:
            brand = ' brand IN (' + ','.join((f'\'{item}\'' for item in brand)) + ')'
        if category is None:
            category = ' (category IS NOT NULL OR NULL)'
        else:
            category = ' category IN (' + ','.join((f'\'{item}\'' for item in category)) + ')'

        print(category)
        print(brand)

        return [GoodsModel(*item) for item in BaseInterface.select(f'SELECT id, title, description, price, image,'
                                                                   f'category, brand, count'
                                                                   f' FROM goods'
                                                                   f' WHERE (title ILIKE \'%{text}%\' OR'
                                                                   f' description ILIKE \'%{text}%\') AND'
                                                                   f' {brand} AND {category};')]

    @staticmethod
    def filter_by_brand(brand: str):
        pass


class BaseObjectModel:
    def __repr__(self):
        return str(tuple(self.__dict__.values()))

    def __iter__(self):
        for item in self.__dict__.values():
            yield item

    def to_json(self):
        return {key: value for key, value in self.__dict__.items()}


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
    def __init__(self, id, title, description, price, image, category=None, brand=None, count=0):
        self.id = str(id)
        self.title = title
        self.description = description
        self.price = price
        self.image = image
        self.category = category
        self.brand = brand
        self.count = count

    def __iter__(self):
        for item in self.__dict__.items():
            if item[0] != 'count':
                yield item[1]

    @staticmethod
    def f():
        return BaseInterface.select(f'SELECT enum_range(NULL::category_choices);')








