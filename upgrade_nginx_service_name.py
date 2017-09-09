#!/usr/bin/env python
# coding: utf-8


import re
import os
import sys
import tempfile
import subprocess
import shutil
import time

CONFIG_PATH = "/tmp"
SERVER_NAME_FILE = "/tmp/err.log"
TIME_STAMP = time.strftime("%Y%m%d%H%M%S")


# 调用系统命令
# 正常返回输出结果，str类型，异常返回IOERROR，中断脚本
def exec_cmd(cmd):
    exec_result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = exec_result.communicate()
    if exec_result.returncode != 0:
#        return False, IOError("执行命令 %s 失败。原因：\n%s" % (cmd, out + err))
        return False, out + err
    return True, out + err

def get_project_list(cfg_path):
    file_list = os.listdir(cfg_path)
    project_list = []
    for fname in file_list:
        if fname.endswith("web.conf") or fname.endswith("mobile.conf"):
            project_name = re.sub("(web\.conf)|(mobile\.conf)$", "", fname)
            if project_name not in project_list:
                project_list.append(project_name)
    return project_list

def rechoose(choice_list):
    chocie_dict = {}
    if isinstance(choice_list, list):
        for k, v in enumerate(choice_list):
            chocie_dict[k] = v
    print "当前全部选项为："
    for k, v in chocie_dict.items():
        print "%s. %s" % (k, v)
    print "请输入选项编号（注意：多选通过\" \"或者\",\"分隔开来，直接回车表示全选）："
    while True:
        select_num = raw_input(":")
        if not select_num.strip():
            return choice_list
        if "," in select_num:
            select_num = select_num.split(",")
        else:
            select_num = select_num.split()
        select_num = [int(x) for x in select_num]
        if set(chocie_dict.keys()).intersection(set(select_num)) == set(select_num):
            break
        else:
            print "选择有误，请重新选择"
            continue
    result_list = []
    for k, v in chocie_dict.items():
        if k in select_num:
            result_list.append(v)
    return result_list

def get_server_name(original_file, web_config_file, mobile_config_file):
    with open(original_file) as fobj:
        service_list = fobj.readlines()
    service_list = [x.strip() for x in service_list if x.strip()]
    old_web_service_list = get_old_name(web_config_file)
    old_mobile_service_list = get_old_name(mobile_config_file)
    web_service_list = []
    for x in service_list:
        if x not in old_web_service_list:
            web_service_list.append("\t\t%s\twww.%s" % (x, x) if not x.startswith("#") else '\t\t%s' % x)
    mobile_service_list = []
    for x in service_list:
        if x not in old_mobile_service_list:
            mobile_service_list.append("\t\tm.%s" % x if not x.startswith("#") else "\t\t%s" % x)
    return {"web_list":web_service_list, "mobile_list":mobile_service_list}


def get_old_name(conf_file):
    cmd = """ sed -r -n "/^\s*server_name.*$/,/^.*;/ p" %s """ % conf_file
    service_info = exec_cmd(cmd)
    if service_info[0]:
        service_info = service_info[1]
    else:
        raise IOError("执行命令 %s 失败。" % cmd)
#    service_info = str(service_info, encoding='utf-8')
    service_list = service_info.split()
    service_list = [x for x in service_list if x not in ("server_name", ";")]
    result_list = []
    for url in service_list:
        if url.startswith("www.") or url.startswith("m."):
            deal_url = re.sub("^(www\.)|(m\.)","",url)
            if deal_url not in result_list: result_list.append(deal_url)
    return result_list

def upgrade_config_file(cfg_file, rule, text):
    is_start = False
    tmp_cfg_file = tempfile.mktemp()
    backup_filename = os.path.join(tempfile.gettempdir(), "backup_%s_%s" % (os.path.basename(cfg_file), TIME_STAMP))
    with open(cfg_file) as fobj, open(tmp_cfg_file, "w") as tmp_fobj:
        for line in fobj:
            if re.match(rule, line):
                is_start = True
            if is_start and re.match("^.*;\s*$", line):
                line_pre = line.split(";")[0]
                if line_pre.strip():
                    tmp_fobj.write("%s\n" % line_pre)
                tmp_fobj.write("%s\n" % text)
                tmp_fobj.write(";\n")
                is_start = False
            else:
                tmp_fobj.write(line)
    diff_info = exec_cmd("diff %s %s" % (tmp_cfg_file, cfg_file))[1]
#    diff_info = str(diff_info, encoding='utf-8')
    print "-"*50
    print "旧的配置文件保存到了 %s" % backup_filename
    print "文件 %s 更新前后差异：" % cfg_file
    print diff_info
    print "-"*50
    shutil.move(cfg_file, backup_filename)
    shutil.move(tmp_cfg_file, cfg_file)
    return True

def ask_file_name(filename):
    new_file_name = str(raw_input("请输入指定的文件的绝对路径[%s]：" % filename))
    if not new_file_name.strip():
        new_file_name = filename
    if not os.path.isfile(new_file_name):
        raise FileExistsError("文件 %s 不存在。" % new_file_name)
    return new_file_name

def main():
    rule = "^\s*server_name.*$"
    server_file_name = ask_file_name(SERVER_NAME_FILE)
    project_list = get_project_list(CONFIG_PATH)
    project_list = rechoose(project_list)
    for item_name in project_list:
        web_config_file = os.path.join(CONFIG_PATH, "%sweb.conf" % item_name)
        mobile_config_file = os.path.join(CONFIG_PATH, "%smobile.conf" % item_name)
        new_name = get_server_name(server_file_name, web_config_file, mobile_config_file)
        if os.path.isfile(web_config_file):
            upgrade_config_file(web_config_file, rule, "\n".join(new_name["web_list"]))
        if os.path.isfile(mobile_config_file):
            upgrade_config_file(mobile_config_file, rule, "\n".join(new_name["mobile_list"]))
    return True

if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)
