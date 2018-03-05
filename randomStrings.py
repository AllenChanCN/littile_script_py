#!/usr/bin/env python
#coding=utf-8


#python生产随机密码
import string, random
a = set(string.printable).difference(set(string.whitespace))
b = ""
for i in range(16):b+=random.choice(list(a));print b