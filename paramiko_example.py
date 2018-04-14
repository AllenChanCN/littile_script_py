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
            result_info = "\n".join(stderr.readlines() + tmp_result[:-1])
            result_status = False
        finally:
            self.do_disconnect()
        return result_status, result_info

    def exe_cmd_channel(self, cmds, is_multi=False, is_root=False, root_pwd=""):
        judge_flag = "$ "
        if not is_multi:
            cmds = [cmds]
        self.do_connect()
        result_status = True
        result_info = ""
        try:
            self.channel = self.ssh.invoke_shell()
            buff = ''
            while not buff.endswith(judge_flag):
                resp = self.channel.recv(9999)
                buff += resp
                if is_root:
                    judge_flag = "# "
                    buff = ""
                    self.channel.send("su -\n")
                    while not buff.endswith("assword: "):
                        resp = self.channel.recv(9999)
                        buff += resp
                    buff = ""
                    self.channel.send("%s\n" % root_pwd)
                    while not buff.endswith(judge_flag):
                        resp = self.channel.recv(9999)
                        buff += resp
                        if "incorrect" in buff or "assword: " in buff:
                            self.do_disconnect()
                            return False, "Invalid password"
            for cmd in cmds:
                buff1 = ""
                buff2 = ""
                self.channel.send("%s\n" % cmd)
                while not buff1.endswith(judge_flag):
                    resp = self.channel.recv(9999)
                    buff1 += resp
                result_info = "\n".join(buff1.split(repr(judge_flag.strip()))[0].split("\n")[1:-1]).strip()
                self.channel.send("echo $?\n")
                while not buff2.endswith(judge_flag):
                    resp = self.channel.recv(9999)
                    buff2 += resp
                status_code = re.search("\$\?\s*([^\s]*)\s*", buff2).groups()
                if status_code[0] != "0":
                    raise IOError("执行命令 %s 失败。" % cmd)
        except:
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