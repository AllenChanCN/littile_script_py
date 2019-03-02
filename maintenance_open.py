#!/usr/bin/env python3
#coding=utf-8

#from __future__ import print_function
import sys
import os
import re
import time
import getopt
import shutil
import logging

import paramiko
import requests


CFG_FILE = "/usr/local/webserver/nginx/conf/sites-enabled/sydefault"
#{"host":"", "user":"", "port":22, "passwd":"", "key_file":"", "remotef":""}
CFG_DICT = [
{"host":"47.52.47.71", "user":"snowchan", "key_file":"/home/allen/.ssh/ali1", }
]
BAK_DIR = "/tmp/wh_bak"
TIMESTAMP = time.strftime("%Y%m%d%H%M%S")
CHECK_URL = "https://xz.zhhe888.com/xtwh.html"

def init_logger(log_name, log_file):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.FileHandler(log_file)
    ch.setLevel(logging.ERROR)

    ch2 = logging.StreamHandler()
    ch2.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #ch.setFormatter(formatter)
    #ch2.setFormatter(formatter)

    #logger.addHandler(ch)
    logger.addHandler(ch2)

    return logger

def useAge():
    useage = """使用示例：
\t{0} -h         # 获取简易的使用信息
\t{0} -t wh      # 切换至维护状态
\t{0} -t open    # 切换至正常运营状态""".format(sys.argv[0])
    print(useage)

def check_opt():
    get_opt = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:h", ["type", "help"])
        if any(map(lambda x: x in ["-h", "--help"], [x[0] for x in opts])) or not len(opts):
            raise AttributeError("print out help information",)
        for k, v in opts:
            if k == "-t" or k == "--type":
                if v not in ["wh", "open"]:
                    raise AttributeError("invalidate arguments",)
                get_opt.setdefault("type", v)
    except:
        useAge()
        return None

    return get_opt

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
        self.Debug = False

    def disconnect(self):
        for ele in (self.conn, self.trans, self.ssh):
            try:
                ele.close()
            except:
                pass
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

    def upload_file(self, localf, remotef):
        if not os.path.isfile(localf):
            return False, "本地文件 %s 不存在" % localf
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
            stdin, stdout, stderr = self.ssh.exec_command("%s;echo $?" % cmd)
            ret_txt = stdout.read()
            if b"0" not in ret_txt:
                errinfo = stderr.read()
                return False, errinfo
        return True, ""


def bak_cfgfile(rhost, file):
    try:
        for program in ("online", "maintenance"):
            if not os.path.isdir(os.path.join(BAK_DIR, TIMESTAMP, program, rhost.hostname)):
                os.makedirs(os.path.join(BAK_DIR, TIMESTAMP, program, rhost.hostname))
        rhost.download_file(os.path.join(BAK_DIR, TIMESTAMP, "online", rhost.hostname, os.path.basename(file)), file)
    except Exception as e:
        return False, str(e)
    return True, os.path.join(BAK_DIR, TIMESTAMP)

def check_cfgfile(num):
    try:
        file_list = os.listdir(BAK_DIR)
        file_list = sorted(file_list, key=lambda x:os.stat(os.path.join(BAK_DIR,x)).st_mtime, reverse=True)
        for x in file_list[num:]:
            shutil.rmtree(os.path.join(BAK_DIR, x))
    except Exception as e:
        return False, str(e)
    return True, ""

def make_maintenance_cfgfile():
    try:
        file_list = os.listdir(os.path.join(BAK_DIR, TIMESTAMP, "online"))
        for f in file_list:
            cfg_file_list = os.listdir(os.path.join(BAK_DIR, TIMESTAMP, "online", f))
            for each_cfg_file in cfg_file_list:
                if not os.path.isdir(os.path.join(BAK_DIR, TIMESTAMP, "maintenance", f)):
                    os.makedirs(BAK_DIR, TIMESTAMP, "maintenance", f)
                wfile = os.path.join(BAK_DIR, TIMESTAMP, "maintenance", f, os.path.basename(each_cfg_file))
                with open(os.path.join(BAK_DIR, TIMESTAMP, "online", f, each_cfg_file)) as fobj, open(wfile, "w")as wfobj:
                    line  = fobj.readline()
                    while line:
                        if not line.strip():
                            wfobj.write(line)
                            line = fobj.readline()
                            continue
                        if re.match("^\s*#\s*include\s+grant_ips/xtwh.zone\s*;\s*$", line):
                            wfobj.write("include grant_ips/xtwh.zone;\n")
                        elif re.match("^\s*#\s*error_page\s+403\s+.*/xtwh.html\s*;\s*$", line):
                            txt = re.search("^\s*#(\s*error_page\s+403\s+.*/xtwh.html\s*;\s*)$", line).groups()[0]
                            wfobj.write(txt)
                        elif re.match("^\s*error_page\s+403\s+.*/fwxz.html\s*;\s*$", line):
                            txt = re.search("^(\s*error_page\s+403\s+.*/fwxz.html\s*;\s*)$", line).groups()[0]
                            wfobj.write("# %s" % txt)
                        else:
                            wfobj.write(line)
                        line = fobj.readline()
                        continue
    except Exception as e:
        print(e)
        return False
    return True

