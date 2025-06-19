.. Kenneth Lee 版权所有 2020-2025

:Authors: Kenneth Lee
:Version: 1.0

PCI/PCI-E
*********

PCI/PCI-E本质上就是一个代理了很多设备的设备。所以它才有那些BDF的复杂概念，好像
很灵活，但如果我们从地址分配这个角度看，每个PCI/PCIE根桥就是一个平台设备，这个
平台设备有自己的MMIO空间，它的所有动态协议，不过是对这个空间的重新分配（基于设
备对应的Bus-Device-Function）。

所以PCI/PCIE根桥的创建本质上分配一个MMIO空间，并用PCI/PCIE作为这个MR的管理设备
而已。一般套路是：

1. 创建一个PCI/PCIE设备作为Root Bridge，比如TYPE_GPEX_HOST（General PCI EXpress）。

2. 创建ECAM空间（配置空间）
   * mb = sysbus_mmio_get_region()
   * mem_region_init_alias(alias...)
   * memory_region_add_subregion(system_memory, addr, alias)

3. 创建BAR空间
   * 同2

剩下的事情就是TYPE_GPEX_HOST驱动的问题了。

.. note::

   我们这里快速补充一下PCI/PCIE上的基本概念：

   在谈PCI/PCIE的时候，Host表示CPU子系统，Host Bridge表示把CPU和PCI/PCIE总线连
   起来的那个IP。这个IP包括三个功能：Bus Master，Bus Target，以及Configure
   Access Generation。

TYPE_GPEX_HOST的继承树结构：::

  DEVICE <- SYS_BUS_DEVICE <- PCI_HOST_BRIDAGE <- PCIE_HOST_BRIDGE <- GPEX_HOST 

中断的行为类似，先为整个RP分配中断，然后用gpex_set_irq_num()建立PCIE局部irq和全
局irq的关系即可。

PCI/PCI-E驱动
=============

前面是全系统的PCI桥的概念，我们用一个PCI设备的backend来看具体的backend的写法：

.. code-block:: C

   static void my_class_init(ObjectClass *oc, void *data) {
     PCIDeviceClass *k = PCI_DEVICE_CLASS(oc);
     k->realize = my_realize;
     k->vendor_id = MY_VENDOR_ID;
     k->device_id = MY_DEVICE_ID;
     k->revision = MY_REVISION;
     k->class_id = PCI_CLASS_XXXX;
   }

   static const TypeInfo my_pci_device_info = {
     .name          = "my-pci-device"
     .parent        = TYPE_PCI_DEVICE,
     .class_init    = my_class_init,
     .interfaces    = {
       { INTERFACE_CONVENTIONAL_PCI_DEVICE },
       { },
     };
   };

这个和其他类没有什么区别，只是父类设置成了TYPE_PCI_DEVICE，在类初始化的时候把
父类的基本属性都设置类（vendor id等），realize中可以调用pci模块提供的比如::

    pci_config_set_interrupt_pin()/msi_init(),
    pci_register_bar()

这些函数，创建相应的pci资源，剩下的工作，留给父类去做就可以了。
