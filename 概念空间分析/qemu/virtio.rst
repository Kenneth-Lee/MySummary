.. Kenneth Lee 版权所有 2020-2025

:Authors: Kenneth Lee
:Version: 1.0

virtio
******

virtio是OASIS的标准，我没有调查它的背景，应该是Redhat和IBM等发起的组织吧，它的
目标是定义一个标准的虚拟设备和Guest的接口。也就是说在设备上实现“半虚拟化”，让
guest感知host的存在，让guest上的模拟变成一种guest和host通讯的行为。

virtio标准
==========

在本文写作的时候，最新的virtio标准的版本是1.1，我们这里先看看这个版本的语义空间。

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

所谓传输层，本质是用什么语义来提供guest一侧的接口。我们前面已经看到了，host有
办法访问guest的所有内存，但Guest还得做出一副“我是个正经的系统”的样子，表明什么
数据是打算让Host去访问的，把这个仪式封装成一个协议，就是virtio的传输层。比如说
，PCI传输层，就是guest认为自己是在访问一个PCI设备，它访问bar空间的时候，就会转
换为host一侧的IO MR的读写，它对内存做DMA，要求Host访问，Host就要打开对应的AS，
从AS上访问这片内存。它不做这个DMA，Host其实也能访问这些内存，只是不知道应该访
问哪里而已。所以传输层，更多是Guest的接口概念。Host只是在配合。

我们这里的建模主要关注传输层以上的语义，传输层怎么实现，总是可以做到的，我们看
做是细节。

下面是一组virtio标准中定义的关键概念：

控制域
------

控制域相当于设备的MMIO空间，提供直接的IO控制。下面是一些典型的控制域：

Device Status
        设备状态。这个概念同时被Host和Guest维护，而被虚拟机管理员认知。它包含
        多个状态位，比如ACKNOWLEDGE表示这个设备被Guest驱动认知了，而
        DEVICE_NEED_RESET表示Host出了严重问题，没法工作下去了。

Feature Bits
        扩展特性位。这个域也是Host和Guest共同维护的。Host认，Guest不认，对应位
        也不会设置，反之亦然。

在MMIO传输层中，部分控制域甚至是复用的，比如配置第一个queue的时候，给queue id
这个控制域写0，后面写其他控制域进行配置就是针对vq 0的；给queue id控制域写1，后
面的配置就是针对vq 1的。

强调这一点，是要说明，标准的制定者并不指望用共享内存来实现控制域。

通知
----

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
---------

virtqueue是Host和Guest的通道，目标是要建立一个两者间的基于共享内存的通讯通道，
后面把它简称为vq。和其他共享内存的通讯方式一样，vq通过环状队列协议来实现。队列
的深度称为Queue Size，每个vq包括收发两个环，称为vring，其中Guest发方的叫
Available ring，另一个方向称为Used ring，深度都是Queue Size。

vq的报文描述符称为Descriptor，在本文中我们简称bd（Buffer Descriptor）或者desc，
它不包含实际的数据，实际的数据称为Buffer，由bd中的指针表达，指针是Guest一侧的物
理地址。virtio允许bd分级，bd的指针可以指向另一个bd的数据，这可以扩展bd数量的不
足。Buffer可以带多个Element，每个Element有自己的读写属性，新的Element需要使用另
一个bd，通过前一个bd的next指向新的bd，把多个Element连成同一个Buffer。

整个通讯的内存控制方都在Guest，是Guest分配了vq和Buffer的内存，然后传输到Host端
，而Host端根据协议，对内存进行读写，响应Guest的请求。这一点和普通的真实设备是一
样的。这也是为什么很多人希望把硬件接口直接统一成virtio接口。这样可以少写一个驱
动，而虚拟设备管理说不定可以直接交给下一层的Hypervisor。

前面描述的概念是virtio 1.0和之前支持的格式，称为split vq。1.1以后增加了一种
packed vq，其原理是把Available和Used队列合并，Buffer下去一个处理一个，不需要不
同步的Used队列来响应。除了这一点，概念空间完全是自恰的。

Host侧的实现
============

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
-----------------

TYPE_VIRTIO_XXXX实现一个具体的设备，这层实现主要通过virtio接口建立通讯通道，原
理大致是：

.. code:: c

   virtio_init(vdev, ...); //设备初始化
   vq[i] = virtio_add_queue(vdev, callback);... //创建q，可多个
   ...
   virtio_delete_queue(vq[i]);
   virtio_cleanup(vdev);

