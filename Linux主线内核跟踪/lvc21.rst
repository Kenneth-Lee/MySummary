.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0

Linaro Virtual Connect 2021
*****************************

介绍
====
Linaro Connect的跟踪不是Linux内核跟踪的一部分，但相关性其实很大，也不知道为这个
跟踪开一个新的主题，所以就写在这里了。

这个跟踪主要是把所有的主题看一遍（在\ `这里`_\ ），把其中感兴趣的主题突出描述出
来。

.. _`这里`: https://connect.linaro.org/resources/lvc21/

今年Linaro的材料特别好，因为是线上会议，所有材料都是完整的，视频和胶片都可以下
载，而且国内访问也没有任何问题。需要了解细节的读者可以直接进去看相关的材料。我
跟踪的目的主要是找兴趣点，如果没有兴趣点的，会看得比较快，很多演讲都是两倍速听
完的，错漏在所难免，请不要太相信这个总结的细节。

主题遍历
=========

300K1：ARM SystemReady
-----------------------
ARM扩展ServerReady的新概念（看来是收益不错，做上瘾了？），现在叫SystemReady，分
多个Profile，原来的ServerReady现在叫ServerReady-SR，还扩展了IR（IoT），ES（边缘
服务器），和LS（Linux Group Server）结构也和ServerReady类似：硬件要求，BIOS要求
加兼容性测试套。

IR的要素包括：UEFI子集+DTS，uboot，TF-A，Yocto。32/64bit。

ES的要素包括：UEFI全集+ACPI+SMBUS，64bit。

LS估计还在设计中，没有详细提。

300K2：Trusted Substrate Panel
--------------------------------
讨论会，没有胶片。

主要观点：

1. 很多IOT厂商的OEM被要求支持10-15年，而BIOS只能支持2年，这个问题如何解决？
   能否把这个问题交给芯片提供商，芯片对应的BIOS被公共地支持，从而让OEM有一个
   可以持续解决问题的基础？（主要是微软的人在答）

   其他人的补充：10-20年，而且每代设备要支持很久，但新技术出的周期却越来越快。
   至少硬件的接口别改那么快（预计可以兼容个5、6年）。

2. Redhat：IoT处于一个不安全的环境中，数量巨大，客户不想一个个处理，而希望可以
   总是整批处理，整批进行安全升级。所以标准化是必须的。

3. ARM成立项目Cociny（不知道怎么拼，这只是听到的语音）解决上面问题，作为
   SystemReady的一部分。请去ARM的官网上去找这个项目的细节。


301：True Story: How Rust for AArch64 Linux became a Tier-1 target platform
----------------------------------------------------------------------------
1. Rust意图统一高层和底层编码的需要

2. 演讲花了大量的篇幅介绍Rust是什么，和做广告。老实说，我的英语不好，没有听明白
   广告具体的技术点。

3. Rust定义的Tier X层次挺有参考价值：

   * T1： “保证能工作”，有官方二进制支持，有自动测试，有文档说明

   * T2：“保证能编译”，也有官方二进制支持，但不是每个测试都能通过，库可能有缺失

   * T3：“理论上能工作”

4. ARM实现T1支持主要是靠双方联合团队实现的，用Ampere@Packet作为硬件开发平台。CI
   用github actions，加Rust自己的用例，自动上Packet云完成。

总的来说，我觉得这是一个广告，广告的内容，就是：ARM是Rust的Tier-1支持平台。

302：Integration Arm SPE in Perf for Memory Profiling
--------------------------------------------------------
SPE是Stastistical Profile Extension，A8.2开始支持，主要目的是不但跟踪内存发生的
地点，同时记录被访问内存的位置（两种位置：内存地址，Cache Line层级）。最后用于
支持perf c2c命令。

具体的工作原理，我觉得现场没有说清楚，这个演讲提取SPE和c2c两个关键字就差不多了。

