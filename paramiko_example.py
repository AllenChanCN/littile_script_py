#!/usr/bin/env python
# coding: utf-8

import sys

import paramiko

class S_Host(object):
    def __init__(self,ip, user, pwd="", port=22, keyfile="", endTag=" "):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if not keyfile:
            ssh.connect(ip, username=user, port=port, password=pwd)
        elif keyfile and not pwd:
            ssh.connect(ip, username=user, port=port, key_filename=keyfile)
        else:
            ssh.connect(ip, username=user, port=port, key_filename=keyfile, password=pwd)
        self.endTag = endTag
        self.Debug = False
        self.ssh = ssh

    def disconnect(self,isEnd=False):
        if hasattr(self, "channel"):
            self.channel.close()
        if isEnd:
            self.ssh.close()
        return True

    def exeCmds(self, cmds):
        retInfo = []
        try:
            self.channel = self.ssh.invoke_shell()
            endTag = " "
            ret = ""
            isGet = False
            isFirst = True
            for cmdinfo in cmds:
                endTag = cmdinfo.get("endTag", endTag)
                cmd =  cmdinfo.get("cmd", "")
                isGet = cmdinfo.get("isGet", False)
                if not cmd:
                    continue
                if isFirst:
                    ret = ""
                    while not ret.endswith(self.endTag):
                        recv = self.channel.recv(65535).decode("utf-8")
                        ret += recv
                self.channel.send("%s\n" % cmd)
                ret = ""
                while not ret.endswith(endTag):
                    recv = self.channel.recv(65535).decode("utf-8")
                    ret += recv
                if self.Debug:
                    print("@"*32)
                    print(ret)
                    print("@"*32)
                if isGet:
#                    ret = "\n".join(ret.split("\r\n")[1:-1])
                    ret = re.split("\n|\r\n", ret)[1:-1]
                    retInfo.append(ret)
                self.endTag = endTag
                if isFirst:
                    isFirst = False
        except Exception as e:
            if self.Debug:
                print("{0}ERROR{0}".format("@"*16))
                print(str(e))
                print("@"*37)
            else:
                pass
        self.disconnect()
        return retInfo

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
