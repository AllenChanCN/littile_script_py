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

function get_pymodule_version(){
    module_name=$1
    checked_name=$2
    if [ "${module_name}" == "${checked_name}" ]
    then
        result_ver=$(python -c "import ${checked_name};print ${checked_name}.__version__")
    else
        result_ver=$(python -c "from ${module_name} import ${checked_name};print ${checked_name}.__version__")
    fi
    eval $3=\${result_ver}
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

function fn_main(){
    RELATIVE_PATH=$(dirname $0)
    ABSOLUTE_PATH=$(cd ${RELATIVE_PATH} &> /dev/null;pwd)
    INSTALL_LOG="${ABSOLUTE_PATH}/install.log"
    python_version=$(python --version 2> /dev/stdout |awk '{print $2}')
    if [ ! -f "/opt/compare_version.sh" ]
        then
        Log "error"  "Cann't to find script compare_version.sh to validate version of python."
        return 5
    fi
    bash /opt/compare_version.sh "${python_version}" "2.7.11" &> /dev/null
    if [ "$?" == "0" ]
    then
        Log "error"  "With invallidate version of python."
        return 3
    fi

    base_pkg=("click-6.6.tar.gz/gz" "MarkupSafe-0.23.tar.gz/gz" "Jinja2-2.8.tar.gz/gz" "itsdangerous-0.24.tar.gz/gz" "Werkzeug-0.11.11.tar.gz/gz" "Flask-0.11.1.tar.gz/gz")
    install_py_modules "${base_pkg[*]}" "1" || return $?


    extends_pkg=("Flask-Script-2.0.5.tar.gz/gz" "visitor-0.1.3.tar.gz/gz" "dominate-2.3.1.tar.gz/gz" "Flask-Bootstrap-3.3.7.0.tar.gz/gz" "Flask-Moment-0.5.1.tar.gz/gz" "WTForms-2.1.zip/zip" "Flask-WTF-0.13.1.tar.gz/gz" "SQLAlchemy-1.0.16.tar.gz/gz" "Flask-SQLAlchemy-2.1.tar.gz/gz" "python-editor-1.0.3.tar.gz/gz" "Mako-1.0.6.tar.gz/gz" "alembic-0.8.9.tar.gz/gz" "Flask-Migrate-2.0.2.tar.gz/gz" "blinker-1.4.tar.gz/gz" "Flask-Mail-0.9.1.tar.gz/gz" "Flask-Login-0.4.0.tar.gz/gz" "Flask-PageDown-0.2.2.tar.gz/gz" "Markdown-2.6.7.tar.gz/gz" "html5lib-0.999.tar.gz/gz" "bleach-1.5.0.tar.gz/gz" "Flask-HTTPAuth-3.2.1.tar.gz/gz" "Pygments-2.1.3.tar.gz/gz" "requests-2.12.4.tar.gz/gz" "httpie-0.9.9.tar.gz/gz" "coverage-4.2.tar.gz/gz" "selenium-3.0.2.tar.gz/gz" )
    install_py_modules "${extends_pkg[*]}" "0" || return $?

    return 0
}

fn_main
MAIN_RET=$?
if [ "${MAIN_RET}" != "0" ] 
then 
    Log "error" "Failed to execute $0."
fi
exit ${MAIN_RET}