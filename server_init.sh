#!/bin/bash

#1，关闭 selinux
function set_se(){
    local tmp_ret=0
    se_status=$(getenforce)
    if [ "${se_status}" == "Enforcing" ]
        then
        setenforce 0 || tmp_ret=$?
        sed -i "s/^SELINUX=.*/SELINUX=disabled/g" /etc/selinux/config  || tmp_ret=$?
    fi
    return ${tmp_ret}
}

#2, 修改hostname
function set_hostname() {
    ip_addr=$(ip addr show |sed -n "s/^\s*inet\s\+\(.*\)\/.*/\1/gp" |grep -v "127.0.0.1")
    newHostname=$(awk -F "." '{print "node_"$3"_"$4}' <<<${ip_addr})
    local tmp_ret=0
    hostname ${newHostname} || tmp_ret=$?
    echo "127.0.0.1 ${newHostname}" >> /etc/hosts || tmp_ret=$?
    sed -i "s/^HOSTNAME=.*/HOSTNAME=${newHostname}/g" /etc/sysconfig/network || tmp_ret=$?
    return ${tmp_ret}
}

#3，安装基础Yum组件 （开发组件，lsof, sar, netstat, net-tools, ntp 等)
function ins_base_component() {
    local tmp_ret=0
    yum groupinstall -y "Development tools" &> /dev/null || tmp_ret=1
    components="wget lsof telnet vim net-tools rsyslog ntpdate"
    for i in ${components}
    do
        yum install -y ${i} &> /dev/null || tmp_ret=1
        if [ "${tmp_ret}" != "0" ]
        then
            echo "安装${i}失败。"
            break
        fi
    done
    return ${tmp_ret}
}

#4，安装系统日志工具rsyslog
#5，同步时间服务器
function add_ntp() {
    local tmp_ret=0
    if ! $(grep -wq "ntpdate" /var/spool/cron/root &> /dev/null)
        then
        echo "*/10 * * * * /usr/sbin/ntpdate -u 0.centos.pool.ntp.org &> /dev/null" >> /var/spool/cron/root || tmp_ret=1
    fi
    return ${tmp_ret}
}

#6，安装zabbix客户端

