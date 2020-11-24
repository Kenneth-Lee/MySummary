.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 0.2

qemu概念空间分析
****************

介绍
=====

最近修改qemu的东西越来越多，很多原来可以忽略的概念都不得不去面对了，基于这个初
始文档把内容扩展为一个完整的概念空间分析：

        :doc:`../软件构架设计/在qemu中模拟设备`

这个文档当前的版本还在不断更新中，后面根据需要会慢慢补充更多的内容。等我觉得补充
的内容足够多了，我会把版本和升级到1.0以上。

基础名称空间
============
我们先定义一些基本的名称以便后面容易说清楚各种概念：

Host
        Host表示模拟虚拟机的那个平台。这个概念比较模糊，可以表示Qemu这个程序，
        也可以表示运行Qemu的那个操作系统，反正不是被虚拟的那个平台。

VM/Guest
        这表示被模拟的那个平台。如果我们在X86上模拟一个RISCV的机器，X86就是Host
        ，而RISCV是VM或者Guest。如果我们说Host的CPU，那么这个CPU是X86的，而如果
        我们说Guest的CPU，那么这个CPU是RISCV的。

Backend
        这是Host中模拟Guest中某种行为的那些代码。比如我们用Qemu模拟了一张e1000
        网卡，在Guest中我们要“看到”这张网卡，我们需要在Guest的OS中装e1000的
        驱动，这个驱动是Guest中的。但为了模拟e1000的行为，我们也需要在qemu装
        一个驱动，这个驱动我们称为这个e1000的backend，它是Qemu概念上的。

Qemu使用glib作为基础设施，所以，读者如果需要和代码细节进行对应，最好对GLib的数
据结构有基本的了解。但本文本身不会深入到这些概念上。

执行模型
========

整个qemu软件的执行模型用Pyhton作为伪码可以表达如下：

.. code-block:: python
  
   def run_a_guest():
     vm = create_vm()
     vm.create_cpu_object()
     vm.create_device_object()
     for cpu in cpus:
       create_thread(cpu_thread, cpu)

   def cpu_thread(cpu):
     while true:
       try:
         cpu.run(vm)
       except EIO eio:
         find_device(eio.io_address).handle_io();

Qemu是Host上的一个进程，它模拟了一个VM，这是我们理解Qemu的基础。

一个VM是一组被模拟对象（Object）的组合体，Qemu的模拟过程就是模拟这些对象在时间
的发展过程中的状态变化，以及它们之间的互相影响，从而模拟VM的行为。

Qemu的对象主要有两种：cpu和device。qemu为每个Guest的CPU对象创建一个线程，这些线
程就可以利用Host CPU的算力，模拟VM CPU在遇到每条指令时的行为，更新VM CPU对象的
状态，如果遇到VM CPU做了IO一类的影响其他对象的行为，这个线程就暂时离开VM CPU的
模拟，跳出来，寻找对应的设备（或者其他CPU），去处理这个变化了。

Device当然也可以创建自己的线程，但更多时候，是它被动被CPU的行为所控制。

.. note::

   这里特别提醒一句：概念空间分析要重视名称空间的“空间”概念，这里说“qemu为每个
   cpu创建一个线程”，其中的CPU是被模拟的系统空间中的“CPU”，而不是Host中的“CPU”
   ，而线程，是Host中的线程，而不是被模拟系统中的线程。进行概念空间分析的时候，
   我们常常不得不跨越这些独立空间之间的交叉空间，请读者特别注意分清楚这些概念属
   于哪个概念空间。

上面代码中的cpu.run(vm)，有不同的cpu backend。比如，对于KVM backend，这本质是一
个系统调用，用户进程进入Hypervisor，由Hypervisor决定如何实际执行相关代码，而用
户进程自身则等待在系统调用上。而对于TCG backend，TCG程序会直接使用当前线程去翻
译当前指令为一段本地执行代码，然后跳进翻译缓冲去执行，这个执行本身就是用户线程
的一部分。

无论是哪种过程，我们在总体上都可以看作是一种黑盒，如果它用自己的逻辑可以一直执
行下去，就在黑盒中一直占据Host上的这个线程，知道它碰到一个无法处理的事件，它就
可以从cpu.run(vm)退出，Qemu就可以分析这个退出的原因，调用其他的对象去处理这个原
因。比如cpu.run(vm)中有人访问了io，Qemu退出来后就可以根据这个io的地址看是哪个
device backend提供的，让对应的backend完成自己的响应动作。


QOM
====

