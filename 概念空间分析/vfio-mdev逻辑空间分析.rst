.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

vfio-mdev逻辑空间分析
*********************

最近评审了一个基于vfio-mdev的解决方案，发现该作者对这个逻辑空间的理解有问题，我
通过本文来解释一下整个vfio逻辑空间是什么样的。

先快速对vfio的概念进行扫盲。这个扫盲的目的不是详细介绍什么是VFIO，而是给对没有
VFIO的读者一个入门的指引，或者一个暂时理解本文上下文的空间；也是给已经有经验的
读者一个能和我对齐的基础表述。

VFIO是Linux Kernel UIO特性的升级版本。UIO的作用是把一个设备的IO和中断能力暴露给
用户态，从而实现在用户态对硬件的直接访问。它的基本实现方法是，当我们probe一个设
备的时候，通过uio_register_device()注册为一个字符设备/dev/uioN，用户程序通过对
这个设备mmap访问它的IO空间，通过read/select等接口等待中断。

UIO的缺点在于，用户态的虚拟地址无法直接用于做设备的DMA地址（因为在用户态无法知
道DMA内存的物理地址），这样限制了UIO的使用范围。基本上UIO现在只能用于做工控卡这
种IO量不大，可以直接把内存地址拷贝到IO空间的场景（相当于不做DMA）。我们有人通过
UIO设备自己的ioctl来提供求物理地址的机制，从而实现DMA，但这种方案是有风险的，因
为你做ioctl求得的物理地址，可能因为swap而被放弃，就算你做gup，但gup只保证物理内
存不被释放，不能保证vma还指向这个物理页，要保证后者需要vm_pin这样的解决方案，但
vm_pin根本就没有能够上传主线。

这里提到的UIO的缺点，基本上拒绝了大流量IO设备使用该机制提供用户空间访问的能力了
。

VFIO通过IOMMU的能力来解决这个问题。IOMMU可以为设备直接翻译虚拟地址，这样我们在
提供虚拟地址给设备前，把地址映射提供给VFIO，VFIO就可以为这个设备提供页表映射，
从而实现用户程序的DMA操作。

背负提供DMA操作这个使命，VFIO要解决一个更大的问题，就是要把设备隔离掉。在Linux
的概念中，内核是可信任的，用户程序是不可信任的，如果我们允许用户程序对设备做DMA
，那么设备也是不可信任的，我们不能允许设备访问程序的全部地址空间（这会包括内核
），所以，每个设备，针对每个应用，必须有独立的页表。这个页表，通过iommu_group承
载（iommu_group.domain)，和进程的页表相互独立。进程必须主动做DMA映射，才能把对
应的地址映射写进去。

