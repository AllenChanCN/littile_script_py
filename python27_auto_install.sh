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
    if [ ! -f "${package_name}" ]
    then
        Log "error" "File ${package_name} is not exists."
        return 6
    fi
    if [ "${package_type}" == "gz" ]
    then
        tar -zxf ${package_name} -C ${target_path}
    elif [ "${package_type}" == "bz2" ]
    then
        tar -jxf ${package_name} -C ${target_path}
    elif [ "${package_type}" == "xz" ]
    then
        tar -Jxf ${package_name} -C ${target_path}
    elif [ "${package_type}" == "gzip" ]
    then
        gzip -d ${package_name} &> /dev/null
    elif [ "${package_type}" == "zip" ]
    then
        unzip -o ${package_name} -d ${target_path} &> ${INSTALL_LOG}
    elif [ "${package_type}" == "tar" ]
    then
        tar -xf ${package_name} -C ${target_path}
    else
        echo "The type(${package_type}) is not support."
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
    cd ${install_dir} &> ${record_log}
    python setup.py install &>> ${record_log} || tmp_result=$?
    if [ "${tmp_result}" == "0" ]
    then
        Log "info" "Success to install ${package_name}."
    else
        Log "error" "Failed to install ${package_name}."
    fi
    cd - &>> ${record_log}
    return ${tmp_result}
}

function install_py_modules(){
    packages=($1)
    is_base=$2
    for pkg in ${packages[@]}
    do
        cd "${ABSOLUTE_PATH}"
        if [ -f "${pkg%/*}" ]
        then
            tmp_result=0
            decompress_package "${pkg#*/}" "${pkg%/*}" "${ABSOLUTE_PATH}" || tmp_result=1
            if [ "${tmp_result}" == "0" ]
            then
                py_install "${pkg%%.*}" "${ABSOLUTE_PATH}/${pkg%%.*}*" || tmp_result=2
            fi
        else
            Log "error" "Can't find package ${pkg%/*}."
            return 4
        fi
        case ${tmp_result} in
            1)
                if [ "${is_base}" == "1" ]
                then
                    Log "error" "Failed to decompress ${pkg%/*}."
                    return 1
                else
                    Log "warn" "Failed to decompress ${pkg%/*}."
                fi
            ;;
            2)
                if [ "${is_base}" == "1" ]
                then
                    Log "error" "Failed to install ${pkg%%.*}."
                    return 2
                else
                    Log "warn" "Failed to install ${pkg%%.*}."
                fi
                ;;
            *)
                continue
            ;;
        esac
    done
    return 0
}

function fn_main()
{
    RELATIVE_PATH=$(dirname $0)
    ABSOLUTE_PATH=$(cd ${RELATIVE_PATH} &> /dev/null;pwd)
    INSTALL_LOG="${ABSOLUTE_PATH}/install.log"
    INSTALL_DIR="/usr/local/python27"
    PKG=""
    python_version=$(python --version 2> /dev/stdout |awk '{print $2}')
    if [ ! -f "/opt/compare_version.sh" ]
    then
        Log "error"  "Cann't to find script compare_version.sh to validate version of python."
        return 5
    fi
    bash /opt/compare_version.sh "${python_version}" "2.7.11" &> /dev/null
    if [ "$?" != "0" ]
    then
        Log "info"  "With newer version of python, need not to install."
        return 0
    fi

    local tmp_result=0

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

    decompress_package "gz" "${ABSOLUTE_PATH}/Python-2.7.11.tgz" "${ABSOLUTE_PATH}" || tmp_result=$?
    if [ "${tmp_result}" == "0" ]
    then
        compile_install "Python27" "${ABSOLUTE_PATH}/Python-2.7.11" "--prefix=/usr/local/python27" || tmp_result=$?
    fi
    if [ "${tmp_result}" != 0 ]
    then
        Log "error" "Failed to compile install Python27."
        return ${tmp_result}
    fi
    ln -s /usr/local/python27/bin/* /usr/local/bin/ &> /dev/null
    source /etc/profile
    Log "info" "Success to install Python27."

    base_pkgs=("setuptools-26.0.0.tar.gz/gz")
    install_py_modules "${base_pkgs[*]}" "1" || return $?

    return ${tmp_result}
}

fn_main
MAIN_RET=$?
if [ "${MAIN_RET}" != "0" ] 
then 
    Log "error" "Failed to execute $0."
fi
exit ${MAIN_RET}