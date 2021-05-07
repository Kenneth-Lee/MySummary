.. Kenneth Lee 版权所有 2017-2021

:Authors: Kenneth Lee
:Version: 1.1

Linux iommu和vfio概念空间解构
*****************************

最近和一些硬件和相关驱动设计的同学讨论SMMU的设计需求，双方讨论的空间不太一致，
我写一个文档澄清一下这些概念。

我们首先得厘清两个概念，当我们说SMMU的时候，硬件设计同学心中是那个进行设备地址
翻译，做DMA操作的那个硬件。软件驱动同学心中是控制SMMU硬件的那个软件。你们之间唯
一的接口是：中断，配置空间和内存，没有其他了。所以，当我们讨论这个问题的时候，
一定首先分清楚对方在说的是哪个概念空间的概念，因为两者是不一样的。硬件的同学说“
设备发出的VA”，包括Substream ID和软件指配给它VA地址，这个地址远远比64位长。但软
件指配地址的时候，可不认为自己发出了Substream ID的。

本文要讨论的是软件的概念空间，所以，我们先抽象一下硬件的模型：

SMMU的作用是把CPU提交给设备的VA地址（软件概念的VA），直接作为设备发出的地址，变
成正确的物理地址，访问到物理内存上。

MMU通过页表完成这个翻译，SMMU也一样，但SMMU的页表比MMU复杂得多，这受两个要素限
制：

第一，一个SMMU控制器可能有多个设备连着，两个设备互相之间可能不会复用同一个页表
，需要区分。SMMU用stream id来做这个区分

第二，一个设备可能被多个进程使用。多个进程有多个页表，设备需要对此进行区分。
SMMU通过substream id来进行区分

这样，设备发出一个地址请求，它的地址就包括stream id, substream id和VA三个部分。
前两者定位一个类似MMU的页表体系，后者的执行一个类似MMU的翻译过程。

要SMMU硬件正确动作，就需要CPU（就是软件了）给它提供正确的信息，用我以前提过的
DFD方法就可以把对应数据模型的充要性建立出来（注意下面这个不是DFD，它是基于AID的
一个数据充要性说明）：

        .. figure:: _static/smmu1.jpg

至于很多人想引入到这个模型的“虚拟化”的概念，我认为你急了，虚拟化的概念在MMU的页
表翻译机制中是自恰的，根本没有必要引入到这里来。

好了，现在轮到软件。软件的概念空间就比这个概念复杂得多了，这是因为软件要扭合多
个硬件平台的意见，有人DMA是64位的，但还有人是32位的啊。而且，软件是有版本概念的
，每个版本都和原来有偏离（我这里用主线Linux内核4.11来作为分析对象），而且都有多
个硬件厂商的角力，我们不但要看到现在如何，还要看到未来的走向。

我们先抛开VFIO，首先建立iommu的概念空间：

在Linux的概念空间中，硬件的设备，用device来代表。设备用总线类型bus_type来区分。
比如众所皆知的pci_device，或者没爹没娘的platform_device。smmu控制器，本身是一种
device，对于ARM来说，它现在是一种平台设备。不同总线有什么设备，可以从
/sys/bus/<bus>/devices/目录中全部列出来。

bus_type说明的是发现设备的方法，不表明设备的功能，设备的功能用class来表达，
/sys/class列出了从功能角度对设备的表达。从这个角度来收，smmu是一种iommu class的
设备（之所以不叫smmu而叫iommu，因为intel先上的主线，所以用intel的名字。现在商业
公司开源，主要是抢名称空间，因为名称空间意味着整个行业为谁服务）

所以我们现在有了device和iommu两个概念了。下一步是device和iommu的关联，从硬件的
逻辑空间，应该是每个device有一个指向iommu的指针，但如果软件也这样做，就掩盖了一
个事实：如果两个设备共享同一个streamid，那么修改其中一个设备的页表体系，也就相
当于修改了另一个设备的页表体系。所以，修改页表的最小单位不是设备，而是stream id
。为此，Linux的模型是增加一个iommu_group的概念，iommu_group代表共享同一个
streamid的一组device（表述在/sys/kernel/iommu_group中）。

