#!/usr/bin/env python3
#coding=utf-8

import paramiko


class RHost(object):
    def __init__(self, host="127.0.0.1", port=22, user="root", passwd="", key_file=""):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.trans = paramiko.Transport(())
        if not key_file:
            self.conn= self.ssh.connect()
            self.trans.connect()
        else:
            self.conn= self.ssh.connect()
            self.trans.connect()

     def disconnect(self):
         pass

    def upload_file(self):
        pass

    def reload_service(self):
        pass


def choose_action_type():
    pass

def choose_ips():
    pass

def single_reload(client):
    client.upload_file()
    client.reload_service()
    pass

def main():
    clients = [

    ]
    action_type = choose_action_type()
    ips = choose_ips()
    check_client = clients[0]
    check_c = RHost()
    checkfile = check_c.get_file()
    reload_file(checkfile, action_type, ips)
    for client in clients:
        c = RHost()
        single_reload(c)



if __name__ == "__main__":
    main()
