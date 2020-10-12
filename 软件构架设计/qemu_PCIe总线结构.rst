.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 1.0

qemu PCIe总线结构
******************

本文是写这个章节的一些边角料：

	source/认识鲲鹏920：一个服务器SoC/设备和设备总线.rst · Kenneth-Lee-2012/从鲲鹏920了解现代服务器实现和应用_公开 - 码云 Gitee.com

由于没法放到那个文档的主逻辑中，我放在这里。（顺便感慨说一句，你看我在那里写一
句话，可能我在背后要确认两三天。正经写点东西还是很难的）

本文用3.1.50源代码版本作为参考。

qemu可以虚拟机模拟一个虚拟的PCIe的总线系统（关于PCIe的基本原理可以看前面的这个
链接）。具体模拟成的样子在具体模拟的那个机器上上定义，比如我在PC上用这个参数启
动虚拟机：::

	~/work/qemu-run-arm64/qemu/aarch64-softmmu/qemu-system-aarch64 \       
		-s -cpu cortex-a57 -machine virt \
		-nographic -smp 2 -m 1024m -kernel arch/arm64/boot/Image \
		-append "console=ttyAMA0"

mainchine是ARM平台virt，它的机器定义在就在hw/arm/virt.c中。所以它会有一个默认的
PCI结构。默认是这样的：

那么如果你要在其中插入一个PCIe设备，方法就是用这个参数：::

	-device <dev>[,bus=pcie.0]...

不同的dev类型会有不同参数，这个可以看对应设备的详细说明，部分qemu的文档中有，但
文档不一定同步，你可以通过这样的命令让qemu直接打印出来：::

        -device help

不同的设备有不同的属性，这个在源代码中是通过object_property_add()或者在设备
class里加的，你可以从qemu源代码的hw目录中找，每种设备类型都有类似的定义的，比如
vfio-pic的定义是这样的：::

        static Property vfio_pci_dev_properties[] = {
            DEFINE_PROP_PCI_HOST_DEVADDR("host", VFIOPCIDevice, host),
            DEFINE_PROP_STRING("sysfsdev", VFIOPCIDevice, vbasedev.sysfsdev),
            DEFINE_PROP_ON_OFF_AUTO("display", VFIOPCIDevice,
                                    display, ON_OFF_AUTO_OFF),
            DEFINE_PROP_UINT32("xres", VFIOPCIDevice, display_xres, 0),
            DEFINE_PROP_UINT32("yres", VFIOPCIDevice, display_yres, 0),
            DEFINE_PROP_UINT32("x-intx-mmap-timeout-ms", VFIOPCIDevice,
                               intx.mmap_timeout, 1100),
            DEFINE_PROP_BIT("x-vga", VFIOPCIDevice, features,
                            VFIO_FEATURE_ENABLE_VGA_BIT, false),
            DEFINE_PROP_BIT("x-req", VFIOPCIDevice, features,
                            VFIO_FEATURE_ENABLE_REQ_BIT, true),
            DEFINE_PROP_BIT("x-igd-opregion", VFIOPCIDevice, features,
                            VFIO_FEATURE_ENABLE_IGD_OPREGION_BIT, false),
            DEFINE_PROP_BOOL("x-no-mmap", VFIOPCIDevice, vbasedev.no_mmap, false),
            DEFINE_PROP_BOOL("x-balloon-allowed", VFIOPCIDevice,
                             vbasedev.balloon_allowed, false),
            DEFINE_PROP_BOOL("x-no-kvm-intx", VFIOPCIDevice, no_kvm_intx, false),
            DEFINE_PROP_BOOL("x-no-kvm-msi", VFIOPCIDevice, no_kvm_msi, false),
            DEFINE_PROP_BOOL("x-no-kvm-msix", VFIOPCIDevice, no_kvm_msix, false),
            DEFINE_PROP_BOOL("x-no-geforce-quirks", VFIOPCIDevice,
                             no_geforce_quirks, false),
            DEFINE_PROP_BOOL("x-no-kvm-ioeventfd", VFIOPCIDevice, no_kvm_ioeventfd,
                             false),
            DEFINE_PROP_BOOL("x-no-vfio-ioeventfd", VFIOPCIDevice, no_vfio_ioeventfd,
                             false),
            DEFINE_PROP_UINT32("x-pci-vendor-id", VFIOPCIDevice, vendor_id, PCI_ANY_ID),
            DEFINE_PROP_UINT32("x-pci-device-id", VFIOPCIDevice, device_id, PCI_ANY_ID),
            DEFINE_PROP_UINT32("x-pci-sub-vendor-id", VFIOPCIDevice,
                               sub_vendor_id, PCI_ANY_ID),
            DEFINE_PROP_UINT32("x-pci-sub-device-id", VFIOPCIDevice,
                               sub_device_id, PCI_ANY_ID),
            DEFINE_PROP_UINT32("x-igd-gms", VFIOPCIDevice, igd_gms, 0),
            DEFINE_PROP_UNSIGNED_NODEFAULT("x-nv-gpudirect-clique", VFIOPCIDevice,
                                           nv_gpudirect_clique,
                                           qdev_prop_nv_gpudirect_clique, uint8_t),
            DEFINE_PROP_OFF_AUTO_PCIBAR("x-msix-relocation", VFIOPCIDevice, msix_relo,
                                        OFF_AUTOPCIBAR_OFF),
            /*
             * TODO - support passed fds... is this necessary?
             * DEFINE_PROP_STRING("vfiofd", VFIOPCIDevice, vfiofd_name),
             * DEFINE_PROP_STRING("vfiogroupfd, VFIOPCIDevice, vfiogroupfd_name),
             */
            DEFINE_PROP_END_OF_LIST(),
        };