作为参考，下面是SPE记录的内容：::

        0.      (Address)       Virtual PC of the load instruction.
        1.      (Type)          Load instruction.
        2.      (Counter)       Number of cycles spent waiting for the
                                instruction to be issued.
        3.      (Address)       Virtual address accessed by the instruction.
        4.      (Counter)       Number of cycles spent executing the instruction.
        5.      (Counter)       Number of cycles spent translating the address.
        6.      (Address)       Physical address accessed by the instruction.
        7.      (Source)        Where in the system the data was returned from.
        8.      (Events)        E.g. Missed in level 1 data cache and TLB.
        9.      (End)           End of record, optionally containing a timestamp
                                for the instruction

303： Secure Partition Manager(Armv8.4 Secure EL2)
---------------------------------------------------
Secure EL2是8.4的重要特性，我是一直没有搞明白这个需求是怎么来的，安全区连虚拟化
都支持，这个安全区功能也太强大了，还能安全吗？

这个胶片对此的解释是：要分开Vendor：进程分Vendor会有合作，但如果从虚拟机开始分
，大家都和Arch提供商的接口合作了。

基于这个方案，EL3上跑SPMD，安全EL2跑SPMC（Hafnium），开源在trustedfirmware.org上。

非安中断先被SPMC捕获，先让安全调度器调度，不截获了，在进EL3，调度给NS区的对应EL。
（其中反复提到一个概念叫NWd，不知道是啥）

这个其实主要介绍Hafnium的实现，其中涉及对Pauth、BTI、SMID/SVE，安全EL0
Partition的支持原理问题。但胶片语焉不详，录像的声音质量很差，我没有太抓到他说了
啥。

另一个演讲者讲到对SMMUv3的支持，这个语音很清楚，其中提到支持SMMU的一大原因是保
护安全，但我的判断是，如果你支持ATS，你就很难保证得了安全，因为你没法拒绝物理地
址，而SMMU的实现者其实很难从物理地址反查PTE。但人家说在Hafnium里不支持这个特性
，同时不支持的还有MSI，RAS，Device PF，PME，SMMU的event queue，MPAM。我对这些不
支持特性的兴趣在于：SMMUv3的最小集合到底可以砍掉多少功能。

304：GDB and LLDB contributions in 2020
----------------------------------------
这个主要是工具团队（调试器部分）的进展汇报。主要做了SVE支持，Pauth，TBI，MTE（
Memory Tag）和Morello项目的支持。

其中这个Morello项目是ARM的一个项目，UKRI Funding，基于剑桥大学的CHERI项目的一个
安全保护特性，Capability Hardware Enhanced RISC Instructions。论文将近500页，晚
点再看吧。论文将近500页，晚点再看吧。

305：Virtualising OP-TEE with Hafnium at S-EL2
-----------------------------------------------
这是Hafnium的一个深入介绍，部件间通过FF-A接口（原来的SPCI，Secure Partition
Client Interface，现在叫Fireware Framework Arch）通讯。在NS这边，软件上原来调
OP-TEE的SMC，现在变成FFA call，实现为一个虚拟的ffa bus，通讯是一个基于共享内存
的消息通讯，加中断通知。

306：X.509 Cer tificate Management with Zephyr/ TF-M
-----------------------------------------------------
介绍Linaro的IoT X.509校验方案，没有什么特别，如果非要说有，就是设备一侧的校验过
程是在安全区完成的。

消息流是EL3上SPMD分发，SPMC处理，在发到每个SP（Security Partition）。

307：FF-A compliant Secure User Mode partition
-----------------------------------------------
翻了一下胶片，这个讲StandaloneMM程序，应该是一个用于最简单的，仅有用户态的安全
区的应用，这个领域我兴趣不大，不深入听讲啥了。

308：Essential ARM Cortex-M Debugging with GDB
------------------------------------------------
这个应该说是一个西风上GDB支持程度的一个广告。但它也确实是一个GDB的基本功能培训，
我觉得看看挺有意思的，因为可以通过别人的演示和使用习惯，优化一下自己的GDB使用习
惯，也对西风的工作环境有一个直观的理解。

对我个人来说，增长的见识主要是现在GDB支持Python脚本了（通过gdb命令source直接调
用）。

