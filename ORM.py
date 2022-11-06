from abc import ABC
from typing import Iterator, Optional
from flask_login import UserMixin
import psycopg2


CATEGORY_CHOICES = {'gas stoves', 'geysers', 'gas meter', 'kitchen hoods', 'null_category'}
BRAND_CHOICES = {'Atlan', 'Graude', 'De Luxe', 'Gefest', 'Oasis', 'Beko', 'null_brand'}


CON = psycopg2.connect(user='postgres',
                       password='postgres',
                       dbname='gas_equipment',
                       host='localhost',
                       port=5432)
CURSOR = CON.cursor()


class BaseInterface:
    @staticmethod
    def raw_select(query, params=()):
        CURSOR.execute(query, params)
        print("status:", CURSOR.statusmessage)
        return CURSOR.fetchall()

    @staticmethod
    def raw_insert(query, params=()):
        CURSOR.execute(query, params)
        CON.commit()

    raw_delete = raw_insert

    raw_update = raw_insert


class UserInterface(BaseInterface):
    def insert(self):
        return super(UserInterface, self).raw_insert(f'INSERT INTO "user"("name","password",email,is_admin)'
                                                     f' VALUES (%s,%s,'
                                                     f' %s,false)', (self.name, self.password, self.email,))

    @staticmethod
    def select(email):
        print('select user!')
        response = BaseInterface.raw_select(f'SELECT "name", email, "password", is_admin FROM "user"'
                                            f' WHERE email = %s', (email,))
        if not response:
            return None
        response = response[0]
        return UserModel(*response)


class GoodsInterface(BaseInterface, ABC):
    def insert(self):
        category = 'null' if self.category is None else f'\'{self.category}\''
        brand = 'null' if self.brand is None else f'\'{self.brand}\''
        image = 'null' if self.image is None else f'\'{self.image}\''
        return super(GoodsInterface, self).raw_insert(f'INSERT INTO goods(title, description, price, image,'
                                                  f' category, brand, count) VALUES (%s,'
                                                  f'%s ,%s ,%s ,'
                                                  f' %s, %s, %s);', (self.title, self.description,
                                                                                            self.price, image, category,
                                                                                            brand, self.count))

    @staticmethod
    def select(goods_id):
        print(goods_id)
        try:
            response = BaseInterface.raw_select(f'SELECT id, title, description, price, image, category, brand, count'
                                                f' FROM goods WHERE id = %s;', (goods_id,))[0]
        except IndexError:
            return
        else:
            print(response)
            return GoodsModel(*response)

    @staticmethod
    def all():

        x = [GoodsModel(*item) for item in BaseInterface.raw_select(f'SELECT id, title, description, price, image,'
                                                                    f' category, brand, count'
                                                                    f' FROM goods;')]
        print('all() query:', f'SELECT id, title, description, price, image,'
                              f' category, brand, count'
                              f' FROM goods;')
        print('x=', x)
        return x

    @staticmethod
    def find_all(goods_id: Optional[Iterator]):
        if not goods_id:
            return
        return [GoodsModel(*item) for item in BaseInterface.raw_select(f'SELECT id, title, description, price, image,'
                                                                       f' category, brand, count'
                                                                       f' FROM goods WHERE id'
                                                                       f' IN ({", ".join(goods_id)});')]

    @staticmethod
    def filter(text: str = '', brand=None, category=None):
        print('!!!!')
        if text is None:
            text = ''
        if brand is None:
            brand = ' (brand IS NOT NULL OR brand IS NULL)'
        elif brand == {'null_brand'}:
            brand = ' (brand IS NULL) '
        else:
            additional = ''
            if 'null_brand' in brand:
                additional = ' OR brand is NULL'
            brand = ' (brand IN (' + ','.join((f'\'{item}\'' for item in brand if item != 'null_brand')) + ')' \
                    + additional + ')'
        if category is None:
            category = ' (category IS NOT NULL OR category IS NULL)'
        elif category == {'null_category'}:
            category = ' (category IS NULL) '
        else:
            additional = ''
            if 'null_category' in category:
                additional = ' OR category is NULL'
            category = ' (category IN (' + ','.join((f'\'{item}\'' for item in category if item != 'null_category')) \
                       + ')' + additional + ')'

        print('cat:', category)
        print('brand:', brand)
        print(f'SELECT id, title, description, price, image,'
              f'category, brand, count'
              f' FROM goods'
              f' WHERE (title ILIKE \'%{text}%\' OR'
              f' description ILIKE \'%{text}%\') AND'
              f' {brand} AND {category};')
        text = '%' + text + '%'
        return [GoodsModel(*item) for item in BaseInterface.raw_select(f'SELECT id, title, description, price, image,'
                                                                   f'category, brand, count'
                                                                   f' FROM goods'
                                                                   f' WHERE (title ILIKE %s OR'
                                                                   f' description ILIKE %s) AND'
                                                                   f' {brand} AND {category};', (text, text)) ]

    @staticmethod
    def stringify(value=''):
        if type(value) == str:
            return f'\'{value}\''
        return value

    def update(self, **kwargs):
        if not kwargs:
            return
        kwargs = [f'{key}={self.stringify(kwargs[key])}' for key in kwargs]
        print(f'UPDATE goods SET {", ".join(kwargs)} WHERE id = {self.id};')
        return BaseInterface.raw_update(f'UPDATE goods SET {", ".join(kwargs)} WHERE id = %s;', (self.id, ))

    def remove(self):
        return BaseInterface.raw_delete(f'DELETE FROM goods WHERE id = %s;', (self.id, ))


class OrderInterface(BaseInterface):
    @staticmethod
    def insert(product_id, booking_id, count):
        return BaseInterface.raw_insert(f"INSERT INTO orders(product_id, booking_id, count) VALUES(%s, %s, %s)",
                                        (product_id, booking_id, count))


class BookingInterface(BaseInterface):
    @staticmethod
    def insert(email, uuid_key, time_value):
        return BaseInterface.raw_insert(f"INSERT INTO booking(email,uuid_key,time) VALUES(%s,%s,%s)",
                                                        (email, uuid_key, time_value))

    @staticmethod
    def select(uuid_id):
        print('query:', f"SELECT email, uuid_key, time, id FROM booking"
                                                      f" WHERE uuid_key = {uuid_id}" )
        response = BaseInterface.raw_select(f"SELECT email, uuid_key, time, id FROM booking"
                                                      f" WHERE uuid_key = %s",
                                                      (uuid_id,))[0]
        return BookingModel(*response)


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
        for key, value in self.__dict__.items():
            if key != 'count':
                yield value


class OrderModel(BaseObjectModel, OrderInterface):
    def __init__(self, product_id, booking_id, count, id=''):
        self.product_id = product_id
        self.id = id
        self.booking_id = booking_id
        self.count = count


class BookingModel(BaseObjectModel, BookingInterface):
    def __init__(self, user_email, uuid_key, time, id=''):
        self.id = id
        self.email = user_email
        self.uuid_key = uuid_key
        self.time = time