所以VFIO的概念空间是container和group，前者代表设备iommu的格式，后者代表一个独立
的iommu_group(vfio中用vfio_group代表），我们先创建container，然后把物理的
iommu_group绑定到container上，让container解释group，之后我们基于group访问设备（
IO，中断，DMA等等）即可。

这个逻辑空间其实是有破绽的，iommu_group是基于设备来创建的，一个设备有一个
iommu_group（或者如果这个设备和其他设备共享同一个IOMMU硬件，是几个设备才有一个
iommu_group），那如果我两个进程要一起使用同一个设备呢？基于现在的架构，你只能通
过比如VF（Virtual Function，虚拟设备），在物理上先把一个设备拆成多个，然后还是
一个进程使用一个设备。这用于虚拟机还可以，但如果用于其他功能，基本上是没戏了。

再说，VF功能基本都依赖SR-IOV这样的实现，也不是你想用就能用的。

这我们就要引出VFIO-mdev（以下简称mdev）了。mdev本质上是在VFIO层面实现VF功能。在
mdev的模型中，通过mdev_register_device()注册到mdev中的设备称为父设备（
parent_dev），但你用的时候不使用父设备，而是通过父设备提供的机制（在sysfs中，后
面会详细谈这个）创建一个mdev，这个mdev自带一个iommu_group，这样，你有多个进程要
访问这个父设备的功能，每个都可以有独立的设备页表，而且互相不受影响。

所以，整个mdev框架包括两个基本概念，一个是pdev（父设备），一个是mdev（注意，我
们这里mdev有时指整个vfio-mdev的框架，有时指基于一个pdev的device，请注意区分上下
文）。前者提供设备硬件支持，后者支持针对一个独立地址空间的请求。

两者都是device(struct device)，前者的总线是真实的物理总线，后者属于虚拟总线mdev
，mdev上只有一个驱动vfio_mdev，当你通过pdev创建一个mdev的时候，这个mdev和
vfio_mdev驱动匹配，从而给用户态暴露一个普通vfio设备的接口（比如platform_device
或者pci_device）的接口。

换句话说，如果一个设备需要给多个进程提供用户态驱动的访问能力，这个设备在probe的
时候可以注册到mdev框架中，成为一个mdev框架的pdev。之后，用户程序可以通过sysfs创
建这个pdev的mdev。

pdev注册需要提供如下参数：::

        struct mdev_parent_ops {
                struct module   *owner;
                const struct attribute_group **dev_attr_groups;
                const struct attribute_group **mdev_attr_groups;
                struct attribute_group **supported_type_groups;
                int     (*create)(struct kobject *kobj, struct mdev_device *mdev); 
                int     (*remove)(struct mdev_device *mdev); 
                int     (*open)(struct mdev_device *mdev); 
                void    (*release)(struct mdev_device *mdev);
                ssize_t (*read)(struct mdev_device *mdev, char __user *buf,
                                size_t count, loff_t *ppos); 
                ssize_t (*write)(struct mdev_device *mdev, const char __user *buf,
                                 size_t count, loff_t *ppos);
                long    (*ioctl)(struct mdev_device *mdev, unsigned int cmd, 
                                 unsigned long arg);
                int     (*mmap)(struct mdev_device *mdev, struct vm_area_struct *vma);
        };

其中三个attribute_group都用于在sysfs中增加一组属性。device本身根据它的bus_type
，就会产生一个sysfs的属性组（所谓属性组就是sysfs中的一个目录，里面每个文件就是
一个“属性”，文件名就是属性名，内容就是属性的值），假设你的pdev是
/sys/bus/platform/devices/abc.0，那么这三个attribute_group产生的属性分别在：

dev_attr_groups：/sys/bus/platform/devices/abc.0下

mdev_attr_groups：/sys/bus/platform/devices/abc.0/<mdev_uuid>下，
/sys/bus/mdev/devices中有这个设备的链接

supported_type_groups：/sys/bus/platform/devices/abc.0/mdev_supported_types/下
，里面有什么属性是框架规定的，包括：

1. name：设备名称

2. available_instances：还可以创建多少个实例

3. device_api：设备对外的接口API标识

这些参数支持具体用户态驱动如何访问这个设备，pdev的驱动当然可以增加更多。mdev框
架在这个目录中还增加如下属性：

1. devices：这是一个目录，链接向所有被创建的mdev

2. create：向这个文件中写入一个uuid就可以创建一个新的mdev，实际上产生对
   mdev_parent_ops.create()的回调

mdev_parent_ops的其他回调，都是支持被pdev创建的mdev设备本身的文件访问的。对它的
read/write/mmap本质上是对设备IO空间的访问，如果你要模拟一个platform设备，就要支
持这个platform设备的io_resource空间的访问（这个通过container的ioctl来获得），如
果你要模拟一个pci设备，则可以直接模拟一个配置空间的访问，用这个配置空间返回BAR
空间的地址，之后支持对BAR空间的访问即可。如果你执行DMA，则通过mdev下的
vfio_group找到它对应的vfio_group，然后用一般vfio的方法来做DMA映射即可。

mdev的类型和pdev的类型是完全无关的，甚至可以不是任何设备类型（如果你不需要用于
qemu一类的虚拟化方案的话），所以，没有必要把这个设备类型和pdev本身的类型关联在
一起。

mdev这个模型建得最不好的地方是，create的时候只能传进去一个uuid，不能传进去参数
，这样如果我创建的设备需要参数怎么办呢？那就只能创建以后再设置了，这增加了“创建
以后没有足够资源提供”的可能性），不过看起来，大部分情况我们是可以接受这个限制的
。