所以，整个概念空间就是：

从SMMU控制器自身发现的角度：总线扫描发现设备(device）（SMMU是一种
platform_device），设备匹配SMMU驱动（SMMU的驱动是drivers/iommu/arm-smmu*.c），
SMMU驱动probe的时候给自己支持的总线设置bus->iommu_ops，让总线具有了iommu attach
的能力。

设备的SMMU关联：总线扫描发现了一般的设备，总线的发现流程负责调用iommu_ops给这个
设备加上iommu_group，由于iommu_ops指向SMMU驱动，该驱动可以根据设备的配置（比如
DTS或者ACPI中的Topo信息），设置iommu_group的共享关系，并让其指向对应的iommu控制
器。

其中，固件（比如DTS或者ACPI）对Topo和smmu的描述，从软件管理的角度，称为（定义为
）iommu_fwspec，属于device，在device发现的时候就可以生成（比如pcie扫描或者
devicetree/ACPI扫描的时候）。

这样，整个框架的模型就是这样的：

        .. figure:: _static/smmu2.jpg

注意这个图右下角的那个对象，ARM是用arm_smmu_domain来管理驱动和设备之间的关联的
，它为每个domain申请了一个独立的asid（和进程的asid完全无关）。也就是说，ARM认为
，一个group只能服务一个进程。


IOMMU的整个框架，首先提供的是针对设备的DMA能力，也就是说，当我们发起dma_map的时
候，设备定位了streamid和group；group定位了iommu_device和iommu_domain，
iommu_domain定位了asid，这样，硬件要求的全部信息都齐了。

（另，特别说明一下，仅仅这些框架并不能把dma_map导过来，ARM平台是通过一个平台初
始化， arch/arm64/mm/dma-mapping.c，来把两者关联起来的。dma-mapping负责提供全系
统的dma-mapping函数，如果设备的iommu机制存在，就用设备的一套，如果不存在，就用
总线的，如果总线也不存在，就会回到最初的全系统的基本方法）

综合起来，我们可以认为ARM也支持这个概念：一个group就是一个独立的隔离空间，是隔
离的最小单位，如果你希望通过两个asid区分两个设备，你必须想办法建立两个group。

然后我们看VFIO。

VFIO的目的（从SMMU的角度来说）是把设备的DMA能力直接暴露到用户态。这个最初的设想
，我猜是为虚拟化服务的，假设我把一个硬件功能（PF），分解成多个软件化的功能VF，
比如把一张网卡模拟成多张，或者把一个显卡模拟成多个虚拟的显示界面。我就需要让PF
（透过VF）直接看到虚拟机的空间。也就是说，当设备做DMA操作的时候，它必须认知虚拟
空间的地址。这个恰恰就是IOMMU要做的事情，所以VFIO正好就基于iommu的逻辑空间来工
作了。

VFIO本身是driver，或者说严格来说，这个子系统提供了两个driver（更严格来说，现在
有三个，mdev我们晚点来说）：vfio-platform和vfio-pci。他们属于什么总线你们猜都能
猜到。但这两个driver不匹配总线上的任何设备。它的作用是通过device的
override_driver接口（通过/sys直接强行重新绑定一个设备的驱动），让自己成为那个设
备的驱动，在这个驱动中，把这个设备的io空间和iommu_group直接暴露到用户态。

被暴露的设备，通过vfio_group的形式暴露给用户程序。这个应用过程大致是这样的：::

        container = open("/dev/vfio/vfio", O_RDWR);
        group = open("/dev/vfio/26", O_RDWR);
        ioctl(group, VFIO_GROUP_SET_CONTAINER, &container);
        ioctl(container, VFIO_SET_IOMMU, VFIO_TYPE1_IOMMU);
        ioctl(container, VFIO_IOMMU_MAP_DMA, &dma_map);

很明显，这个概念空间包括container和group两个概念，vfio_container是访问的上下文
，vfio_group是vfio对iommu_group的表述。

如果我们再看仔细一点，我们应该要注意到，这里还有一个针对iommu_group的driver，这
个driver决定如何使用IOMMU（前面过程中的VFIO_SET_IOMMU的概念），现在只有两个
driver：vfio-iommu-type1和iommu-vfio-powerpc。但很明显，你可以有更多的type。

综合起来，这个名称空间是这样的：

        .. figure:: _static/smmu3.jpg

最后看看vfio-mdev。vfio-platform和vfio-pci都是针对静态设备的，前者描述在DTS或者
ACPI DSDT表中。后者描述在PCI的硬件枚举中。但如果我的设备是动态创建出来的呢？比
如我动态让显卡给我创建3个虚拟屏幕，这怎么说？我不可能给DTS/DSDT或者PCI总线动态
增加这个设备吧？mdev就是解决这个问题的。

它的模式是通过mdev_device_create()为某个设备创建一个动态VF创建点，然后你向
/sys/devices/...<you_device>/dev_supported_type/<type>/create中写入一个UUID来动
态创建设备（如何创建看你如何实现create回调函数了）（注2），这个设备的
iommu_group默认是空的（也就是说，你要用其他手段来做DMA），但很明显，你很容易自
己在Create的时候主动创建一个自己的iommu_group，然后设置为你想要的工作模式（注：
当前4.11的代码不行，需要对mdev做一点点修改才行）。之后的事情，就和前面的名称空
间可以拟合了。


综上，我觉得如果要实现一个设备（拥有一个独立的streamid）动态提供多个VF功能，最
简单的办法是把VF创建为mdev，然后人为加入一个iommu_group，并在这个group中创建独
立的asid，这样，是最容易被接受的。


上面的整个表述，有些地方并非实际情况（实际上这些地方都可以Bargain），这也是一个
很多好的架构设计的思维模型：我们看到的“工作量深度”，我们说的“可行”和“不可行”，
不是被当前代码严格限定的，我们是用工作量来限定的。


注1：本文的概念仅仅是工作过程的副产品，不保证正确性。

注2：mdev的总线是mdev_bus_type，所以mdev->dev是被mdev_driver驱动的。但
mdev_device_create本身会在/sys/class/mdev_bus中创建一个母设备的链接，这个不是总
线，而是class，不要被它的名称骗了。mdev如果要给它创建一个独特的iommu_group，就
需要使用总线上的iommu_ops，但mdev_bus_type上是没有设置这个域的，所以不能依靠这
个总线来分配这个空间，要想办法用父类的总线来完成这个功能。

注3: 我们特别补充一下IOMMU中的reserved region的原理。Linux架构中，IOMMU可以通过
get/put/apply_recv_region()控制IOMMU的保留区，保留区表示这片空间不能被使用。通
常用于比如MSI这类应用，在这段空间内，如果设备发出一个IOVA要求翻译，IOMMU硬件要
单独处理它（比如直接变成一个中断）。这个概念在硬件角度很好理解，但在软件角度比
较绕：硬件保留一段IOVA不让动，这好办，映射进行地址分配的时候不要分配这一段就好
了。但如果我把一个进程的空间整体提供交给它翻译，那具体的IOVA不在我的选择范围内
了，我怎么办？比如SMMUv3的MSI的位置在128M的位置（长度为1M），怼在主程序映射区和
heap中间。如果主程序足够大，两者就会有冲突。Linux现在（5.9）其实没有解决方案，
我们需要考虑这两个方向去解决问题：第一，就像ARM这样，这个位置肯定是精心挑选过了
，不容易撞上。第二，在IOMMU->bind_sva的时候进行检查，但这仍是有毛病的，因为mm的
页表维护不经过iommu，这个修改对应代码才能解决。
