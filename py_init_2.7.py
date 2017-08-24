#!/usr/bin/env python
# coding: utf-8

"""
1，确认py版本
    ---2.7以下安装
    ---2.7以上跳过安装

2，确认pip是否已经安装
    ---已安装，跳过
    ---未安装
        ---2以上版本安装pip_9.0.1
        ---3以上版本安装pip
"""

import sys
import os
import re
import subprocess
import shutil

ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))
PY_FILE = os.path.join(ABSOLUTE_PATH, "Python-2.7.13.tgz")
INSTALL_PATH = "/usr/local/python2.7.13"
PY_MODULE_PATH = os.path.join(ABSOLUTE_PATH, "py_module")

# 调用系统命令
# 正常返回输出结果，str类型，异常返回IOERROR，中断脚本
def exec_cmd(cmd):
    exec_result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = exec_result.communicate()
    if exec_result.returncode != 0:
        raise IOError("执行命令 %s 失败。原因：\n%s" % (cmd, out + err))
    return out + err


def decompress(file, target_path):
    file_type = re.search(".*\.([^.]*)$", file).groups()[0]
    if file_type in ['gz', 'tgz', 'bz2', 'tar']:
        file_type = "tar"
    if file_type == "tar":
        cmd1 = "tar -xf %s -C %s" % (file, target_path)
    elif file_type == "zip":
        cmd1 = "unzip -o %s -d %s" % (file, target_path)
    else:
        print "不支持的解压类型%s，脚本终止。" % file_type
        return False
    try:
        exec_cmd(cmd1)
    except Exception, e:
        print e
        return False
    print "执行命令 %s 成功。" % cmd1
    return True


def source_install(tar_file, install_path, config_args=""):
    decompress(tar_file, ABSOLUTE_PATH)
    install_dir_path = os.path.join(ABSOLUTE_PATH, re.sub(".tgz$", "", os.path.basename(tar_file)))
    os.chdir(install_dir_path)
    cmd1 = "./configure --prefix=%s %s" % (install_path, config_args)
    cmd2 = "make"
    cmd3 = "make install"
    for cmd in (cmd1, cmd2, cmd3):
        try:
            cmd_info = exec_cmd(cmd)
        except Exception, e:
            print e
            return False
        print "执行命令 %s 成功。" % cmd
    if os.path.isdir(install_dir_path):
        shutil.rmtree(install_dir_path)
    return True


def py_install(tar_file, install_path):
    decompress(tar_file, install_path)
    install_dir_path = os.path.join(install_path, re.sub("(\.tar\.gz)|(\.tgz)|(\.zip)$", "", os.path.basename(tar_file)))
    os.chdir(install_dir_path)
    cmd1 = "python setup.py install"
    for cmd in (cmd1, ):
        try:
            cmd_info = exec_cmd(cmd)
        except Exception, e:
            print e
            return False
        print "执行命令 %s 成功。" % cmd
    if os.path.isdir(install_dir_path):
        shutil.rmtree(install_dir_path)
    return True

def compare_version(str1, str2):
    list1 = str1.split(".")
    list2 = str2.split(".")
    compare_num = min(len(list1), len(list2))
    for i in range(compare_num):
        if list1[i] < list2[i]:
            return False
    return True


def py_install_2_7_13():
    source_file = PY_FILE
    install_path = INSTALL_PATH
    config_args = ""
    if not os.path.isfile(source_file):
        print "安装源文件 %s 不存在，退出安装。" % source_file
        return False
    if not os.path.isdir(install_path):
        os.makedirs(install_path)
    try:
        cur_version = exec_cmd("python --version")
        cur_version = cur_version.split()[-1]
    except Exception,e:
        cur_version = "0"
    print "@cur_version=%s" % cur_version
    if not compare_version(cur_version, "2.7"):
        source_install(source_file, install_path, config_args)
        if make_link(INSTALL_PATH):
            print "创建link链接成功。"
    else:
        print "当前python版本高于或者等于2.7，跳过安装python 2.7.13的步骤。"
    return True


def make_link(app_path):
    bin_path = os.path.join(app_path, "bin/")
    if os.path.isdir(bin_path):
        cmd = "ln -s %s %s" %(os.path.join(bin_path, "./*"), "/usr/local/bin/")
    try:
        exec_cmd(cmd)
    except:
        pass
    return True

def install_py_module_online(module_name):
    cmd = "pip install  %s" % "".join(module_name.split("-")[:-1])
    try:
        exec_info = exec_cmd(cmd)
        if not exec_info:
            raise IOError("")
    except Exception, e:
        print "err:%s" % e
        print "在线安装模块 %s 失败，尝试离线安装。" % module_name
        return False
    print "在线安装模块 %s 成功。" % module_name
    return True

def install_py_module_offline(module_name):
    module_file_path_gz = os.path.join(PY_MODULE_PATH, "%s.tar.gz" % module_name)
    module_file_path_zip = os.path.join(PY_MODULE_PATH, "%s.zip" % module_name)
    if not os.path.isdir(PY_MODULE_PATH):
        print "py模块安装目录 %s 不存在。" % PY_MODULE_PATH
        return False
    is_exist = False
    for m_file in (module_file_path_gz, module_file_path_zip):
        if os.path.isfile(m_file):
            is_exist = True
            break
    if not is_exist:
        print "py模块 %s 的源文件不存在，退出安装。" % module_name
        return False
    if not py_install(m_file, PY_MODULE_PATH):
        return False

    return True

def main():
    if not py_install_2_7_13():
        return False
    modules_list = ["setuptools-36.2.7", "pip-9.0.1"]
    for module_name in modules_list:
        if not install_py_module_online(module_name):
            if not install_py_module_offline(module_name):
                print "安装模块 %s 失败。" % module_name
    return True


if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)