def put_cfgfile(rhost,file, is_wh=True):
    try:
        if is_wh:
            tag = "maintenance"
        else:
            tag = "online"
        upload_ret = rhost.upload_file(os.path.join(BAK_DIR, TIMESTAMP, tag, rhost.hostname, os.path.basename(file)), file)
        if not upload_ret[0]:
            raise IOError(upload_ret[1],)
    except Exception as e:
        print(e)
        return False
    return True

def mail_info():
    pass

def reload_service(rhost):
    reload_ret = rhost.reload_service()
    return reload_ret

def recheck_webpage(url, is_wh=True):
    http_headers = { 'Accept': '*/*','Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'}
    req = requests.get(url, headers=http_headers, timeout=10)
    if is_wh and "xtwh.html" in req.url:
        return True
    elif not is_wh and "xtwh.html" not in req.url:
        return True
    return False

def do_maintenance(logger):
    logger.info("开始切换运营状态，运行--->维护。")
    check_ret = recheck_webpage(CHECK_URL,is_wh=False)
    if not check_ret:
        logger.warn("当前运营状态为\"维护中\"，放弃切换为\"维护\"状态，结束操作。", )
        return False
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        bak_ret = bak_cfgfile(rhost, ele.get("cfg_file", CFG_FILE))
        if not bak_ret[0]:
            logger.error("获取配置文件 {0} 失败，原因：{1}。结束操作。".format(ele.get("cfg_file", CFG_FILE), bak_ret[1]))
            return False
        logger.info("获取配置文件 {0} 成功。备份位置 {1}".format(ele.get("cfg_file", CFG_FILE), bak_ret[1]))
    check_ret = check_cfgfile(1)
    if not check_ret:
        logger.error("检查备份目录 {0} 下的文件并删除过期文件失败，请检查。结束操作。".format(BAK_DIR))
        return False
    make_ret = make_maintenance_cfgfile()
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        put_cfgfile(rhost, ele.get("cfg_file", CFG_FILE))
    mail_info()
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        reload_service(rhost)
    check_ret = recheck_webpage(CHECK_URL,is_wh=True)
    if not check_ret:
        return False
    mail_info()
    return True

def do_open(logger):
    check_ret = recheck_webpage(CHECK_URL,is_wh=True)
    if not check_ret:
        logger.warn("当前运营状态为\"运行中\"，放弃切换为\"运行\"状态，结束操作。", )
        return False
    global TIMESTAMP
    for ele in sorted(os.listdir(BAK_DIR), key=lambda x:os.stat(os.path.join(BAK_DIR,x)).st_mtime, reverse=True):
        is_match = True
        for client in CFG_DICT:
            if not os.path.isfile(os.path.join(BAK_DIR, ele, "online", client.get("host", "null"), os.path.basename(client.get("cfg_file", CFG_FILE)))):
                is_match = False
        if is_match:
            TIMESTAMP = ele
            break
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        put_ret = put_cfgfile(rhost, ele.get("cfg_file", CFG_FILE), is_wh=False)
        print(put_ret)
    mail_info()
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        reload_service(rhost)
    recheck_webpage(CHECK_URL, is_wh=False)
    mail_info()
    return True

def main():
    #挂机维护
    # 1. 备份配置文件
    # 2. 删除过久或者过多的备份文件
    # 3. 修改配置文件
    # 4. 替换配置文件
    # 5. 邮件通知准备停机维护
    # 6. 刷新服务
    # 7. 确认是否成功挂维护
    # 8. 邮件通知已经停机维护

    #正常运营
    # 1. 替换配置文件
    # 2. 邮件通知准备正常运营
    # 3. 刷新服务
    # 4. 确认页面是否正常运营
    # 5. 邮件通知已经正常运营

    log_name = "maintenance_online"
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maintenance.log")
    logger = init_logger(log_name, log_file)

    opts_dict = check_opt()
    if opts_dict is None:
        return False
    exe_type = opts_dict.get("type", "")
    if exe_type == "wh":
        do_maintenance(logger)
    elif exe_type == "open":
        do_open(logger)
    else:
        return False
    return True

if __name__ == "__main__":
    exe_ret = main()
    sys.exit(0) if exe_ret else sys.exit(1)
