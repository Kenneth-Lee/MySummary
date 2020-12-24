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
。所以Qemu写了一套用C模拟的面向对象接口，QOM，Qemu Object Model。Qemu几乎所有被
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
法在创建类的时候完成。这个回调的作用是让你有机会替换父类的回调函数。以便让你调
用父类实现的方法的时候，可以换用一个新的函数。比如你的父类是A，子类是B，父类实
现一个relealize函数，里面调用ClassA->config()，你要换掉这个函数，只要在B的
class_init中换一个函数就可以了。

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

实际上，整个机器的对象machine就是根对象的一个child。下面是qemu控制台下运行
qom-list的一个示例：::

        (qemu) qom-list /
        type (string)
        objects (child<container>)
        machine (child<virt-5.2-machine>)
        chardevs (child<container>)

        (qemu) qom-list /machine
        type (string)
        ...
        virt.flash1 (child<cfi.pflash01>)
        unattached (child<container>)
        peripheral-anon (child<container>)
        peripheral (child<container>)
        virt.flash0 (child<cfi.pflash01>)
        ...

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
的CPU或者设备访问，我们还需要Host中有backend去支撑这个访问，所以，qemu有Host视
角中的内存。Qemu使用MemoryRegion描述这个视角的内存。它包含如下一些子概念：

MemoryRegion
        这表示一个面向VM的内存区，以下简称MR。请注意了，MR的VM的内存区的描述，
        而不是那片内存本身。MR的要素是base_address, size这些信息，而不是void
        \*ptr这样的内存本身。整个系统的所有内存就是一个MR，整个系统的所有IO空间
        （不是说mmio，是说x86的LPC的IO）也是一个MR。MR内部包含多个不同设备的
        mmio也是一个MR。所以MR是个层叠的概念。

        但部分基础的内存层是真的分配和Host一侧用于支持前端的backend内存的，这个
        这个真正的内存指针在MR->ram_block中。

        全系统的内存MR可以通过get_system_memory()拿到，IO MR可以通过
        get_system_io()拿到。

RAMBlock
        这是MR的ram_block的类型，表示一段真实的Host一侧的内存，它可以是创建的
        时候就分配的，也可能是用Lazy算法动态一点点增加的。

MemoryRegionSection
        MR中的一个分段，简称MRS。

FlatView
        这表示看到的地址空间，本文简称FV。这个概念比较绕。我们这样说：AS是立体
        的，里面的MR是相互独立的，他们可以交叠，转义，动态开关等。但当你去访问
        的时候，某个时刻，某个物理地址总是对应着某个MR中（某段MRS）的地址，
        FlatView用来表示层叠的结果。另外它也提供多个访问源互斥的锁。

AddressSpace
        这表示一个地址空间，以下简称AS。一个地址空间可以包含多个不同属性的MR，
        AS是MR的地址表述，基于MR的信息把空间分段成多个MRS，然后组成FV。

        全系统的get_system_memory()和get_system_io()对应的AS是
        address_space_meory和address_space_io，也可以直接被其他驱动所访问。

        综合来说，MR是提供者角度的内存，AS是使用者角度的内存。MRS和FV是两者的
        关联。全系统可以有AS，从一个设备看这个系统，也可以有AS。全系统AS看到的
        MR，从设备的AS上就不一定能看到。

MemoryRegionCache
        IO MR中访问过的数据可以放在Cache中，这个Cache简称MRC，现在主要就是给
        virtio用。

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

   dma_memory_rw(&address_space_memory, pa, buf, size, direction);

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

还有一种Device Backend的DMA访问路径是这样的：

.. code-block: C

        dma_memory_map(address_space, pa, len, direction);
        dma_memory_unmap(address_space, buffer, len, direction, access_len);

这有两种实现策略：如果这片MR背后有直接分配的内存，那最好办，直接把本地内存的指
针拿过来就可以了，unmap的时候保证发起相关的通知即可。如果没有，那可以使用Bounce
DMA Buffer机制。也就是说，直接另外分配一片内存，到时映射过来就是了。

MR有很多类型，RAM，ROM，IO等：