Qemu的代码主要是基于C的，不支持面向对象特性，但偏偏设备极为适合使用面向对象管理
。所以Qemu写了一套用C模拟的面向对象接口，QOM，Qemu Object Model。Qemu机会所有被
模拟的对象，都通过这种对象管理。

QOM是一个粗封装的面向对象模型，它包含这样一些子概念：

Type
        类型。每种类型用TypeInfo描述。请注意了：类型是类的描述，在实现的时候，
        它本质是一个用名称（字符串）索引的一个全局列表的成员，包含父类的索引（
        也是通过字符串索引），class_size，instance_size，以及各种回调等信息。它
        不代表那个类，它是说明类的相关信息的对象，通过type_register_xxx()系列函
        数全局注册。

Class
        类。这个才是类本身，这个概念类似Java中的class和object的关系：class的静
        态数据全局唯一，被所有同一类型共享，而object是实例，每个class可以创建
        很多实力（比如在Java中通过New创建的对象）。类自己的数据（类似Java中类的
        静态数据），保存在class_size的空间中，这个size必须包含父类的空间。在操
        作上，通常是在定义TypeInfo.class_size的时候，让它等于你的私有数据结构，
        并保证这个数据结构的第一个成员等于父类的私有数据结构。这样的结果就是父
        类拿到这个指针也可以直接索引到自己的数据结构。

        Class的继承树的根是ClassObject。
        
Object/Instance
        实例。通过object_new()等方法创建，当我们执行qemu -device xxxx的时候，本
        质就是在创建实例。它的数据保存在instance_size的空间中，原理和Class一样，
        需要为父类留空间。

        Instance的继承树的根是Object。

Interface
        一种特殊的类。不用于继承，用于实现。类不能有多个父类，但可以有多个
        Interface。

State
        一个纯概念的东西，表示类或者类实例的数据。呈现为TypeInfo的class_size和
        instance_size，子类的State必须包含父类的数据本身。

props
        DeviceClass的一组属性，每个成员叫Property，包含一对set/get函数，从而可
        以呈现为命令行的-device driver-name的参数（qemu -device
        driver-name,help可以直接查询device的属性）

下面是一些常用的全局的类：

.. list-table::
   :header-rows: 1

   * - 类
     - 名称
     - Class
     - State
     - 备注
   * - 机器
     - "machine"
     - MachineClass
     - MachineState
     - 
   * - 总线
     - "bus"
     - BusClass
     - BusState
     - 包含一组qbus_控制函数
   * - 设备
     - "device"
     - DeviceClass
     - DeviceState
     - 可以通过qdev_new创建，还包括一组qdev_控制函数

实例化这些类，就可以构成一个完整的VM。

我们看一个简单的例子对类建立感性认识：

.. code-block:: C

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

   static void my_device_register_types(void) {
          type_register_static(&my_device_info);
   }
   type_init(my_device_register_types)
   //这一段可以通过提供一个TypeInfo的数组这样定义:
   //DEFINE_TYPES((devinfo_array)

首先type_register_static注册了一个叫“mydevice”的TypeInfo，父类是“device”，没有
定义class_size（表示这个类没有自己的静态数据），instance的私有数据由
MyDviceState定义，这个数据结构的地一个成员是DeviceState，保存了自己的父类的
instance State。

Instances列表中给定了一组类名称，表示一组没有State数据的类型，可以索引过去拿到
对应的回调，但不能使用那一层的数据。

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

整个QOM主要就管理两种对象：Device和Bus。两者通过props进行互相关联。这种关联有两
种类型：composition和link，分别用object_property_add_child/link()建立。最后在
qemu console中使用Info qom-tree命令看到的树状结构就是这个属性建立的关联。

child和link关联
----------------
child和link是通过对象props建立的关联。本质上就是给一个对象增加一个prop，名字叫
child<...>或者link<...>，和手工创建一个这样的属性也没有什么区别。

child的主要作用是可以枚举，比如：

.. code-block:: C

   object_child_foreach();
   object_child_foreach_recursive();

利用这个机制，比如你模拟一个SAS卡，上面有多个端口，端口就可以创建为SAS的一个
child，而端口复位的时候就可以用这种方法找到所有的子端口进行通知。

而link通常用来做简单的索引，比如：

.. code-block:: C

   object_link_get_targetp();

这可以用于找关联设备，比如IO设备的IOMMU或者GIC控制器，或者一个网卡关联的PHY设备
等。

这不算什么特别的功能，只是简单的数据结构控制而已。用户自己用其他方法建立索引
去找到其他设备，也无不可。

MemoryRegion
=============

