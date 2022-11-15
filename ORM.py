from abc import ABC
from typing import Iterator, Optional
from flask_login import UserMixin
import psycopg2


CATEGORY_CHOICES = ['gas stoves', 'geysers', 'gas meter', 'kitchen hoods', 'null_category']
BRAND_CHOICES = ['Atlan', 'Graude', 'De Luxe', 'Gefest', 'Oasis', 'Beko', 'null_brand']


def db_conn():
    return psycopg2.connect(user='postgres',
                            password='postgres',
                            dbname='gas_equipment',
                            host='localhost',
                            port=5432)


class BaseInterface:
    @staticmethod
    def raw_select(query, params=()):
        CON = db_conn()
        CURSOR = CON.cursor()
        try:
            CURSOR.execute(query, params)
            print(CURSOR.query)
        except Exception as ex:
            print(ex)
            print('RAW SELECT ERROR!!!')
            CURSOR.execute("ROLLBACK")
            CON.commit()
            CON.close()
        else:
            print("status:", CURSOR.statusmessage)
            res = CURSOR.fetchall()
            CON.close()
            return res

    @staticmethod
    def raw_insert(query, params=()):
        CON = db_conn()
        CURSOR = CON.cursor()
        try:
            CURSOR.execute(query, params)
            print(CURSOR.query)
            CON.commit()
        except Exception as ex:
            print('RAW INSERT ERROR!!!')
            print(ex)
            CURSOR.execute("ROLLBACK")
            CON.commit()
            CON.close()
            return
        else:
            CON.close()
            return True

    raw_delete = raw_insert

    raw_update = raw_insert

    @staticmethod
    def stringify(value=''):
        if type(value) == str:
            return f'\'{value}\''
        return value

    def update(self, table_name, attr='id', **kwargs):
        if not kwargs:
            return
        kwargs = [f'{key}={self.stringify(kwargs[key])}' for key in kwargs]
        print(f'UPDATE {table_name} SET {", ".join(kwargs)} WHERE {attr} = {getattr(self, attr)};')
        return BaseInterface.raw_update(f'UPDATE {table_name} SET {", ".join(kwargs)} WHERE {attr} = %s;', (getattr(self, attr), ))


class UserInterface(BaseInterface):
    def insert(self):
        query_result = super(UserInterface, self).raw_insert(f'INSERT INTO "user"("name","password",email,is_admin)'
                                                     f' VALUES (%s,%s,'
                                                     f' %s,false)', (self.name, self.password, self.email,))
        return query_result

    @staticmethod
    def select(email):
        print('select user!')
        response = BaseInterface.raw_select(f'SELECT "name", email, "password", is_admin FROM "user"'
                                            f' WHERE email = %s', (email,))
        if not response:
            return None
        response = response[0]
        print('user select response:', response)
        return UserModel(*response)

    def update(self, **kwargs):
        return super(UserInterface, self).update(table_name='"user"', attr='email', **kwargs)


class GoodsInterface(BaseInterface, ABC):
    def insert(self):
        category = self.category
        brand = self.brand
        image = self.image
        response = super(GoodsInterface, self).raw_insert(f'INSERT INTO goods(title, description, price, image,'
                                                  f' category, brand, count) VALUES (%s,'
                                                  f'%s ,%s ,%s ,'
                                                  f' %s, %s, %s);', (self.title, self.description,
                                                                                            self.price, image, category,
                                                                                            brand, self.count))
        return response

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
                                                                    f' FROM goods ORDER BY title;')]
        print('all() query:', f'SELECT id, title, description, price, image,'
                              f' category, brand, count'
                              f' FROM goods ORDER BY title;')
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
        print('filter-query:', f'SELECT id, title, description, price, image,'
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
                                                                       f' {brand} AND {category};', (text, text))]

    @staticmethod
    def stringify(value=''):
        if type(value) == str:
            return f'\'{value}\''
        return value

    def update(self, **kwargs):
       return super(GoodsInterface, self).update(table_name='goods', **kwargs)

    def remove(self):
        return BaseInterface.raw_delete(f'DELETE FROM goods WHERE id = %s;', (self.id, ))


class OrderInterface(BaseInterface):
    @staticmethod
    def insert(product_id, booking_id, count):
        return BaseInterface.raw_insert(f"INSERT INTO orders(product_id, booking_id, count) VALUES(%s, %s, %s)",
                                        (product_id, booking_id, count))

    @staticmethod
    def select_orders_by_uuid_id(uuid_id):
        return [(OrderModel(*item), product_title, product_price) for *item, product_title, product_price in BaseInterface.raw_select(f"SELECT product_id, booking_id, o.count, o.id, g.title,g.price FROM orders o"
                                        f" INNER JOIN booking b ON o.booking_id = b.id INNER JOIN goods g on o.product_id = g.id  WHERE "
                                        f"b.uuid_key = %s", (uuid_id,))]


class BookingInterface(BaseInterface):
    @staticmethod
    def insert(email, uuid_key, time_value, total_amount):
        return BaseInterface.raw_insert(f"INSERT INTO booking(email,uuid_key,time, total_amount) VALUES(%s,%s,%s,%s)",
                                                        (email, uuid_key, time_value, total_amount))

    @staticmethod
    def select(uuid_id):
        print('query:', f"SELECT email, uuid_key, time, total_amount, id FROM booking"
                                                      f" WHERE uuid_key = {uuid_id}" )
        response = BaseInterface.raw_select(f"SELECT email, uuid_key, time, total_amount, id FROM booking"
                                                      f" WHERE uuid_key = %s",
                                                      (uuid_id,))[0]
        return BookingModel(*response)

    @staticmethod
    def select_by_user(user_email):
        response = BaseInterface.raw_select(f"SELECT email, uuid_key, time, total_amount, id FROM booking WHERE"
                                            f" email = %s ORDER BY time desc", (user_email,))
        print("SELECT_BY_USER BOOKING_INTERFACE:", f"SELECT email, uuid_key, time, total_amount, id FROM booking WHERE"
                                                   f" email = {user_email} ORDER BY time desc")
        return [BookingModel(*obj) for obj in response]



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
    def __init__(self, user_email, uuid_key, time, total_amount, id=''):
        self.id = id
        self.email = user_email
        self.uuid_key = uuid_key
        self.time = time
        self.total_amount = total_amount