.. code-block: C

   memory_region_init(mr, owner, name, size);
   memory_region_init_alias(mr, owner, name, orig, offset, size);
   memory_region_init_io(mr, owner, ops, opaque, name, size);
   memory_region_init_iommu(_iommu_mr, instance_size, mrtypename, owner, name, size);
   memory_region_init_ram_nomigrate(mr, owner, name, size, errp);
   memory_region_init_ram_shared_nomigrate(mr, owner, name, size, share, errp);
   memory_region_init_ram_shared_nomigrate(mr, owner, name, size, share, errp);
   memory_region_init_ram(mr, owner, name, size, errp);
   memory_region_init_ram_ptr(mr, owner, name, size, ptr);
   memory_region_init_ram_device_ptr(mr, owner, name, size, ptr);
   memory_region_init_ram_from_fd(mr, owner, name, size, share, fd, errp);
   memory_region_init_ram_from_file(mr, owner, name, size, align, ram_flags, path, errp);
   memory_region_init_rom(mr, owner, name, size, errp);
   memory_region_init_rom_device(mr, owner, ops, opaque, name, size, errp);
   memory_region_init_rom_device(mr, owner, ops, opaque, name, size, errp);
   memory_region_init_rom_device_nomigrate(mr, owner, ops, opaque, name, size, errp);
   memory_region_init_rom_device_nomigrate(mr, owner, ops, opaque, name, size, errp);

这个不在这里一一细究，我们只深入分析一下IOMMU类型。

IOMMU的作用是把设备发出的地址进行一次映射，再作为物理地址去访问。如果你仅仅是要
给你自己的设备创建翻译，自己实现一套协议就可以了，最终访问物理地址的时候还是可
以用上面的方法访问。

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
在qemu中，中断本质是cpu_exec()过程中的一个定期判断（如果是KVM一类的真正执行就靠
KVM本身的硬件机制了，那个原理可以自然想像）。

qemu通过cpu_reset_interrupt/cpu_interrupt()把一个标记种入到CPU中，CPU执行中就
可以检查这个标记，发现有中断的要求，就调用一个回调让中断控制器backend修改CPU状
态，之后CPU就在新的状态上执行了。

所以，最原始的方法是你强行吊cpu_reset_interrupt()和cpu_interrupt()。当然，很少
硬件会这么简单，大部分CPU需要通过中断控制器来控制。中断控制器是个设备（比如
qdev），具体怎么做完全是实现者的自由度。

可能是历史原因，qemu统一把中断看作是CPU的gpio行为，变成一套完整的接口。比如
RISCV就是这样的：

.. code-block: C

   static void sifive_plic_irq_request(void *opaque, int irq, int level) {
        plic_dev = opaque;
        ...
        cpu_interrupt(); //给对应的CPU发中断，是哪个CPU看plic算法了
        ...
   }
   qdev_init_gpio_in(plic_dev, sifive_plic_irq_request, plic->num_sources);

这样组织一下，给中断控制器加下级中断的方法就变成一套统一的函数：

.. code-blokc: C

   qdev_init_gpio_in_xxx(plic, callback, num_irqs);
   qemu_irq qdev_get_gpio_in(plic, n);
   qdev_connect_gpio_in_xxx(cpu, n, qemu_irq);
   sysbus_connect_irq(dev, n, qemu_irq);

这里的in可以换成out，是gpio的片信号标记，对于模拟来说我觉得关系不大，都用同一
种就好了。qemu_irq是表示中断的控制结构，包含中断控制器的信息，n是中断控制器内
的下标。sysbus_开头的接口是对qdev接口的封装，把处理中断的设备作为参数传递进去
而已（会据此建立设备间的一些关联）。综合起来，这个概念是：

1. 用init实现中断控制器

2. 中断控制器用qev系列函数建立qemu_irq的管理，把plic本地中断号和qemu_irq对应起
   来

3. connect系列函数把qemu_irq和设备关联起来，和CPU或者全局中断号关联起来（具体
   和谁关联看中断控制器的设计）。

有了这个设施以后，其他后端发中断就不用去找对应的CPU和设备了，只要给定qemu_irq就
可以了。这个核心函数是qemu_set_irq()，在实际使用的时候封装成这样一些更贴近使用
名称空间的接口：