但这个还是很烦，因为部分参数是从父类继承过来的。更好的办法和前面用help参数一样
，可以这样让它打印：::

        -device vfio-pic,?

缺点是通常没有解释，如果你需要知道详细的意思，还是需要看代码。

下面给出一些比较常用的参数：

* id，设备标识，用于指定的一个字符串，用于其他配置引用这个设备

* host，host本地的设备标识，比如vfio-pci设备的bdf

* bus，总线代号，比如这里的pcie.0，如果你创建更多的总线，就可以是那个总线的id

* addr，总线上的设备地址，也就是bdf中的d或者df，不能和其他地址冲突。比如pcie.0
  上默认已经有0和1了，你指定这个地址就会失败

* slot和chassis，这个概念我不知道为了什么引入的，这两个都是硬件的概念，是指PCI
  的插槽和扩展器。反正你保证两者的组合不会和别人重复就可以了。

下面插入两张virtio的网卡到pcie.0中：::

        ~/work/qemu-run-arm64/qemu/aarch64-softmmu/qemu-system-aarch64 \
                -s -cpu cortex-a57 -machine virt \
                -nographic -smp 2 -m 1024m -kernel arch/arm64/boot/Image \
                -netdev type=user,id=net0,hostfwd=tcp::5555-:22 \
                -netdev type=user,id=net1 \
                -device virtio-net-pci,bus=pcie.0,netdev=net0,addr=6.0 \
                -device virtio-net-pci,bus=pcie.0,netdev=net1,addr=7.0 \
                -append "console=ttyAMA0"

-netdev创建了两个本地设备，-device用这两个本地设备制造了两张网卡，我们给定了
addr，整个拓扑就是这样的：

        .. figure:: _static/pcie_topo1.jpg

我们再增加两条根桥和一个virtio网卡：::

        ~/work/qemu-run-arm64/qemu/aarch64-softmmu/qemu-system-aarch64 \
                -s -cpu cortex-a57 -machine virt \
                -nographic -smp 2 -m 1024m -kernel arch/arm64/boot/Image \
                -netdev type=user,id=net0,hostfwd=tcp::5555-:22 \
                -netdev type=user,id=net1 \
                -netdev type=user,id=net2 \
                -device pcie-root-port,id=pcie.1,bus=pcie.0,port=1,chassis=1,slot=0 \
                -device pcie-root-port,id=pcie.2,bus=pcie.0,port=2,chassis=2,slot=0 \
                -device virtio-net-pci,bus=pcie.0,netdev=net0,addr=5.0 \
                -device virtio-net-pci,bus=pcie.1,netdev=net1,addr=0.0 \
                -device virtio-net-pci,bus=pcie.2,netdev=net2,addr=0.0 \
                -append "console=ttyAMA0"

整个系统变成这样：

        .. figure:: _static/pcie_topo2.jpg

这里这个chassis不能省略，qemu里现在没有自动分配这个id，你不给它就直接互相冲突，
保证你至少给定chassis或者slot就可以规避（保证这个组合对每个设备都是唯一的）。我
感觉这个设计是多余的，也许我体会不够深。

这里的根桥id组织不优美，因为理论上根桥应该是挂在RC下面而不是第一条总线下面，但
qemu现在就做成这样了，也只好忍着了。

用这种方法快速了解Linux的PCIe发现流程是个挺好的体验。
