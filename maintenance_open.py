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
LOG_NAME = "maintenance_online"
LOG_FILE = os.path.join(BAK_DIR, "maintenance.log")
#LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maintenance.log")

def init_logger(log_name, log_file):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.FileHandler(log_file)
    ch.setLevel(logging.DEBUG)

    ch2 = logging.StreamHandler()
    ch2.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(process)s - %(name)s - %(levelname)s - %(message)s')

    ch.setFormatter(formatter)
    ch2.setFormatter(formatter)

    logger.addHandler(ch)
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
        file_list = [x for x in file_list if re.match("^\d+$",x)]
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
        return False, str(e)
    return True,""

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
        return False, str(e)
    return True, ""

def mail_info():
    toname='allen.c@auxworld.net'
    subject = "XX平台切换web运营状态记录邮件"

    info = "<h2>{}</h2><pre>".format(subject)
    with open(LOG_FILE) as fobj:
        info += fobj.read()
    info += "</pre>"

#    os.system('python /data/shell/mail.py %s %s %s' %(toname, subject, info))
    print(info)

def mail_notice(is_wh=True, timenum=180):
    toname='allen.c@auxworld.net'
    subject = "XX平台切换web运营状态预通知邮件"
    try:
        timenum = int(timenum)
    except:
        timenum = 180
    time1 = time.strftime("%Y-%m-%d %H:%M:%S")
    time2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+timenum))
    if is_wh:
        t1 = "维护"
        t2 = "运营"
    else:
        t2 = "维护"
        t1 = "运营"

    info = """<h2>{}</h2>
<p>预计 <strong>{}秒</strong> 后开始切换web运营状态。</p>
<pre>          <strong>状态</strong>： <span style="color:red">{}</span> ---> <span style="color:blue">{}</span>
     <strong>当前时间为</strong>： <span>{}</span>
     <strong>切换时间为</strong>： <span>{}</span>
        <strong>本机IP</strong>： <span>{}</span>
      <strong>终止cmds</strong>： <span>kill -9 {} 或者执行者直接 ctrl+C 终止操作</span>
</pre>""".format(subject, timenum, t1, t2, time1, time2, "x.x.x.x", os.getpid())

#    os.system('python /data/shell/mail.py %s %s %s' %(toname, subject, info))
#    n = 0
#    while  n < timenum:
#        n += 1
#        time.sleep(1)
#    print(info)

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
    #挂机维护
    logger.info("开始切换运营状态，运行--->维护。")

    # 1. 检查网页当前运营状态是否为运营中。
    check_ret = recheck_webpage(CHECK_URL,is_wh=False)
    if check_ret:
        logger.warn("当前运营状态为\"维护中\"，放弃切换为\"维护\"状态，结束操作。", )
        return False

    # 2. 备份所有web的配置文件
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        bak_ret = bak_cfgfile(rhost, ele.get("cfg_file", CFG_FILE))
        if not bak_ret[0]:
            logger.error("获取配置文件 {0} 失败，原因：{1}。结束操作。".format(ele.get("cfg_file", CFG_FILE), bak_ret[1]))
            return False
        logger.info("获取配置文件 {0} 成功。备份位置 {1} 。".format(ele.get("cfg_file", CFG_FILE), bak_ret[1]))

    # 3. 删除过久或者过多的备份文件
    check_ret = check_cfgfile(1)
    if not check_ret:
        logger.error("检查备份目录 {0} 下的文件并删除过期文件失败，请检查。结束操作。".format(BAK_DIR))
        return False

    # 4. 修改配置文件
    make_ret = make_maintenance_cfgfile()
    if not make_ret[0]:
        logger.error("修改配置文件失败，失败原因：{0}。中断操作。".format(make_ret[1]))
        return False
    logger.info("修改配置文件成功，保存路径为 {}。".format(os.path.join(BAK_DIR, TIMESTAMP, "online")))

    # 5. 邮件通知准备停机维护
    mail_notice(is_wh=False)

    # 6. 生成维护状态的配置文件
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        put_ret = put_cfgfile(rhost, ele.get("cfg_file", CFG_FILE))
        if not put_ret[0]:
            logger.error("推送【维护状态】配置文件到 {} 失败，原因为： {}。中断操作。".format(rhost.hostname, put_ret[1]),)
            return False
    logger.info("推送【维护状态】的配置文件成功。")

    # 7. 刷新服务
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        reload_ret = reload_service(rhost)
        if not reload_ret[0]:
            logger.error("刷新主机 {} nginx配置文件失败，原因：{}。中断操作。".format(rhost.hostname, reload_ret[1]),)
            return False
    logger.info("刷新nginx配置文件成功。",)

    # 8. 确认是否成功挂维护
    check_ret = recheck_webpage(CHECK_URL,is_wh=True)
    if not check_ret:
        logger.error("切换运营状态至【维护】失败，请检查。中断操作。", )
        return False
    logger.info("切换运营状态至【维护】成功。", )

    return True