.. code-block: C

        void qemu_irq_raise(qemu_irq irq);
        void qemu_irq_lower(qemu_irq irq);
        void qemu_irq_pulse(qemu_irq irq);
        void pci_irq_assert(PCIDevice *pci_dev);
        void pci_irq_deassert(PCIDevice *pci_dev);
        void pci_irq_pulse(PCIDevice *pci_dev);

如果用的是PCI MSI/MSI-X，则中断触发通过msi_notify()来做。按MSI/MSI-X的原理，这
个行为实际上就是根据MSX PCI配置，在对应的内存地址中写入要求的参数，这个内存地
址写入的过程通过MR的翻译，最终会匹配到中断控制器的io写上，最后还是那组
qemu_set_irq()调用。

PCI/PCI-E
==========
PCI/PCI-E本质上就是一个代理了很多设备的设备。所以它才有那些BDF的复杂概念，好像
很灵活，但如果我们从地址分配这个角度看，每个PCI/PCIE根桥就是一个平台设备，这个
平台设备有自己的MMIO空间，它的所有动态协议，不过是对这个空间的重新分配（基于设
备对应的Bus-Device-Function）。

所以PCI/PCIE根桥的创建本质上分配一个MMIO空间，并用PCIE作为这个MR的管理设备而已
。一般套路是：

1. 创建一个PCI/PCIE设备作为Root Bridge，比如TYPE_GPEX_HOST（General PCI EXpress）。

2. 创建ECAM空间（配置空间）
   * mb = sysbus_mmio_get_region()
   * mem_region_init_alias(alias...)
   * memory_region_add_subregion(system_memory, addr, alias)

3. 创建BAR空间
   * 同2

剩下的事情就是TYPE_GPEX_HOST驱动的问题了。

TYPE_GPEX_HOST的继承树结构：::

  DEVICE <- SYS_BUS_DEVICE <- PCI_HOST_BRIDAGE <- PCIE_HOST_BRIDGE <- GPEX_HOST 

中断的行为类似，先为整个RP分配中断，然后用gpex_set_irq_num()建立PCIE局部irq和全
局irq的关系即可。

virtio
=======

virtio是OASIS的标准，我没有调查它的背景，应该是Redhat和IBM等发起的组织吧，它的
目标是定义一个标准的虚拟设备和Guest的接口。也就是说在设备一侧实现“半虚拟化”，让
guest感知host的存在，让guest上的模拟变成一种guest和host通讯的行为。

标准
-----
在本文写作的时候，最新的virtio版本是1.1，我们这里先看看这个版本的语义空间。

virtio现在支持三种传输层，virtio的语义可以建立在任一种传输层上，只要传输层能满
足这些语义的表达就可以了：

PCI
        这是较通用的方式，设备可以通过PCI协议自动发现，Host-Guest之间也可以直接
        模拟成PCI/PCI接口进行相互访问。

MMIO
        这用于平台设备，需要通过devtree一类的方式进行设备枚举。Host-Guest间通过
        一般的MMIO方式进行通讯。

Channel I/O
        这是IBM S/390的通用IO接口，我们有两种方式做分析就够了，这种忽略。

不同的方式使用不同的传输层协议，但这些传输层协议维护一样的高层语义。下面重点讨
论这些高层语义的概念空间。在下面的讨论中，比如我们说virtio支持Device Status，这
个域具体呈现为PCI的配置空间还是MMIO中的一个域，是一个域还是多个域，我们不关心，
我们关心的是必须存在这么一个概念，并且这个概念必须承载所定义的语义。


控制域
-------
控制域相当于设备的MMIO空间，提供直接的IO控制。下面是一些典型的控制域：

Device Status
        设备状态。这个概念同时被Host和Guest维护，而被虚拟机管理员认知。它包含
        多个状态位，比如ACKNOWLEDGE表示这个设备被Guest驱动认知了，而
        DEVICE_NEED_RESET表示Host出了严重问题，没法工作下去了。

Feature Bits
        扩展特性位。这个域也是Host和Guest共同维护的。Host认，Guest不认，对应位
        也不会设置，反之亦然。

