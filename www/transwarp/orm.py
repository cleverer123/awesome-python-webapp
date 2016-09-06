#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
orm模块设计的原因：
    1. 简化操作
        sql操作的数据是 关系型数据， 而python操作的是对象，为了简化编程 所以需要对他们进行映射
        映射关系为：
            表 ==>  类
            行 ==> 实例
设计orm接口：
    1. 设计原则：
        根据上层调用者设计简单易用的API接口
    2. 设计调用接口
        1. 表 <==> 类
            通过类的属性 来映射表的属性（表名，字段名， 字段属性）
                from transwarp.orm import Model, StringField, IntegerField
                class User(Model):
                    __table__ = 'users'
                    id = IntegerField(primary_key=True)
                    name = StringField()
            从中可以看出 __table__ 拥有映射表名， id/name 用于映射 字段对象（字段名 和 字段属性）
		2. 行 <==> 实例
            通过实例的属性 来映射 行的值
                # 创建实例:
                user = User(id=123, name='Michael')
                # 存入数据库:
                user.insert()
            最后 id/name 要变成 user实例的属性
"""
import db
import time
import logging

_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])

class ModelMetaclass(type):
	 def __new__(cls, name, bases, attrs):
        # skip base Model class:
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
		# store all subclasses info:
        if not hasattr(cls, 'subclasses'):
            cls.subclasses = {}
        if not name in cls.subclasses:
        	cls.subclasses[name] = name
        else:
        	logging.warning('Redefine class: %s' % name)

        logging.info('Scan ORMapping %s...' % name)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
        	if isinstance(v, Field):
        		if not v.name:
        			v.name = k
        		logging.info('[MAPPING] Found mapping: %s => %s' % (k, v))
        		# check duplicate primary key:
                if v.primary_key:
	        		if primary_key:
	        			raise TypeError('Cannot define more than 1 primary key in class: %s' % name)
	        		if v.updatable:
	        			logging.warning('Note: change primary key to non-updatable')
	        			v.updatable = false
	        		if v.nullable:
	        			logging.warning('Note: change primary key to non-nullable')
	        			v.nullable = false
	        		primary_key = v
	        	mappings[k] = v
		#check exist of primary key:
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        for k in mappings.iterkeys():
        	attrs.pop(k)
        if not '__table__' in attrs:
        	attrs['__table__'] = name.lower()
        attrs['__mappings_'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self:_gen_sql()(attrs['__table__'], mappings)
        for trigger in _triggers:
        	if not trigger in attrs:
        		attrs[trigger] = None
        return type.__new__(cls, name, bases, attrs)

def _gen_sql(table_name, mappings):
	pk = None
	sql = sql = ['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]

	for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
		if not hasattr(f, 'ddl'):
			raise StandardError('no ddl in field "%s".' %n)
		ddl = f.ddl
		nullable = f.nullable
		if f.primary_key:
			pk = f.name
		sql.append(nullable and ' `%s` %s,' % (f.name, ddl) or ' `%s` %s not null,' % (f.name, ddl))
	sql.append(' primary key(`%s`)' % pk)
	sql.append(');')
	return '\n'.join(sql)       

class StringField(Field):
    """
    保存String类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)

class IntegerField(Field):
    """
    保存Integer类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0
        if 'ddl' not in kw:
            kw['ddl'] = 'bigint'
        super(IntegerField, self).__init__(**kw)

class FloatField(Field):
    """
    保存Float类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0.0
        if 'ddl' not in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)

class BooleanField(Field):
    """
    保存BooleanField类型字段的属性
    """
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = False
        if not 'ddl' in kw:
            kw['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kw)

class TextField(Field):
    """
    保存Text类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'text'
        super(TextField, self).__init__(**kw)

class BlobField(Field):
    """
    保存Blob类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'blob'
        super(BlobField, self).__init__(**kw)

class VersionField(Field):
    """
    保存Version类型字段的属性
    """
    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

class Model(dict):
	__metaclass__ = ModelMetaclass

	def __init__(self, **kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value

	@classmethod
	def get(cls, pk):
		'''
        Get by primary key.
        '''
		d = db.select_one('select * from %s where %s=?' % (cls.__table__, cls.__primary_key__), pk)
		return cls(**d) if d else None

	@classmethod
	def find_first(cls, where, *args):
		'''
        Find by where clause and return one result. If multiple results found, 
        only the first one returned. If no result found, return None.
        '''
         d = db.select_one('select * from %s %s' % (cls.__table__, where), *args)
         return cls(**d) if d else None

    @classmethod
    def find_all(cls, *args):
    	L = db.select('select * from `%s`' % cls.__table__)
    	return [cls(**d) for d in L]
 	
 	@classmethod
    def find_by(cls, where, *args):
        '''
        Find by where clause and return list.
        '''
        L = db.select('select * from `%s` %s' % (cls.__table__, where), *args)
        return [cls(**d) for d in L]

    @classmethod
    def count_all(cls):
        '''
        Find by 'select count(pk) from table' and return integer.
        '''
        return db.select_int('select count(`%s`) from `%s`' % (cls.__primary_key__.name, cls.__table__))

    @classmethod
    def count_by(cls, where, *args):
        '''
        Find by 'select count(pk) from table where ... ' and return int.
        '''
        return db.select_int('select count(`%s`) from `%s` %s' % (cls.__primary_key__.name, cls.__table__, where), *args)
    
	def update(self):
        """
        如果该行的字段属性有 updatable，代表该字段可以被更新
        用于定义的表（继承Model的类）是一个 Dict对象，键值会变成实例的属性
        所以可以通过属性来判断 用户是否定义了该字段的值
            如果有属性， 就使用用户传入的值
            如果无属性， 则调用字段对象的 default属性传入
            具体见 Field类 的 default 属性
        通过的db对象的update接口执行SQL
            SQL: update `user` set `passwd`=%s,`last_modified`=%s,`name`=%s where id=%s,
                 ARGS: (u'******', 1441878476.202391, u'Michael', 10190
        """
        self.pre_update and self.pre_update()
        L = []
        args = []
        for k, v in self.__mappings__.iteritems():
            if v.updatable:
                if hasattr(self, k):
                    arg = getattr(self, k)
                else:
                    arg = v.default
                    setattr(self, k, arg)
                L.append('`%s`=?' % k)
                args.append(arg)
        pk = self.__primary_key__.name
        args.append(getattr(self, pk))
        db.update('update `%s` set %s where %s=?' % (self.__table__, ','.join(L), pk), *args)
        return self

    def delete(self):
    	"""
        通过db对象的 update接口 执行SQL
            SQL: delete from `user` where `id`=%s, ARGS: (10190,)
        """
    	self.pre_delete and self.pre_delete()
    	pk = self.__primary_key__.name
    	args = (getattr(self, pk),)
    	db.update('delete from `%s` where `%s`=?' % (self.__table__,pk), *args)
    	return self

    def insert(self):
    	"""
        通过db对象的insert接口执行SQL
            SQL: insert into `user` (`passwd`,`last_modified`,`id`,`name`,`email`) values (%s,%s,%s,%s,%s),
            　　　　　 ARGS: ('******', 1441878476.202391, 10190, 'Michael', 'orm@db.org')
        """
        self.pre_insert and self.pre_insert()
        params = {}
        for k, v in self.__mappings__.iteritems():
        	if v.insertable:
        		if not hasattr(self, k):
        			setattr(self, k, v.default)
        		params[v.name] = getattr(self, k)
        db.insert('%s' % self.__table__, **params)
        return self

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.create_engine('www-data', 'www-data', 'test', '192.168.10.128')
    db.update('drop table if exists user')
    db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()