def do_open(logger):
    #正常运营
    logger.info("开始切换运营状态，运行--->维护。")

    # 1. 确认网页当前运营状态为维护中
    check_ret = recheck_webpage(CHECK_URL,is_wh=True)
    if not check_ret:
        logger.warn("当前运营状态为\"运行中\"，放弃切换为\"运行\"状态，结束操作。", )
        return False

    # 2. 获取最新一次备份的正常运营状态的配置文件
    global TIMESTAMP
    is_match = False
    file_list = os.listdir(BAK_DIR)
    file_list = [x for x in file_list if re.match("^\d+$",x)]
    for ele in sorted(file_list, key=lambda x:os.stat(os.path.join(BAK_DIR,x)).st_mtime, reverse=True):
        is_match = True
        for client in CFG_DICT:
            if not os.path.isfile(os.path.join(BAK_DIR, ele, "online", client.get("host", "null"), os.path.basename(client.get("cfg_file", CFG_FILE)))):
                is_match = False
        if is_match:
            TIMESTAMP = ele
            break
    if not is_match:
        logger.error("在备份目录 {} 获取最近一次有效备份配置文件失败，中断操作。".format(BAK_DIR), )
        return False

    # 3. 邮件通知准备正常运营
    mail_notice()

    # 4. 替换配置文件
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        put_ret = put_cfgfile(rhost, ele.get("cfg_file", CFG_FILE), is_wh=False)
        if not put_ret[0]:
            logger.error("推送【维护状态】配置文件到 {} 失败，原因为： {}。中断操作。".format(rhost.hostname, put_ret[1]),)
            return False
    logger.info("推送【维护状态】的配置文件成功。")

    # 5. 刷新服务
    for ele in CFG_DICT:
        rhost = RHost(**ele)
        reload_ret = reload_service(rhost)
        if not reload_ret[0]:
            logger.error("刷新主机 {} nginx配置文件失败，原因：{}。中断操作。".format(rhost.hostname, reload_ret[1]),)
            return False
    logger.info("刷新nginx配置文件成功。",)

    # 6. 确认页面是否正常运营
    check_ret = recheck_webpage(CHECK_URL, is_wh=False)
    if not check_ret:
        logger.error("切换运营状态至【维护】失败，请检查。中断操作。", )
        return False
    logger.info("切换运营状态至【维护】成功。", )

    return True

def main():
    #设置日志对象
    with open(LOG_FILE, "w") as fobj:
        fobj.write("")
    logger = init_logger(LOG_NAME, LOG_FILE)

    opts_dict = check_opt()
    if opts_dict is None:
        return False
    exe_type = opts_dict.get("type", "")

    exe_ret = False
    if exe_type == "wh":
        exe_ret = do_maintenance(logger)
    elif exe_type == "open":
        exe_ret = do_open(logger)

    # 邮件通知已经正常运营
    mail_info()

    return exe_ret

if __name__ == "__main__":
    exe_ret = main()
    sys.exit(0) if exe_ret else sys.exit(1)
