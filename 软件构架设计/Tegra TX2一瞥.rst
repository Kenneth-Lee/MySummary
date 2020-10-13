.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

Tegra TX2一瞥
**************

最近入手了一台Tegra TX2做玩具，职业习惯，快速总结一下这个东西，供其他有兴趣的同
学参考。（注：一如过往，这只是快速形成的印象，不保证正确性，如果你信这个搞出什
么问题来，别回来找我）。


这个总结分三部分写：

1. 第一印象

2. IO子系统

3. 内存子系统分析

第一印象
========
首先说说硬件，总的来说，我还是很喜欢这个硬件的：

        .. figure:: _static/tx2-1.jpg

关键是小巧玲珑，到处带很容易，而且机能基本上足够：本地编译Kernel，基于Docker启
动个web服务器，都没有什么困难。

对于小巧玲珑这一点，估计用惯树莓派或者HiKey这种板子的人会有不同意见。但这两个东
西用来做开发，完全不够看。要知道我平时在家里用的都是这样的货色：

        .. figure:: _static/tx2-2.jpg

接着说软件——简单总结，这个东西具有一切商业公司对待开源社区的傲慢无知的缺点。

你说你做一块自恰的单板，你直接给我做一个USB启动，直接插盘安装不就完了？它偏不，
非要做一个管理软件（JetPack），把一台服务器形态的单板做成一个嵌入式单板，
JetPack需要先安装到Host上，然后用Host来安装Target。

最大的问题是，这个JetPack安装的时候，默认安装目标是安装程序本身的路径，而且一旦
你确认，立即删除同目录下的所有文件，问都不问一声：

        .. figure:: _static/tx2-3.jpg

（看不清的话，这里是手册上的内容清单：

        | OS Image:
        |       A sample file system derived from Ubuntu for Jetson
        | Libraries:
        |       CUDA Toolkit for Host PC (Ubuntu with cross-development support)
        |       CUDA Toolkit for Jetson
        |       OpenCV
        |       VisionWorks
        |       cuDNN
        |       TensorRT
        |       MultiMedia API
        | Dev Tools:
        |       NV System Profiler Tegra Graphics Debugger (OpenGL调试）
        |       Sample Code
        | Documentation

）

真是自来熟，不把自己当外人啊。这风格和cuda那一堆库那样，装起来就到处撒东西，装
完机器就不是你的了。一副缺乏竞争，“你不用我不行”，为所欲为的模样。

(这个安装也是一样的，直接给我的PC加了dpkg --add-architecture arm64，装binutils
，把我的本地库管理弄得一塌糊涂，直接锁住了一堆本地程序的升级——关键是包括安全升
级。弄得我装好Target就把这个Host给卸了，还卸了半天）

不说这个安装过程要翻某某神秘障碍物了，更神奇的是，你看着它是个图形界面，实际上
，它里面是个脚本调用，而且这个调用过程调了sudo，所以，如果你不仔细看它的日志窗
口，在里面输一下密码，这个安装过程会永远挂在这里。

出现这种问题，怎么看都是毫无开源文化的商业公司，找了几个小外包，根据需求说明单
一天天算钱做出来的。

这一点也表现在内核的下载上，你说你要给我源代码，你给内核的git路径不就结了吗，结
果你做了这个：::

        git clone https://github.com/jetsonhacks/buildJetsonTX2Kernel.git

里面居然仅仅是下载kernel的脚本

而执行这个脚本，居然又在里面调sudo。大哥，我就下载个Kernel源码，这和sudo权限啥
关系啊？

有了前面被删光download目录的经验，这次我去看了一下sudo是干哈的——原来它非要把内
核给我下载到/usr/src目录下——谁告诉你我一定会在目标系统上编译这个代码啊？

再说了，makeKernel我也就只是想编译一下，我没想要替换现在的内核啊，你给我拷上去
又算怎么回事？……

无论如何吧，这次源代码中是一个.o都没有了，不再玩原来nv驱动那种“用户自己链接，所
以我不用开源”的游戏了。这也算一大进步。


再说说TensorFlow，你说你买TX2，一般就是想搞TF, Caffe,MXNet一类的东西了。这些应
该默认就可以正常工作吧——现实是，我现在都没有能够装起来。TX2默认装的是Cuda9，官
网给的方案TensorFlow是基于Cuda8的，没法用。后来给了一个Cuda9的版本，跑起来还是
去找Cuda8的库，这个我晚点再去折腾吧。


总的来说，第一印象来说，硬件不错，软件渣渣。最后给一个perf的性能数据做对比：

TX2的：::

    nvidia@tegra-ubuntu:~/work/tegra-tx2-kernel/kernel-4.4/tools/perf$ sudo
    ./perf bench all [sudo] password for nvidia: # Running sched/messaging
    benchmark...  # 20 sender and receiver processes per group # 10 groups ==
    400 processes run

    Total time: 0.382 [sec]

    # Running sched/pipe benchmark...  # Executed 1000000 pipe operations
    between two processes

    Total time: 30.084 [sec]

    30.084290 usecs/op 33239 ops/sec

    # Running mem/memcpy benchmark...  # function 'default' (Default memcpy()
    provided by glibc) # Copying 1MB bytes ...

    3.985969 GB/sec

    # Running mem/memset benchmark...  # function 'default' (Default memset()
    provided by glibc) # Copying 1MB bytes ...

    4.002305 GB/sec

