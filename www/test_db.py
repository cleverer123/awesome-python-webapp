#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import User, Blog, Comment

from transwarp import db

db.create_engine(user='root', password='root', database='test', host='121.42.58.105')

u = User(id=10190, name='Test', email='test@example.com', password='1234567890')

u.insert()

print 'new user id:', u.id

u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name

u1.delete()

u2 = User.find_first('where email=?', 'test@example.com')
print 'find user:', u2