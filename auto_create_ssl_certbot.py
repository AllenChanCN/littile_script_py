#!/usr/bin/env python3
#coding=utf-8

import os
import sys
import re
import time
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import paramiko
import requests

#ALL_ADMIN = "admin@weststarinc.co"
#PH_ADMIN = "ph.admin@weststarinc.co"
ALL_ADMIN = "allen.c@auxworld.net"
PH_ADMIN = "allen.c@auxworld.net"
#这个证书是为了方便脚本执行shell命令，要求能够
KEY_FILE = "/opt/id_rsa"

class S_Host(object):
    def __init__(self,ip="127.0.0.1", user="root", pwd="", port=22, keyfile="", endTag=" ", *args):
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
        self.Debug = True
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
            endTag = self.endTag
            ret = ""
            isGet = False
            isFirst = True
            for cmdinfo in cmds:
                endTag = cmdinfo.get("endTag", endTag)
                cmd =  cmdinfo.get("cmd", "")
                match = cmdinfo.get("match", [])
                isGet = cmdinfo.get("isGet", False)
                breakpoint = cmdinfo.get("breakpoint", [])
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
                    for index,(out_key, in_words, match_num) in enumerate(match):
                        if ret.endswith(out_key) and match_num != 0:
                            self.channel.send("%s\n" % in_words)
                            if match_num > 0:
                                match[index][2] -= 1
                            time.sleep(0.1)
                            break
                        elif ret.endswith(out_key) and match_num == 0:
                            for key,bp in breakpoint:
                                if not callable(bp):
                                    continue
                                if key in ret:
                                    bp(ret)
                                    match[index][2] -= 1
                                    self.channel.send("%s\n" % in_words)
                                    break
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

#[[shaValue, address, retInfo, url, ssl_url],]
def analytics_info(infos):
    infos_dict = {}
    domain_uniq_list = {}
    new_domain_sort_dict = {}
    domain_match_list = []
    sha_list = []
    new_infos = []

    for info in infos:
        shaValue = info[0]
        address = info[1]
        urls = info[3]
        infos_dict.setdefault(shaValue, [])
        for url in urls:
            main_domain = ".".join(url.split(".")[-2:])
            if main_domain not in domain_uniq_list.keys():
                domain_uniq_list.update({main_domain:[[shaValue, url, address],]})
            else:
                domain_uniq_list[main_domain].append([shaValue,url, address])

    m, n = 0, 0
    while n < len(domain_uniq_list.keys()):
        tmp_domain = sorted(domain_uniq_list.keys())[n]
        infos = domain_uniq_list[tmp_domain]

        tmp_sha_list = []
        for info in infos:
            if info[0] not in sha_list:
                tmp_sha_list.append(info[0])
                sha_list.append(info[0])

        if not tmp_sha_list:
            n += 1
            continue
        new_array_list = []
        for _, tmp_infos in domain_uniq_list.items():
            for tmp_info in tmp_infos:
                if tmp_info[0] in tmp_sha_list:
                    m += (len(tmp_info) -1)
                    if m >= 50:
                        new_infos.append(new_array_list)
                        new_array_list = []
                        m = (len(tmp_info) -1)
                    new_array_list.append(tmp_info[1:])
        new_infos.append(new_array_list)
        n += 1

    list_count = zip(range(len(new_infos)),[len(x) for x in new_infos])
    list_count = sorted(list_count, key=lambda x:x[1])
    n = 0
    new_sort_list = [[]]
    for x,y in list_count:
        n += y
        if n >= 50:
            new_sort_list.append([])
            n = y
        new_sort_list[-1].append(x)

    new_domain_list = []
    for x in new_sort_list:
        new_domain_list.append([])
        for n in x:
            new_domain_list[-1] += new_infos[n]

    return new_domain_list