作为对比，这是我的Carbon X1 2017的：::

    # Running sched/messaging benchmark...  # 20 sender and receiver processes
    per group # 10 groups == 400 processes run

    Total time: 0.218 [sec]

    # Running sched/pipe benchmark...  # Executed 1000000 pipe operations
    between two processes

    Total time: 4.265 [sec]

    4.265017 usecs/op 234465 ops/sec

    # Running mem/memcpy benchmark...  # function 'default' (Default memcpy()
    provided by glibc) # Copying 1MB bytes ...

    34.877232 GB/sec # function 'x86-64-unrolled' (unrolled memcpy() in
    arch/x86/lib/memcpy_64.S) # Copying 1MB bytes ...

    23.251488 GB/sec # function 'x86-64-movsq' (movsq-based memcpy() in
    arch/x86/lib/memcpy_64.S) # Copying 1MB bytes ...

    44.389205 GB/sec # function 'x86-64-movsb' (movsb-based memcpy() in
    arch/x86/lib/memcpy_64.S) # Copying 1MB bytes ...

    44.389205 GB/sec

    # Running mem/memset benchmark...  # function 'default' (Default memset()
    provided by glibc) # Copying 1MB bytes ...

    54.253472 GB/sec

        .. figure:: _static/tx2-4.png

6个A57，慢不到10倍，比起模拟器，还可以接受啦。

IO子系统
=========

TX2的启动系统使用的是UEFI+dtb=>grub=>kernel的方案，文件系统使用标准的Ubuntu
ARM64版本（可能经过定制，但至少apt source是标准的）。

（但我怀疑这里做错了，如果用UEFI方案，正确的方法应该是把单独UEFI放在一个fat目录
下，这样最初的加载程序只需要解释fat目录就可以了。现在把UEFI和它东西放在一起，就
发挥不出UEFI和grub加载多种文件系统的效果了）

