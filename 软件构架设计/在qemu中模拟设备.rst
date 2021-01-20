.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.1

在qemu中模拟设备
*****************

介绍
====

本文作为这个文档的补充：:doc:`X86上的ARM Linux调试环境` 。

在那个文档中，我们已经可以在x86机器上模拟一个ARM Linux的运行环境。本文我们简单
介绍一下怎么在qemu中模拟一个设备给Guest Linux。这对于很多SoC软件使能工程师来说
很重要。因为对他们来说，单板都是受限的，而且软件开发要和SoC同步进行，软件开发初
期不一定有SoC。再说，SoC模拟阶段Bug一堆，硬件Simulator太慢，使用Emulator就成为
最好的选择了。

相比硬件Simulator（包括FPGA），Eumlator最大的好处是快（很多时候，比真实单板都快
得多，因为可以精简配置，一台10个SAS接口的服务器，我可以只留下一个端口来做调试）
，自由度高（想模拟什么情形就模拟什么情形），缺点是非cylcle精确。但对软件工程师
来说这无所谓，因为本来我们就是要调软件功能，不是调硬件实现。

qemu的设备模拟原理很简单，可以很快上手，是值得SoC软件工程师作为一个必备技能来学
习的。

首先我们理解一下Qemu的工作原理。很多系统工程师对Qemu有距离感，其实只是不熟悉，
说起来，我觉得Qemu比Linux Kernel还是容易很多的。作为最基础的原理，我原来写过一
个演示性的例子：

        https://github.com/nekin2017/pipeline_simulator.git

那个只写了几个小时，当然并不实用，但用来说明模拟器是什么已经足够了。这一定程度
上说明，模拟器在原理上并不复杂。

Qemu要解决具体问题，相对当然复杂得多，但得益于良好的封装性，我们要在Qemu里面加
模拟设备，需要知道的原理并不多。它的代码模型大概就是这样的（我用Python当做伪码
来表述这个逻辑）：

.. code-block:: python

   def run_a_guest():
     vm = create_vm()
     vm.create_cpu_object()
     vm.create_device_object()
     for cpu in cpus: create_thread(cpu_thread, cpu)

   def cpu_thread(cpu):
     while true:
       try:
         cpu.run(vm)
       except EIO eio:
         find_device(eio.io_address).handle_io();

对很多人来说，那个cpu.run()是最难理解的，在Qemu中有各种各样的实现方式，比如基于
qemu.ko的，基于TCG（翻译执行），或者基于KVM的。但对于做设备的人来说，这些统统不
用管，你就认为它是个系统调用好了。如果是KVM，这个地方其实就是个ioctl(KVM_RUN）
，如果是TCG，那里就是翻译块的动态执行。反正你认为是个黑盒，Hypervisor帮你能执行
到哪里就执行到哪里，如果执行不了了（比如虚拟机里面访问IO空间了），就从系统调用
中返回，注册了这片IO空间的设备出来响应要求，进行一些处理。处理完了，就回去接着
ioctl(KVM_RUN)就好了。

而这个设备处理的整个过程，其实就是qemu这个进程在运行，这和一个普通的操作系统的
进程编程环境没有任何不同，完全就是响应IO空间的读写操作而已。这样一想，是不是其
实很简单？


增加设备驱动
============

首先，我们要能够重新编译qemu，这随便上网一搜就是一大把，我在Ubuntu@x86_64上模拟
ARM aarch64，编译命令如下（我验证的时候最新的stable版本是2.9）：::

        git clone git://git.qemu.org/qemu.git
        apt-get build-deps qemu #安装开发库
        cd qemu
        ./configure #如果喜欢，可以自己挑选具体要什么特性
        make

先确认你可以编译过，这样我们加东西的基础就有了。（现在的版本使用了submodule，你
还需要更新submodule，submodule的原理可以看这里：《:doc:`git-submodule的理解` 》
）

然后我们要加一个设备驱动，qemu/hw/目录里面全部都是，每个就是一个设备驱动，你找
一种驱动来拷贝就好。

如果你要模拟PCIE设备，推荐模仿edu.c，这个模块有文档(qemu/docs/specs)，解释比较
充分，但你要图简单（模拟PCIE设备你至少要模拟配置空间吧），你可以像我一样，直接
模拟platform_device，我选的拷贝对象是pl011，你自己可以先运行一个虚拟机，然后到
/sys/devices/platform里面挑，看哪个顺眼学哪个就好了。

要把这个文件加入到编译系统中，只需要在它所在目录的Makefile.objs加一个xxx.o就可
以了，方式和Linux Kernel基本上是一样的。

一个设备驱动类似一个Linux内核的LKM，通过type_init(type_init_function)定义，其语
义空间如下：

Type/Class
        一种设备类型（相当于Java中的Class）

Instance
        一个设备实例（相当于Java中的Object)

