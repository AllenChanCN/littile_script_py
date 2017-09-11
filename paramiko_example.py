#!/usr/bin/env python
# coding: utf-8

import sys

import paramiko

class S_Host(object):
    def __init__(self, hostname, username, password, port=22, key_file=""):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.key_file = key_file

    def do_connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(username=self.username, hostname=self.hostname, password=self.password, port=self.port, key_filename=self.key_file)
        return True

    def do_disconnect(self):
        self.ssh.close()
        return True

    def exe_cmd(self, cmds, is_multi=False):
        self.do_connect()
        result_info = ""
        result_status = True
        if not is_multi:
            cmds = [cmds]
        try:
            for cmd in cmds:
                _, stdout, stderr = self.ssh.exec_command("%s; echo $?" % cmd)
                tmp_result = stdout.readlines()
                if tmp_result[-1].strip() != "0":
                    raise SystemError("执行命令 %s 失败。" % cmd)
                if not is_multi:
                    result_info = "\n".join(tmp_result[:-1])
        except Exception as e:
#            print e
            result_info = "\n".join(stderr.readlines() + tmp_result[:-1])
            result_status = False
        finally:
            self.do_disconnect()
        return result_status, result_info

def main():
    vm_host = "127.0.0.1"
    vm_user = "root"
    vm_password = ""
    vm_keyFile = "/tmp/id_rsa"
    host_vm = S_Host(hostname=vm_host, username=vm_user, password=vm_password, key_file=vm_keyFile)
    print host_vm.exe_cmd("s")
    print host_vm.exe_cmd(["ls", "cd /opt", "ls"], is_multi=True)
    return True


if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)