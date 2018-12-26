#!/usr/bin/env python3
#coding=utf-8

ORIGINAL_FILE = ""
CHECK_FILE = ""
TMP_FILE = ""

def check_ips():
    original_list = []
    is_change = False
    with open(original_file) as fobj1, open(check_file) as fobj2, open(tmpfile) as fobj3:
        line = fobj1.readline()
        original_list.append(line.strip())

        while line:
            if not line.strip():
                line = fobj1.readline
                continue
            line = fobj1.readline
            original_list.append(line.strip())
        original_list = [x for x in original_list if x.strip()]

        line = fobj2.readline()
        if line.strip() not in original_list:
            is_change = True
        while line:
            if not line.strip():
                line = fobj2.readline
                continue
            line = fobj2.readline
            if line.strip() not in original_list:
                is_change = True
    return is_change

def reload_file():
    ip_list = []
    with open(original_file) as fobj:
        line = fobj.readline()
        ip_list.append(line)
        while line:
            if not line.strip():
                line = fobj.readline()
                continue
            ip_list.append(line)
            line = fobj.readline()
    pass 

def reload_service():
    cmds = ""
    pass