def exec_certbo_single(info):
#    cmds = [
#    {"cmd":"mkdir -p /data/shell"},
#    {"cmd":"[ ! -f \"/data/shell/certbot-auto\" ] && wget https://dl.eff.org/certbot-auto -P /data/shell"},
#    {"cmd":"[ ! -x \"/data/shell/certbot-auto\" ] && chmod a+x /data/shell/certbot-auto"},
#    ]
#    s = S_Host(keyfile=KEY_FILE, endTag="# ")
#    ret = s.exeCmds(cmds)
#    cmd = "/data/shell/certbot-auto --manual --preferred-challenges dns-01 certonly"
#    for ele in info:
#        cmd += " -d \"%s\"" % ele[0]
#    url_num = len(info) - 1
#    cmd_info = {"cmd":cmd, "endTag":"# ", "isGet":True, "match":[["(Y)es/(N)o: ", "y",-1],["Press Enter to Continue", "",url_num]], "breakpoint":[["verify the record is deployed", modify_txt_records],]}
#    ret = s.exeCmds([cmd_info])
    info = [['downloads.mihoyo168.com', ['104.155.231.35']], ['auto.mihoyo168.com', ['104.155.231.35']], ['auth.mihoyo168.com', ['104.155.231.35']]]
    ret = [['Saving debug log to /var/log/letsencrypt/letsencrypt.log', 'Plugins selected: Authenticator manual, Installer None', 'Obtaining a new certificate', 'Performing the following challenges:', 'dns-01 challenge for auth.mihoyo168.com', 'dns-01 challenge for auto.mihoyo168.com', 'dns-01 challenge for downloads.mihoyo168.com', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'NOTE: The IP of this machine will be publicly logged as having requested this', "certificate. If you're running certbot in manual mode on a machine that is not", "your server, please ensure you're okay with that.", '', 'Are you OK with your IP being logged?', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', '(Y)es/(N)o: y', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Please deploy a DNS TXT record under the name', '_acme-challenge.auth.mihoyo168.com with the following value:', '', 'lnaVT-N0YeTcXjCCxxTaWfuY3azCdchxPYT7RkpicKY', '', 'Before continuing, verify the record is deployed.', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Press Enter to Continue', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Please deploy a DNS TXT record under the name', '_acme-challenge.auto.mihoyo168.com with the following value:', '', 'WeU6fa3TfpaLDivBr_DqKLvYbdd98QxcGnFOsJ1Jp08', '', 'Before continuing, verify the record is deployed.', '(This must be set up in addition to the previous challenges; do not remove,', 'replace, or undo the previous challenge tasks yet. Note that you might be', 'asked to create multiple distinct TXT records with the same name. This is', 'permitted by DNS standards.)', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Press Enter to Continue', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Please deploy a DNS TXT record under the name', '_acme-challenge.downloads.mihoyo168.com with the following value:', '', 'SvX2IIIlggn48r12cfMrypu5PIvqzOaujLaJooqEHEU', '', 'Before continuing, verify the record is deployed.', '(This must be set up in addition to the previous challenges; do not remove,', 'replace, or undo the previous challenge tasks yet. Note that you might be', 'asked to create multiple distinct TXT records with the same name. This is', 'permitted by DNS standards.)', '', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -', 'Press Enter to Continue', 'Waiting for verification...', 'Cleaning up challenges', '\x1b[1m', 'IMPORTANT NOTES:', '\x1b[0m - Congratulations! Your certificate and chain have been saved at:', '   /etc/letsencrypt/live/downloads.mihoyo168.com/fullchain.pem', '   Your key file has been saved at:', '   /etc/letsencrypt/live/downloads.mihoyo168.com/privkey.pem', '   Your cert will expire on 2019-06-25. To obtain a new or tweaked', '   version of this certificate in the future, simply run certbot-auto', '   again. To non-interactively renew *all* of your certificates, run', '   "certbot-auto renew"', ' - If you like Certbot, please consider supporting our work by:', '', "   Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate", '   Donating to EFF:                    https://eff.org/donate-le', '']]
    mail_result(info, ret[0])
    return

def modify_txt_records(ret):
    ret = deal_Info(ret.split("\n"))
    m, n = 0, 0
    is_done = False
    notice_infos = ret
    while True:
        if n == 0:
            mail_notice(notice_infos, m)
        notice_infos = query_txt(notice_infos)
        n += 1
        if n >= 180:
            m += 1
            n = 0
        if not len(notice_infos):
            is_done = True
            break
        if m >= 5:
            break
        time.sleep(20)

    return ret

def deal_Info(info):
    ret = []
    n = -2
    for ele in info:
        if re.match("^\s*Please deploy a DNS TXT record under the name\s*$", ele):
            n = 3

        if n == 2:
            domain = ele.split()[0]
        elif n == 0:
            value = ele.strip()

        if n > 0:
            n -= 1
        elif n == 0:
            ret.append([domain, value])
            domain = ""
            value = ""
            n = -2
    return ret

def exec_certbo(infos):
    for info in infos:
        exec_certbo_single(info)
    return

def mail_send(toname, subject, text, attachment=[], is_html=True):
    smtpserver = 'smtp.gmail.com'
    sender = 'admin.tech2@networkws.com'
    username= 'admin.tech2@networkws.com'
    password='zaki@ph.admin'
    port=587

    # 创建一个带附件的实例
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = toname
    message['Subject'] = Header(subject, 'utf-8')

    # 邮件正文内容
    if is_html:
        text_type = "html"
    else:
        text_type = "plain"
    message.attach(MIMEText(text, text_type, 'utf-8'))

    # 构造附件1（附件为TXT格式的文本）
    for ele in attachment:
        fname = os.path.basename(ele)
        att = MIMEText(open(ele, 'rb').read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="%s"' % fname
        message.attach(att)

    smtpObj = smtplib.SMTP_SSL()  # 注意：如果遇到发送失败的情况（提示远程主机拒接连接），这里要使用SMTP_SSL方法
    smtpObj.connect(smtpserver)
    smtpObj.login(username, password)
    smtpObj.sendmail(sender, toname, message.as_string())
    smtpObj.quit()
    return

def mail_notice(infos, num):
    text = """Dear 臺灣同事：
      請幫忙添加一下TXT類型的解析記錄，詳情如下。
"""
    for domain,value in infos:
        text += """
 Add TXT record with the name/host
 {}
 with the value
 {}
 and a TTL (Time to Live) (in seconds) of
 1""".format(domain, value)
    subject = "請根据郵件內容添加TXT類型解析記錄"

    if num == 0:
        toname = ALL_ADMIN
    else:
        toname = PH_ADMIN
        text = "请根据实际情况确定是否需要转发给台湾同事，并加以催促\n" + text

    mail_send(toname, subject, text)
    return

def mail_result(domainInfo, fileInfo):
    cert_file = ""
    key_file = ""
    zipfile = ""

    toname = PH_ADMIN
    subject = "CA证书更新邮件"

    n = -1
    for line in fileInfo:
        if "Congratulations!" in line:
            n = 3
            continue

        if n < 0:
            continue
        elif n >= 0:
            n -= 1

        if n == 2:
            cert_file = line.strip()
        elif n == 0:
            key_file = line.strip()

    if not key_file or cert_file:
        text = """<pre>申请CA证书失败，详情如下：
        <code>
        {}
        </code>
        </pre>""".format("\n".join(fileInfo))
        mail_send(toname, subject, text)
    else:
        zipfile = compress_file([cert_file, key_file])
        attachment = [zipfile, ]
        text = "<pre>请为以下域名更新CA证书。证书请见附件。如果包含高防IP，请转发给台湾同事。"
        for ele in domainInfo:
            text += """

            域名：{}
            解析地址：{!r}""".format(*ele)
        text += "</pre>"
        mail_send(toname, subject, text, attachment=attachment)

    if os.path.isfile(zipfile):
        os.remove(zipfile)
    return

def compress_file(files):
    timestamp = time.strftime("%Y%m%d%H%M%S")
    while True:
        filename = "/tmp/sslforfree_%s" % timestamp
        if os.path.isdir(filename):
            timestamp = str(int(timestamp) + 1)
            continue
        else:
            os.makedirs(filename)
            break

    cmds = []
    for f in files:
        tmp_cmd = {"cmd":"cp {} /tmp/sslforfree_{}".format(f, timestamp)}
        cmds.append(tmp_cmd)
    cmds += [
    {"cmd":"zip -q -r /tmp/sslforfree_{0}.zip /tmp/sslforfree_{0}".format(timestamp)},
    {"cmd":"rm -rf /tmp/sslforfree_%s" % timestamp}
    ]
    s = S_Host(keyfile=KEY_FILE, endTag="# ")
    ret = s.exeCmds(cmds)

    filename = "/tmp/sslforfree_%s.zip" % timestamp
    if os.path.isfile(filename):
        return "/tmp/sslforfree_%s.zip" % timestamp
    else:
        return None

def query_txt(infos):
    ret = []
    for info in infos:
        url = info[0]
        expect_value = info[1]
        query_url = "https://www.sslforfree.com/create?dns_txt_verify=%s" % url
        req = requests.get(query_url).text
        req_value = re.split("<strong>|</strong>",req)
        if not(len(req_value) > 1 and req_value[-2] == expect_value):
            ret.append([url, expect_value])
    return ret

def main(infos):
    new_infos = analytics_info(infos)
    exec_certbo(new_infos)
    return

if __name__ == "__main__":
    infos = [['A4:9A:08:22:D4:F0:48:20:AB:99:0C:0A:EF:D8:17:D8:6D:8A:FB:DC', ['104.155.231.35'], (True, '证书未过期，到期时间为 2019年06月04日00时04分18秒'), ["downloads.mihoyo168.com", "auto.mihoyo168.com", "auth.mihoyo168.com"], ['']]]
    RET = main(infos)
    sys.exit(0) if RET else sys.exit(1)
