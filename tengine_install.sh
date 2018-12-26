#!/bin/bash


function Log() {
    local level=$2
    local msg=$1
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    case ${level} in
        info|INFO)
            level="\033[44;37;1m INFO \033[0m"
            ;;
        warn|WARN)
            level="\033[44;32;1m WARN \033[0m"
            ;;
        error|ERROR)
            level="\033[44;31;5m ERROR \033[0m"
            ;;
        *)
            level="\033[44;37;1m INFO \033[0m"
            ;;
        esac
    echo -e "[${timestamp}] ${level}: ${msg}"
    return 0
}

function decompress_pkg() {
    local pkg_path=$1
    local target_path="/tmp"

    if [ ! -f "${pkg_path}" -o ! -d "${target_path}" ]
        then
        Log "文件 ${pkg_path} 或者目录 ${target_path} 不存在。" "error"
        return 1
    fi
    local ext=${pkg_path##*.}
    Log "开始解压文件 ${pkg_path}。"
    case ${ext} in
        tar|gz|bz2)
            tar -xf ${pkg_path} -C ${target_path}
            ;;
        zip)
            unzip -o ${pkg_path} -d ${target_path} &> /dev/null
            ;;
        *)
            Log "不支持文件 ${pkg_path} 所指定的解压类型 ${ext}。" "error"
            return 1
            ;;
    esac
    Log "解压文件 ${pkg_path} 成功。"
    return 0
}


function compile_install() {
    local compile_path=$1
    local ins_path=$2
    local compile_args=$3
    local tmp_ret=0

    cd ${compile_path} &> /dev/null
    Log "切换目录到${compile_path},开始编译安装。编译参数为：${compile_args}"

    if [ -f "autogen.sh" ]
        then
        ./autogen.sh &> install.log || tmp_ret=1
    fi
    if [ "${tmp_ret}" == "0" ]
        then
        ./configure --prefix=${ins_path} ${compile_args} &>> install.log || tmp_ret=1
    fi
    if [ "${tmp_ret}" == "0" ]
        then
        make &>> install.log || tmp_ret=1
    fi
    if [ "${tmp_ret}" == "0" ]
        then
        make install &>> install.log || tmp_ret=1
    fi
    if [ "${tmp_ret}" != "0" ]
        then
        Log "编译安装失败，中断操作,详情请见日志文件 ${compile_path}/install.log。" "error"
        return ${tmp_ret}
    fi

    Log "编译安装成功。"

    return ${tmp_ret}
}

function clean_dir() {
    local target_path=$1
    local tmp_ret=0

    if [ ! -e "${target_path}" ]
        then
        Log "目标路径 ${target_path} 不存在。" "warn"
        return 1
    fi
    rm -rf ${target_path}  &> /dev/null  || tmp_ret=1
    if [ "${tmp_ret}" != "0" ]
        then
        Log "删除路径 ${target_path} 失败。" "warn"
        return ${tmp_ret}
    fi
    return 0

}

function main() {

    decompress_pkg "/tmp/GeoIP.tar.gz" || return $?
    decompress_pkg "/tmp/pcre-8.39.tar.gz" || return $?
    decompress_pkg "/tmp/tengine-2.2.2.tar.gz" || return $?

    compile_install "/tmp/GeoIP-1.4.8" "/usr/local" "" || return $?
    compile_install "/tmp/pcre-8.39" "/usr/local/pcre" "" || return $?

    /sbin/ldconfig &> /dev/null

    compile_args=" --user=nginx --group=nginx \
--without-select_module --with-file-aio --with-http_ssl_module  \
--with-http_realip_module  --with-http_addition_module \
--with-http_xslt_module --with-http_image_filter_module \
--with-http_geoip_module --with-http_sub_module \
--with-http_dav_module --with-http_flv_module \
--with-http_gzip_static_module \
--with-http_random_index_module --with-http_secure_link_module \
--with-http_degradation_module  --with-http_stub_status_module \
--with-http_perl_module --with-pcre=/tmp/pcre-8.39 \
--with-http_upstream_check_module --with-http_stub_status_module \
--with-http_v2_module "

    compile_install "/tmp/tengine-2.2.2" "/usr/local/nginx" "${compile_args}" || return $?

    cd /tmp &> /dev/null
    gunzip GeoIP.dat.gz &> /dev/null
    gunzip GeoLiteCity.dat.gz &> /dev/null
    mv /tmp/GeoIP.dat /usr/local/nginx/conf/
    mv /tmp/GeoLiteCity.dat /usr/local/nginx/conf/

    clean_dir "/tmp/GeoIP-1.4.8"
    clean_dir "/tmp/pcre-8.39"
    clean_dir "/tmp/tengine-2.2.2"
    clean_dir "/tmp/GeoIP.tar.gz"
    clean_dir "/tmp/pcre-8.39.tar.gz"
    clean_dir "/tmp/tengine-2.2.2.tar.gz"


    return 0
}

Log "开始执行脚本 $0" 
main
MAIN_RET=$?

if [ "${MAIN_RET}" != "0" ]
    then
    Log "脚本 $0 执行失败。" "error"
else
    Log "脚本 $0 执行成功。" "info"    
fi

exit ${MAIN_RET}