#!/usr/bin/env python3
#coding=utf-8

import sys
import getopt
import tempfile
import paramiko


class RHost(object):
    def __init__(self, host="127.0.0.1", port=22, user="root", passwd="", key_file="", **kwargs):
        self.hostname = host
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.trans = paramiko.Transport((host,port))
        if not key_file:
            self.conn= self.ssh.connect(hostname=host, username=user, port=port, password=passwd)
            self.trans.connect(username=user, password=passwd)
        else:
            self.conn= self.ssh.connect(hostname=host, username=user, port=port, password=passwd, key_filename=key_file)
            self.trans.connect(username=user, password=passwd, pkey=key_file)
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)

    def disconnect(self):
        for ele in (self.conn, self.trans, self.ssh):
            try:
                ele.close()
            except:
                pass
        return True

    def upload_file(self, localf, remotef):
        if not os.path.isfile(localf):
            return False, "本地文件 %s 不存在"
        try:
            self.sftp.put(localpath=localf, remotepath=remotef)
        except Exception as e:
            return False, str(e)
        else:
            return True, ""

    def download_file(self, localf, remotef):
        if os.path.isfile(localf):
            return False, "本地文件 %s 已存在"
        try:
            self.sftp.get(remotepath=remotef, localpath=localf)
        except Exception as e:
            return False, str(e)
        else:
            return True, ""

    def reload_service(self):
        cmds = [
            "/usr/local/webserver/nginx/sbin/nginx -t",
            "/usr/local/webserver/nginx/sbin/nginx -s reload",
        ]
        for cmd in cmds:
            stdin, stdout, stderr = self.ssh.exec_command("%s;echo $?" % cmd1)
            ret_txt = stdout.read()
            if "" in ret_txt:
                errinfo = stderr.read()
                return False, errinfo
        return True, ""


def choose_action_type():
    pass

def choose_ips():
    pass

def single_reload(client, localf, remotef):
    upload_ret = client.upload_file(localf, remotef)
    if not upload_ret[0]:
        return False,"上传本地文件 {} 至 {}:{} 失败。原因：\n{}".format(localf, client.hostname, remotef, upload_ret[1])
    reload_ret = client.reload_service()
    if not reload_ret[0]:
        return False, "远程主机 {} 刷新nginx服务失败。".format(client.hostname)
    return True, ""

def check_options():
    vars_dict = {}
    try:
        args, opt = getopt.getopt(sys.argv[1:], "-a:-i:-h",["action_type", "ips", "help"])
    #args, opt = getopt.getopt("-a put 127.0.0.1 192", "a:",)
        for o,v in args:
            if o in ["-h", "--help"]:
                print("")
            if o in ["-a", "--action_type"]:
                vars_dict.setdefault("action_type", v)
            if o in ["-i", "--ips"]:
                vars_dict.setdefault("ips", v.split())
    except:
        pass
    return vars_dict

def check_ips(ip_list):
    for ip in ip_list:
        if len(ip.split(".")) != 4:
            return False
        for ele in ip.split("."):
            if ele >= 255 or ele <= 0:
                return False
    return True

def main():
    #{"host":"", "user":"", "port":22, "passwd":"", "key_file":"", "remotef":""}
    clients = [
    ]
    tmpf = tempfile.mktemp()
    cfgfile = ""

    #获取命令行传入的参数
    vars_dict = check_options()

    #获取操作类型
    action_type = vars_dict.get("action_type", "")
    if not action_type or action_type not in ["add", "delete", "query"]:
        action_type = choose_action_type()

    #获取操作目标IP
    ips = vars_dict.get("ips", "")
    if not ips or not check_ips(ips):
        ips = choose_ips()

    #获取文件模板
    check_client = clients[0]
    check_c = RHost(**check_client)
    rfile = check_client.get("remotef", cfgfile)
    checkfile = check_c.download_file(localf=tmpf, remotef=rfile)
    check_c.disconnect()

    #刷新模板文件
    reload_file(checkfile, action_type, ips)

    #将模板文件同步到所有客户端
    exe_ret = []
    for client in clients:
        c = RHost(**client)
        rfile = c.get("remotef", cfgfile)
        tmp_ret = single_reload(c, localf=tmpf, remotef=rfile)
        exe_ret.append({c.hostname: tmp_ret})
        c.disconnect()

    return True



if __name__ == "__main__":
    main()