在MMIO传输层中，部分域甚至是复用的，比如配置第一个queue的时候，给queue id写0，
后面的配置就是针对vq 0的；给queue id写1，后面的配置就是针对vq 1的。强调这一点，
是要说明，控制域不大可能直接通过共享内存可以实现。

通知
`````
通知用于主动激活另一端的行为。virtio支持三种通知：

配置更改
        Host到Guest，在配置空间发生更改的时候发出

Available Buffer更改
        Guest到Host，表示数据被写入virtio队列

Used Buffer更改
        Host到Guest，表述virtio处理了数据，返回数据到Guest。

这些通知在不同的传输层协议会有不同的方式，比如Host到Guest常常会用Guest一侧的中
断，但这个不是根本性的要求。

virtqueue
``````````
virtqueue是Host和Guest的通道，目标是要建立一个两者间的共享内存通讯通道，后面把
它简称为vq。和其他共享内存的通讯方式一样，vq通过环状队列协议来实现。队列的深度
称为Queue Size，每个vq包括收发两个环，称为vring，其中Guest发方的叫Available
ring，另一个方向称为Used ring，深度都是Queue Size。

vq的报文描述符称为Descriptor，在本文中我们简称bd（Buffer Descriptor），它不包含
实际的数据，实际的数据称为Buffer，由bd中的指针表达，指针是Guest一侧的物理地址。
virtio允许bd分级，bd的指针可以指向另一个bd的数据，这可以扩展bd数量的不足。
Buffer可以带多个Element，每个Element有自己的读写属性，新的Element需要使用另一个
bd，通过前一个bd的next指向新的bd，把多个Element连成同一个Buffer。

整个通讯的内存控制方都在Guest，是Guest分配了vq和Buffer的内存，然后传输到Host端
，而Host端根据协议，对内存进行读写，响应Guest的请求。这一点和普通的真实设备是一
样的。这也是为什么很多人希望把硬件接口直接统一成virtio接口。这样可以少写一个驱
动，而虚拟设备管理说不定可以直接交给下一层的Hypervisor。

前面描述的概念是virtio 1.0和之前支持的格式，称为split vq。1.1以后增加了一种
packed vq，其原理是把Available和Used队列合并，Buffer下去一个处理一个，不需要不
同步的Used队列来响应。除了这一点，概念空间完全是自恰的。

Host
-----
理解了标准接口定义上的基本理念，现在看看Host一侧实现的概念空间。

Host一层virtio设备的继承树一般是这样：::

        TYPE_BUS -> TYPE_VIRTIO_BUS -> TYPE_VIRTIO_PCI_BUS
        TYPE_DEVICE -> TYPE_VIRTIO_DEVICE -> TYPE_VIRTIO_XXXXX
        TYPE_PCI_DEVICE -> TYPE_VIRTIO_PCI -> TYPE_VIRTIO_PCI_XXXX_BASE -> TYPE_VIRTIO_PCI_XXXX
                                                                        -> TRANSITIONAL_DEV
                                                                        -> NON_TRANSITIONAL_DEV

总线类用于设备的总线注册，属于辅助性质的，重点的是设备本身。在设备中，PCI这里比
较特别，分了两层，下面有多种设备的类型的变体，这涉及VIRTIO不同版本的兼容性问题
，这里不深入讨论，我们下面的讨论聚焦在TYPE_VIRTIO_DEVICE的通用概念上，PCI设备可以
类比。但我们还是给出这个概念的定义：

TRANSITIONAL_DEV
        这个概念现在仅针对PCI virtio设备，表示这个设备是否支持新旧接口的过渡。
        NON_TRANSITIONAL_DEV就支持一种接口，TRANSITIONAL_DEV支持多个版本接口的
        协商。

TYPE_VIRTIO_XXXXX
``````````````````
TYPE_VIRTIO_XXXX实现一个具体的设备，这层实现主要通过virtio接口建立通讯通道，原
理大致是：::

        virtio_init(vdev, ...);
        vq[i] = virtio_add_queue(vdev, callback);...
        ...
        virtio_delete_queue(vq[i]);
        virtio_cleanup(vdev);

这里的初始化主要是在vdev中创建基本的数据结构，然后挂入vm的管理系统中（比如挂入
vm状态更新通知列表中等）。由于真正的queue的共享内存是Guest送下来的，所以这里仅
仅是在创建相关的管理数据结构而已。

callback的实现原理展示如下：::

        element = virtqueue_pop(vq[i]);
        处理element，这是一个sg接口，需要分段处理或者合并以后处理。
        if (need_respose) {
                virtqueue_push(vq[i], element);
                virtio_notify(vdev, vq[i]);
        } else {
                virtqueue_detach_element(vq[i], element, ...);
                g_free(element);
        }

virtqeue_push/pop()做了一次拷贝，理论上你是可以直接在原位处理的，但qemu现在没有
提供这样的接口。

TYPE_VIRTIO_DEVICE
````````````````````
然后我们看TYPE_VIRTIO_DEVICE一层的原理：TYPE_VIRTIO_DEVICE是一个总线为
TYPE_VIRTIO_BUS的设备，这一层在设备实现上主要是创建vq（固定数量，现在是1024），
处理标准配置，以及实现各种通知机制。比如vq内存被访问的时候进行对应的响应等。
这主要通过跟踪事件通知机制实现，比如guest访问了设备配置空间，变成host端的
io_writex()，host侧IO驱动（比如PCIE）发起memmory_region_transaction，在commit的
时候触发virtio_memory_listener_commit()。

所以，所有配置性的行为，其实走的都是io dma访问的路径。而virqueue_push/pop则走的
是MemoryRegionCache的路径，后者通过dma_memory_map() 找到实际的host可见的内存位
置，直接在原位访问。这一层对上一层的接口在分析上一层的使用接口时已经可以看到了。
这里完整整理一下：::

        virtio_instance_init_common(obj); //用于PCI的实现中子类instance_init的初始化

        //设备级处理
        virtio_init(vdev, ...);
        virtio_cleanup(vdev, ...);
        virtio_error(vdev, ...);
        virtio_device_set_child_bus_name(vdev, bus_name);

        //队列管理
        virtio_add_queue(vdev, ...);
        virtio_del_queue(vdev, ...);
        virtio_delete_queue(vq);
        virtqueue_push(vq, elem, ...);
        virtqueue_flush(vq, ...);
        virtqueue_detach_element(vq, elem, ...);
        virtqueue_unpop(vq, elem, ...);
        virtqueue_rewind(vq, ...);
        virtqueue_fill(vq, elem, ...);
        virtqueue_map(vdev, elem);
        virtqueue_pop(vq, ...);
        virtqueue_drop_all(vq);
        qemu_get_virtqueue_element(vdev, file, ...); //用本地文件做backend
        qemu_put_virtqueue_element(vdev, file, ...);
        virtqueue_avail_bytes(vq, ...);
        virtqueue_get_avail_bytes(vq, ...);

        // 通知和状态类
        virtio_notify_irqfd(vdev, vq);
        virtio_notify(vdev, vq);
        virtio_notify_config(vdev);
        virtio_queue_get_notification(vq);
        virtio_queue_set_notification(vq, ...);
        virtio_queue_ready(vq);
        virtio_queue_empty(vq);

        // snapshot管理
        virtio_save(vdev, file);
        virtio_load(vdev, file, ...);

这一层之后下面提供了Host的直接访问接口层：::

        /*
         * 注1：X是字长后缀
         * 注2：modern修饰1.0以后的版本的协议
         */
        virtio_config_<modern>_readX(vdev, addr);
        virtio_config_<modern>_writeX(vdev, addr, data);
        virtio_queue_set_addr/num/max_num...(vdev, ...);
        virtio_queue_get_addr/num/max_num...(vdev, ...);
        int virtio_get_num_queues(vdev);
        virtio_queue_set_rings(vdev, ...);
        virtio_queue_update_rings(vdev, ...);
        virtio_queue_set_align(vdev, ...);
        virtio_queue_notify(vdev, ...);
        virtio_queue_vector(vdev, ...); //MSI-X特性支持
        virtio_queue_set_vector(vdev, ...);
        virtio_queue_set_host_notifier_mr(vdev, mr, ...);
        virtio_set_status(vdev, ...);
        virtio_reset(vdev);
        virtio_update_irq(vdev);
        virtio_set_features(vdev, feature);

Guest
------
再看看Guest一侧Linux的概念空间。Guest一侧包括两层，一层是virt，实现具体的设备，
一层是ring，提供传输接口。Linux上只有PCI接口的virtio，因为也没有其他办法做设备
发现了。

virt
`````
virt层类似其他的设备驱动，基于::

        register_virtio_driver(&driver);
        unregister_virtio_driver(&driver);