这里的初始化主要是在vdev中创建基本的数据结构，然后挂入vm的管理系统中（比如挂入
vm状态更新通知列表中等）。由于真正的queue的共享内存是Guest送下来的，所以这里仅
仅是在创建相关的管理数据结构而已。

callback用于响应guest发过来的消息，可以这样收：

.. code:: c

   element = virtqueue_pop(vq[i], sz);
   my_handle_element(element);
   if (need_respose) {
       virtqueue_push(vq[i], element);
       virtio_notify(vdev, vq[i]);
   } else {
       virtqueue_detach_element(vq[i], element, ...);
       g_free(element);
   }

内存由pop函数负责分配，如果不复用这个内存（push回去），由调用方自己负责用glib标
准方法释放。这个内存的大小至少是sz，但根据实际有多少个sg，实际大小是不同的，如果
数据在push进来的时候就是scatter-gather的，host收到也是一样的，数据就在原地（
guest和host共享），如果你不用iov_to_buf()这种方法强行把它们拷贝在一起，你完全
可以直接一段段进行处理。所以virtio的通讯效率还是很高的。

virtio_init()等初始化行为可以在类的realize/unrealize回调中做，这些回调可以在
class_init中初始化，类似这样：

.. code:: c

   static void my_class_init(ObjectClass *oc, void *data) {
     DeviceClass *dc = DEVICE_CLASS(oc);
     VirtioDeviceClass *vdc = VIRTIO_DEVICE_CLASS(oc);

     vdc->realize = my_realize;
     vdc->unrealize = my_unrealize;
     vdc->get_features = my_get_features;
     vdc->get_config = my_get_config;
     vdc->set_status = my_set_status;
     vdc->reset = my_reset;
   }

注意了，这里的realize设置的不是DeviceClass的realize，而是子类VirtioDeviceClass
的realize（其他回调类似）。因为这是VirtioDeviceClass要靠父类DeviceClass的
realize来进行自己的初始化，在用子类提供的realize进行子类的初始化。

get_features()用于guest和host协商协议，当这个函数被调用的时候是guest问host能否
提供对应的feature，host可以修改相关的项，返回回去，告知自己想要支持的属性，双方
可以多次协商取一个双方认可的子集。get_config用于guest向host要配置参数，具体是什
么格式，是这种自己的定义。

.. note::

   feature是跨层使用的，比如如果你在get_feature中给对方返回了
   VIRTIO_F_RING_PACKED特性，应用层不需要做任何事情，协议层会根据这个属性把
   vring的格式修改成pack的。

而set_status()用于host和guest交换Device Status控制域用的，一般一个设备启动会逐
步把下面这些位都置上，设备才是可用的：::

        VIRTIO_CONFIG_S_ACKNOWLEDGE     1
        VIRTIO_CONFIG_S_DRIVER          2
        VIRTIO_CONFIG_S_DRIVER_OK       4
        VIRTIO_CONFIG_S_FEATURES_OK	8

特定的设备可以有更多的Status位。

最后reset()用于设备复位到原始状态。

TYPE_VIRTIO_DEVICE
------------------

TYPE_VIRTIO_DEVICE一层提供基本的virtio功能（由TYPE_VIRTIO_XXXX继承），并对外部
提供公共的操作接口，这一层对上一层的接口在分析上一层的使用接口时已经可以看到了。
这里完整整理一下。这一层又分成两层，对上可见的一层包括这样一些接口::

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

PCI传输层
=========

TYPE_VIRTIO_DEVICE只封装了virtio核心接口，但没有包含传输层的封装，我们用一种传
输层(PCI)来感知加上传输层后的概念空间。

前面的继承树可看到，PCI传输层继承TYPE_PCI_DEVICE，和TYPE_VIRTIO_DEVICE不兼容，
而QoM是单继承的，所以PCI的virtio设备被实现成了TYPE_VIRTIO_DEVICE的一个代理，实
现起来是这样的：

.. code:: c

   static VirtioPCIDeviceTypeInfo my_virtio_pci_proxy_info = {
     .base_name     = MY_PROXY_TYPE_NAME "-base",
     .generic_name  = MY_PROXY_TYPE_NAME,
     .transitional_name      = MY_PROXY_TYPE_NAME "-transitional",
     .non_transitional_name  = MY_PROXY_TYPE_NAME "-non-transitional",
     .instance_size = sizeof(struct BBoxProxyState),
     .instance_init = my_proxy_init,
     .class_init    = my_proxy_class_init,
   };

   static void my_register_types(void)
   {
     virtio_pci_types_register(&my_virtio_pci_proxy_info);
   }
   type_init(my_register_types)

