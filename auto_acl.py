#!/usr/bin/env python3
#coding=utf-8

import sys
import time
import subprocess


ORIGINAL_FILE = ""
CHECK_FILE = ""
IS_DEBUG = True

def exe_cmds(cmds):
    for cmd in cmds:
        cmd_ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while cmd_ret.poll() == None:
            time.sleep(1)
        if cmd_ret.poll() == 0:
            debug_info("执行命令 %s" % cmd, "")
        else:
            debug_info("执行命令 %s" % cmd, cmd_ret.stdout.read()+b"\n"+cmd_ret.stderr.read())
            return False
    return True

def debug_info(item, info):
    if not IS_DEBUG:
        return True
    if not info:
        info = "完成【%s】" % item
    else:
        info = "{0} 开始【{1}】错误信息 {0}\n{2}\n{0} 结束【{1}】错误信息 {0}".format("-"*16, item, info)
    print(info)
    return True

def check_ips():
    is_change = False
    info = ""
    ret = True
    try:
        with open(ORIGINAL_FILE) as fobj1, open(CHECK_FILE) as fobj2:
            original_list = sorted([x.strip() for x in fobj1.readlines() if x.strip()])
            check_list =  sorted([x.strip() for x in fobj2.readlines() if x.strip()])
            if original_list != check_list:
                is_change = True
            debug_info("文件对比", "")
    except Exception as e:
        original_list = []
        check_list = []
        exe_cmds(["systemctl stop firewalld &> /dev/null", ])
        debug_info("文件对比", str(e))
        ret = False
    return ret, is_change, original_list, check_list

def reload_file():
    info = ""
    try:
        with open(CHECK_FILE) as fobj1, open(ORIGINAL_FILE, "w") as fobj2:
            linelist = [x for x in fobj1.readlines() if x.strip()]
            for l in linelist:
                fobj2.write(l)
        debug_info("文件刷新", "")
        return True
    except Exception as e:
        debug_info("文件刷新", str(e))
        return False

def reload_service(original_list, check_list):
    cmd1 = "firewall-cmd --add-rich-rule 'rule family=\"ipv4\" source address=\"{}\" accept'"
    cmd2 = "firewall-cmd --remove-rich-rule 'rule family=\"ipv4\" source address=\"{}\" accept'"
    cmdlist = []

    try:
        for ele in original_list:
            if ele not in check_list:
                cmdlist.append(cmd2.format(ele))
                cmdlist.append(cmd2.format(ele)+ " --permanent")
        for ele in check_list:
            if ele not in original_list:
                cmdlist.append(cmd1.format(ele))
                cmdlist.append(cmd1.format(ele)+ " --permanent")
        exe_ret = exe_cmds(cmdlist)
        info = ""
        if not exe_ret:
            info = "略"
    except Exception as e:
        info = str(e)
        exe_ret = False
    debug_info("文件刷新", info)
    return exe_ret

def main():
    ret, is_change, original_list, check_list = check_ips()
    if not ret:
        return False
    if not is_change:
        return True
    file_ret = reload_file()
    if not file_ret:
        return False

    service_ret = reload_service(original_list, check_list)
    if not service_ret:
        return False

    return True

if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)
