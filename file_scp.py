#!/usr/bin/env python3
# coding: utf-8


import os
import sys

import paramiko
from paramiko import SSHClient
from scp import SCPClient


class S_Host(object):
    def __init__(self, host="127.0.0.1", password="", user="root", port=22, key_file=""):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.key_file = key_file

    def do_connect(self):
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.key_file:
            self.ssh.connect(username=self.user, password=self.password, port=self.port, hostname=self.host, key_filename=self.key_file)
        else:
            self.ssh.connect(username=self.user, password=self.password, port=self.port, hostname=self.host)
        self.scp = SCPClient(self.ssh.get_transport())
        return True

    def do_disconnect(self):
        try:
            self.scp.close()
            self.ssh.close()
        finally:
            return True
    def do_put(self, source_file, target_file, single_call=True):
        try:
            if single_call:
                self.do_connect()
            if os.path.exists(source_file):
                self.scp.put(source_file, target_file)
            else:
                raise ValueError("Source file %s is not exists." % source_file, "")
        except Exception as e:
            print("Transport file from %s to %s failed." % (source_file, target_file))
            print("Error reasonn: %s" % e)
            return False
        finally:
            if single_call:
                self.do_disconnect()
        return True

    def do_get(self, source_file, target_file, single_call=True):
        try:
            if single_call:
                self.do_connect()
            if not os.path.isfile(target_file):
                self.scp.get(source_file, target_file)
            else:
                raise ValueError("Target file %s is exists." % target_file)
        except Exception as e:
            print("Transport file from %s to %s failed." % (source_file, target_file))
            print("Error reasonn: %s" % e)
            return False
        finally:
            if single_call:
                self.do_disconnect()
        return True

    def do_put_files(self, source_file_list, target_dir):
        if not hasattr(source_file_list, "__getitem__"):
            raise ValueError("Input value %s cannot iterable." % source_file_list)
        try:
            self.do_connect()
            for file in source_file_list:
                file_name = os.path.basename(file)
                target_file_path = os.path.join(target_dir, file_name)
                try:
                    self.do_put(file, target_file_path, single_call=False)
                except:
                    continue
        finally:
            self.do_disconnect()
        return True

    def do_get_files(self, source_file_list, target_dir):
        pass
        if not hasattr(source_file_list, "__getitem__"):
            raise ValueError("Input value %s cannot iterable." % source_file_list)
        try:
            self.do_connect()
            for file in source_file_list:
                file_name = os.path.basename(file)
                target_file_path = os.path.join(target_dir, file_name)
                try:
                    self.do_get(file, target_file_path, single_call=False)
                except:
                    continue
        finally:
            self.do_disconnect()
        return True

def main(atype, s_info, file1, file2):
    if not isinstance(s_info, dict):
        s_info = {}
    s_host = s_info.get("host", "")
    s_user = s_info.get("user", "")
    s_password = s_info.get("password", "")
    s_port = s_info.get("port", 22)
    s_file = s_info.get("key_file", "")
    node1 = S_Host(host=s_host, user=s_user, password=s_password, port=s_port, key_file=s_file)
    if atype == "PUT":
        node1.do_put(file1, file2)
    elif atype == "GET":
        node1.do_get(file1, file2)
    return True

if __name__ == "__main__":
    s_info = {'info': 'normal_value=keyword1\nsuper_value=keyword2', 'title': 'admin', 'host': '127.0.0.1', 'user': 'user1', 'key_file': '/opt/elif_yek/id_rsa1', 'password': 'value1', 'port': 22}
    main("GET", s_info, "/opt/file", "/tmp/file")
    sys.exit(0)
