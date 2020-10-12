.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

Linux发行版的库软件包组织
**************************

本文回答有同事问到的Linux的libxxx,libxxx-dbg和libxxx-dev软件包到底有什么关系。

我用ubuntu的libssl作为例子说明一下这个问题，其他平台和库可以用类似的概念来理解
。

比如你的程序需要使用libssl，你安装libssl1.0.0这个包，它包含
/lib/x86_64-linux-gnu/或者/usr/lib/x86_64-linux-gnu/目录下的.so文件，有了这个库
，你基于这个库运行的程序就可以正常运行了。Debian系的发行版支持单安装多平台，所
以/lib和/usr/lib目录下会有x86_64-linux-gnu这一层，部分不支持多平台的发行版就没
有这层目录。

libssl安装的.so文件是用strip命令strip过的，没有调试信息。所以libssl1.0.0-dbg包
提供对应的没有strip过的文件。这些文件以build-id的形式提供。所谓build-id，是每个
二进制进行编译的时候，基于所使用的编译器，编译平台，编译对象生成的一个SHA-1摘要
。放在所生成的elf文件的.note.gnu.build-id section中，你可以用readelf或者简单用
file命令读出一个二进制库或者执行文件的build-id。libssl1.0.0-dbg把用build-id命名
的没有strip过的二进制文件加入/usr/lib/debug/.build-id/目录下。安装dbg包后，你可
以通过build-id找到对应程序的调试文件，加入到perf或者gdb中就可以进行有符号调试。

libssl-dev就简单了，这是你要用这个库进行开发所用的文件，这个包包括如下内容：

1.  /usr/lib/x86_64-linux-gnu下的.a和.so文件（静态库和动态库）

2. /usr/include中的头文件

3. /usr/lib/x86_64-linux-gnu/pkgconfig下的.pc文件

前两个很好理解，最后一个是用来支持pkg-config工具的，pkg-config是一个开发库管理
工具，比如你要链接libssl，那你应该-I什么头文件，-L什么库呢？pkg-config --cflags
--libs libssl就可以了。.pc是些文本文件，就是描述这里提供的信息而已。