直接查dtb的compatible，有如下外设（我感兴趣的都标记了对应的驱动，方括号是未入主
线的代码）：::

    compatible = "a-edp,1080p-14-0"; [drivers/video/tegra/dc/panel/panel-a-edp-1080p-14-0.c]
    compatible = "a-edp,1080p-14-0-bl";
    compatible = "ak,ak89xx";(iio/imu/inv_mpu/inv_compass/inv_ak89xx_core.c)
    compatible = "android,CustomIPI";(kernel/smp.c)
    compatible = "android,firmware";(drivers/platform/tegra/firmwares-all.c)
    compatible = "android,trusty-fiq-v1";
    compatible = "android,trusty-irq-v1";
    compatible = "android,trusty-log-v1";
    compatible = "android,trusty-ote-v1";
    compatible = "android,trusty-smc-v1";
    compatible = "android,trusty-virtio-v1";
    compatible = "arm,armv8-pmuv3";
    compatible = "arm,armv8-timer";
    compatible = "arm,coresight-etm3x", "arm,primecell";
    compatible = "arm,coresight-etm4x", "arm,primecell";
    compatible = "arm,coresight-funnel", "arm,primecell";
    compatible = "arm,coresight-replicator";
    compatible = "arm,coresight-stm", "arm,primecell";
    compatible = "arm,coresight-tmc", "arm,primecell";
    compatible = "arm,coresight-tpiu", "arm,primecell";
    compatible = "arm,cortex-a15-gic";
    compatible = "arm,cortex-a57-64bit", "arm,armv8";
    compatible = "arm,mmu-500";
    compatible = "arm,psci-1.0";
    compatible = "bmp,bmpX80";（drivers/iio/pressure/nvi_bmpX80.c）
    compatible = "bosch,mttcan";[drivers/staging/mttcan/m_ttcan_linux.c]
    compatible = "bosch,mttcan-ivc";
    compatible = "cache";
    compatible = "capella,cm32180";（drivers/iio/light/nvs_cm3218.c）
    compatible = "dp, display";
    compatible = "dummy-cooling-dev";
    compatible = "extcon-gpio-states";
    compatible = "fixed-clock";
    compatible = "gpio-keys";
    compatible = "gps-wake";
    compatible = "hdmi,display";
    compatible = "invensense,mpu6xxx";（iio/imu/nvi_mpu/nvi.c）
    compatible = "linux,spdif-dit";（sound/soc/codecs/spdif_transmitter.c）
    compatible = "maxim,max16984-tegra186-cdp-phy";（drivers/phy/phy-max16984-cdp.c）
    compatible = "maxim,max20024";（drivers/mfd/max77620.c）
    compatible = "null,dsi-hotplug";
    compatible = "nvidia, tegra-camera-platform";（drivers/video/tegra/camera/tegra_camera_platform.c）
    compatible = "nvidia, tegra186-mipical";（drivers/media/platform/tegra/mipical/mipi_cal.c）
    compatible = "nvidia,bwmgr";（drivers/platform/tegra/mc/emc_bwmgr.c）
    compatible = "nvidia,carveouts";[drivers/video/tegra/nvmap/nvmap_init.c]
    compatible = "nvidia,denver", "arm,armv8";[drivers/platform/tegra/tegra18_perf_uncore.c]
    compatible = "nvidia,denver-hardwood";
    compatible = "nvidia,denver15-pmu";
    compatible = "nvidia,eqos";[net/ethernet/nvidia/eqos/init.c]
    compatible = "nvidia,fiq-debugger";(drivers/staging/android/fiq_debugger/fiq_debugger.c)
    compatible = "nvidia,generic_carveout";
    compatible = "nvidia,imx185"; --i2c
    compatible = "nvidia,imx219";
    compatible = "nvidia,imx274";
    compatible = "nvidia,mods-clocks";
    compatible = "nvidia,ov23850";(drivers/media/i2c/ov23850.c)
    compatible = "nvidia,ov5693";
    compatible = "nvidia,pca9570";
    compatible = "nvidia,ramoops";
    compatible = "nvidia,smmu_test";
    compatible = "nvidia,storm", "nvidia,tegra186";
    compatible = "nvidia,t18x-cluster-clk-priv";
    compatible = "nvidia,tegra-audio-t186ref-mobile-rt565x";
    compatible = "nvidia,tegra-gic";
    compatible = "nvidia,tegra-t18x-mc";
    compatible = "nvidia,tegra-wdt-t18x";
    compatible = "nvidia,tegra18-rtc";
    compatible = "nvidia,tegra186";
    compatible = "nvidia,tegra186-AXI2APB-bridge";[drivers/platform/tegra/bridge_mca.c]
    compatible = "nvidia,tegra186-AXIP2P-bridge";
    compatible = "nvidia,tegra186-adma";
    compatible = "nvidia,tegra186-adsp-pd";(drivers/platform/tegra/pm_domains.c)
    compatible = "nvidia,tegra186-ahc";[drivers/misc/tegra186-ahc/tegra186_ahc.c]
    compatible = "nvidia,tegra186-ahci-sata";(drivers/ata/tegra/ahci_tegra.c)
    compatible = "nvidia,tegra186-aon";[drivers/platform/tegra/tegra-aon.c]
    compatible = "nvidia,tegra186-aon-ivc-echo";
    compatible = "nvidia,tegra186-aon-spi";
    compatible = "nvidia,tegra186-aondbg";
    compatible = "nvidia,tegra186-aowake";
    compatible = "nvidia,tegra186-ape-ivc";[drivers/platform/tegra/tegra-camera-rtcpu.c]
    compatible = "nvidia,tegra186-ape-pd";
    compatible = "nvidia,tegra186-arad";
    compatible = "nvidia,tegra186-asrc";
    compatible = "nvidia,tegra186-bpmp";[drivers/thermal/tegra_bpmp_thermal.c]
    compatible = "nvidia,tegra186-bpmp-i2c";
    compatible = "nvidia,tegra186-bpmp-thermal";
    compatible = "nvidia,tegra186-cactmon";(drivers/platform/tegra/central_actmon/actmon_common.c)
    compatible = "nvidia,tegra186-camera-ivc-protocol-capture";
    compatible = "nvidia,tegra186-camera-ivc-protocol-capture-control";
    compatible = "nvidia,tegra186-camera-ivc-protocol-dbg";
    compatible = "nvidia,tegra186-camera-ivc-protocol-debug";
    compatible = "nvidia,tegra186-camera-ivc-protocol-echo";
    compatible = "nvidia,tegra186-camera-ivc-protocol-mods";
    compatible = "nvidia,tegra186-camera-ivc-protocol-vinotify";
    compatible = "nvidia,tegra186-cec";(drivers/misc/tegra-cec/tegra_cec.c)
    compatible = "nvidia,tegra186-chipid";(drivers/platform/tegra/tegra_chipid.c)
    compatible = "nvidia,tegra186-combined-uart";
    compatible = "nvidia,tegra186-cpuidle-a57";
    compatible = "nvidia,tegra186-cpuidle-a57-cluster";
    compatible = "nvidia,tegra186-cpuidle-a57-thresholds";
    compatible = "nvidia,tegra186-cpuidle-denver";
    compatible = "nvidia,tegra186-cpuidle-denver-cluster";
    compatible = "nvidia,tegra186-cpuidle-denver-thresholds";
    compatible = "nvidia,tegra186-dc";[drivers/video/tegra/dc/dc.c]
    compatible = "nvidia,tegra186-disa-pd";[drivers/video/tegra/dc/nvdisp/nvdisp.c]
    compatible = "nvidia,tegra186-dpaux";
    compatible = "nvidia,tegra186-dpaux-pinctrl";
    compatible = "nvidia,tegra186-dpaux1";
    compatible = "nvidia,tegra186-dpaux1-pinctrl";
    compatible = "nvidia,tegra186-dsi";
    compatible = "nvidia,tegra186-dspk";
    compatible = "nvidia,tegra186-dspk";
    compatible = "nvidia,tegra186-efuse", "nvidia,tegra210-efuse";
    compatible = "nvidia,tegra186-efuse-burn";
    compatible = "nvidia,tegra186-gp10b", "nvidia,gp10b";[drivers/gpu/nvgpu/nvgpu_gpuid_t18x.h]
    compatible = "nvidia,tegra186-gpcdma";[drivers/dma/tegra186-gpc-dma.c]
    compatible = "nvidia,tegra186-gpio";
    compatible = "nvidia,tegra186-gpio-aon";
    compatible = "nvidia,tegra186-host1x", "simple-bus";
    compatible = "nvidia,tegra186-host1x-pd";
    compatible = "nvidia,tegra186-hsp";
    compatible = "nvidia,tegra186-hsp-mailbox";
    compatible = "nvidia,tegra186-hsuart";
    compatible = "nvidia,tegra186-i2c";
    compatible = "nvidia,tegra186-iommu-context";
    compatible = "nvidia,tegra186-isp";[drivers/video/tegra/host/isp/isp.c]
    compatible = "nvidia,tegra186-ispa-pd";
    compatible = "nvidia,tegra186-kfuse";
    compatible = "nvidia,tegra186-mc-sid";
    compatible = "nvidia,tegra186-mce";
    compatible = "nvidia,tegra186-miscreg";
    compatible = "nvidia,tegra186-msenc-pd";
    compatible = "nvidia,tegra186-nvcsi";[drivers/video/tegra/host/nvcsi/nvcsi.c]
    compatible = "nvidia,tegra186-nvdec";[drivers/video/tegra/host/nvdec/nvdec.c]
    compatible = "nvidia,tegra186-nvdec-pd";
    compatible = "nvidia,tegra186-nvdumper";
    compatible = "nvidia,tegra186-nvenc"; --drm驱动，主线和外部皆有
    compatible = "nvidia,tegra186-nvjpg"; --drm驱动，主线和外部皆有
    compatible = "nvidia,tegra186-nvjpg-pd";
    compatible = "nvidia,tegra186-pcie";
    compatible = "nvidia,tegra186-pcie-pd";
    compatible = "nvidia,tegra186-pinmux";
    compatible = "nvidia,tegra186-pm-irq";
    compatible = "nvidia,tegra186-pmc";
    compatible = "nvidia,tegra186-pmc-iopower";
    compatible = "nvidia,tegra186-pwm";
    compatible = "nvidia,tegra186-qspi";
    compatible = "nvidia,tegra186-roc-flush";
    compatible = "nvidia,tegra186-safety-cmd-resp";
    compatible = "nvidia,tegra186-safety-hb";
    compatible = "nvidia,tegra186-safety-ivc";
    compatible = "nvidia,tegra186-sata-pd";
    compatible = "nvidia,tegra186-sce-ivc";
    compatible = "nvidia,tegra186-sdhci";
    compatible = "nvidia,tegra186-se-elp";（drivers/crypto/tegra-se-elp.c）
    compatible = "nvidia,tegra186-se-pd";
    compatible = "nvidia,tegra186-se1-nvhost"; --这个是未主线化的
    compatible = "nvidia,tegra186-se2-nvhost";
    compatible = "nvidia,tegra186-se3-nvhost";
    compatible = "nvidia,tegra186-se4-nvhost";
    compatible = "nvidia,tegra186-sor";
    compatible = "nvidia,tegra186-sor1";
    compatible = "nvidia,tegra186-spi";
    compatible = "nvidia,tegra186-spi";
    compatible = "nvidia,tegra186-system-config";
    compatible = "nvidia,tegra186-tachometer";
    compatible = "nvidia,tegra186-timer";
    compatible = "nvidia,tegra186-tsec";
    compatible = "nvidia,tegra186-tsec-pd";
    compatible = "nvidia,tegra186-usb-cd";
    compatible = "nvidia,tegra186-ve-pd";
    compatible = "nvidia,tegra186-vi"; [drivers/video/tegra/host/vi/vi4.c]
    compatible = "nvidia,tegra186-vi-bypass";
    compatible = "nvidia,tegra186-vic";
    compatible = "nvidia,tegra186-vic03-pd";
    compatible = "nvidia,tegra186-xhci";
    compatible = "nvidia,tegra186-xotg";
    compatible = "nvidia,tegra186-xudc";
    compatible = "nvidia,tegra186-xusb-mbox";
    compatible = "nvidia,tegra186-xusb-padctl";
    compatible = "nvidia,tegra186-xusba-pd";
    compatible = "nvidia,tegra186-xusbb-pd";
    compatible = "nvidia,tegra186-xusbc-pd";
    compatible = "nvidia,tegra18x-adsp";
    compatible = "nvidia,tegra18x-adsp-carveout";
    compatible = "nvidia,tegra18x-agic";
    compatible = "nvidia,tegra18x-balanced-throttle";
    compatible = "nvidia,tegra18x-car";
    compatible = "nvidia,tegra18x-cpufreq";
    compatible = "nvidia,tegra18x-cpuidle";
    compatible = "nvidia,tegra18x-eqos-ape";
    compatible = "nvidia,tegra20-uart", "nvidia,tegra186-hsuart";
    compatible = "nvidia,tegra210-admaif";
    compatible = "nvidia,tegra210-adsp-audio";
    compatible = "nvidia,tegra210-adx";
    compatible = "nvidia,tegra210-afc";
    ompatible = "nvidia,tegra210-amixer";
    compatible = "nvidia,tegra210-amx";(sound/soc/tegra-alt/tegra210_amx_alt.c)
    compatible = "nvidia,tegra210-axbar";
    compatible = "nvidia,tegra210-dmic";
    compatible = "nvidia,tegra210-i2s";
    compatible = "nvidia,tegra210-iqc";
    compatible = "nvidia,tegra210-mvc";
    compatible = "nvidia,tegra210-mvc";
    compatible = "nvidia,tegra210-ope";
    compatible = "nvidia,tegra210-pmc-blink-pwm";
    compatible = "nvidia,tegra210-sfc";
    compatible = "nvidia,tegra210-spdif";
    compatible = "nvidia,tegra210-spkprot";
    compatible = "nvidia,tegra30-hda";
    compatible = "nvidia,vpr-carveout";
    compatible = "nxp,pca9546";
    compatible = "pwm-fan";
    compatible = "realtek,rt5658";(sound/soc/codecs/rt5659.c)
    compatible = "regulator-fixed";
    compatible = "regulator-fixed-sync";
    compatible = "s,wqxga-10-1";
    compatible = "s,wqxga-10-1-bl";
    compatible = "s,wuxga-8-0";
    compatible = "s,wuxga-8-0-bl";
    compatible = "s-edp,uhdtv-15-6";
    compatible = "s-edp,uhdtv-15-6-bl";
    compatible = "sharp,lr388k7_ts";(drivers/input/touchscreen/lr388k7_ts.c)
    compatible = "simple-bus";
    compatible = "softdog-platform";
    compatible = "synopsys,dwc_eqos_virt_test";
    compatible = "tegra,ufs_variant";
    compatible = "tegra-power-domains";
    compatible = "thermal-fan-est";
    compatible = "ti,ina3221x";--大部分是iio驱动
    compatible = "ti,lp8556";
    compatible = "ti,tas2552";
    compatible = "ti,tca6408";
    compatible = "ti,tca6416";
    compatible = "ti,tca9539";
    compatible = "ti,tmp451";
    compatible = "ti,tps65132";

