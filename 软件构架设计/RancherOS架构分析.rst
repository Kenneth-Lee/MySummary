.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

RancherOS架构分析
******************

最近开始在我们的平台上支持RancherOS，本文对RancherOS的系统架构进行一个分析。

RancherOS公司主页在这里：Container Management and Deployment，

开源项目在这里：https://github.com/rancher/os。

项目和Docker一样，都是golang的。版权是Apache License。

本文的分析基于RancherOS 1.0.2，其使用的Linux内核是4.9.30，从源代码上没有patch这
一点来快速猜，这个内核应该没有经过特别定制。

RancherOS是一个基于Docker的Linux的发行版。简单说，它的init进程(1号进程）就是一
个Docker Container（称为System Docker），这个Container被精简到仅仅可以用来运行
其他Docker Container（称为User Docker），剩下的事情就不用我解释了，有了Docker以
后你可以干什么就不需要我解释了。

RancherOS的System Docker只有60M，以busybox+uclibc为基础构建，可以构建成一个ios
文件从光盘或者USB Key启动，启动后可以快速通过ros命令写入磁盘，从而完成安装，安
装时间只有一两分钟。

RancherOS的维护理念是：光盘启动的时候免密码进入Rancher用户，通过ros命令安装的时
候提供ssh pub key（相当于提供了rancher用户的authrorized_keys）。完成安装后，仅
可以通过ssh进入。之后你获得管理员的权限，通过每个独立的Docker使用独立的功能

从这里可以看出，RancherOS的定位是“远程服务器”，特别是“云服务器”。无论是
Barematal的还是基于虚拟机的。

RancherOS并不复杂，但它代表了一个非常重要的技术趋势，就是“操作系统固件化”。

“发行版”的竞争力在什么地方？我认为如下：

1. 背锅和基于背锅的支持

2. 广泛的硬件兼容性

3. 广泛的软件集成

我认为，现在这个时世，为第三点付钱的人少，大部分都是为了前两者。前者在硬件多样
化和白牌化的时代，不拉上硬件提供商一起，光发行版背的锅越来越难找人接受了。你说
你的网卡丢包了，你找某个发行版来背锅，它赔你几万块钱了不起了，要解决问题不找网
卡提供商这个事情没法弄。

而广泛的硬件兼容性这点也受到一样的冲击，比如你要弄一个200个节点的数据中心，使用
几乎一样的硬件平台，某个发行版对10种DIMM条，20种PCIE Extender，30种磁盘，100种
网卡做过兼容性测试，这个有多大意义？过几年你真要大规模升级你的软件的时候，你的
硬件也该淘汰了。

而RancherOS这样的解决方案，意味着服务器出厂的时候，直接带一个高级“固件”，连着
Kernel和基础的维护命令一次提供，这个基础固件升级就整体升级，测试也从这里提供，
安全保证等也直接从这个提供，很多安全措施也可以直接和硬件设计结合。使用者仅基于
Container来使用设备的计算，通讯和存储能力。这种局面，可能会对现有的发行版模型产
生巨大的冲击。
