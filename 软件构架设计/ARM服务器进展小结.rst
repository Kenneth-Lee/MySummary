.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

ARM服务器进展小结
******************

最近的Linaro Connect（SFO17）上ARM服务器进行了一波密集的发布。其中最显眼的是高
通的Centriq 2400，采用的是10nm制程，2.6GHz，48核单Socket的设计。SoC内内置32Lane
的PCIE Gen3控制器，50G NIC，8通道SAS接口。可以把两个单板集成到一个1U的盒子中，
主要面对数据中心市场。

此前Cavium和HP发布的ThunderX2单板则主要针对HPC市场，采用48核双Socket设计，10G双
光口，可以外接GPU。

更前（去年年底），APM发布的X-Gene 3的数据也很漂亮，32核，最高可以上到3.3GHz。也
针对数据中心（主要是网络前端，Cache，存储和大数据处理等应用节点）市场，但非常强
调计算性能，其4发射的CPU Core以更低的功耗和密度可以达到和E5 2699v4的SPECint性能
。（参考：http://www.linleygroup.com/uploads/x-gene-3-white-paper-final.pdf）

比较有趣的是日本厂商Socinext的方案，相对来说，这个厂家的配置比较低，它每个CPU只
有24个A53的核，工作在1G的频率，但它支持64个单板直接通过PCIE连成集群，每个CPU功
耗低于5W。

另外还有一些没有发布的厂家也提供和前面这些方案类似的解决方案，每家可能只是着重
点不同，有些重点是功耗，有些重点是IO，有些重点是垂直整合的优化。

和很多人想象不一样的是，现在ARM Server的生态也相对成熟了。三大Linux发行版都已经
直接有支持ARM Server的版本（一个二进制支持全部ARM Server）：

Ubuntu的：https://certification.ubuntu.com/soc/models/

Suse的（参考8.2节）：SUSE Linux Enterprise Server 12 SP3

Redhat的正式版本2017年11月15日发布：https://access.redhat.com/articles/3158541
。在这之前，CentOS已经首先发布了：SpecialInterestGroup/AltArch/AArch64 - CentOS
Wiki

（很多人认为国内知需要CentOS，不需要RHEL。但请想清楚，没有RHEL，给你一个CentOS
你会用吗？）


上面是商用版本，如果要用最新的软件和硬件，可以考虑使用Linaro的ERP版本：

https://platforms.linaro.org/documentation/Reference-Platform/Platforms/Enterprise/README.md


ARM Server用起来完全就是普通的x86 Server一样，也是UEFI启动，ACPI接口，grub
loader。安装都可以直接把下载的ISO文件提交给BMC，用各发行版的标准方法‘’安装。要
替换Kernel可以直接git clone主线Kernel，然后用标准的方法编译（配置用标准的
defconfg即可），然后安装到grub中启动。Docker和KVM的支持也和普通的x86服务器一样
，但现在针对ARM的Docker Image比较少，使用者可以通过基础的比如Ubuntu的镜像自行进
行定制。


现在ARM Server生态的主要问题就是认知度低，很多人还把这种Server看做是一种“嵌入式
单板”，而实际上它是一种通用的服务器。需要深入了解这种服务器，可以考虑申请Linaro
的OpenStack云虚拟机：The Linaro Developer Cloud

如果需要Baremetal的机器，也可以申请Packet的服务：

https://www.packet.net

后者是要钱的，如果你需要Baremetal的服务器，又缺钱，但是个有一定影响的开源项目，
你可以……嗯……找我要硬件；）

另外，Socinext正在和Linaro 96Board合作开发便宜的ARM开发服务器单板，希望他们早点
出来吧。


再放些图：

Cavium Thunder X2，也是1U半框，以计算力为中心，不像Centriq那样留下很多磁盘位。

        .. figure:: _static/thunder2.jpg

Socinext做的小开发Desktop：

        .. figure:: _static/socinext.jpg

