#!/bin/bash

function Log(){
    log_level=$(echo $1 |tr [a-z] [A-Z])
    case ${log_level} in
    ERROR)
        log_level=$(echo -e "\E[33;42m\033[1mERROR\033[0m")
    ;;
    INFO)
        log_level=$(echo -e "\E[34;43m\033[1mINFO\033[0m")
    ;;
    *)
        log_level=$(echo -e "\E[34;49m\033[1mUNKNOWN\033[0m")
    ;;
    esac
    log_info=$2
    cur_pid=\[$$\]
    cur_time=\[$(date +"%Y-%m-%d %H:%M:%S")\]
    printf "%s %-7s %-9s : %s\n" "${cur_time}" "${cur_pid}" "${log_level}" "${log_info}" | tee -a ${INSTALL_LOG}
}

function pre_check(){
    local func_result=0
    local tools_list=$@
    yum repolist &> /dev/null
    local tmp_result=$?
    if [ "${tmp_result}" != "0" ] 
    then
        Log "error" "Config with yum is invallidate."
    fi
    for tool in ${tools_list}
    do
        tmp_result=$(rpm -qa ${tool})
        if [ -z "${tmp_result}" ]
        then
            yum install -y ${tool} &> /dev/null
            install_result=$?
            if [ ${install_result} != 0 ]
            then
                Log "error" "Failed to install ${tool}."
                func_result=1
            fi
        fi
    done
    return ${func_result}
}

function decompress_package(){
    local package_type=$1
    local package_name=$2
    local target_path=$3
    if [ "${package_type}" == "gz" ]
    then
        tar -zxf ${package_name} -C ${target_path} &>> ${INSTALL_LOG}
    elif [ "${package_type}" == "bz2" ]
    then
        tar -jxf ${package_name} -C ${target_path} &>> ${INSTALL_LOG}
    elif [ "${package_type}" == "xz" ]
    then
        tar -Jxf ${package_name} -C ${target_path} &>> ${INSTALL_LOG}
    elif [ "${package_type}" == "gzip" ]
    then
        gzip -d ${package_name} &> /dev/null &>> ${INSTALL_LOG}
    elif [ "${package_type}" == "zip" ]
    then
        unzip -o ${package_name} -d ${target_path} &>> ${INSTALL_LOG}
    elif [ "${package_type}" == "tar" ]
    then
        tar -xf ${package_name} -C ${target_path} &>> ${INSTALL_LOG}
    else
        Log "error" "The type(${package_type}) is not support."
        return 1
    fi
    local tmp_result=$?
    if [ "${tmp_result}" == "0" ]
    then
        Log "info" "Decompress ${package_name} success."
        return 0
    else
        Log "error" "Decompress ${package_name} failed."
        return 1
    fi
}

function compile_install(){
    package_name=$1
    filename=$2
    compile_option=$3
    local tmp_result=0
    record_log="${ABSOLUTE_PATH}/${package_name}.log"
    cd ${filename} &> ${record_log}
    
    ./configure ${compile_option} &>> ${record_log} || tmp_result=1
    make &>> ${record_log} || tmp_result=1
    make install &>> ${record_log} || tmp_result=1
    
    cd ${ABSOLUTE_PATH} &>> ${record_log}
    if [ "${tmp_result}" == "0" ]
    then
        Log "info" "Success to install ${package_name}."
    else
        Log "error" "Failed to install ${package_name}."
    fi
    return ${tmp_result}

}

function py_install(){
    local package_name=$1
    local install_dir=$2
    local tmp_result=0
    local record_log="${ABSOLUTE_PATH}/${package_name}.log"
    pip install ${package_name} &> ${record_log}
    if [ "$?" == "0" ]
        then
        return 0
    fi
    if [ ! -d "${install_dir}" ]
        then
        Log "error" "Failed to install ${package_name}."
        return 1
    fi
    cd ${install_dir} &> ${record_log}
    python setup.py install &> ${record_log} || tmp_result=$?
    cd - &> ${record_log}
    return ${tmp_result}
}

function fn_main()
{
    RELATIVE_PATH=$(dirname $0)
    ABSOLUTE_PATH=$(cd ${RELATIVE_PATH} &> /dev/null;pwd)
    INSTALL_LOG="${ABSOLUTE_PATH}/install.log"
    INSTALL_DIR="/usr/local/python27"
    PKG=""
    local tmp_result=0

    if [ "$(whoami)" != "root" ]
    then
        Log "error" "This script must executed by root."
        return 1
    fi

    pre_check "libffi" "openssl-devel" "python-devel" "libffi-devel"
    check_result=$(rpm -qa libffi-devel)
    if [ "${check_result}" == "" ]
    then
        if $(grep -q " 6\.. " /etc/redhat-release )
        then
            rpm -ih "${ABSOLUTE_PATH}/libffi-devel-3.0.5-3.2.el6.x86_64.rpm" &> ${INSTALL_LOG}
        fi
    fi
    ldconfig

    cd ${ABSOLUTE_PATH} &> /dev/null
    for package_name in "Python-2.7.14.tgz/gz" "pycrypto-2.6.1.tar.gz/gz" "pyasn1-0.1.9.tar.gz/gz" "cryptography-1.5.tar.gz/gz" "cffi-1.7.0.tar.gz/gz" "pycparser-2.14.tar.gz/gz" "six-1.10.0.tar.gz/gz" "idna-2.1.tar.gz/gz" "paramiko-2.1.0.tar.gz/gz" "setuptools-26.0.0.tar.gz/gz" "enum34-1.1.6.tar.gz/gz" "ipaddress-1.0.17.tar.gz/gz"
    do
        local tmp_package=${package_name%/*}
        local tmp_type=${package_name#*/}
        decompress_package "${tmp_type}" "${ABSOLUTE_PATH}/${tmp_package}" "${ABSOLUTE_PATH}"
        tmp_result=$?
        if [ "${tmp_result}" != 0 ]
        then
            if [ "${tmp_package}" != "Python-2.7.14.tgz" ]
                then
                continue
            fi
            Log "error" "Failed to decompress ${package_name}."
            return ${tmp_result}
        fi
    done

    if [ ! -d "/usr/local/python27" ]
    then
        compile_install "Python27" "${ABSOLUTE_PATH}/Python-2.7.14" "--prefix=/usr/local/python27" 
        tmp_result=$?
        if [ "${tmp_result}" != 0 ]
        then
            Log "error" "Failed to compile install Python27."
            return ${tmp_result}
        fi
        ln -s /usr/local/python27/bin/* /usr/local/bin/ &> /dev/null
        source /etc/profile
        Log "info" "Success to install Python27."
    fi

    for pkg in "setuptools-26.0.0" "pycrypto-2.6.1" "pycparser-2.14" "cffi-1.7.0" "ipaddress-1.0.17" "enum34-1.1.6" "six-1.10.0" "pyasn1-0.1.9" "idna-2.1" "cryptography-1.5" "paramiko-2.1.0"
    do
        py_install "${pkg%-*}" "${ABSOLUTE_PATH}/${pkg}"
        if [ "${tmp_result}" != 0 ]
        then
            Log "error" "Failed to install ${pkg%-*}."
            return ${tmp_result}
        fi
        Log "info" "Success to install ${pkg%-*}."
    done

    return ${tmp_result}
}

fn_main
MAIN_RET=$?
if [ "${MAIN_RET}" != "0" ] 
then 
    Log "error" "Failed to execute $0."
fi
exit ${MAIN_RET}