通常你在Instance的初始化函数中申请一些MemoryRegion，注册你的IO空间被访问的回调
函数，问题就基本解决了）

        | 注：更多信息，参考后面的QOM一节。

创建设备
=========

增加设备驱动仅仅是表明这个设备可以被创建了，还没有创建。设备由“机器”来定义，就
是你用-machine xxxx指定的那个东西。这也是一个驱动，比如我们在ARM平台上常用virt
这种平台，用的机器定义就是qemu/hw/arm/virt.c。RISCV也有类似的，比如
qemu/hw/riscv/virt.c。

这个也基本上不用学，你仿照其他设备那样创建一个设备就可以了。一般包括两个动作：

1. 在某个总线下面创建设备，比如在系统总线上创建设备，我们可以：
   sysbus_create_simple(驱动的名字，IO地址，IRQ编号)。

2. 创建dts或者acpi入口，这个都有标准函数，比如qemu_fdt_add_subnode()。

代码示意如下：

        .. code-block:: c

        dev = qdev_new(设备类型);
        ... // 设置dev其他属性
        sysbus_realize_and_unref(SYS_BUS_DEVICE(dev), &error_fatal);
        sysbus_connect_irq(dev, i, irq)... //注册每个irq
        memory_region_add_subregion(get_system_memory(), base, sysbus_mmio_get_region(s, 0)); //注册mmio空间

通用平台设备和PCIE桥也是一种特殊的设备，方法是一样的。

做完这个动作，用这个虚拟机运行你的Linux，对应的设备就能被发现到。

这是静态的，动态的可以通过在命令行用-device来分配，这个读者自己去摸吧，基本原理
基本是一样的。


trace
======

一般调试这种驱动我们都不直接打印（因为虚拟机还需要占用控制台呢。不过你不在于打
印混合在一起，直接打印是没有问题的），所以我们都用trace，trace可以通过qemu命令
行-trace或者直接在qemu的控制台中使能，怎么用可以自己看手册，我们这里主要讲编程
接口。

trace的编程接口和Linux内核ftrace event很接近，但比Linux内核的接口容易很多。你不
需要定义Linux ftrace那一大堆头文件，qemu都写成脚本了，你只需要在目录下面放一个
trace-events文件，里面描述你的函数原形，然后在你的主程序中直接调就可以了。

这里唯一要注意的是，qemu的Makefile做得比较蠢，如果你创建了新的目录，需要在根目
录的Makefile.objs中更改trace-events-subdirs变量，把你的目录包含进去，子目录也必
须手工加。

但仅仅trace需要这样，你不用trace就不需要，简单修改对应目录的Makefile.objs就可以
了。


MemoryRegion
=============

好了，前面都是比较简单的东西，最后我们重点理解一下qemu的MemoryRegion的概念。我
们刚才说了，硬件模拟无外乎两个东西，一个是中断，一个是IO访问。

中断很简单，知道中断号，用qemu_set_irq()或者qemu_irq_pluse()往里种就可以了。内
存区会麻烦很多，所以我们需要多介绍一些概念：

MemoryRegion
        这表示一组面向Guest的，具有相同属性的内存区。后面简称MR。系统有全局的总
        MR，你直接用get_system_memory()就可以拿到了。所以你实际上任何时候都可以
        访问全局任何内存。

MemoryRegionCache
        这表示一片为了满足Guest需要的一片临时的“真内存”。换句话说，MemoryRegion
        是描述一片内存区，MemoryRegionCache是真的要用的内存，Hypervisor根据需要
        动态申请，后面简称MRC。如果你不是要深入定制，一般你不管这个东西没有任何
        问题。

AddressSpace
        这表示一个地址空间，一个地址空间可以包含多个不同属性的MR。后面简称AS。
        AS是和MR直接对应的，所以你可以直接用address_space_memory拿到对应
        get_system_memory()的AS。