本小节看看qemu的内存管理逻辑。对于VM来说，它有它视角中的内存，当这个内存被VM中
的CPU或者设备访问，我们还需要Host中有backend去支撑这个访问。Qemu使用
MemoryRegion描述这个视角的内存。它包含如下一些子概念：

MemoryRegion
        这表示一个面向VM的内存区，以下简称MR。请注意了，MR的VM的内存区的描述，
        而不是那片内存本身。MR的要素是base_address, size这些信息，而不是void
        \*ptr这样的内存本身。整个系统的所有内存就是一个MR，整个系统的所有IO空间
        （不是说mmio，是说x86的LPC的IO）也是一个MR。MR内部包含多个不同设备的
        mmio也是一个MR。所以MR是个层叠的概念。

        全系统的内存MR可以通过get_system_memory()拿到，IO MR可以通过
        get_system_io()拿到。

MemoryRegionSection
        MR中的一个分段，简称MRS。

FlatView
        这表示看到的地址空间，本文简称FV。这个概念比较绕。我们这样说：AS是立体
        的，里面的MR是相互独立的，他们可以交叠，转义，动态开关等。但当你去访问
        的时候，某个时刻，某个物理地址总是对应着某个MR中的地址，FlatView用来表
        示层叠的结果。另外它也提供多个访问源互斥的锁。

AddressSpace
        这表示一个地址空间，以下简称AS。一个地址空间可以包含多个不同属性的MR，
        AS是MR的地址表述，基于MR的信息把空间分段成多个MRS，然后组成FV。

        综合来说，MR是提供者角度的内存，AS是使用者角度的内存。MRS和FV是两者的
        关联。

根据这个定义，MR是层叠的概念，上一层是本层的container，全系统的根container就是
system_memory和system_io。这个空间的大小就是Guest的虚拟空间的大小。其他世界的内
存，无论是ram还是mmio空间，都是这个空间的一个子空间。

我们通过例子看看从MR的创建方法。

RISCV的系统RAM是这样创建的：

.. code-block: C

   memory_region_init_ram(main_mem, NULL, "riscv_virt_board.ram",
                           machine->ram_size, &error_fatal);
   memory_region_add_subregion(system_memory, memmap[VIRT_DRAM].base,
        main_mem);
   
MMIO空间的MR一般由设备创建，通常长这样：

.. code-block: C

   memory_region_init_io(&ar->pm1.evt.io, memory_region_owner(parent),
                         &acpi_pm_evt_ops, ar, "acpi-evt", 4);
   memory_region_add_subregion(parent, 0, &ar->pm1.evt.io);

再看看使用者的角度。使用者手中拿到的是物理地址和CPU的AS，需要做的是用AS翻译
物理地址到MR。

Guest的CPU指令执行的时候一般不会直接去访问这些内存，而是先通过缺页填TLB。有了
这样一个过程，CPU模拟程序可以直接判断对应地址的类型，如果是RAM类型的，直接访问
过去就可以了，如果是IO类型的，就走调用这个MR的回调函数的路线。

CPU的TLB流程通过每种CPU的fill_tlb回调填TLB，每种CPU在实现这个回调的时候用
address_space_translate()就可以完成这个翻译，如果是RAM，直接引用MR里的ram_block
就可以支持自己的backend工作。

Device Backend的访问则走这个路径：

.. code-block: C

   dma_memory_rw(&address_space_memory, pa, buf, size, directory)

这仍从AS开始，从AS得到FV，然后定位MRS，最终找到MR，之后作为RAM处理还是IO处理，
就又MR的属性决定了。这个代码是这样的：

.. code-block: C

   static MemTxResult flatview_write(FlatView *fv, hwaddr addr, MemTxAttrs attrs,
                                  const void *buf, hwaddr len)
   {
       ...
       mr = flatview_translate(fv, addr, &addr1, &l, true, attrs);
       result = flatview_write_continue(fv, addr, attrs, buf, len,
                                     addr1, l, mr);
       ...
   }

MR有很多类型，RAM，ROM，IO等，这个不在这里细究，我们只深入分析一下IOMMU类型。

IOMMU的作用是把设备发出的地址进行一次映射，再作为物理地址去访问。如果你仅仅是要
给你自己的设备创建翻译，自己实现一套协议就可以了，最终访问物理地址的时候还是可
以用上面的方法访问就行。

但如果要实现通用的IOMMU驱动，则可以用IOMMU MR，比如下面这个是ARM SMMU实现：

