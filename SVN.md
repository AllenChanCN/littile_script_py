####1. 建立版本库目录（这个和安装目录请区分开，以下讲的是版本库）
```
[root@DB2 subversion-1.6.1]# mkdir -p /opt/svndata/game
```
 
####2. 建立svn版本库
```
[root@DB2 subversion-1.6.1]# svnadmin create /opt/svndata/game/
```

执行此命令后svn自动在repos目录下添加必须的配置文件.
```
[root@DB2 subversion-1.6.1]# ls /opt/svndata/game/
conf db format hooks locks README.txt
```

注意:版本库不同于一般的文件夹, 直接在操作系统上新建文件无法被SVN识别, 必须使用import等命令将文件导入版本库.此为svn内部指令，create用于新建版本库。请使用svn help查看详细说明。
 
 
####3. 修改版本库配置文件
```
[root@DB2 conf]# vi /opt/svndata/game/conf/svnserve.conf
```
 
各参数功能在配置文件的注释中有说明, 此处配置如下:

```
[general]
anon-access = none # 使非授权用户无法访问
auth-access = write # 使授权用户有写权限
password-db = passwd # 指明密码文件路径
authz-db = authz # 访问控制文件
realm = /opt/svndata/game #认证命名空间，subversion会在认证提示里显示，并且作为凭证缓存的关键字。
其它采用默认配置. 各语句都必须顶格写, 左侧不能留空格, 否则会出错.
指令简介：这是svn配置文件的格式，请按照以上格式书写。
```
 
####4. 配置用户
```
[root@DB2 conf]# vi /opt/svndata/game/conf/passwd
```
插入如下内容
```
[users]
haifeng = 123456
game = 123456
```
>可以添加多个，此为用户名密码对。
 
####5. 配置权限
```
[root@DB2 conf]# vi /opt/svndata/game/conf/authz
```
插入以下内容
```
[/]
 
haifeng = rw
game = r
```
>列出对各用户的授权。包括只读r，读写rw。没有列出的用户，则不允许访问。还可以对用户分组，具体请参考svn手册



####6. 启动SVN 
>>sudo svnserve -d -r /home/data/svn/ 
其中 -d 表示守护进程， -r 表示在后台执行 
/home/data/svn/  为svn的安装目录 


####7. 关闭SVN 
>>这里采取linux杀死进程的方式处理的 
ps -ef|grep svnserve 
root      4967     1  0 Aug23 ?        00:00:00 svnserve -d -r repository/  
这里  kill -9 4967杀死进程， 此4967为进程号