进行驱动注册，driver中给定id表进行设备匹配，在probe的时候，通过
virtio_cread...()函数直接读配置。然后按如下Pattern进行通讯：::

        probe(vdev) {
                vqs = kalloc(...)

                vdev->config->find_vqs(vdev, num_vqs, vqs, callbacks, names, 
                        ctx, irq_affi);

                // 发
                在data中准备数据
                virtqueue_add_outbuf(vq, sg, num, data, gfp);

                // 收（可以放在callback中）
                buf = virtqueue_get_buf(vq, ...);
                处理buf的数据
                free(buf);
        }

这个工作Pattern值得注意点有这么几个：

1. vqs通过vdev提供，这要靠设备发现逻辑来配，比如PCI的配置逻辑就在
   vp_modern_find_vqs()中，主体是ring一层的函数vp_find_vqs()。

2. 接收一侧使用callback的方式做的，这个回调的上下文是中断。

3. virtio驱动匹配的不是PCIE设备，而是virtio设备，所以一个virtio设备实际上有两个
   驱动，一个是PCI驱动，通过虚拟的PCIE总线枚举发现virtio设备，然后用那个设备的
   驱动创建virtio设备，从而匹配对应的驱动。

ring
`````
现在来看完整的ring层对上层暴露的接口（vp是virtio_pci的缩写）：::

        /* 设备管理 */
        register_virtio_device(dev);
        unregister_virtio_device(dev);
        virtio_add_status(dev, ...);
        virtio_break_device(dev);
        virtio_config_changed(dev);
        virtio_config_disable(dev);
        virtio_config_enable(dev);
        virtio_finalize_features(dev);
        virtio_max_dma_size(vdev);
        virtio_device_for_each_vq(vdev, vq)

        /* 关联vqs ×/
        vp_find_vqs(vdev, nvqs, vqs[], callbacks[], ...);
        vp_del_vqs(vdev);

        /* 通知 */
        vp_synchronize_vectors(vdev);
        vp_notify(vq);
        vp_bus_name(vdev);

        /* CPU affinity */
        vp_set_vq_affinity(vq, cpu_mask);
        vp_get_vq_affinity(vdev, index);

        /* vq */
        virtqueue_add_outbuf(vq, ...);
        virtqueue_add_inbuf(vq, ...);
        virtqueue_add_inbuf_ctx(vq);
        virtqueue_add_sgs(vq, ...);
        virtqueue_kick(vq);
        virtqueue_kick_prepare(vq);
        virtqueue_notify(vq);
        virtqueue_get_buf(vq, ...);
        virtqueue_get_buf_ctx(vq, ...);
        virtqueue_enable/disable_cb(vq);
        virtqueue_enable_cb_prepare(vq);
        virtqueue_poll(vq, ...);
        virtqueue_enable_cb_delayed(vq);
        virtqueue_detach_unused_buf(vq);
        virtqueue_get_vring_size(vq);
        virtqueue_is_broken(vq);
        virtqueue_get_vring/desc_addr/avail_addr/used_addr(vq);

这是ring层自己内部的封装接口：::

        /* vring建立 */
        vring_create_virtqueue(...);
        vring_new_virtqueue(...);
        void vring_del_virtqueue(vq);
        vring_transport_features(vdev);
        vring_interrupt(irq, vq);


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

事件通知
--------
Qemu的时间通知用于两个线程间进行事件通知，在Linux下主要是对eventfd(2)的封装，在
Windows下是对CreateEvent()的封装。它主要是封装这样一对接口：::

        event_notifier_set(EventNotifier);
        event_notifier_test_and_clear(EventNotifier);

前者发起通知，后者测试通知。

.. vim: set tw=78
