.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

X86上的ARM Linux调试环境
************************

以前写过怎么在PC上调试Linux内核：:doc:`怎样快速调试Linux内核` 。那个是在x86上调
试x86平台的，用的是x86本地的软件。这里再介绍一下怎么在x86（模拟）调试ARM平台。
我个人的日常工作环境都是这个平台，我个人也更推荐这个平台。因为我个人在这个平台
上遇到的问题更少一些。

本文中涉及的部分配置或者脚本我会合并到前面这个x86@x86共享的工程中：
nekin2017/lk-tester-maker，放在在ARM64的目录下。

我用的Ubuntu，所以方案只在Ubuntu 18.04.1 LTS上验证过。Ubuntu对aarch64的支持已经
很好了，你可以直接装aarch64的工具链：::

        apt-get install gcc-8-aarch64-linux-gnu

        qemu支持arm64的版本也可以直接装

        apt-get install qemu-system-arm

唯一比较恶心的是现在aarch64的gdb主线还有问题（有个头文件冲突的问题没有解决），
所以没有gdb版本，如果你在乎，去这里下Linaro的gcc 二进制版本（里面带gdb）：

http://releases.linaro.org/components/toolchain/binaries/gcc-8/

这样基础就有了，编译内核你肯定会了（自己根据需要调整参数）：::

        ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- make -j4 O=$BUILD_DIR

配置用默认配置就可以了，我建议开9pfs，在我前面共享的工程中，我放了一个4.19的
config.kernel.aarch64_debug，你懒得调，就用这个。

然后是文件系统部分，我是用buildroot来编译的，从这里下工程：::

        git clone git://git.buildroot.net/buildroot

肯定可以用的配置我放在共享工程的arm64目录下了：config.buildroot.aarch64_debug。

编译完，把对应的根文件系统配置到内核的CONFIG_INITRAMFS_SOURCE配置项中。

然后这样运行这个系统：::

        qemu-system-aarch64 \                
                -s -cpu cortex-a57 -machine virt \                                      
                -nographic -smp 1 -m 1024m -kernel arch/arm64/boot/Image \              
                -device virtio-net-pci,netdev=net0 \                                    
                -netdev type=user,id=net0,hostfwd=tcp::5555-:22 \                       
                -fsdev local,id=p9fs,path=p9root,security_model=mapped \                
                -device virtio-9p-pci,fsdev=p9fs,mount_tag=p9 \                         
                -append "console=ttyAMA0 mymodule.dyndbg=+p debug"

这是一个能跑的配置，你自己根据需要调整吧。

它共享了一个虚拟目录（这里是p9root）到虚拟机里面，你可以在虚拟机控制台上直接运
行如下命令mount：::

        mount -t 9p p9 /mnt

这样很容易在本地编译用户态的代码，然后丢虚拟机里面去运行。

要单步调试内核，可以用启动aarch64的gdb，然后::

        gdb> file <your_kernel_vmlinux_file>
        gdb> target remote :1234

然后设断点就行了。我一般不用单步执行，一方面这东西没什么用，调试程序不应该靠单
步的。另一方面是Linux Kernel必须-O2编译，代码优化过后，基本上执行过程和代码序列
对不上。但这个东西启动运行一次只需要十几秒，比启动一台Server动辄几分钟不可同日
而语。所以，一般的功能调试，用这个是最快的和最方便的。
