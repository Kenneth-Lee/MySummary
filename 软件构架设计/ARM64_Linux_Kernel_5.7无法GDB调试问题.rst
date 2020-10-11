.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 1.0

ARM64 Linux Kernel 5.7无法GDB调试问题
*************************************

Linux主线Kernel刚发布了5.7，同步上去后，我的gdb调试功能异常了，加载内核一堆错误
：::

        FD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000
        BFD: warning: vmlinux: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0000000

强行调试会出各种错误。

从这里（https://github.com/ClangBuiltLinux/linux/issues/844）可以知道，这是新的
ARM8.3a+ PAC和BTI特性（指针和跳转鉴权）引起的，这两个特性需要binutils支持这种新
的段类型，但gdb还没有支持。

查了一下内核的编译参数，在arch/arm64/Makefile中可以看到这个定义：::

        ifeq ($(CONFIG_ARM64_PTR_AUTH),y)
        branch-prot-flags-$(CONFIG_CC_HAS_SIGN_RETURN_ADDRESS) := -msign-return-address=all
        branch-prot-flags-$(CONFIG_CC_HAS_BRANCH_PROT_PAC_RET) := -mbranch-protection=pac-ret+leaf
        # -march=armv8.3-a enables the non-nops instructions for PAC, to avoid the
        # compiler to generate them and consequently to break the single image contract
        # we pass it only to the assembler. This option is utilized only in case of non
        # integrated assemblers.
        branch-prot-flags-$(CONFIG_AS_HAS_PAC) += -Wa,-march=armv8.3-a
        endif

代码是3月份Kristina Martsenko提交的补丁（但合入应该是5.7才正式生效的）：::

        74afda4016a74 (Kristina Martsenko 2020-03-13 14:35:03 +0530  72) ifeq ($(CONFIG_ARM64_PTR_AUTH),y)
        74afda4016a74 (Kristina Martsenko 2020-03-13 14:35:03 +0530  73) branch-prot-flags-$(CONFIG_CC_HAS_SIGN_RETURN_ADDRESS) := -msign-r eturn-address=all

暂时不知道有稳定的支持的gdb可以使用，所以如果各位需要继续正常调试当前ARM的内核
，请关掉这个配置项：CONFIG_ARM64_PTR_AUTH。