显示部分传到主线的大部分都是drm和fb的，没有上传的统一放在一个叫flcn的框架中，里
面的东西包罗万有。

用来支持cuda运算的驱动都没有主线化，也不在flcn中，而是放在driver/gpu目录下，提
供的主要是用户态的接口（通过一组字符设备），和内核的关系不大。

从大量的电源域和调频的设计看，这是从手机改过来的片子。当然，Tegra系列本来就是给
手机做的，这也没有什么可说的。

gk20a的驱动是2014年开始上传主线的，当时的内核版本是3.16，但一直仅包含drm的驱动
。从现在这个代码的样子，应该是一个内部的ML的产品线集成了计算核心到手机SoC中，然
后把对应的代码拼上来了。

查iommu_group，可以看到大部分外设都用iommu_group分割：::

    sdhci x2
    i2c x7
    spi x3
    serial x4
    ether_qos
    rtcpu
    ahci-sata
    aon
    smmu_test
    xhci
    xudc
    host1x x10
    host1x:ctx0
    nvcsi
    vi
    isp
    nvdisplay
    vic
    nvenc
    nvdec
    i2c
    nvjpg
    tsec
    tsecb
    se x4
    gp10b
    bpmp
    dma
    pcie-controller
    sound
    hda
    adsp_audio
    adsp


