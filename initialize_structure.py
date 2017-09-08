#!/usr/bin/env python3
# coding: utf-8

#initialize ansible directories

import os
import sys

DIR_STRUCTURE = """production                # inventory file for production servers 关于生产环境服务器的清单文件
stage                     # inventory file for stage environment 关于 stage 环境的清单文件

group_vars/
    group1                 # here we assign variables to particular groups 这里我们给特定的组赋值
    group2                 # ""
host_vars/
    hostname1              # if systems need specific variables, put them here 如果系统需要特定的变量,把它们放置在这里.
    hostname2              # ""

library/                  # if any custom modules, put them here (optional) 如果有自定义的模块,放在这里(可选)
filter_plugins/           # if any custom filter plugins, put them here (optional) 如果有自定义的过滤插件,放在这里(可选)

site.yml                  # master playbook 主 playbook
webservers.yml            # playbook for webserver tier Web 服务器的 playbook
dbservers.yml             # playbook for dbserver tier 数据库服务器的 playbook

roles/
    common/               # this hierarchy represents a "role" 这里的结构代表了一个 "role"
        tasks/            #
            main.yml      #  <-- tasks file can include smaller files if warranted
        handlers/         #
            main.yml      #  <-- handlers file
        templates/        #  <-- files for use with the template resource
            ntp.conf.j2   #  <------- templates end in .j2
        files/            #
            bar.txt       #  <-- files for use with the copy resource
            foo.sh        #  <-- script files for use with the script resource
        vars/             #
            main.yml      #  <-- variables associated with this role
        defaults/         #
            main.yml      #  <-- default lower priority variables for this role
        meta/             #
            main.yml      #  <-- role dependencies

    webtier/              # same kind of structure as "common" was above, done for the webtier role
    monitoring/           # ""
    fooapp/               # "" """

def split_describe(text):
    line_record = []
    for line in text.split("\n"):
        if not line.split("#")[0].strip():
            continue
        line_info = line.split("#")
        if line_info[0].strip().endswith(os.sep):
            f_type = "d"
        else:
            f_type = "f"
        level_length = len(line_info[0].rstrip()) - len(line_info[0].strip())
        file_name = line_info[0].strip().rstrip(os.sep)
        if f_type == "f":
            comments = line_info[1].strip()
        else:
            comments = ""
        line_record.append([f_type, level_length, file_name, comments])
    return line_record

def build_structure(info_list):
    for index, ele in enumerate(info_list):
        if index != 0:
            is_up = ""
            for pre_index, pre_ele in enumerate(reversed(info_list[:index])):
                if ele[1] == pre_ele[1]:
                    break
                elif ele[1] > pre_ele[1]:
                    if pre_ele[0] != "d":
                        raise ValueError("Error describe information.")
                    os.chdir(os.path.join("./", pre_ele[2]))
                    break
                elif ele[1] < pre_ele[1]:
                    if not is_up or is_up < pre_ele[1]:
                        is_up = pre_ele[1]
                        os.chdir("../")
                    continue
        if ele[0] == "f":
            with open(ele[2], 'w') as fobj:
                fobj.write("#%s\n" % ele[3])
        else:
            if not os.path.isdir(os.path.join("./",ele[2])):
                os.mkdir(ele[2])
    return True

if __name__ == "__main__":
    build_info = split_describe(DIR_STRUCTURE)
    sys.exit(0) if build_structure(build_info) else sys.exit(1)

