#!/usr/bin/env python2
#coding=utf-8
from __future__ import print_function

import os
import sys
import time
import getopt
import tempfile
import paramiko


ACTIONS = ["add", "delete", "query"]

class RHost(object):
    def __init__(self, host="127.0.0.1", port=22, user="root", passwd="", key_file="", **kwargs):
        self.hostname = host
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.trans = paramiko.Transport((host,port))
        pk = paramiko.RSAKey.from_private_key(open(key_file))
        if not key_file:
            self.conn= self.ssh.connect(hostname=host, username=user, port=port, password=passwd)
            self.trans.connect(username=user, password=passwd)
        else:
            self.conn= self.ssh.connect(hostname=host, username=user, port=port, password=passwd, key_filename=key_file)
            self.trans.connect(username=user, password=passwd, pkey=pk)
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
    choose_num = None
    print("{0} {1} {0}".format("-"*16, "选择操作类型"))
    for index, a in enumerate(ACTIONS):
        print("{0:>10s} : {1}".format("[%d]" % index, a))
    while choose_num is None:
        choose_num = input("输入选项编号[2]:")
        if choose_num.strip() == "":
            choose_num = len(ACTIONS) - 1
        try:
            choose_num = int(choose_num)
            if choose_num in range(len(ACTIONS)):
                break
        except:
            pass
        print("选择编号不在范围内，请重新选择")
        choose_num = None
        continue
    print("{0} {1} {0}".format("-"*16, "操作类型选择结束"))
    return ACTIONS[choose_num]

def choose_ips():
    ips = []
    is_right = False
    print("{0} {1} {0}".format("-"*16, "输入IP值"))
    while not is_right:
        ips = input("输入被添加的ip值，多IP之间以空格隔开，输入回车结束输出：")
        ips = ips.split()
        if not len(ips) or not check_ips(ips):
            print("输入IP中存在不合法的值，请重新输入")
            continue
        is_right = True
    print("{0} {1} {0}".format("-"*16, "输入结束"))
    return ips

def reload_file(checkfile, action_type, ips):
    infos = []
    exists_ips = []
    tmp_writefile = tempfile.mktemp()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    is_deny = False
    with open(checkfile) as fobj, open(tmp_writefile, "w") as tfobj:
        line = fobj.readline()
        while line and not is_deny:
            if not line.strip():
                line = fobj.readline()
                continue
            if line.split("#")[0].strip().split() == ["deny", "all;"]:
                is_deny == True
                line = fobj.readline()
                continue
            line_ip = line.split("#")[0].strip().split()[-1]
            line_ip = line_ip.replace(";", "")
            for ip in ips:
                is_once = True
                if is_once and not (ip == line_ip and action_type == "delete") and not action_type == "query":
                    tfobj.write(line)
                    is_once = False
                if ip == line_ip and line_ip not in exists_ips and action_type != "delete":
                    infos.append("目标IP {} 已存在文件中".format(ip))
                if ip ==line_ip and line_ip not in exists_ips:
                    exists_ips.add(ip)
                if ip == line_ip:
                    break
            line = fobj.readline()
        for ip in ips:
            if ip not in exists_ips:
                if action_type == "query":
                    infos.append("目标IP {} 不存在文件中".format(ip))
                elif action_type == "add":
                    tfobj.write("allow {0}; #{1}\n".format(ip, timestamp))
        if is_deny:
            tfobj.write("deny all;\n")
        while line:
            tfobj.write(line)
            line = fobj.readline()
    for ele in infos:
        print(ele)
    return True

def showInfo(item, info):
    if not info:
        info = "完成【%s】" % item
    else:
        info = "{0} 开始【{1}】错误信息 {0}\n{2}\n{0} 结束【{1}】错误信息 {0}".format("-"*16, item, info)
    print(info)
    return True

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
        try:
            for ele in ip.split("."):
                ele = int(ele)
                if ele > 255 or ele < 0:
                    return False
        except:
            return False
    return True

def main():
    #{"host":"", "user":"", "port":22, "passwd":"", "key_file":"", "remotef":""}
    clients = [
    {"host":"47.52.47.71", "key_file":"/home/allen/.ssh/ali1", "remotef":"/usr/local/nginx-1.14/conf/allows.ip", "user":"snowchan"},
    ]
    tmpf = tempfile.mktemp()
    cfgfile = "/usr/local/webserver/nginx/conf/grant_ips/front.zone"

    #获取命令行传入的参数
    vars_dict = check_options()

    #获取操作类型
    action_type = vars_dict.get("action_type", "")
    if not action_type or action_type not in ACTIONS:
        action_type = choose_action_type()

    #获取操作目标IP
    ips = vars_dict.get("ips", "")
    if not ips or not check_ips(ips):
        ips = choose_ips()

    #获取文件模板
    check_client = clients[0]
    check_c = RHost(**check_client)
    rfile = check_client.get("remotef", cfgfile)
    download_ret = check_c.download_file(localf=tmpf, remotef=rfile)
    check_c.disconnect()
    if not download_ret[0]:
        showInfo("获取文件模板", download_ret[1])
        return False
    showInfo("获取文件模板", "")

    #刷新模板文件
    reload_ret = reload_file(tmpf, action_type, ips)
    showInfo("刷新文件模板", "")

    #将模板文件同步到所有客户端
    if action_type == "query":
        return True
    exe_ret = []
    for client in clients:
        c = RHost(**client)
        rfile = client.get("remotef", cfgfile)
        tmp_ret = single_reload(c, localf=tmpf, remotef=rfile)
        exe_ret.append({c.hostname: tmp_ret})
        if not tmp_ret[0]:
            showInfo("同步文件模板到%s" % c.hostname,tmp_ret[1])
        showInfo("同步文件模板到%s" % c.hostname, "")
        c.disconnect()

    return True


if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)