.. code-block: C

   memory_region_init_iommu(&sdev->iommu, sizeof(sdev->iommu),
                            TYPE_SMMUV3_IOMMU_MEMORY_REGION,
                            OBJECT(s), name, 1ULL << SMMU_MAX_VA_BITS);
   address_space_init(&sdev->as, MEMORY_REGION(&sdev->iommu), name);

其中这里的s->mrtypename是要实现的IOMMU对象的名字。这个对象的实现是这样的：

.. code-block: C

   static void smmuv3_iommu_memory_region_class_init(ObjectClass *klass,
                                                  void *data)
   {
       ...
       imrc->translate = smmuv3_translate;
       imrc->notify_flag_changed = smmuv3_notify_flag_changed;
   }

   static const TypeInfo smmuv3_iommu_memory_region_info = {
      .parent = TYPE_IOMMU_MEMORY_REGION,
      .name = TYPE_SMMUV3_IOMMU_MEMORY_REGION,
      .class_init = smmuv3_iommu_memory_region_class_init,
   };

简单说，你需要为这个MR创建一个TYPE_IOMMU_MEMORY_REGION类型的对象，然后为它创建
translate和notifiy_flag_changed回调，决定地址作什么转换，剩下的地址翻译就可以留
给AS-MR的翻译体系了。

中断
=====
可能是历史原因，Qemu中的中断都认为是对CPU的一个gpio行为，每个中断源都可以实现为
一个设备上的gpio pin，比如这样：

.. code-block: C

   static void sifive_plic_irq_request(void *opaque, int irq, int level) {
        dev = opaque;
        ...
        cpu_interrupt(); //给对应的CPU发中断，是哪个CPU看你的设计了
        ...
   }
   qdev_init_gpio_in(dev, sifive_plic_irq_request, plic->num_sources);

这里的初始化，第一个参数是中断所属设备（用于回调的时候可以找到上下文而已），第
二个参数是回调，第三个参数是中断的数量。而在回调中，cpu_interrupt()里面具体怎么
做，就看cpu的backend怎么做的了，通过硬件调度进去也行，在TCG中找一个检查点也行。

这个函数也可以直接封装成sysbus_init_irq()，这可以少些参数（比如n=1）。

除了有qdev_init_gpio_in，还有qdev_init_gpio_out。这里的in，out，就是指gpio的输
入输出信号，在用于中断的时候，什么时候是in，什么时候是out，好像也没有什么影响，
因为作为中断使用，根本就不管是in还是out的。

有了这个设施以后，发起中断的时候对对应的irq做一个qemu_set_irq，中断就种到系统中
了。如果你模拟的系统有中断控制器，实现你的回调，然后让你的设备关联它，想办法通过
比如prop等手段把请求转过去，让中断控制器发qemu_set_irq()就可以了。


其他小设施
===========

Monitor
--------
Qemu的Monitor是Qemu的控制界面，它可以占据当前的控制台，也可以通过其他tty控制台
进行访问。Qemu的Monitor当前在概念空间上有两种：

QMP
        Qemu Message Protocol，这是通过json消息对运行中的Qemu进行控制。
        通过Qemu参数-qmp启动。启动后可以用telnet一类的中断登录上去控制。

HMP
        Human Message Protocol，这直接就是命令行接口了，这在Qemu启动后通过热键
        进入（默认是ctl-a c）。

QMP是Qemu的核心逻辑，HMP最终都是解释为QMP的实现完成相应的功能的。比如
hmp_info_version查qemu的版本，实际调用的是qmp_query_version()。

Error
------
Qemu使用一种层次化的报错机制，也就是说，由调用者决定这个错误的严重程度。比如这
样一个调用关系：

.. code-block:: C

   a(err) {
     b(err) {
        c(err);
     }
   }

当a调用b的时候，不是b决定这个错误有多严重，而是a决定这个错误有多严重。c用b的err
参数报错，而b用a提供参数报错。如果b调用c的时候，觉得我不在乎这个调用会错（这很
常见，比如我查找一个字符串，找不到就找不到了，无所谓），就可以传一个NULL进去，
这样c继续基于这个NULL报错，这个错误就会被忽略。

Qemu当前提供了两种错误控制类型：

error_abort
        需要abort()的错误。

error_fatal
        需要exit()的错误。

报错的一层用这些函数报告错误：::

        error_setg(error, ...);         // 设置错误
        error_append_hint(error, ...);  // 补充错误提示
        error_propagate(error, ...);    // 向上一级传递

调用一方把error_abort或者error_fatal传进去，出来的时候根据这个参数检查实际的错误
是什么。