309：SVE and SVE2 in LLVM
--------------------------
SVE/SVE2在LLVM上的进展介绍，但也是SVE/SVE2/ACLE的一个很好的入门介绍。用的例子都
是最基本的向量化算法，把原来循环的计算放到向量寄存器的每个Lane上而已，很好懂。

ACLE扩展主要通过pragma实现，但介绍者说这主要还是因为不安全，最终的目的还是希望
这个变成自动化的。

演讲中用到一个工具叫Complier Explorer，这个东西很有意思，它可以一边修改程序，一
边看到汇编代码的变化。比如你可以先用progma clang loop unroll(diaable)关掉SVE，
然后再打开它，就直接可以在旁边看到汇编发生了什么变化。或者你可以调整pragma loop
vectorize_width(2, scalable)改成4，立即看代码的变化。

它的前端是个基于Node.js的开源项目，github地址在这里：

        https://github.com/compiler-explorer

看项目名它支持c/c++，python，go，ocaml等语言，可以用作VSCode的插件。它的介绍是
这样的：

        | Run compilers interactively from your web browser and interact with
        | the assembly

实际的工作都在后台，前端只是把代码发给后端的Compiler Explorer的服务器，由服务器出
结果给客户端。

项目的Sponsor中我看到了Intel和PC-Lint。

310：Unifying Kernel Test Reporting with KernelCI
--------------------------------------------------
这个演讲的逻辑大概是这样的：现在有很多内核测试方案，报告都不一样，比如LKFT，
KernelCI（Linaro自己的），0-Day（Inte），Google syzbot，CKI（Redhat的）等等，大
的有14个标准。所以几个大厂，比如Redhat，Google，MS，IBM等聚集起来，准备弄一个大
家都承认的标准。但这样做呢，很可能最终的结果我们就会再多一个标准出来。

现在是打算弄一个kci_data的标准出来，都存在KCIDB里面，先把报告标准化了。KCIDB的输入
接口用json，命令行提供维护管理接口（都叫kdbci-xxxxx），其他细节其实都是网站技术了，
这里没有什么好总结的。

要说KernelCI这些年从磕磕碰碰，就凭一点服务器资源做到现在这地步，我觉得还是挺好
的（至少表面逻辑上说起来，实际效果没有分析过）。这种东西也没有什么技巧，关键是
一直得有架构定力和设计而已。

200k1：BUILDING THE FUTUREOF PERVASIVE, UBIQUITOUSCOLLABORATIVE INTELLIGENCE
-----------------------------------------------------------------------------
我司的胶片，不知道哪个市场部门的人又去卖概念了，我只看到了openHarmony和
openEuler两个概念，完全不知道说了啥。

209：96Boards, Drones & PX4
----------------------------
介绍一个用于无人机的96Board，这个我没有兴趣，不看了。

211：Boosting ApplicationPerformance on Arm Data Centers
---------------------------------------------------------
这也是我司的胶片，将数据中心ARM应用的优化经验的，这个记录一下：

1. 把SPINLOCK中的TAS换成CAS，在数据库中带来12%的性能提升

2. 把仅在x86中的优化手段在ARM中也放开，用向量减少循环

3. 使用ARM的CRC指令处理CRC算法

4. 用NEON指令优化ISA-L/JDK等开发库

鲲鹏特有的：

1. 基于鲲鹏硬件优化的毕昇JDK

2. 用KAE（存储的UADK Clone）处理openSSL和zlib软算法

3. 替换鲲鹏特有的数学库，比如Spark ML，处理性能提升1.5-20倍

212：Firmware Framework-M1.1 Feature Updatein Trusted Firmware-M
-----------------------------------------------------------------
m-profile的TrustFirmware实现，我不关心，不看了。不过快速扫了一下内容，感叹：做
嵌入式真好，要考虑的烂事少多了，怀念那种日子啊。

