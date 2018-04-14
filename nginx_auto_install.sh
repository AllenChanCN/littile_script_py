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
    tmp_result=$?
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
    tmp_result=$?
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
    tmp_result=0
    record_log="${ABSOLUTE_PATH}/${package_name}.log"
    cd ${filename} &> ${record_log}
    
    if [ -f "autogen.sh" ]
    then
        ./autogen.sh &>> ${record_log} || tmp_result=1
    fi
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
    
#   ./configure --prefix=/usr/local/nginx1.11 --user=nginx --group=nginx --with-threads --with-file-aio --with-http_ssl_module --with-http_v2_module --with-http_realip_module --with-http_addition_module --with-http_image_filter_module --with-http_geoip_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_auth_request_module --with-http_random_index_module --with-http_secure_link_module --with-http_degradation_module --with-http_slice_module --with-http_stub_status_module --with-stream --with-stream_ssl_module --with-stream_realip_module --with-stream_geoip_module --with-stream_ssl_preread_module  --with-pcre=/opt/cdn_tar/pcre-8.39 --with-zlib=/opt/cdn_tar/zlib-1.2.8 --with-openssl=/opt/cdn_tar/openssl-1.1.0c

}




function main()
{
    RELATIVE_PATH=$(dirname $0)
    ABSOLUTE_PATH=$(cd ${RELATIVE_PATH} &> /dev/null;pwd)
    INSTALL_LOG="${ABSOLUTE_PATH}/install.log"
    INSTALL_DIR="/usr/local/nginx"
    DATA_DIR=""
    PACKAGE_NAME="nginx-1.13.9.tar.gz"
    dir_name=$(awk -F ".tar.gz" '{print $1}' <<< "${PACKAGE_NAME}")
    USER="nginx"
    GROUP="nginx"

    groups ${GROUP} &> /dev/null
    local tmp_result=$?
    if [ "${tmp_result}" != 0 ]
    then
        groupadd ${GROUP}
        tmp_result=$?
        if [ "${tmp_result}" != 0 ]
        then
            Log "error" "Failed to create group ${GROUP}."
            return ${tmp_result}
        fi
    fi

    id ${USER} &> /dev/null
    tmp_result=$?
    if [ "${tmp_result}" != 0 ]
    then
        useradd ${USER} -g ${GROUP}
        tmp_result=$?
        if [ "${tmp_result}" != 0 ] 
        then
            Log "error" "Failed to create user ${USER}."
            return ${tmp_result}
        fi
    fi
    pre_check "autoconf" "automake" "libtool" "make" "gcc" "gd"  "tar" "zip" "gzip" "unzip" "gcc-c++" "fontconfig-devel" "freetype-devel" "libX11-devel" "libXpm-devel" "libjpeg-devel" "libpng-devel"
    ldconfig
    
    cd ${ABSOLUTE_PATH} &> /dev/null
    for package_name in "pcre-8.39.tar.gz/gz" "zlib-1.2.8.zip/zip" "openssl-1.1.0c.zip/zip" "${PACKAGE_NAME}/gz" "GeoIP.tar.gz/gz" "libunwind-1.2.1.tar.gz/gz" "gperftools-perftools-1.6.zip/zip"
    do
        local tmp_package=${package_name%/*}
        local tmp_type=${package_name#*/}
        decompress_package "${tmp_type}" "${ABSOLUTE_PATH}/${tmp_package}" "${ABSOLUTE_PATH}"
        tmp_result=$?
        if [ "${tmp_result}" != 0 ]
        then
            Log "error" "Failed to decompress ${package_name}."
            return ${tmp_result}
        fi
    done
    cd - &> /dev/null

    tmp_result=0
    compile_install "zlib" "${ABSOLUTE_PATH}/zlib-1.2.8" ""
    check_result=$(rpm -qa gd-devel)
    if [ "${check_result}" == "" ]
    then
        if $(grep -q " 7\.. " /etc/redhat-release )
        then
            rpm -ih ${ABSOLUTE_PATH}/gd-devel-2.0.35-26.el7.x86_64.rpm &> ${INSTALL_LOG} || tmp_result=$?
        elif $(grep -q " 6\.. " /etc/redhat-release)
        then
            rpm -ih ${ABSOLUTE_PATH}/gd-devel-2.0.35-11.el6.x86_64.rpm &> ${INSTALL_LOG} || tmp_result=$?
        fi
        if [ "${tmp_result}" != 0 ] 
        then
            Log "error" "Failed to instll gd-devel."
            return ${tmp_result}
        fi
    fi
    
    compile_install "GeoIP" "${ABSOLUTE_PATH}/GeoIP-1.4.8" ""
    compile_install "libunwind-1.2.1" "${ABSOLUTE_PATH}/libunwind-1.2.1" ""
   # compile_install "gperftools-perftools-1.6" "${ABSOLUTE_PATH}/gperftools-perftools-1.6" "--enable-frame-pointers"
    tmp_result=$?
    if [ "${tmp_result}" != 0 ]
    then
        Log "error" "Failed to install GeoIP."
        return ${tmp_result}
    fi
    
    /usr/bin/id nginx &> /dev/null
    if [ "$?" != 0 ]
    then
        useradd nginx -s /sbin/nologin
    fi
    
    compile_option=" --prefix=${INSTALL_DIR} --user=${USER} --group=${GROUP} --with-threads --with-file-aio --with-http_ssl_module --with-http_v2_module --with-http_realip_module --with-http_addition_module --with-http_image_filter_module --with-http_geoip_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_auth_request_module --with-http_random_index_module --with-http_secure_link_module --with-http_degradation_module --with-http_slice_module --with-http_stub_status_module --with-stream --with-stream_ssl_module --with-stream_realip_module --with-stream_geoip_module --with-stream_ssl_preread_module --with-google_perftools_module --with-pcre=${ABSOLUTE_PATH}/pcre-8.39 --with-zlib=${ABSOLUTE_PATH}/zlib-1.2.8 --with-openssl=${ABSOLUTE_PATH}/openssl-1.1.0c"
    
    compile_install "${dir_name}" "${ABSOLUTE_PATH}/${dir_name}" "${compile_option}"
    tmp_result=$?
    if [ "${tmp_result}" != 0 ]
    then
        Log "error" "Failed to compile ${dir_name}."
        return ${tmp_result}
    fi
    
    for dir in ${DATA_DIR}
    do
        if [ ! -z "$（echo ${dir} |grep -v "^\s*$")" ]
        then
            mkdir -p ${dir}
        fi
    done

    for dir in ${DATA_DIR}
    do
        if [ ! -z "$（echo ${dir} |grep -v "^\s*$")" ]
        then
            chown ${USER}:${GROUP} ${dir} -R
        fi
    done
    
    if [ -f "${ABSOLUTE_PATH}/GeoLiteCity.dat" ]
    then
        /bin/cp -f "${ABSOLUTE_PATH}/GeoLiteCity.dat" "${INSTALL_DIR}"
    fi

    if [ -f "${ABSOLUTE_PATH}/GeoIP-1.4.8" ]
    then
        /bin/cp -f "${ABSOLUTE_PATH}/GeoIP-1.4.8" "${INSTALL_DIR}"
    fi
    
    if [ -d "${ABSOLUTE_PATH}/conf" ]
    then
        /bin/cp -rf "${ABSOLUTE_PATH}/conf" "${INSTALL_DIR}/conf"
    fi
    
    ln -s ${INSTALL_DIR}/sbin/nginx /usr/local/sbin/ &> /dev/null
    ldconfig &> /dev/null

    return 0
}
main
MAIN_RET=$?
if [ "${MAIN_RET}" != "0" ] 
then 
    Log "error" "Failed to install ${PACKAGE_NAME}"
fi
exit ${MAIN_RET}
