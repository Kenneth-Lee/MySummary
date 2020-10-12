.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

IOMMU的现状和发展
*****************

本文给合作伙伴介绍Linux IOMMU子系统的发展情况，作为我们现在一个相关设计思路的背
景。我会尽量写得通用，但可能关注的重点都是讨论时问得比较多的问题，请其他读者谅
解。

话说，盘古开天的时候，设备访问内存（DMA）就只接受物理地址，所以CPU要把一个地址
告诉设备，就只能给物理地址。但设备的地址长度还比CPU的总线长度短，所以只能分配低
地址来给设备用。所以CPU这边的接口就只有dma=dma_alloc(dev, size)，分配了物理地址
，然后映射为内核的va，然后把pa作为dma地址，CPU提供给设备，设备访问这个dma地址，
就得到内存里面的那个数据了。

后来设备做强了，虽然地址总线不长，但可以带一个页表，把它能访问的有限长度的dma地
址转换为和物理空间一样长的物理地址。这样就有了dma=dma_map(dev, va)。这样，其实
我们对同一个物理地址就有三个地址的概念了：CPU看到的地址va，设备看到的地址dma，
和总线看到的pa。

设备带个页表，这不就是mmu吗？于是，通用的iommu的概念（硬件上）就被发明了。所以
dma_map(dev, va)，在有iommu的设备上，就变成了对iommu的通用页表操作。
iova=iommu_alloc(), iommu_map(domain, iova, pa);

这里我们发现了两个新概念，一个是iova，这个很好理解，就是原来的dma地址了（io的va
嘛），另一个是domain，这本质是一个页表，为什么要把这个页表独立封装出来，这个我
们很快会看到的。

我这个需要提醒一句，iommu用的页表，和mmu用的页表，不是同一个页表，为了容易区分
，我们把前者叫做iopt，后者叫pt。两者都可以翻译虚拟地址为物理地址，物理地址是一
样的，都是pa，而对于va，前者我们叫iova，后者我们叫va。

又到了后来，人们需要支持虚拟化，提出了VFIO的概念，需要在用户进程中直接访问设备
，那我们就要支持在用户态直接发起DMA操作了，用户态发起DMA，它自己在分配iova，直
接设置下来，要求iommu就用这个iova，那我内核对这个设备做dma_map，也要分配iova。
这两者冲突怎么解决呢？

dma_map还可以避开用户态请求过的va空间，用户态的请求没法避开内核的dma_map的呀。

VFIO这样解决：默认情况下，iommu上会绑定一个default_domain，它具有
IOMMU_DOMAIN_DMA属性，原来怎么弄就怎么弄，这时你可以调用dma_map()。但如果你要用
VFIO，你就要先detach原来的驱动，改用VFIO的驱动，VFIO就给你换一个domain，这个
domain的属性是IOMMU_DOMAIN_UNMANAGED，之后你爱用哪个iova就用那个iova，你自己保
证不会冲突就好，VFIO通过iommu_map(domain, iova, pa)来执行这种映射。

等你从VFIO上detach，把你的domain删除了，这个iommu就会恢复原来的default_domain，
这样你就可以继续用你的dma API了。

这种情况下，你必须给你的设备选一种应用模式，非此即彼。

很多设备，比如GPU，没有用VFIO，也会自行创建unmanaged的domain，自己管理映射，这
个就变成一个通用的接口了。

好了，这个是Linux内核的现状（截止到4.20）。如果基于这个现状，我们要同时让用户态
和内核态都可以做mapping的话，唯一的手段是使用unmanaged模式，然后va都从用户态分
配（比如通过mmap），然后统一用iommu_map完成这个映射。

但实际上，Linux的这个框架，已经落后于硬件的发展了。因为现在大部分IOMMU，都支持
多进程访问。比如我有两个进程同时从用户态访问设备，他们自己管理iova，这样，他们
给iommu提供的iova就可能是冲突的。所以，IOMMU硬件同时支持多张iopt，用进程的id作
为下标（对于PCIE设备来说，就是pasid了）。

这样，我们可以让内核使用pasid=0的iopt，每个用户进程用pasid=xxx的iopt，这样就互
相不会冲突了。

为了支持这样的应用模式，ARM的Jean Philipse做了一套补丁，为domain增加pasid支持。
他的方法是domain上可以bind多个pasid，bind的时候给你分配一个io_mm，然后你用
iommu_sva_map()带上这个io_mm来做mapping。

这种情况下，你不再需要和dma api隔离了，因为他会自动用pasid=0（实际硬件不一定是
这样的接口，这只是比喻）的iopt来做dma api，用其他pasid来做用户态。这时你也不再
需要unmanaged的domain了。你继续用dma的domain，然后bind一个pasid上去即可。

但Jean这个补丁上传的时候正好遇到Intel的Scalable Virtual IO的补丁在上传，Intel要
用这个特性来实现更轻量级的VFIO。原来的VFIO，是整个设备共享给用户态的，有了pasid
这个概念，我可以基于pasid分配资源，基于pasid共享给用户态。但Jean的补丁要求使用
的时候就要bind一个pasid上来。但VFIO是要分配完设备，等有进程用这个设备的时候才能
提供pasid。

为了解决这个问题，Jean又加了一个aux domain的概念，你可以给一个iommu创建一个
primary domain，和多个aux domain。那些aux domain可以晚点再绑定pasid上来。

后面这个变化，和前面的接口是兼容的，对我们来说都一样，我们只要有pasid用就可以了
。
