.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

Linux设备异常复位逻辑分析
*************************

本文分析Linux设备复位的逻辑空间，包括对实体设备（PF）和虚拟设备（VF）的相关逻辑
。整个分析基于Linux Kernel 5.1。

先快速扫个盲，建立一个基本的讨论空间：

Linux的设备模型主要包括三个实体：driver，bus和device。基础的bus一般是预定义的（
比如platform_bus和pci_bus），其他的bus有预定义的也有被新的device动态定义的。
driver是内核模块，注册到bus上，等着驱动device。device由bus枚举来发现，也注册给
bus。这样，挂在bus上的驱动和device就可以互相匹配（一般通过名字匹配一类的方法）
，这种匹配称为binding。最终就是一般驱动工程师能感受到的：驱动的probe函数被调用
，传进来一个device，然后你爱怎么弄这个device都可以了。比如注册为一个netdev，注
册为另一条总线，注册为一个sas控制器，等等。

binding过程和device和driver谁先注册无关，谁注册都会发生一个match过程，match上了
就会probe，所以，无论你在内核中预先编译了driver，还是在总线找到device之后，
modprobe插入一个driver，都不影响这个match的过程。

binding的driver和device可以unbinding，这个通过sysfs接口就可以做到了，VFIO就是通
过这种方法，把设备的普通驱动rebinding为VFIO驱动，这样原来的比如注册给netdev的驱
动，就变成注册给vfio的驱动，生成一个字符设备，由qemu这样的用户态程序打开，供虚
拟机使用。

如果device之间有依赖关系，则通过一个称为link的概念进行关联。比如A设备依赖B设备
，A probe的时候可以直接返回EPROBE_DEFFER，等B设备probe的时候再device_link_add，
加上这个link，再次触发A的probe。

driver在probe阶段为device分配的资源通过remove释放，这个调用是没有返回值的。换句
话说，系统可以无条件要求你释放资源，你一定要响应。所以，我们应该可以比较安全地
建立一个初步的认识：如果一个硬件被强行从socket上拔走了，总线可以强行删除这个设
备，而设备和用户态建立的关联（比如打开了一个设备），必须可以在remove后保持状态
自恰。

我们再解释一下“remove后保持状态自恰”的含义：unregister_device()包含两个动作，一
个是device_del()，负责删除device相关的所有资源和资源关联——除了device这个数据结
构本身。另一个是device_put()，这个负责把device这个数据结构本身的引用计数减1。所
以，如果你靠open建立了一个fd和这个device关联，在里面必须保证你get了这个device，
并在device_lock()的保护范围内，确认device的状态是否还有效，如果无效，给用户态错
误的响应即可。

所以，如果不考虑比如PCI这个的平台框架，作为一个纯工作在基础驱动框架上的驱动。你
可以做unregiester_device()来随意清除设备，然后通过register_device把它重新加回来
，但这种骚操作显然比较适合在parent device上做（比如某条总线，或者某个VF的PF），
而不用于某个设备自己。

所以，如果我们做复位功能，在PF上，我们没有办法杀掉自己，这个device不能被删除，
我们作为一种设备状态来出来。但PF上建立的VF则有两种方法，一种是干脆全部干掉重新
建。另一种方法是，发一个通知给对应的VF，让VF也去做一样的复位。

最后看pci的实现思路。PCI子系统把reset和hotplug两个行为分开处理的，如果你做FLR，
那么，它是认为所有的VF和PF的配置是不变的，所以Reset行为就是硬件的一个状态变更，
VF也是收到一个通知而已。

如果是hotplug，这是一个独立的，基于slot的框架，pci使用
pci_hp_remove_devices(bus)作为helper来帮你移除所有的子设备（包括VF）。

这个helper实现的主体是调device_release_driver()，把和驱动的关联关掉，然后清除
PCI一层建立的资源。这并没有增加什么特殊的东西，基本上我们认为硬件被拔掉了，就强
行unregister_device();

而对于SRIOV设备，当初在pci_iov_add_virtfn()增加虚拟设备的时候，已经给pf->bus加
了一条子bus了，所以，如果你remove这个设备本身，它的VF就会作为子设备全部清除。

这样考虑的话，如果PF坏了，你要不通知所有VF reset，然后reset PF，并保持所有VF的
配置。要不硬件做不到安全的话，你可以直接用pci_hp_remove_devices()删掉所有的VF，
然后reset硬件，这样正在使用VF的设备就会受影响，但你就会更安全一些。