FlatView
        这表示看到的地址空间。这就比较绕了。这么说：AS是立体的，里面的MR是相互
        独立的，他们可以交叠，转义，动态开关等。但当你去访问的时候，某个时刻，
        某个物理地址总是对应着某个MR中的地址，FlatView用来表示层叠的结果。后面
        这个简称FV。FV大部分时候写设备模拟的时候都不用管，它是用于深入处理Host
        这边访问内存的时候用的，比如通过address_space_to_flatview(as)把as换成fv
        ，然后用flatview_read/write()进行本地内存访问。

MR可以有很多类型，其中前面提到的都是IO类型的，这种算是最简单的。它的实际地址在
创建设备的时候给定，而在设备驱动只要在instance的初始化函数中，从传入的系统总线
对象中就可以拿到了。一般方法是：::

        memory_region_init_io(&iomr, owner, ops, priv, name, size);

        sysbus_init_mmio(sys_bus_device, &iomr);

这样你就有了一个mr对象，Guest的访问由ops的读写函数来响应。

但除了GPIO这种简单设备，几乎没有什么设备只有IO空间的，我们还需要做DMA。如果不使
用IOMMU，这也很简单，请求总是通过IO空间进来的，进来以后调用
dma_memory_rw(&address_space_memory, pa, buf, size, directory)就可以了。那个
address_space_memory是个全局变量，就是整个虚拟机的AS。反正整个物理空间你都有了
，给你物理地址你想访问啥不行啊。

如果你需要IOMMU，基本的方法是再创建一个设备接口，让CPU通过这个接口给你设置页表
，之后你要访问目标地址的时候先做一个转换就好了。

Qemu提供了一种特殊的Region：::

        memory_region_init_iommu(&iommumr, instance_size, mrtypename, owner, name, size);

iommumr是我们要创建的MR内存，instance_size是它的大小，size是这个这个翻译器的输
入地址的范围（iova的范围），其他域可以直接理解。唯一比较麻烦的是这个mrtypename
。这个东西需要再创建一个父类是TYPE_IOMMU_MEMORY_REGION的新设备类型，例如这样：::

        static const TypeInfo rc4030_iommu_memory_region_info = {
            .parent = TYPE_IOMMU_MEMORY_REGION,
            .name = TYPE_RC4030_IOMMU_MEMORY_REGION,
            .class_init = rc4030_iommu_memory_region_class_init,
        };

然后在class_init中给这个域创建一组用于翻译的函数就可以了。其中最核心的显然是其
中的translate函数了。我们简单看看它的API定义：::

        IOMMUTLBEntry translate(IOMMUMemoryRegion *iommu, hwaddr addr, IOMMUAccessFlags flag, int iommu_idx);

iommu是操作上下文，addr是物理地址，flag是访问属性，iommu_idx用来给你区分实例。
其实我觉得如果用来做软件的设备模拟，这玩意儿用不上，还不如用我前面说的，需要访
问的时候自己翻译好了。

剩下的问题可能是花几个小时试一试了。



QOM
====

这一章其实不太需要，但前面讨论MR的时候，很多人肯定会注意到里面的面向对象要素，
我们这里简单总结一下Qemu Object Model。这样有助于读者阅读和修改相关代码。

Qemu是用C写的，不支持面向对象特性，但偏偏设备极为适合使用面向对象管理。所以Qemu
写了一套用C模拟的面向对象接口。

在我们具体介绍细节前，我们先建立一些基本概念：面向对象中，说A是B的时候，表达的
关系是A继承或者实现B，但在QOM中，这个关系被对外暴露出来了，所以当我们说A是B的时
候，表示的是A数据结构中包含了B的数据结构。另外，当我们定义一个类的时候，我们用
一个“类描述符”来表达它。这个描述符不是那个类本身。另外，A和B表示一种身份，这种
身份还有自己数据，这个数据不是身份描述的一部分，这会类似Linux内核中的各种数据接
口和priv成员一样，表示这个类型的私有数据，这个数据称为State。在后面的讨论中，请
注意一个数据结构，什么时候是它的描述符，什么时候是它的类，什么时候是它的类实例
，以及类和类实例的State。

有这个理解后，QOM的概念空间可以这样描述：

