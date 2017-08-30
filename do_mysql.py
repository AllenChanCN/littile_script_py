#!/usr/bin/env python
# coding: utf-8

"""
    1, prepare for database
    2, initialize database
    3, initialize git repository
    4, modify config file
    5, add conrab task
    6, add nginx config file
    7, truncate database
"""

import sys
import MySQLdb

class MySQLdbObject():
    def __init__(self, host, password, user="root", port=3306, database="test"):
        self.host  = host
        self.user = user
        self.password = password
        self.port = port
        self.database = database

    def db_connect(self):
        try:
            self.conn = MySQLdb.connect(user=self.user, passwd=self.password, host=self.host, port=self.port, db=self.database)
            self.cur = self.conn.cursor()
        except Exception, e:
            print "Error reason: %s" % e
            self.db_disconnect()
            return False
        return True

    def db_disconnect(self):
        try:
            self.cur.close()
            self.conn.close()
        finally:
            return True

    def do_sql(self, sqls, multi=False):
        not_failed = True
        try:
            if not self.db_connect():
                raise(IOError("Failed to connect database", ""))
            if not multi:
                sqls = [sqls,]
            for sql in sqls:
                self.cur.execute(sql)
        except Exception,e:
            print "Error reason: %s" % e
            not_failed = False
        finally:
            self.db_disconnect()
            return not_failed

    def query_sql(self, sqls, multi=False):
        not_failed = True
        result_list = []
        try:
            if not self.db_connect():
                raise(IOError("Failed to connect database", ""))
            if not multi:
                sqls = [sqls]
            for sql in sqls:
                tmp_num = self.cur.execute(sql)
                tmp_info = self.cur.fetchmany(tmp_num)
                result_list.append(tmp_info)
        except Exception,e:
            print "error: %s" % e
            not_failed = False
        else:
            not_failed = result_list
        finally:
            self.db_disconnect()
            return not_failed


if __name__ == "__main__":
    dbobj = MySQLdbObject(host="127.0.0.1", password="mysql")
    result = dbobj.query_sql(["show databases", "show tables"], multi=True)
    print result
    sys.exit(0) if result else sys.exit(1)