片内带一个gpu设备（/sys/device/gpu.0），支持虚拟化，但仅包含一个iommu_group（所
以才支持了vfio-mdev？），驱动是/sys/bus/platform/drivers/gk20a。


gk20a的构架是一个统一的PCI化的设备框架nvgpu，不同的硬件实现则通过一个称为
platform的数据结构进行封装（放在device的priv中），从gk20a的实现看，主要是是些初
始化，时钟一类的东西，也就是说，标准的数据流是统一的设计。我猜这样的构架撑不了
三代（当然，Tegra也不需要），这可能是没有主线化的主要原因。


用户态接口主要暴露为如下字符设备：

/dev/nvhost-gpu：共享内存和通道管理

/dev/nvhost-as-gpu：Address Space

/dev/nvhost-ctrl-gpu：设备状态控制

/dev/nvhost-dbg-gpu：设备调试信息控制

/dev/nvhost-prof-gpu: GPU profiling事件导出和控制

/dev/nvhost-tsg-gpu: 不知道是啥，看起来是做任务控制的

/dev/nvhost-sched-gpu：看起来是tsg的辅助功能，可能前者是任务组管理，后者是调度

其他媒体codec也有类似的结构：::

    /dev/nvhost-as-gpu /dev/nvhost-ctrl-isp /dev/nvhost-ctrl-vi /dev/nvhost-gpu /dev/nvhost-nvcsi /dev/nvhost-prof-gpu /dev/nvhost-tsecb /dev/nvhost-vic
    /dev/nvhost-ctrl /dev/nvhost-ctrl-nvcsi /dev/nvhost-ctxsw-gpu /dev/nvhost-isp /dev/nvhost-nvdec /dev/nvhost-sched-gpu /dev/nvhost-tsg-gpu
    /dev/nvhost-ctrl-gpu /dev/nvhost-ctrl-nvdec /dev/nvhost-dbg-gpu /dev/nvhost-msenc /dev/nvhost-nvjpg /dev/nvhost-tsec /dev/nvhost-vi