#7, 优化内核配置 （/etc/sysctl.conf）
function init_sysctl() {
    local tmp_ret=0
    cat > /etc/sysctl.conf << EOF
#禁用包过滤功能 
net.ipv4.ip_forward = 0  
#启用源路由核查功能 
net.ipv4.conf.default.rp_filter = 1  
#禁用所有IP源路由 
net.ipv4.conf.default.accept_source_route = 0  
#使用sysrq组合键是了解系统目前运行情况，为安全起见设为0关闭
kernel.sysrq = 0  
#控制core文件的文件名是否添加pid作为扩展
kernel.core_uses_pid = 1  
#开启SYN Cookies，当出现SYN等待队列溢出时，启用cookies来处理
net.ipv4.tcp_syncookies = 1  
#每个消息队列的大小（单位：字节）限制
kernel.msgmnb = 65536  
#整个系统最大消息队列数量限制
kernel.msgmax = 65536  
#单个共享内存段的大小（单位：字节）限制，计算公式64G*1024*1024*1024(字节)
kernel.shmmax = 68719476736  
#所有内存大小（单位：页，1页 = 4Kb），计算公式16G*1024*1024*1024/4KB(页)
kernel.shmall = 4294967296  
#timewait的数量，默认是180000
net.ipv4.tcp_max_tw_buckets = 6000  
#开启有选择的应答
net.ipv4.tcp_sack = 1  
#支持更大的TCP窗口. 如果TCP窗口最大超过65535(64K), 必须设置该数值为1
net.ipv4.tcp_window_scaling = 1  
#TCP读buffer
net.ipv4.tcp_rmem = 4096 131072 1048576
#TCP写buffer
net.ipv4.tcp_wmem = 4096 131072 1048576   
#为TCP socket预留用于发送缓冲的内存默认值（单位：字节）
net.core.wmem_default = 8388608
#为TCP socket预留用于发送缓冲的内存最大值（单位：字节）
net.core.wmem_max = 16777216  
#为TCP socket预留用于接收缓冲的内存默认值（单位：字节）  
net.core.rmem_default = 8388608
#为TCP socket预留用于接收缓冲的内存最大值（单位：字节）
net.core.rmem_max = 16777216
#每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目
net.core.netdev_max_backlog = 262144  
#web应用中listen函数的backlog默认会给我们内核参数的net.core.somaxconn限制到128，而nginx定义的NGX_LISTEN_BACKLOG默认为511，所以有必要调整这个值
net.core.somaxconn = 262144  
#系统中最多有多少个TCP套接字不被关联到任何一个用户文件句柄上。这个限制仅仅是为了防止简单的DoS攻击，不能过分依靠它或者人为地减小这个值，更应该增加这个值(如果增加了内存之后)
net.ipv4.tcp_max_orphans = 3276800  
#记录的那些尚未收到客户端确认信息的连接请求的最大值。对于有128M内存的系统而言，缺省值是1024，小内存的系统则是128
net.ipv4.tcp_max_syn_backlog = 262144  
#时间戳可以避免序列号的卷绕。一个1Gbps的链路肯定会遇到以前用过的序列号。时间戳能够让内核接受这种“异常”的数据包。这里需要将其关掉
net.ipv4.tcp_timestamps = 0  
#为了打开对端的连接，内核需要发送一个SYN并附带一个回应前面一个SYN的ACK。也就是所谓三次握手中的第二次握手。这个设置决定了内核放弃连接之前发送SYN+ACK包的数量
net.ipv4.tcp_synack_retries = 1  
#在内核放弃建立连接之前发送SYN包的数量
net.ipv4.tcp_syn_retries = 1  
#开启TCP连接中time_wait sockets的快速回收
net.ipv4.tcp_tw_recycle = 1  
#开启TCP连接复用功能，允许将time_wait sockets重新用于新的TCP连接（主要针对time_wait连接）
net.ipv4.tcp_tw_reuse = 1  
#1st低于此值,TCP没有内存压力,2nd进入内存压力阶段,3rdTCP拒绝分配socket(单位：内存页)
net.ipv4.tcp_mem = 94500000 915000000 927000000   
#如果套接字由本端要求关闭，这个参数决定了它保持在FIN-WAIT-2状态的时间。对端可以出错并永远不关闭连接，甚至意外当机。缺省值是60 秒。2.2 内核的通常值是180秒，你可以按这个设置，但要记住的是，即使你的机器是一个轻载的WEB服务器，也有因为大量的死套接字而内存溢出的风险，FIN- WAIT-2的危险性比FIN-WAIT-1要小，因为它最多只能吃掉1.5K内存，但是它们的生存期长些。
net.ipv4.tcp_fin_timeout = 15  
#表示当keepalive起用的时候，TCP发送keepalive消息的频度（单位：秒）
net.ipv4.tcp_keepalive_time = 30  
#对外连接端口范围
net.ipv4.ip_local_port_range = 2048 65000
#表示文件句柄的最大数量
fs.file-max = 102400
EOF

    sysctl -p &> /dev/null || tmp_ret=1
    return ${tmp_ret}
}

#8, 修改最大文件打开数
function modify_openFiles() {
    local tmp_ret=0
    local file_cfg="/etc/security/limits.conf"
    if $(egrep -q "^\*\s*soft\s*nofile\s*.*" ${file_cfg})
        then
        sed -i "s/^\(\*\s*soft\s*nofile\s*\).*/\165535/g" ${file_cfg} || tmp_ret=1
    else
        echo -e "*\t\tsoft\tnofile\t65535" >> ${file_cfg} || tmp_ret=1
    fi
    if $(egrep -q "^\*\s*hard\s*nofile\s*.*" ${file_cfg})
        then
        sed -i "s/^\(\*\s*hard\s*nofile\s*\).*/\165535/g" ${file_cfg} || tmp_ret=1
    else
        echo -e "*\t\thard\tnofile\t65535" >> ${file_cfg} || tmp_ret=1
    fi
    ulimit -n 65535

    return ${tmp_ret}
}