213：96Boards: progress on Autoware.IO PCU
-------------------------------------------
自动驾驶的96Boards介绍，包括在HiKey 970和DragonBoard上运行Ubuntu+ROS2（美帝贸易
战祸害不浅，否则现在不可能还用这么旧的板子。真所谓时代的一颗尘土，行业的一座大
山啊）。

(演讲者没有提，不过看起来HiKey的实时性可比DragonBoard好多了：））

还介绍了一个Autocore的PCU，包括模拟器，跑Ubuntu20.04+ROS2Foxy或者FreeRTOS。没有AI，
没有网络，但有PCIe接口。看图我还以为这玩意儿和HiKey一个大小，看视频才知道，这个
基本上是个大号机顶盒那种规模的。演讲者说从中国买的。性能类似PC，比手机芯片好，
比服务器差。

Autoware的软件栈就Yocto，测试的第一优先级是实时性，下来的工作估计不少是使能PCU
。其他的演示大部分我都看不懂了，因为不知道那些测试例子是干什么的，只知道用了K8s，
内核会打prempt-rt和i-pipe补丁，需要用AI。

214：Booting Linux on Arm’s CCIX：enabled Quad-ChipletReference Design platform
-----------------------------------------------------------------------------------
这是用ARM参考平台Neoverse+CCIX做的多片互联系统。相当于用CCIX充当鲲鹏的Hydra互联
，做多Socket的互联（这个性能高不到哪去吧？）。

Neoverse作为参考平台，里面基本上是个功能全集，有MCP和SCP。单个芯片的时候复位后
MCP和SCP同步启动，然后用SCP启动CPU，然后就是：

* BL1：应用核的第一步初始化

* BL2：EL3安全启动

* BL31：EL3 Runtime (GIC, SCMI初始化）

* BL32：安全EL1初始化(UEFI MM)

* BL33：非安全初始化（UEFI）

* Grub：Firmware之外的东西

这样一个启动过程。这个胶片倒是让我正经学了一次ARM推荐的启动过程了。从描述来说，
很多时间是花在GIC和SCMI的初始化上的，因为要在多个Chip间分配MMIO地址和中断编号。

另一部分工作就是调整NUMA相关的几张ACPI表：MADT（GIC），SRAT，HMAT。

215：PKCS#11 in OP-TEE
-----------------------
PKCS#11是一个访问密码令牌的API标准，又叫Cryptoki（Crypto Key的意思）。传统的做
法不用OP-TEE，是运行系统，通过I2C之类的协议访问加密卡，让加密卡完成相关的加解密，
这个胶片讲一个方案，把加密卡的部分放到OP-TEE中去完成，全部提供源代码。

我其实一直对把CPU分成S和NS两个部分有疑问：为什么分成两个部分就安全了呢？这和特
权级本质有什么区别？首先光靠这个你没法防我把硬件拆下来读数据的，对吧？那就是数
据请求变得更难而已，但你还是共享同一个CPU，只是CPU处于不同状态而已。剩下的而保护
可能就是内存的分割，让部分内存在另一个状态下不可见，这种加上很大的工作量（安全
区要另外的程序），寻求一个心理安慰，真的就比靠特权级隔离更加好吗？

216：EFI Secure Boot of LEDGE RP on STM32MP1, KEK provisioning and direct booting of Linux
-------------------------------------------------------------------------------------------
我看到STM32这几个字，就决定不看了。

217：Zephyr on Jailhouse Hypervsior
------------------------------------
这是个工作报告，用Jailhouse虚拟机把i.MX分成西风和Linux两个部分运行。得个知字。

218：Suppor ting Qualcomm wcn3680 on Android and upstream
----------------------------------------------------------
这也是个工作报告，wcn3680是用在刷卡机上的，我都不明白干嘛要跑Android（这个工作
还跑Debian），不少工作是处理wpa_supplicant wifi网卡驱动。也是得个知字。

219：Enabling Collaborative Processor Performance Control (CPPC) on Arm Platforms
----------------------------------------------------------------------------------
CPPC是一个ACPI特性，用于管理CPU的性能范围（在调频的时候），原来是在Intel上做的
。这个胶片介绍ARM上的工作，大概的原理是在OS一侧监控性能范围，如果需要调整了，就
通过SCMI接口控制SCP去进行DVFS调频。ARMv8.4的AMU标准支持这个监控功能，通过系统寄存器
控制（不是MMIO）。

220：Generic image approach and LEDGE RP
-----------------------------------------
边缘服务器的参考平台，值得看的是选择的方案：
Uboot/EDK2可选，optee，linux kernel。
目标硬件包括ARM32，ARM64和x86，但实际开发是用qemu搞定的。对我来说，主要是知道：
qemu现在支持安全OS跑进来了？有空得试试。

221：Large Virtual Address support (52-bit) in ARM64 kernel
------------------------------------------------------------
ARMv8.2-LVA特性使能，4PB的虚拟空间（Intel最大支持到57位VA，52位PA）。和原来48位相比，
仍用3级页表，但第一级页表规模变大（Intel用了5级页表）。

实现目标是单二进制支持多中页表长度。这带来一个问题，48位的时候内核起始地址在
0xFFFF 0000 0000 0000，52位的时候就变成0xFFF0 0000 0000 0000了，这两个地址不一
样，没法放在一个Image中，所以只能想48位对齐，都放0xFFFF ....中。这样就需要重新
调整比如kdump这样的工具。

这个特性可以用qemu来验证的。

222：A networking chipat the heart of an Arm-on-Arm workstation?
------------------------------------------------------------------
NXP LX2160A网络芯片的使能，A72x16的片子，比一般PC快，比服务器慢，编Linux内核11
多分钟。uboot/UEFI可选。作者想着要当PC用。

112：Devicetree BOF
--------------------
讨论DTS有关的东西。我感兴趣的几个信息：

1. 有人考虑做DTS转ACPI表的工作，一种场合是这样的：我Host上是DTS的，但我要起一个依赖ACPI
   的操作系统，比如Windows。我想：反过来，我服务器上跑手机需要反着做吗？看起来，答案是不
   需要，因为这是我虚拟机配置的问题，和本地应用没啥关系。

2. SystemReady在server上选ACPI，但没有打算断DTS，对ARM来说，这会长期共存。

3. 讨论中反复谈到一个概念叫System Device Tree，我从上下文中感觉，这好像是一种标
   准化DTS格式和内容的手段，因为很多接口，比如remotePRC，每家都是不同的。有人还
   提到，部分硬件是可编程的，接口可以动态改变，预计这也是System Device Tree要解
   决的问题之一。

4. EBBR公开维护，不是ARM控制的社区标准

5. 本来想听听风河对DTS的观点的，但语音断断续续的，不知道说了啥，只听到一个观点
   是vxworks和linux共享dts现在看来运作良好。

6. 当前Kernel 4000 binding， 1000+ schemas，

113：TENSORFLOWLITE DELEGATES ON ARM-BASED DEVICES
---------------------------------------------------
就是一个NXP的TensorFlow使能工作，没啥东西。

114：The Case for UEFI Boot on Arm-powered IoT Devices (Again)
---------------------------------------------------------------
没意思，不看。

115：SystemReady SR and ES
---------------------------
入门级的介绍，没有什么可看的。

116：Physical Attack Mitigation
--------------------------------
主要介绍MCUboot的安全启动方案（非要说得标题上那么高大上），主要是防比如通过一个
干扰，导致执行跳过一段代码执行，或者导致某个循环提早结束什么的。

这类攻击是有成熟的平台的，比如Chip Whisperer，可以通过化学药剂，激光，声音等对
目标系统造成干扰。MCUBoot针对这种攻击把启动的每一步都包在一个FIH_CALL和
fih_not_eq()的处理，把判断条件变复杂，让简单的物理位变化干扰不了执行流程。

这是挺好的一个初步了解物理攻防手段的入门教程。

117：SystemReady IR in practice
--------------------------------
i.MX一个平台符合IR的过程介绍，主要是演示，呈现为最终用UEFI启动几个（注意，是几
个，这是SystemReady证明这个方案具有通用性的手段）规定的标准OS。

从演示来看，它用uboot启动指定的UEFI，带特定的命令行（sct），然后加载ebbr.seq文
件得到一个测试菜单系统，可以选择一组测试例，测试完成后从存储中取出日志文件看结
果就可以了（需要格式转换）。完成测试后，即使用UEFI命令启动多个OS映像，然后就算
通过Certification了。

118：The Qualcomm IPA Driver
-----------------------------
IPA是高通SoC连Modem的设备，所以，这本质是一个网卡驱动的开发过程。这东西本来就开
源的，只是没有upstream，这个介绍就是介绍这个upstream而已。

但这个过程对于习惯于私有商业开发去理解开源开发还是挺有帮助的。

我highlight部分我平时在说服内部开发者老要解释的一些情况：

1. HAL层被Linux Maintainer质疑了。这是显然的事情，内部开发者都习惯做各种各样的
   HAL，但HAL对于每个具体被Abstract的系统来说，都是成本。所以，不要在合入人家
   系统的时候那么

2. 第一个RFC 2018年的，到现在也做了3年了。这仅仅是一个驱动（不是框架）。这个时
   间也许可以作为我们打算上传主线工作的一个参考。当然这个代码原始规模确实很大，
   估计在20万行以上，但实际上上传的时候减掉了一半以上的代码了。这其实一个架构
   代码和产品化代码的差别，说明为什么我们需要同时维护架构主线和战地分支，产品化
   分支是免不了要飞线的，但只有这一个飞线的版本，肯定也是不够的。

3. 更有趣的是：简单删除了10万行以上的代码后，代码还是被放弃了。社区根本不想收：
   原因是：

   * 太大，难以理解它的复杂性

   * 功能被组合在了一起

   * 代码风格和Linux对不上，重复代码

   * 代码设计和Linux的经验不一致（我觉得大部分都是老代码跟不上技术进步），比如
     学会了workqueue，无论什么情况都用workqueue，但更能优化代码的threaded
     interrupt就不用，在“能跑就好”，赚钱第一的理念下，这种东西就没人管了。从这
     个角度来说，架构分支的存在，和战地分支的博弈，是架构能够长治久安的基本手段。

     类似的问题还有，多余的锁范围，没有使用NAPI等等。

   * 从不会使用的代码：商业代码最喜欢干的事情，代码反正也写了，等着以后用，反正
     能跑就行，你们管不着我。在架构版本上，就有人管得着你了：）

   * 大量#ifdef...

   * 等等。

4. 不要用ioctl, bug()和不要封装内核的公共设施，这一点也是Linux越来越重视整体统
   一构架和对外呈现的一个标志。

5. IPA有特殊的路由功能，但现在都还没有上传成功。这是一种常见的情形，你做一个特
   定的产品，这个产品的功能是固定的，所以你把部分路径组合在一个模块内（包括硬件
   模块内），这很正常，但Linux本身有自己的架构，路由就是路由，端口就是端口，你
   要加一个路由进去，就要修改它原来的架构空间，然后才能让你进去。这个场景解释了
   为什么很多时候拉分支是必须的。

6. 还有一个经常发生的场景也发生在这个产品上：在上传的过程中，另一个框架（Intel
   的WWAN）上线了，又得停下来进行配合。

7. 在上传的过程中，downstream的那个代码，还是在发展，而预计还需要存活很长一段时
   间，Bug也不能指望在两边共享，这些都是必须面对的现实。这告诉我们，拉了分支，就
   不要指望什么Share开发，Share开发的前提就是你不要拉分支。但不来分支针对不同的
   Topic，就是成本。这是我们进行架构权衡的基础。

8. 演讲者有一个归纳特别好：upstream code我们重视的是质量（我理解这包括构架质量
   和测试质量），downstream code我们重视的是符合进度要求和pass the test。后面这个
   pass the test是精要：）。

   这个归纳还有其他说法：upstream code是为演进（就是我说的为架构），downstream
   code是为了特定的平台，特定的生命周期（就是我说的战地版本）。

还有其他一些值得关注的观点：

1. 推荐使用BQL，这个特性3.3开始有的，看来是类似qdisc的其中一个队列算法，下来我
   再看看。

   https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/#:~:text=Byte%20Queue%20Limits%20%28BQL%29%20is%20a%20new%20feature,to%20avoid%20starvation%20under%20the%20current%20system%20conditions.


120：Moving to DMA-BUF Heaps:Now is the Time!
----------------------------------------------

.. note::

   不了解什么是DMA-BUF的读者需要自己去学习一下，本文不假设这种情况。

   其实本质是把DMA需要的数据放到一起，以便每个驱动和用户态拿到这个数据结构都可
   以map它。

DMA-BUF支持在用户态分一片然后作为堆来分配，通过/dev/dma_heap设备来提供，封装了
一个C++的访问接口，class BufferAllocator::Alloc()。我觉得猜都能猜到怎么实现的，
不细看了。

不要值得补一句的是这个设计的目标，它是要解决是让用户态去控制整个DMA-BUF的属性，
比如你的Buf传递路径上，有人要求物理地址连续，这个事情你让驱动给你分配（比如你让
机顶盒的Tuner来给你分配这个空间），它根本不知道这个业务的属性和它需要经过的
pipeline，这个问题就无解了。

121：Firmware Configuration Framework in TF-A and Chain of Trust
-----------------------------------------------------------------
这也是一个标准化的工作，是把ARM的BLx的各种设备属性都通过fconf接口
通过get_property的方式访问出来。

122：Trust Ain’t Easy:Challenges of TEE Security
---------------------------------------------------

.. sidebar:: 架构思考

   这个问题让我想起经常在做架构（包括解释《道德经》）时的一个经验：人们总是很容
   易被一个概念（所谓“名”）所绑定。比如说，做安全，真正要解剖这个概念，你要定义
   的是你要从什么上下文中，保护什么信息，为什么这些信息得到了保护。但讨论这个问
   题太难的，人们就会更容易想去讨论enclave，讨论SGX，讨论TrustZone，甚至连客户
   都可以接受：有了这个名字，我的系统就安全了。但没有人愿意去讨论真正的信息保护
   的逻辑。

   做计划也是，很多项目经理都希望我们可以有一个计划，设计，开发，测试这样一个循
   环，这样我们的事情就成了。但对于复杂的项目，我们需要定位几个路径目标，然后设
   计验证，调整路径目标，再设计验证，再调整路径目标，这是一个现实情况，但这个不
   容易描述，不容易思考，他们就接受不了了。就算有些项目经理接受了所谓的“迭代交
   付”，他们同样接受不了第一个迭代做了3个特性，第二个迭代再做1个特性，并且废掉
   两个特性。他们说：“这怎么可以？”，你看这句话，表达的是一种“期望”，但从接受客
   观现实的角度，我们要做一个摸路的事情，这不是很自然的规律吗？好比你要走出一座
   大山，你不能不走，但走出去一段，发现这段路方向不对，你不是很自然需要换路走吗
   ？（当然退到哪里需要设计，这也是架构设计提供帮助的地方），你怎么可能认为你需
   要死活的要往前走呢？

   说到底，这些问题就是个是否负责的问题，就好像前面这个大山的问题，如果这是你自
   己的事情，走不出大山你自己的命都会交代在这里，你就会更“理智”，而不是维护你建
   立的“名”。如果你进行要证明“这事情不是我的责任，结果如何有别人背锅”，那人就会
   更容易被“名”绑定。他们希望自己做的每件事都和目标搭上关系，至于对这些事情的排
   序和取舍，他们就管不到了。所以，管理和战略设计中，形势情（
   :doc:`../道德经直译/形势情`\ ），需要把“情”放到这么高的地位，因为一群人的决
   策中，不能把这群人逼到达成目标就是“为自己活着”的位置上，这个事情就会流于“名”
   这个表面，就不会有集体的力量了。
   
这个演讲看来回答我前面关于TEE的设计思路的问题，开一个安全区，其实物理上就是隔离
的，只是分享CPU算力而已。这是它和特权级的主要区别。

另外，其实这个演讲我感觉更多的是设计理念上的交流，作者是一家专门做TEE解决方案公
司的Cofounder，算是这个领域有很多经验的架构师吧，不少观点挺值得讨论的。

演讲者一个观点我很赞同：现在TEE的安全策略，其实不是Consistent的，并没有回答每个
对象被限定的空间在哪里。你不允许进程访问某片内存，并不能保证它不能通过设备（比
如DMA引擎）作为跳板去访问这片内存，这些Trust Zone并不能解决，必须在解决方案层面
来给方案，而这个方案不会简单，因为你要一个个系统组件去确定他们的身份和它们可以
访问的范围。如果考虑你要跨产品支持一样的特征，这就会更困难。

所以，整个设计的难度其实是你怎么分配隔间，TrustZone不是一个安全解决方案，而是一
个“可能可以为你设计隔间提供帮助的基础设施”。

演讲者还有一个观点我也很赞同：特性做得好，没有什么意义，关键是你能否在你需要用
的时候，它有Availability。所以做生态架构，关键支持哪些发行版显得那么重要。你自
己做一个版本，然后说，某某特性我已经有了，结果客户又不用你那个版本，这个所谓“有
了”，虚伪得很。（演讲者用的例子）

最后，演讲者有一个从其他工业借过来的安全团队的设计方向：

* Certificatation

* Vulerability跟踪 & 0-day测试

* 持续升级

所以，本质上，这个工作不是一个“建设性”工作，而是一个攻击-修补的一个“反面性”工作。

我觉得这个演讲捅破了不少皇帝的新衣，但也没有提出什么解决方案。

123：Qualcomm upstream update
------------------------------
高通芯片的驱动上传状态，高通也算是正式“拥抱开源”了，之前好像可没有这么主动。

200k3：Android Automotive OS
-----------------------------
Google的Keynote，Android用于车上，主要做车的多媒体系统，状态显示等（原话是
Android System for Autmotive Entertaiment），所以基本上还是个Android，还是基于
Linux内核的，就是不知道这玩意儿要不要做车规认证啊。

但这和手机还是不同的，手机绑定一个人，车绑定多个驾驶员，甚至服务车上不同位置上
的不同用户，手机需要Wifi，车不需要，等等。

解决方案依赖虚拟化（觉得车芯片可以拆虚拟化功能的可以死心了），Android部分作为
Host的一个虚拟机运行，下面全部设备使用virtio来实现（加入相关标准和社区组织，看
来是基本构架的一部分），包括virtio-snd/gpu/video/scmi。所以，Android一侧可以完全
看不到实际硬件，包括不需要看到vehicle bus，直接通过vsock通讯就可以了。

方案依赖TrustZone，但没说为什么，估计是等Vendtor自己想应用场景。

方案对Kernel的维护时长是6年。其中提到一个数据比较有趣：2019年92%的被Google SPL
程序识别为安全漏洞的问题，都在LTS中已经修复了。从这个角度来说，LTS的安全漏洞保
护还有有效果的。对Google来说，现在的问题就是维护时限了。

对于性能，最大的问题是，车里的硬件又不能升级，后面新应用出来了，怎么保证性能够
？我是觉得这个问题无解，因为摩尔定律还是基本存在的，唯一的方法是让硬件升级吧。

可靠性的主要应对是CarWatchdog，这和一般意义的Watchdog，它似乎一个主动服务，会查
所有有可能有问题的调度和服务，如果这些调度和服务不正常，就根据策略采取动作。

小结
=====

内容没有什么可以总结的，我看到的特征有两个：

1. 投入上，还是过去那样，嵌入式的投入比较多，IoT第一，Android的分量一直在下降，
   服务器只有少数人完，大玩家都没有进来。主要是ARM和华为在Linaro投。

2. 今年的项目管理可能好了，因为看起来每个独立技术介绍都挺清楚的。但也许是因为现
   在我不用背责任，对目标没有期望了？
