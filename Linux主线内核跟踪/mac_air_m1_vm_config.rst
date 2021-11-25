.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0

MacBook Air M1 Paralles VM的配置分析
*************************************


CPU特性
========

本文对MacBook Air M1中运行Paralles VM的硬件配置进行一个分析，看看这种应用模式的
特点是什么样的。

我个人很看好这种Host私有，VM环境标准化的发展方向，这样保证了硬件发展的速度，也
保证了生态系统的稳定。这是这个分析背后的主要动力。

这是虚拟CPU支持的所有特性：::

        fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid
        asimdrdm jscvt fcma lrcpc dcpop sha3 asimddp sha512 asimdfhm dit uscat
        ilrcpc flagm ssbs sb paca pacg dcpodp flagm2 frint

我们对比一下鲲鹏920的：::

        fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid
        asimdrdm jscvt fcma       dcpop      asimddp        asimdfhm

前者多出来的内容包括（内容参考内核文档Documentation/arm64/elf_hwcaps.rst）：

* lrcpc：Load-acquire RCpc instructions (v8.3)

* sha3/sha512：加密算法指令 (SVE2)

* dit: Data Independent Timing instructions (v8.4)

* uscat: Ralexed Alianment (ID_AA64MMFR2_EL1.AT，v8.4-A)
 
* ilrcpc: 没有查到，应该也是一个RCpc功能，（ID_AA64ISAR1_EL1.LRCPC）

* flagm1/2: Condition flag manipulation (v8.4/8.5)

* ssbs: Speculative Store Bypass Safe Instrucltion (v8.0)

* sb: Speculative Barrier (v8.0)

* paca/pacg: Pointer-Authentification

* frint: FRINT32Z/32X/64Z/64X instruction

每个特别多特征，主要还是因为支持了v8.4的特性。

外设
=====

lspci空，没有任何PCI相关的东西。

lsusb：::

        Bus 003 Device 004: ID 203a:fff9 Parallels FaceTime HD Camera
        Bus 003 Device 003: ID 203a:fffb Parallels Virtual Keyboard
        Bus 003 Device 002: ID 203a:fffc Parallels Virtual Mouse
        Bus 003 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
        Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
        Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

把和host设备的分享都做成usb设备了。

lshw，抽取IO的部分：::

     *-virtio0 UNCLAIMED
          description: Virtual I/O device
          physical id: 5
          bus info: virtio@0
          configuration: driver=virtio_gpu
     *-virtio1 UNCLAIMED
          description: Virtual I/O device
          physical id: 6
          bus info: virtio@1
          configuration: driver=virtio_balloon
     *-virtio2
          description: Ethernet interface
          physical id: 7
          bus info: virtio@2
          logical name: eth0
          serial: 00:1c:42:80:5f:61
          capabilities: ethernet physical logical
          configuration: autonegotiation=off broadcast=yes driver=virtio_net driverversion=1.0.0 ip=10.211.55.3 link=yes multicast=yes
     *-scsi
          physical id: 8
          logical name: scsi1
          capabilities: emulated
        *-cdrom
             description: DVD reader
             product: Virtual DVD-ROM
             physical id: 0.0.0
             bus info: scsi@1:0.0.0
             logical name: /dev/cdrom
             logical name: /dev/cdrw
             logical name: /dev/dvd
             logical name: /dev/dvdrw
             logical name: /dev/sr0
             version: R103
             capabilities: removable audio dvd
             configuration: ansiversion=5 status=nodisc

GPU/Ethernet做成virtio设备(Balloon用于host/guest分时分享内存的），存储单独模拟了scsi接口。

lsblk，忽略loop设备后的结果：::

        sda      8:0    0   128G  0 disk
        ├─sda1   8:1    0   512M  0 part /boot/efi
        └─sda2   8:2    0 127.5G  0 part /
        sr0     11:0    1  1024M  0 rom

mac一侧文件系统挂载进来使用的是prl_fs，源代码在这里：

        /usr/lib/parallels-tools/kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs

主要是一个基于共享内存的Host/Guest通讯协议进行数据交换。

dmesg分析
=========

有如下观察：

1. 使用UEFI+ACPI启动

2. 支持PSIC接口

3. 支持SMBIOS，可以用dmidecode看到整机信息，不过作为虚拟机，没有多少东西

4. 支持6个hardware breakpoint，说明硬件功能可以透到Guest中。

5. 开了IOMMU，这个有意思，说明Guest中创建了虚拟IOMMU，不知道为什么有这个必要：::

        ./bus/platform/drivers/arm-smmu-v3
        ./bus/platform/drivers/arm-smmu
        ./module/arm_smmu_v3
        ./module/arm_smmu

6. KVM Nest……那是肯定不用指望的：::

        kvm [1]: HYP mode not available

其他prl外挂
============

除了prl_fs外，paralles还加入如下外挂驱动：

1. prl_freeze：处理OS休眠

2. prl_vid：处理显示，但没有代码，怀疑直接和xorg关联。

prl_tg则是Guest-Host进行通讯的基础支持模块（称为ToolGate），依靠
/proc/driver/prl_tg调用。

除了内核模块（这部分提供源代码，其他部分是不提供的，而且内部部分的版权也不是GPL
，而是Paralles），还有这样一些工具：::

        hostname:/usr/lib/parallels-tools/tools/tools-arm64/bin$ ls
        prlcc  prlcp  prldnd  prlhosttime  prlsga  prl_showvmcfg  prlshprint
        prlshprof  prltimesync  prltoolsd  prlusmd

        hostname:/usr/lib/parallels-tools/tools/tools-arm64/sbin$ ls
        prl_nettool  prl-opengl-switcher.sh  prl_snapshot  prltools_updater.sh
        prl-xorgconf-fixer

（都是各种Guest对Host代理，有elf也有脚本）以及xorg多个版本的驱动。


总结
=====

没有什么可总结的，一个没有什么可以惊奇的设计吧。

网上有一个叫\ *M1 Explainer*\ 的文档，讲了不少M1的创新，看起来都是在微架构上的。