#9, 创建普通用户
function add_user() {
    local tmp_ret=0
    if ! $(id avgUser &> /dev/null)
        then
        useradd avgUser &> /dev/null || tmp_ret=1
    fi
    echo "W\"l0X$C,o_Mn{6aw" | passwd avgUser --stdin &> /dev/null || tmp_ret=1
    mkdir -p /home/avgUser/.ssh &> /dev/null || tmp_ret=1
    cat > /home/avgUser/.ssh/authorized_keys << EOF || tmp_ret=1
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAukHEI8+TZc0qyJ5oIPe/73mElDod3ZR0jVakwUZDnKBdefFauj5kGqCrhKy8iR9QXYXs4aBc+rEj5s8DJzcO50khLOOeSK1b/ztvUa1gfUGtCG/1ZhE13J2M5UqjNm1DdPXoMR52gW3EiA2N/acsNS+yjxUsKZadJxXo/QHJm1R4OOskV+4AdiJZpbZdnm9f7DMFg1L+VPFvQR0Oo118z44zaatllsUZ33J+4iwwo8+BYLO1gWoVi+giiLsPZ0a0d/p7/UtHLzfbdEdSQYKAXmax+CzAUXvDAqbSgMUHXBIx2FohOdR7bQhQXVEOhY0sPLORq8sVeR6dTBvXxjJMcQ== root@node_0_73
EOF
    chmod 600 /home/avgUser/.ssh -R &> /dev/null || tmp_ret=1
    chmod 700 /home/avgUser/.ssh/ &> /dev/null || tmp_ret=1
    chown avgUser.avgUser -R /home/avgUser &> /dev/null || tmp_ret=1

    return ${tmp_ret}
}
#10, 修改登录密码，禁止root登录，禁止密码登录，修改SSH端口
function init_sshd() {
    local tmp_ret=0
    echo "copyleft" |passwd root --stdin &> /dev/null || tmp_ret=1
    sed -i "s/^#\?PermitRootLogin.*$/PermitRootLogin no/g" /etc/ssh/sshd_config || tmp_ret=1
    sed -i "s/^#\?PasswordAuthentication \+.*/PasswordAuthentication no/g" /etc/ssh/sshd_config || tmp_ret=1
    sed -i "s/^#\?Port *.*/Port 2022/g" /etc/ssh/sshd_config || tmp_ret=1
    if [ "${tmp_ret}" == "0" ]
        then
        /etc/init.d/sshd restart &> /dev/null || tmp_ret=1
    fi
    return ${tmp_ret}
}


#11, 修改iptables规则
function modify_iptables() {
    local tmp_ret=0
    cat > /etc/sysconfig/iptables << EOF || tmp_ret=1 
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [727015:39726150]
-A INPUT -s 127.0.0.1 -j ACCEPT
-A INPUT -s 192.168.0.0/16 -j ACCEPT
-A INPUT -s 103.212.33.132 -j ACCEPT 
-A INPUT -s 221.120.162.108 -j ACCEPT 
-A INPUT -s 118.107.181.52 -j ACCEPT 
-A INPUT -s 203.160.52.37 -j ACCEPT 

-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT 
-A INPUT -j REJECT --reject-with icmp-host-prohibited 
-A FORWARD -j REJECT --reject-with icmp-host-prohibited 
COMMIT
EOF

    if [ "${tmp_ret}" == "0" ]
        then
        /etc/init.d/iptables restart &> /dev/null || tmp_ret=1
        /etc/init.d/iptables save &> /dev/null || return $?
    fi

    return ${tmp_ret}
}


function main() {
    echo "开始进行系统初始化..."

    processes_flow=("set_se" "set_hostname" "ins_base_component" "add_ntp" "init_sysctl" "modify_openFiles" "add_user" "init_sshd" "modify_iptables")
    fail_messages=("关闭SELINUX" "修改主机名" "安装基础组件" "添加时间同步服务器" "内核配置文件初始化" "修改最大文件句柄数" "添加普通用户" "初始化sshd服务" "初始化iptables服务")
    
    for ele in $(seq ${#processes_flow[@]})
    do
        eval ${processes_flow[$((${ele}-1))]}
        if [ "$?" != "0" ]
            then
            echo "${fail_messages[$((${ele}-1))]}失败，中断操作。"
            return 1
        fi
        echo "${fail_messages[$((${ele}-1))]}成功。"
    done
    echo "初始化结束。"
    return 0
}

main

exit $?