如果直接看一个cuda的调用过程，主要包括如下动作：::

        openat(AT_FDCWD, "/dev/nvhost-ctrl-gpu", O_RDWR|O_CLOEXEC) = 4
        ioctl(4, NVGPU_GPU_IOCTL_GET_CHARACTERISTICS
        ioctl(4, NVGPU_GPU_IOCTL_GET_TPC_MASKS
        ioctl(4, NVGPU_GPU_IOCTL_GET_FBP_L2_MASKS
        ioctl(4, NVGPU_GPU_IOCTL_ZCULL_GET_CTX_SIZE
        ioctl(4, NVGPU_GPU_IOCTL_ZCULL_GET_INFO
        ioctl(4, NVGPU_GPU_IOCTL_GET_ENGINE_INFO
        ioctl(4, NVGPU_GPU_IOCTL_ALLOC_AS //5是这里分配的句柄
        ioctl(5, NVGPU_AS_IOCTL_GET_VA_REGIONS
        ioctl(5, NVGPU_AS_IOCTL_GET_VA_REGIONS
        ioctl(5, NVGPU_AS_IOCTL_ALLOC_SPACE
        ioctl(5, NVGPU_AS_IOCTL_ALLOC_SPACE
        openat(AT_FDCWD, "/dev/nvmap", O_RDWR|O_SYNC|O_CLOEXEC) = 9
        ioctl(9, NVMAP_IOC_CREATE //和nvmap有关的我们先放下一篇分析里
        ioctl(9, NVMAP_IOC_ALLOC
        ioctl(5, NVGPU_AS_IOCTL_UNMAP_BUFFER
        ioctl(9, NVMAP_IOC_CREATE
        ioctl(9, NVMAP_IOC_ALLOC
        ...上两个调用的多次重复
        ioctl(4, NVGPU_GPU_IOCTL_OPEN_TSG 
        ioctl(4, NVGPU_GPU_IOCTL_OPEN_CHANNEL //这里也是创建句柄，从设备分配一个通道
        ioctl(5, NVGPU_AS_IOCTL_BIND_CHANNEL //把channel和AS关联起来
        ioctl(4, NVGPU_GPU_IOCTL_OPEN_CHANNEL 
        ioctl(5, NVGPU_AS_IOCTL_BIND_CHANNEL 
        ioctl(4, NVGPU_GPU_IOCTL_OPEN_CHANNEL
        ...

简单从这个语义上下文理解，一次通讯是这样的：先从进程和GPU建立一个关联，驱动GPU
的能力，然后分配一个或者多个独立的地址空间（AS），可能是把MMU的一部分复制给SMMU
，然后在设备和进程间建立一个通道，然后把AS和通道绑定，估计这个时候设定streamid
和substreamid给设备，这样剩下的缺页行为就可以交给设备，设备发起缺页中断的时候，
靠进程这边接管对应的mm.handle_fault()，完成后面的过程。

这个设计优先保性能，上传是下一步的事情（也不一定会上传）。

其他没有什么感兴趣了的了，就这样吧。

nvmap
======

这是这个系列最后一篇，看看TX2的GPU和host是怎么共享内存的。主要是要单独看看nvmap
这个模块的工作原理。

TX2的内核源代码是这样放的：

        | display kernel-4.4 nvgpu nvgpu-t18x nvhost nvhost-t18x nvmap
        | nvmap-t18x t18x

没有上传的代码不是Patch，而是一个个目录树的形态。但里面非常完整，连
NVIDIA-REVIEWERS这种文件都是按MAINTAINER的格式整理的，说起来应该是按随时可以
upstream的方式设计的，但整个功能通用性不强，估计upstream的难度不低。

其中gpu的驱动在nvgpu目录下（如前所述，drm驱动是已经upstream的，在kernel-4.4目录
中）。这个Kernel外的模块代码量93,913Loc)。而nvmap是个独立的目录(代码量6,334Loc
），nvgpu强依赖于nvmap。由于没有资料，nvgpu目录下的程序不太好看懂，很多概念比如
TSG是什么，估计需要分析很久，所以我们从一个相对独立逻辑空间来看看它的语义是怎么
样的。（这也是想介绍一下，应该如何具体解构一个已经存在的设计）


在分析这个逻辑前，我们先看看计算加速器设计中的一个关键问题：内存管理。

比如我做一个大型的矩阵计算，一个100x100的矩阵乘以另一个100x100的矩阵，用32位整
数，这样我就有120000个字节的空间要处理，放到4K的页中，就需要接近30页的内存需要
访问。我一开始在CPU一侧整理这些数据，这些数据当然是放在靠近CPU的内存中比较实在
，这样CPU算起来比较快。但准备好了，我希望这个乘法让加速器（比如GPU）给我算。那
么GPU离这些内存就比较远了，每个乘法加法，都要经过层层总线节点更新到内存里，这还
不如CPU自己算。所以，这是个两难的问题，根据不同的总线带宽和时延，可以考虑的方案
有：

1. 内存选择在CPU一侧（让加速器吃亏）

2. 内存选择在加速器一侧（让CPU吃亏）

3. 内存开始的时候选择在CPU一侧，但某一页的内容被加速器访问的时候，拷贝到GPU一侧
   ，完成计算后，如果CPU访问这个内存，再从加速器拷贝回CPU一侧。这个过程，既可以
   是人工的，也可以是动态的。

这里还有一个地址空间的问题，一般的Linux内核驱动，如果一片内存要分享给设备，需要
先做dma=dma_map(va)，其中va是CPU的地址，dma是设备的地址。这样一来，如果CPU要把
一个地址提交给设备，就需要转换到另一个地址空间。这种情况对于那些“弱智外设”，比
如网卡，SAS等控制器，大部分时候做DMA就是为了拷贝一段数据到外设上，这当然没有问
题，但对于那些“智能设备”如加速器，很可能我的数据中就带有指针，我的头指针可以给
你dma_map()，你不能要求我把里面的指针也全部替换了吧？

最后是，现代加速器（特别是计算加速器），基本上要求服务于用户态，所以，前面的问
题，都要在用户态解决。

我们关键看这个代码如何处理这两个问题的。

首先，nvmap的配置项如下（把子配置项和功能无关的项忽略了，只看大特性）：::

    NVMAP_HIGHMEM_ONLY：分配内存时仅用HIMEM（64位系统要这东西干嘛？）
    NVMAP_PAGE_POOLS：基于内存池管理内存分配
    NVMAP_CACHE_MAINT_BY_SET_WAYS：Cache分配算法
    NVMAP_DMABUF_STASH：重用DMABUF，降低重新分配成本
    NVMAP_FORCE_ZEROED_USER_PAGES：安全功能，分配用户内存
    NVMAP_DEFER_FD_RECYCLE：延迟FD号的使用（为后续分配重用）

没有什么涉及主功能的配置项，都是优化类的设计，这对构架分析来说是个好消息。


程序入口在nvmap_init中，实现为一个名叫tegra-carveouts的platform_device。查一下
carveout的含义，它是“切割出”的意思，也是CPU侧切出一片内存给GPU用这个商业特性的
名字。

以此为根，遍历整个代码树，功能分列如下：::

    nvmap_init.c：平台设备驱动总入口，配置参数管理
    nvmap_dev.c：platform_driver实现，注册为misc设备/dev/nvmap，核心是提供ioctl控制
    nvmap_ioctl.c：具体实现nvmap_dev.c中的ioctl功能
    nvmap_alloc.c：handle分配管理
    nvmap.c：基于handle进行内存分配
    nvmap_cache.c：在debugfs中创建接口进行cache控制，这里的cache控制指的是CPU一侧的控制，通过调用msr等动作实现的。这个接口的存在，说明CPU和GPU间不是CC的。
    nvmap_dmabuf.c：nv版本的dma_buf实现，dma_buf是内核用于用户态直接对设备做DMA的一个封装[1]
    nvmap_fault.c：实现vma的ops，进行fault处理，主要从handle预分配的空间中取
    nvmap_handle.c：handle管理，主要是做一个rb树，建立vma和处理handle的关联
    nvmap_heap.c：kmem_cache的封装（kmem_cache是内核一个管理固定大小内存的一个数据结构），用作CPU/GPU共享内存，这时称为Carveout。
    nvmap_mm.c：进程的mm管理，是cache管理的一部分
    nvmap_pp.c：page pool管理，自行管理了一个page list，NVMAP_IOC_ALLOC要求分配的也都在这里管理的
    nvmap_tag.c：handle的名字管理，提供给handle命名和基于名字访问的能力

如果我们把优化性的语义收缩一下，比如pp和heap如果不做池化，就是个简单的
alloc_page()和kmalloc，tag如果不做rb树的管理，就是个handle name。cache操作是CPU
一侧的，不封装就是基本流程中的其中一步……

这样，我们可以初步猜测这个系统的功能是这样构造的：

实现一个平台设备，注册为misc设备，用户态通过ioctl分配handle，基于handle提供vma
的分配，分配后的页面依靠自己管理的page进行填充，提供dma_buf接口，剩下的功能都是
用户态如何基于handle对设备进行硬件交互了。

为了确认这一点，接着看看ioctl的设计：::

    NVMAP_IOC_CREATE/NVMAP_IOC_FROM_FD：创建handle和dma_buf
    NVMAP_IOC_FROM_VA：同上，但同时设置vma
    NVMAP_IOC_FROM_IVC_ID：同上，但同时分配Carveout
    NVMAP_IOC_GET_FD：查找功能，FD2handle
    NVMAP_IOC_GET_IVC_ID：同上，FD2VimID
    NVMAP_IOC_GET_IVM_HEAPS：列出支持IVM的所有carveout内存块
    NVMAP_IOC_ALLOC：为handle分配page
    NVMAP_IOC_GET_IVC_ID：同上，但从Carveout分配
    NVMAP_IOC_VPR_FLOOR_SIZE：似乎是设置特定设备的最小DMA缓冲
    NVMAP_IOC_FREE：靠，这是关掉handle的fd（而不是释放Page）
    NVMAP_IOC_WRITE/READ：数据读写，WTF，就是说至少部分数据必须通过系统调用来访问（看不到用户库的代码，不好猜）
    NVMAP_IOC_CACHE：Cache操作
    NVMAP_IOC_CACHE_LIST：同上，维护类功能。
    NVMAP_IOC_GUP_TEST：不用test了，这个东西逻辑上肯定是有问题的：用户态DMA的问题
    NVMAP_IOC_SET_TAG_LABEL：这是给handle命名

基本不改变前面的逻辑，关键是这里有一个Carveout的概念，我猜在普通的实现上，这个
就是普通内存，从CPU直接分配kmemcache来共享，如果是高性能实现，就是不同的内存，
然后靠两边的读写来产生缺页来实现拷贝过程。

再看看handle的数据结构：::

        struct nvmap_handle {
                struct rb_node node;    /* entry on global handle tree */
                atomic_t ref;           /* reference count (i.e., # of duplications) */
                atomic_t pin;           /* pin count */
                u32 flags;              /* caching flags */
                size_t size;            /* padded (as-allocated) size */
                size_t orig_size;       /* original (as-requested) size */
                size_t align;
                struct nvmap_client *owner;
                struct dma_buf *dmabuf;
                union {
                        struct nvmap_pgalloc pgalloc;
                        struct nvmap_heap_block *carveout;
                };
                bool heap_pgalloc;      /* handle is page allocated (sysmem / iovmm) */
                bool alloc;             /* handle has memory allocated */
                bool from_va;           /* handle memory is from VA */
                u32 heap_type;          /* handle heap is allocated from */
                u32 userflags;          /* flags passed from userspace */
                void *vaddr;            /* mapping used inside kernel */
                struct list_head vmas;  /* list of all user vma's */
                atomic_t umap_count;    /* number of outstanding maps from user */
                atomic_t kmap_count;    /* number of outstanding map from kernel */
                atomic_t share_count;   /* number of processes sharing the handle */
                struct list_head lru;   /* list head to track the lru */
                struct mutex lock;
                struct list_head dmabuf_priv;
                u64 ivm_id;
                int peer;               /* Peer VM number */
        };

rbtree，成组的vma，多个dmabuf，cpu/gpu二选一的page或者carveout……基本上和前面的
逻辑一致。

再快速查一次nvgpu一侧的代码，除了by-pass-smmu以外，没有独立的SMMU操作，查所有的
中断处理，都是关于channel的，没有关于SMMU的中断处理，所以基本上可以认为，这个方
案是处理不了设备一侧的缺页的。


这个方案看起来挺……简陋的，重点还是聚焦在基本功能架构的一般优化上，没到向上提炼
构架的程度。

从功能上说，最不好的一点就是和IOMMU是结合不起来的，但它完全基于FD的管理比
WrapDrive基于vfio-mdev的管理带来一个好处，就是进程退出，通道就自动回收了，WD现
在做这个功能不好做。另外，WD需要考虑这里的另外两个需求：

1. 它的Host和加速器之间不是CC的，得有个办法把Cache操作插入到语义中

2. WD现在没有考虑支持大页


附录
----

[1] dma_buf的功能在内核Documentation/driver-api/dma-buf.rst中表述。如果我没
    有记错，这是当初三星在Linaro首先推的特性，它主要解决像视频播放器这种：需要
    软件动两下，转给硬件动两下，然后软件再动两下，交给下个硬件动两下这样的场景
    的。它的核心就是让用户态可以分配一片DMA内存，然后让这个内存可以在多个驱动和
    进程之间互相传递。
