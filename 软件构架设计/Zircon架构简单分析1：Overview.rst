.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

Zircon架构简单分析1：Overview
******************************

有朋友让我评价一下Zircon的可用性，所以我花了几天时间大概看了一下这个系统的构架
相关信息。对它的判断我私下和他说，但看到的基础事实我记录在这里，供其他也有兴趣
的同行一起探讨。

先运行一下看看系统成熟度。按文档的建议（
https://fuchsia.googlesource.com/zircon/+/HEAD/docs/getting_started.md），git
clone，安装依赖，build arm64版本（现在只支持x64和arm64两个平台），用qemu运行，
系统可以轻松模拟起来：

        .. figure:: _static/zircon1.jpg

这不是个标准的Unix目录结构，但形式类似。大部分目录都还是空的，主要的命令在/boot
下，这是一个内置的只读文件系统，在编译内核的时候用lz4压缩直接放到加载镜像中，启
动完成后mount成文件系统，提供最基础的用户支持。我把所有命令都运行了一遍。看起来
，很多命令还不稳定，一言不合就coredump：

        .. figure:: _static/zircon2.jpg

从代码上看，内核主要是C++写的，系统调用（参考
build-arm64/gen/global/include/zircon/zx-syscall-numbers.h）主要包括这些类型：

clock，sleep，handle，object，channel，socket，thread，process，task，event，
futex，port，time，vmo，vmar，prng，fifo，trace，interrupt，pci，pager。

大部分从名字上可以猜出提供什么功能。我解释其中几个关键的：

object是对象，类似微软DCOM中的IUNKNOWN，本质是一个C++的类，内核中的各种管理对象
，都是object，内部通过koid索引，用户态通过handle来访问它，handle索引没有了，
object就自动释放了。这提供最基础的名称服务。当你创建对象（比如创建线程）你得到
一个handle，把handle通过channel等手段传递出去，就产生新的channel索引，这样通讯
就建立起来了。

channel和socket是IPC，一个提供报文式通讯，一个提供流式通讯。

Job、Task、Process和Thread是调度概念，Job是进程组（控制权限和总体资源），
Process是进程（控制独立资源），Thread是线程（控制调度）。Task是三者的抽象，比如
，你可以用zx_task_kill(handle)杀掉任何一个对象。这个进程的对外接口做得挺有意思
的，我们下一篇再来分析。

vmo和vmar提供内存服务。从vma的定义可以看出这里的思路：vmo代表一组物理内存，可以
被vmap等系统调用映射到进程空间中被一个或者多个进程使用。而vmar提供进程空间的管
理服务。由此可以初步猜测，系统会认为大数据流是通过类似Android的
Binder+SurfaceFlinger那样的IPC加共享内存来完成了。

系统调用中包含pci和interrupt的接口，基本上可以猜测这是通过用户态的进程map bar空
间，然后等待中断的形态来完成的。

（提示一句：由于代码比较新，现在找代码特别容易，知道系统调用的名字，找sys_XXXX
，基本上就找到入口了。我都是基于入口的参数猜具体的设计目标的）

系统调用使用了vdso技术，直接从内核中提供出来(libzircon.so)，不需要libc来提供了
。

从系统调用就可以看出，传统的POSIX程序和Linux内核驱动都不要指望可以无缝迁移过来
（这是和QNX很大的不同，QNX上几乎所有的Unix程序都可以直接迁移的）

它的用户态程序大概是这个样子的（看system/uapp目录可以找到很多）：::

        zx_status_t ZirconDevice::CallDevice(const zx_channel_call_args_t& args, uint64_t timeout_msec) {
            uint32_t resp_size;                                                         
            uint32_t resp_handles;                                                      
            zx_time_t deadline;                                                         
                                                                                        
            if (timeout_msec == ZX_TIME_INFINITE) {                                     
                deadline = ZX_TIME_INFINITE;                                            
            } else if (timeout_msec >= std::numeric_limits<zx_time_t>::max() / ZX_MSEC(1)) {
                return ZX_ERR_INVALID_ARGS;                                             
            } else {                                                                    
                deadline = zx_deadline_after(ZX_MSEC(timeout_msec));                    
            }                                                                           
                                                                                        
            return zx_channel_call(dev_channel_, 0, deadline, &args, &resp_size, &resp_handles);
        }

设备无关的就是标准的C/C++接口，设备相关的主要是通过文件系统提供名称服务找到对方
的进程，然后通过IPC服务通讯获得数据。

到此为止，可以看到Zircon的心的很大的，是打算彻底抛弃Unix世界重头来的，这也大大
增加了它失败的可能性。
