##运维中的日志切割操作梳理


###logrotate配置
######配置文件地址:
/etc/logrotate.conf
/etc/logrotate.d/

######实际是通过cron任务执行：
/etc/cron.daily/logrotate

######手动切割日志的方法:
```
# /usr/sbin/logrotate -f /etc/logrotate.d/nginx
# /usr/sbin/logrotate -d -f /etc/logrotate.d/nginx
```


######logrotate命令格式：
```
logrotate [OPTION...] <configfile>
-d, --debug ：debug模式，测试配置文件是否有错误。
-f, --force ：强制转储文件。
-m, --mail=command ：压缩日志后，发送日志到指定邮箱。
-s, --state=statefile ：使用指定的状态文件。
-v, --verbose ：显示转储过程。
```

######根据日志切割设置进行操作，并显示详细信息
```
[root@huanqiu_web1 ~]# /usr/sbin/logrotate -v /etc/logrotate.conf 
[root@huanqiu_web1 ~]# /usr/sbin/logrotate -v /etc/logrotate.d/php
```

######根据日志切割设置进行执行，并显示详细信息,但是不进行具体操作，debug模式
```
[root@huanqiu_web1 ~]# /usr/sbin/logrotate -d /etc/logrotate.conf 
[root@huanqiu_web1 ~]# /usr/sbin/logrotate -d /etc/logrotate.d/nginx
```

###切割介绍
比如以系统日志/var/log/message做切割来简单说明下：
第一次执行完rotate(轮转)之后，原本的messages会变成messages.1，而且会制造一个空的messages给系统来储存日志；
第二次执行之后，messages.1会变成messages.2，而messages会变成messages.1，又造成一个空的messages来储存日志！
如果仅设定保留三个日志（即轮转3次）的话，那么执行第三次时，则 messages.3这个档案就会被删除，并由后面的较新的保存日志所取代！也就是会保存最新的几个日志。
日志究竟轮换几次，这个是根据配置文件中的dateext 参数来判定的。

#####配置文件参数
- weekly          //默认每一周执行一次rotate轮转工作
- rotate 4       //保留多少个日志文件(轮转几次).默认保留四个.就是指定日志文件删除之前轮转的次数，0 指没有备份
- create         //自动创建新的日志文件，新的日志文件具有和原来的文件相同的权限；因为日志被改名,因此要创建一个新的来继续存储之前的日志
- dateext       //这个参数很重要！就是切割后的日志文件以当前日期为格式结尾，如xxx.log-20131216这样,如果注释掉,切割出来是按数字递增,即前面说的 xxx.log-1这种格式
- compress      //是否通过gzip压缩转储以后的日志文件，如xxx.log-20131216.gz ；如果不需要压缩，注释掉就行
- include /etc/logrotate.d // 将/etc/logrotate.d/目录中的所有文件都加载进来
- nocompress    //不做gzip压缩处理
- copytruncate   //用于还在打开中的日志文件，把当前日志备份并截断；是先拷贝再清空的方式，拷贝和清空之间有一个时间差，可能会丢失部分日志数据。
- nocopytruncate     //备份日志文件不过不截断
- create mode owner group    //轮转时指定创建新文件的属性，如create 0777 - nobody nobody
- nocreate   //不建立新的日志文件
- delaycompress   //和compress 一起使用时，转储的日志文件到下一次转储时才压缩
- nodelaycompress    //覆盖 delaycompress 选项，转储同时压缩。
- missingok           //如果日志丢失，不报错继续滚动下一个日志
- errors address      //专储时的错误信息发送到指定的Email 地址
- ifempty     //即使日志文件为空文件也做轮转，这个是logrotate的缺省选项。
- notifempty              //当日志文件为空时，不进行轮转
- mail address       //把转储的日志文件发送到指定的E-mail 地址
- nomail             //转储时不发送日志文件
- olddir directory    //转储后的日志文件放入指定的目录，必须和当前日志文件在同一个文件系统
- noolddir        //转储后的日志文件和当前日志文件放在同一个目录下
- sharedscripts   //运行postrotate脚本，作用是在所有日志都轮转后统一执行一次脚本。如果没有配置这个，那么每个日志轮转后都会执行一次脚本
- prerotate       //在logrotate转储之前需要执行的指令，例如修改文件的属性等动作；必须独立成行
- postrotate     //在logrotate转储之后需要执行的指令，例如重新启动 (kill -HUP) 某个服务！必须独立成行
- daily         //指定转储周期为每天
- weekly        //指定转储周期为每周
- monthly       //指定转储周期为每月
- rotate count   //指定日志文件删除之前转储的次数，0 指没有备份，5 指保留5 个备份
- dateext            //使用当期日期作为命名格式
- dateformat .%s     //配合dateext使用，紧跟在下一行出现，定义文件切割后的文件名，必须配合dateext使用，只支持 %Y %m %d %s 这四个参数
- size(或minsize) log-size   //当日志文件到达指定的大小时才转储，log-size能指定bytes(缺省)及KB (sizek)或MB(sizem).
当日志文件 >= log-size 的时候就转储。 以下为合法格式：（其他格式的单位大小写没有试过）
- size = 5 或 size 5 （>= 5 个字节就转储）
- size = 100k 或 size 100k
- size = 100M 或 size 100M


#####配置示例
```
/var/log/wtmp {                 //仅针对 /var/log/wtmp 所设定的参数
monthly                    //每月一次切割,取代默认的一周
minsize 1M              //文件大小超过 1M 后才会切割
create 0664 root utmp            //指定新建的日志文件权限以及所属用户和组
rotate 1                    //只保留一个日志.
}
```

#####切割nginx日志示例
```
[root@master-server ~]# vim /etc/logrotate.d/nginx
/usr/local/nginx/logs/*.log {
daily
rotate 7
missingok
notifempty
dateext
sharedscripts
postrotate
    if [ -f /usr/local/nginx/logs/nginx.pid ]; then
        kill -USR1 `cat /usr/local/nginx/logs/nginx.pid`
    fi
endscript
}
```

```
/usr/local/nginx/logs/*.log {
daily
rotate 30
dateext
compress
delaycompress
nocopytruncate
create 0755 nobody nobody
missingok
ifempty
sharedscripts
postrotate
    if [ -f /usr/local/nginx/logs/nginx.pid ]; then
        kill -USR1 `cat /usr/local/nginx/logs/nginx.pid`
    fi
endscript
}
```

#####系统日志切割示例
```
[root@huanqiu_web1 ~]# cat /etc/logrotate.d/syslog
/var/log/cron
/var/log/maillog
/var/log/messages
/var/log/secure
/var/log/spooler
{
    sharedscripts
    postrotate
    /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
    endscript
}
```

```
/var/log/cron
/var/log/maillog
/var/log/secure
/var/log/spooler
{
    sharedscripts
    postrotate
        /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
    endscript
}

/var/log/messages
{
    prerotate
            /usr/bin/chattr -a /var/log/messages
    endscript
    postrotate
            /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
            /usr/bin/chattr +a /var/log/messages
    endscript
}
```

#####tomcat日志切割示例
```
[root@huanqiu-backup ~]# cat /etc/logrotate.d/tomcat
/Data/app/tomcat-7-huanqiu/logs/catalina.out {
rotate 14
daily
copytruncate
compress
notifempty
missingok
}
```