* Class/Type：类。基类数据结构叫ObjectClass，但它的“描述符”叫TypeInfo。Class本
  身也可以有数据。体现为TypeInfo的class_size。

* Object/Instance：实例。基类数据结构叫Object。

* Interface：一种特殊的类。不用于继承，用于实现

* State：一个纯概念的东西，表示类或者类实例的数据。呈现为TypeInfo的class_size和
  instance_size，子类的State必须包含父类的数据本身

* Device：类型是DeviceClass的“device”的一种Object。

* DeviceState：Device类的Instance的State数据结构

* props：DeviceClass的一组属性，每个成员叫Property，包含一对set/get函数，从而可
  以呈现为命令行的-device driver-name的参数（qemu -device driver-name,help可以
  直接查询device的属性）

* Bus：类型是BusClass的"bus"的一种ObjectBusState：Bus类的Instance的State数据结
  构

很容易乱，是吧，不要紧，我们后面对具体的实例会理解的。

大体上可以这样理解：

这是一个单继承系统，每个对象只能有一个父类（但可以有多个interface）。父类和
interface定义的空间在创建类的时候都会在本类中占据一个空间。类和对象进行类型转化
的时候（代码：object_class_dynamic_cast_assert()和object_dynamic_cast_assert()
），换成对应的类型的ObjectClass和Object（后者其实就是那个State本身了）。数据的
原理一样。

我们先看一个简单的例子建立感性认识：::

        typedef DeviceClass MyDeviceClass;
        typedef struct MyDeviceState { //这个定义类的实例的数据
          DeviceState parent; //包含父类的State数据，而且必须保证在第一个位置上
          type my_own_data;...
        } MyDevice;
        static const TypeInfo my_device_info = {
          .name = "mydevice",
          .parent = TYPE_DEVICE, // "device"
          .instance_size = SIZEOF(MyDevice);  //State数据的大小
          .interfaces = (InterfaceInfo[]) {  //一组接口
              { TYPE_HOTPLUG_HANDLER },
              { TYPE_ACPI_DEVICE_IF },
              { INTERFACE_CONVENTIONAL_PCI_DEVICE },
              { }
            }
        };

        //后面玩的是个__attribute__((constructor))游戏，自动全局注册这个类型而已
        static void my_device_register_types(void) {
          type_register_static(&my_device_info);
        }
        type_init(my_device_register_types)
        //这一段可以通过提供一个TypeInfo的数组这样定义:
        //DEFINE_TYPES((devinfo_array)

首先我们可以看到，Type是全局静态定义的。通过TypeInfo来描述对这个类的要求。如果
在类上就有数据，可以给定TypeInfo.class_size（注意也要在最前面包含父类的State结
构），然后用class_init()给定初始化方法。

此外，一个Type只能有一个parent，但可以有一组interface，都用字符串表示。Type注册
后，系统用一个hash表进行全局管理，以name为key。这样创建真正的对象的时候总可以找
到整个继承树。

静态定义的Type的class_init可以在系统初始化的时候完成调用，动态定义的通过Lazy算
法在创建类的时候完成。

对象通过object_new("object_name")来创建，这可能会是在machine初始化的时候调用
qdev_create()创建，也可能会是在处理命令行参数device的时候用qdev_device_add()创
建。创建的时候会从类树上创建这个对象自己和所有父类和接口的State，并分别调用它们
的instance_init()。

这样你得到这个对象的指针的时候，它可以用OBJECT_GET_CLASS(class, obj, name)转化
任何类型了。

对象可以附加属性，静态通过提供属性表实现，动态通过object_property_add_xxx()添加
。这些属性可以在运行前和运行中修改（qemu console中的qom-set/get命令可以设置）。
不同的类可以定义自己的属性，本质是一对读写函数。属性也用字符串管理。

属性的管理是Device和Bus管理重要的组成部分，比如DeviceClass有realized属性，设备
管理通过把这个属性设置为true去调用它的

设备被创建后，这个设备的realized属性被设置为true，对应的函数就会被调用，这里一
般用于实现和backend的关联。

整个QOM就管理两种对象：Device和Bus。两者通过props进行互相关联。这种关联有两种类
型：composition和link，分别用object_property_add_child/link()建立。最后用qemu
console中使用Info qom-tree命令看到的树状结构就是这个属性建立的关联。

