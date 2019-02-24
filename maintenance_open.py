#!/usr/bin/env python
#coding=utf-8

import sys
import getopt


CFG_FILE = ""
#{"host":"", "user":"", "port":22, "passwd":"", "key_file":"", "remotef":""}
CFG_DICT = [
{"host":"47.52.47.71", "user":"snowchan", "key_file":"/home/allen/.ssh/ali1", }
]
BAK_DIR = ""
TIMESTAMP = time.strftime("%Y%m%d%H%M%S")

def useAge():
    useage = """使用示例：
\t{0} -h         # 获取简易的使用信息
\t{0} -t wh      # 切换至维护状态
\t{0} -t open    # 切换至正常运营状态""".format(sys.argv[0])
    print useage

def check_opt():
    get_opt = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:h", ["type", "help"])
        if any(map(lambda x: x in ["-h", "--help"], [x[0] for x in opts])):
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
            stdin, stdout, stderr = self.ssh.exec_command("%s;echo $?" % cmd)
            ret_txt = stdout.read()
            if b"0" not in ret_txt:
                errinfo = stderr.read()
                return False, errinfo
        return True, ""


def bak_cfgfile(rhost, file):
    try:
        for program in ("online", "maintenance"):
            if not os.path.isdir(BAK_DIR, TIMESTAMP, program, rhost.hostname):
                os.makedirs(BAK_DIR, TIMESTAMP, program, rhost.hostname)
        rhost.download_file(os.path.join(BAK_DIR, TIMESTAMP, "online", rhost.hostname, os.path.basename(file)), file)
    except:
        return False, ""
    return True, os.path.join(BAK_DIR, TIMESTAMP)

def check_cfgfile():
    try:
        file_list = os.listdir(BAK_DIR)
        file_list = sorted(file_list, key=lambda x:os.stat(os.path.join(BAK_DIR,x)).st_mtime, reverse=True)
        for x in file_list[20:]:
            shutil.rmtree(x)
    except Exception as e:
        return False, str(e)
    return True, ""

def make_maintenance_cfgfile():
    try:
        file_list = os.listdir(os.path.isdir(BAK_DIR, TIMESTAMP, "online"))
        for f in file_list:
            cfg_file_list = os.listdir(os.path.join(BAK_DIR, TIMESTAMP, "online", f))
            for each_cfg_file in cfg_file_list:
                if not os.path.isdir(BAK_DIR, TIMESTAMP, "maintenance", f):
                    os.makedirs(BAK_DIR, TIMESTAMP, "maintenance", f)
                wfile = os.path.join(BAK_DIR, TIMESTAMP, "maintenance", f, os.path.basename(each_cfg_file))
                with open(each_cfg_file) as fobj, open(wfile, "w")as wfobj:
                    pass
    except:
        return False
    return True

def put_cfgfile(rhost,file):
    try:
        rhost.upload_file(os.path.join(BAK_DIR, TIMESTAMP, "maintenance", rhost.hostname), file)
    except:
        return False
    return True

def mail_info():
    pass

def reload_service(rhost):
    reload_ret = rhost.reload_service()
    return reload_ret

def recheck_webpage():
    pass

def do_maintenance():
    for ele in CFG_DICT.getitems():
        rhost = RHost(**ele)
        bak_cfgfile(rhost, ele.get("cfg_file", CFG_FILE))
    check_cfgfile()
    make_maintenance_cfgfile()
    put_cfgfile()
    mail_info()
    reload_service()
    recheck_webpage()
    mail_info()
    pass

def do_open():
    put_cfgfile()
    mail_info()
    reload_service()
    recheck_webpage()
    mail_info()
    pass

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

    opts_dict = check_opt()
    if opts_dict is None:
        return False
    exe_type = opts_dict.get("type", "")
    if exe_type == "maintenance":
        do_maintenance()
    elif exe_type == "open":
        do_open()
    else:
        return False
    return True

if __name__ == "__main__":
    exe_ret = main()
    sys.exit(0) if exe_ret else sys.exit(1)