virtio_pci_types_register()是register_type_static的封装，同时注册了多个相互继
承的对象，但基本可以认为主要名字是.gnereric_name的类的封装，下面的那些回调函数
这是针对这个类的，我们这里不深入细节。

.. note::

  transitional那个概念是用于表示是否支持PCIe的，如果是non-transitional，就仅支
  持PCI标准，不支持PCIe。

PCIE的BAR空间，中断等设计都代理给这个类，从而实现整个PCI之上的传输层。而真正的
驱动要做的是把这个PCI设备的行为代理到一个真正的TYPE_VIRTIO_DEVICE设备，像这样
：

.. code-block:: c

   static void my_proxy_realize(VirtIOPCIProxy *vpci_dev, Error **errp) {
     MyProxyState *dev = BBOX_PROXY(vpci_dev);
     DeviceState *vdev = DEVICE(&dev->the_real_virtio_device);

     qdev_realize(vdev, BUS(&vpci_dev->bus), errp);
   }

   static void my_proxy_init(Object *obj)
   {
      MyProxyState *s = MY_PROXY(obj);

      virtio_instance_init_common(obj, &s->impl, sizeof(s->impl), BBOX_TYPE_NAME);
    }

   static void my_proxy_class_init(ObjectClass *klass, void *data)
   {
     DeviceClass *dc = DEVICE_CLASS(klass);
     PCIDeviceClass *pcidev_k = PCI_DEVICE_CLASS(klass);
     VirtioPCIClass *vpci_k = VIRTIO_PCI_CLASS(klass);

     pcidev_k->vendor_id = ...;
     pcidev_k->device_id = ...;
     pcidev_k->revision = ...;
     pcidev_k->class_id = ...;
     vpci_k->realize = my_proxy_realize;
   }

在这个proxy的class_init中，我们原样设置pci的vendor_id等信息，但如果你的Guest中
需要用Linux的virtio-pci驱动，你这里的vendor_id就需要匹配redhat的PCI驱动，
device_id也必须落在这个驱动支持的范围内，否则你只能整个协议自己写了。

但realize要注意了，要用PCIDeviceClass的realize，不能覆盖DeviceClass的realize，
否则proxy自己就没法初始化了。

而在instance_init中，除了做一般你自己希望做的初始化，最终要的是要用
virtio_instance_init_common()创建真正的virtio设备，这样proxy的传输层才这个设备
关联起来，当PCI Proxy被guest访问的时候，才转化为virtio的上层语义。

而在realize的时候，还要一个关键问题需要做：你要主动调用qdev_realize()把那个真
virtio设备的bus实例化了，否则这个真virtio设备会没有总线。

Guest
=====

再看看Guest一侧Linux的概念空间。Guest一侧包括两层，传输层和协议层。传输层对应
virtio标准中定义的三种传输层，呈现为PCI，Platform，CCW等设备。比如PCI传输层就呈
现为一个pci的驱动，它用通用的PCI方法发现virtio设备，匹配到Redhat的VendorID，然
后就直接用传输层协议找到设备，用register_virtio_device()创建virtio设备。

另一层是协议层，这一层的驱动匹配register_virtio_device()创建的设备，根据类似PCI
device_id表一样的virtio_device_id表来匹配具体的设备，其他行为基本上就和其他设备
驱动一样了。

这个驱动主要包含这些回调：

.. code-block:: c

   static struct virtio_driver kenny_bbox_drv = {
       ...
       .id_table = id_table,
       .validate = my_validate,
       .probe = my_probe,
       .remove = my_remove,
       .config_changed = my_config_changed,
   };

其中validate是给驱动一个机会判断是否支持这个设备，config_changed用于对端通知配
置更改，而关键的probe主要就是用virtio_cread()读配置，创建vq，并在初始化成功后
，通过virtio_device_read()把这个设备的status设置到DRIVER_OK的状态，两端的状态
对齐成功后，就可以发消息了。

发消息一般分两步，一步是用virtqueue_add_xxx()系列函数把数据写入两者的bd队列，第
二步是用virtqueue_kick()通知对端取取。

收消息通过创建virtqueue时指定的函数回调，这个有可能在中断上下文中（取决与传输
层的实现），里面用virtqueue_get_buf()读，当然你也可以像其他驱动那样，raise一个
softirq来读。
