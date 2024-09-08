.. Kenneth Lee 版权所有 2024

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2024-09-08
:Status: Draft

在WSL上安装和使用MySQL
**********************

本文总结一下如何在WSL上安装MySQL。

MySQL一开始就是个Linux软件，所以在Windows下安装远不如在Linux下安装起来方便，而
且MySQL本来就是个网络服务（类似Web Server那样，安装好了你只是通过网络去使用它，
所以并非你装了一个Linux下的MySQL，你就要用Linux下的MySQL客户端访问它，其实你用
什么平台，在任何一台能从网络上连上这台机器的客户端都能连上它。

我们用WSL的Ubuntu来演示怎么做这个安装：::

  sudo apt install mysql-server
  /etc/init.d/mysql start                # start换成stop就可以停止服务

第一个命令安装mysql服务器，第二个命令启动这个服务。你可以通过下面的网络命令看
到mysql等待在网络的端口上：::

  ss -ltp

下面是我这里的输出：::

  State            Recv-Q           Send-Q                     Local Address:Port                      Peer Address:Port          Process
  LISTEN           0                70                             127.0.0.1:33060                          0.0.0.0:*
  LISTEN           0                151                            127.0.0.1:mysql                          0.0.0.0:*

最后一行就是mysql的服务了，这个端口号它自动解释了，你如果你想看直接的号码，可
以用ss -ltpn来显示：::

  LISTEN           0                151                            127.0.0.1:3306                           0.0.0.0:*

这样，就搞定了。很简单吧？当然，严肃地配置一个服务器一般我们会配置一下的，比如
可以修改一下/etc/mysql/mysql.conf.d/mysqld.cnf的配置文件，然后再启动。但我们只
用默认的配置，所以启动一下就可以了。

我们现在测试一下，先用Ubuntu本地的客户端连接：::

  sudo mysql

这样就能连进去，它会进入一个SQL语言的控制台，让你运行SQL命令，我们可以这样实验
一下：::

  mysql> show databases;
  +--------------------+
  | Database           |
  +--------------------+
  | information_schema |
  | mysql              |
  | performance_schema |
  | sys                |
  +--------------------+
  4 rows in set (0.00 sec)

这个命令显示有哪些已有的数据库（MySQL安装后就会有一些默认的），然后你可以看看
数据库里面有什么（注意每个SQL命令后面要加分号的，SQL命令的结束符不是回车，而是
分号）：::

  mysql> use mysql;                    <-- 进入mysql这个数据库
  mysql> show tables;                  <-- 显示数据库中所有表格
  mysql> select * from user;           <-- 从表格user中查找所有记录
  mysql> create database test;         <-- 创建一个数据库test
  mysql> create user kenny@localhost identified with mysql_native_password by 'mypassword';
  mysql> grant all priviledges to kenny@localhost;
  mysql> use database test;            <-- 进入数据库test
  mysql> create table test (name string, age int, sex bool);   <-- 创建表格test
  mysql> insert into table test ("xiaoliu", 30, 1);            <-- 插入记录
  mysql> insert into table test ("laoma", 50, 0);              <-- 插入记录
  mysql> select * from test where sex=1                        <-- 查询
  mysql> drop database test            <-- 删除数据库test
  mysql> quit

其实所有的数据库基本就是这些功能了（SQL语言在不同数据库中语法是一样的），就是
在不同的表格之间select这个，select那个，也就这样了。

我们刚才运行的时候是用root权限运行的，但我们也创建了一个叫kenny的用户了，所以，
我们也可以这样连：::

  mysql -u kenny -p

输入密码就可以用kenny身份进去操作数据库了。

现在我们换用Windows的Client。一个比较常用的Client是MySQL Workbench。可以在这里
下载：
`<https://www.mysql.com/products/workbench/>`_
。

在database菜单中找到connect to database菜单，修改服务器的路径（现在是
localhost），用户名改成你创建的用户名，就可以连上去，然后在窗口里面输入前面一
样的命令了。

剩下就是怎么学习SQL语法的问题了。其实和学习Java或者Python没什么区别，只是这个
语法主要用来操作数据库而已。

数据库原理这门课其实主要不是学怎么用这种语法的，是学怎么实现这种语法功能的，只
是要理解怎么实现，当然需要先学习它能提供什么语法了。
