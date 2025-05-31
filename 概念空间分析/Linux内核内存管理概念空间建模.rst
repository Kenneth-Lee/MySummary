.. Kenneth Lee 版权所有 2025

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2025-05-30
:Status: Draft

Linux内核内存管理概念空间建模
*****************************

介绍
====

Linux内核的内存管理概念层次和观察视图极多，而且经过长期的历史变化，很容易造成
误解，本文试图理清这些概念的关系。

这个分析基于6.12的主线内核。

Linux内核启动的时候，它已经在使用内存了，它至少认为自己正在占用的代码和静态数
据的内存是可以用的。更多的内存在哪里，它从两个地方获得：

* 内核参数mem=指定
* BIOS说明

有了这些数据，它就有一个内存表，这是一个分段的数据。类似“地址aaa到地址bbb是系
统内存”，“地址cccc到地址dddd是IO空间等等”。这些数据被Linux记录在两个地方：

* memory_resource。这个接口是add_memory_resource()系列函数，这个部分的信息主要
  是用来全局观察用的，至少可以知道整个系统的物理地址空间具体如何分布，是否有重
  叠等等。这个数据在启动后可以从/proc/iomem看到。

* memblock。这个接口是memblock_add()系列函数。每片内存按一个个连续空间的方式保
  存起来，可以通过memblock_alloc()系列函数进行分配。在其他机制没有起作用的时候
  这种分配都被认为内存被reserved了（不能释放的）。等buddy管理系统初始化
  （mem_init)的时候，没有reserved的内存全部交给buddy/slab系统进行管理。这之后
  memblock_alloc()调用就会转化成kalloc()系列调用，被slub系统进行管理。这个数据
  在使能了相关编译选项的时候，可以在debugfs的memblock中查到。

buddy的接口是alloc_pages()系列函数，它提供指数方式分配的页分配接口，要求每次分
配的都是固定的2的某个指数（称为order）个页。它成为伙伴系统，就是因为分配2的3次
方页，可以从2的4次方也分成两份（伙伴）得到，释放的时候只要两个伙伴都释放了，就
可以合并起来作为2的4次方的块使用。这种方法不容易出现碎片。只是通常被要求的大小
大，空间利用率不那么高。

slob/slab/slub算法是buddy之上的实现（三个名字是三代不同的实现，当前版本主要用
slub，但因为这个东西在用户态看到的管理接口叫slab，我们后面统一称为slab）。对外
接口有两部分：

* kmemcache_alloc系列函数
* kmalloc系列函数

这两者都是按固定的大小从buddy分配成order的页再零切成固定大小的小块给其他模块用
的。slab接口的信息可以从/proc/slabinfo文件中获得。

内核模块最基础的设施就是Buddy这个接口，所以我们理解整个内存的概念空间，以这个
部分的概念为中心。

如前所述，Linux已知的内存区域加入到MemBlock中，每个Block会有一个固定的单位，这
个单位在不同的平台是是不一样的，比如在ARM64上，这是128M。这个大小主要受限于管
理成本，这种成本主要体现在Buddy系统所需的线性地址寻址要求，Linux尽量希望内核中
访问的内存的虚拟地址和物理地址可以通过线性变换进行一一对应，如果中间出现空洞，
就会需要多一个基址来表示这一段的截距，就会增加变换的成本，所以，这种128M的选择，
是一种根据具体情况的权衡。

Block
=====

MemBlock模块混用两个概念：这种Block的空间，在一些数据结构或者函数中称为一个
Block或者MemoryBlock，在一些数据结构中称为一个Region。我们在下文中统一称为
Memory Block或者简称Block。

MemBlock中的内存如果没有被分配，就叫Memory，分配出去了，就叫Reserved。每个
Block会被生成一个kobject device，呈现在/sys/bus/memory/devices中，名字叫
memoryXXXX，后面的数字是这个Block的物理地址（以Block的大小为单位）。

MemBlock具有一些控制属性，比如是否允许热插拔等。所以，Linux内存热插拔的单位是
Block，但如果你物理上一个热插拔的单位不止一个Block，可以把他们创建为同一个
group。这样它们会被一体插拔。

在系统启动后，可以通过add_memory_driver_managed()系列函数增加更多的内存。

Node
====

MemBlock还有Node的概念。这个概念和物理地址是正交的，所有的MemBlock在一个物理地
址空间中编址，但不同的Block可以在不同Node上。参考如下例子：

.. figure:: _static/linux_memory_block_node.svg

从物理地址的角度，所有的MemBlock都编址在一个空间中，但不同的空间可以属于不同的
Node。

Node表达的是距离的概念，每个Node包含一组CPU和一组内存，在同一个Node内的，就认
为距离是最短的，到其他不同的Node，有不同的距离。这样Linux调度器可以尽量把应用
的内存和CPU限制在一个Node内，不能在一个Node内，就尽量分布在距离近的Node之间，
这样可以提高效率。

大部分的内存管理接口，都带Node这个概念，允许你在指定的Node上分配内存。

Zone
====

CPU和外设都可能访问内存，访问地址长度不同，就会造成访问能力的不同。所以Linux又
把地址分成了ZONE。比如说，在64位的CPU上，可能它的物理寻址能力是52位（是的，虽
然理论上可以实现64位的物理地址，但现阶段没人需要那么大的物理内存，所以通常CPU
的寻址范围不会是64位的），所以内存编址在52位这个空间上都是可以的，但外设比较简
单，可能只能访问24位以内的地址，所以如果内核要和外设共享内存，就必须分配物理空
间在24位以内的地址。所以，管理内存分配的时候，要决定内存在哪个物理空间内。这个
空间，在Linux中称为Zone。

这种分配又和Node有关，所以Zone属于Node。但其实Zone还是在物理地址空间中统一编址
（不会重复）的。

一些常见的，最基本的ZONE是：

* ZONE_DMA，一般设备能寻址的空间（通常是24位）
* ZONE_DMA32，增强的32位设备能寻址的空间
* ZONE_NORMAL，CPU能寻址的空间

每个Node都可以有自己的，相同类别的ZONE。比如Node 0有一个Block在地址0上，属于
ZONE_DMA，而Node 1上有一个Block在地址128M上，也属于ZONE_DMA。如果你指定Node来
分配内存，它就会找对应那个Node上的DMA ZONE来分配内存。这些分配的内存是可以同时
使用的，因为他们的物理地址不同，只是从不同的Node上发起访问，它们的效率不一样而
已。

Buddy的内存分配函数通过GFP标志说明对ZONE的要求，比如alloc_pages(GFP_DMA)指明必
须在DMA ZONE分配内存。但GFP不一定只说明对Zone的要求，还可以是其他要求，比如
GFP_ATOMIC要求不要进行可以引起调度的操作等。

Zone不需要连续，它可以由多个Region组成，但它确实有首地址（start_pfn），同时它
也有span_pages, present_pages的概念，前者是跨越的空间（包括空洞），后者减去空
洞。它还有一个预留水线的概念，保留部分内存在紧急的时候使用，称为reserved_pages，
present_pages减去reserved_pages，表达为managed_pages。

内核启动的时候时候会打印zone的初始化信息，下面是一个例子：::

 NODE_DATA(0) allocated [mem 0x4fffd9c0-0x4fffffff]
 NODE_DATA(1) allocated [mem 0x5fef3f00-0x5fef653f]
 Zone ranges:
   DMA      [mem 0x0000000040000000-0x000000005fffffff]
   DMA32    empty
   Normal   empty
 Movable zone start for each node
   Node 0: 0x0000000048000000
   Node 1: 0x0000000058000000
 Early memory node ranges
   node   0: [mem 0x0000000040000000-0x000000004fffffff]
   node   1: [mem 0x0000000050000000-0x000000005fffffff]

插入新的memblock后，内核会更新这个结构，但不会再打印了，下面是一个我人为加入的
打印显示的结果：::

 # chmem -e 0x0000003fc8000000-0x0000003fcfffffff
 node[0].zone DMA: from pfn: 40000, span:8000
 node[0].zone DMA32: empty
 node[0].zone Normal: empty
 node[0].zone Movable: from pfn: 48000, span:8000

加入一个新的memblock后(128M），Movable Zone被更新了。

线性区
======

现代CPU支持页表映射，可以设定每个页（通常是4K）从虚拟地址的不同位置指向物理地
址的不同位置。我们把这种映射关系称为乱序映射，使用这种映射，要从虚拟地址获得物
理地址，或者反过来，需要查表，内核中经常要做这种操作，这个非常影响效率。所以
Buddy系统使用线性映射的方式来加速这个查询过程。也就是说，对于每片连续的空间
（称为Section），物理地址pa和虚拟地址的va，总是呈现如下关系：

        va=pa+PAGE_OFFSET。

在这个范围内的va和pa，就称为处于线性区。在线性区内，va和pa可以快速翻译。

由于线性区的存在，32位系统就多了一种ZONE，这种ZONE称为HIGHMEM。它的来源是这样
的：32位的虚拟和物理空间都可以达到最大，4G。但虚拟空间要同时给用户态和内核态使
用，所以如果真的有4G物理空间，那么内核就不可能线性映射全部物理空间。很多实现中，
内核是1G的虚拟空间，最多就只能映射1G的物理空间，其他物理空间内核完全访问不了，
这会导致很多功能都无法实现。为了解决这个问题Linux把内核的虚拟空间分成两部分，
一部分用于线性区，一部分根据需要进行映射，前者用于ZONE_NORMAL，后者用于
ZONE_HIGHMEM。ZONE_NORMAL的空间属于线性区，而ZONE_HIGHMEM属于非线性区。

实际上ZONE_DMA和ZONE_DMA32都属于线性区。这些也可以用作ZONE_NORMAL，所以其实
ZONE_NORMAL只是用于剩下的线性区，这三者都属于线性区，都可以被Kernel的模块使用，
这些ZONE就被统称为KERNEL ZONE（通过alloc_page(GFP_KERNEL)分配）。

要注意：ZONE是物理空间的概念，ZONE_HIGHMEM是一个物理空间的范围，这个限制是虚拟
空间不足造成的，这个这个限制被传递到物理空间是因为我们有线性映射这个要求。这很
容易让我们误会ZONE是个虚拟空间的概念，其实它不是。

对于64位的系统，这个问题就不存在了，比如ARM64的内核空间用64位空间的一半，这也
是EB级别了，现阶段几乎没有什么系统有这么大的物理空间。所以线性区可以覆盖所有物
理内存，这种情况下就没有ZONE_HIGHMEM这个区了。

页
==

Buddy系统提供页的分配功能，这里的页，是页表管理的最小块的大小。现代CPU可以支持
多种页大小，这些大小都是最小块的2的指数倍。Linux中用最小那个作为页的大小。

这也是一个被发展的概念，因为过去的CPU只支持一种页大小，并没有上面这个问题。这
种历史遗留还在代码有体现，会认为这种最小的页，就是唯一的页的存在形式。

比最小页更大的页，在内核中以透明大页（THP，Tranparent Page）或者大页文件系统
（HugePageFS）的形式存在，它们都是Buddy系统之上的设施，而不是Buddy系统提供的接
口。换句话说，你在Buddy系统中分配的永远都是小页的概念，THP和HugePageFS只是对这
些拼接在一起的小页的应用。为了表达一组小页实际被用作了大页，页具有Compound属性，
当一个页是Compound页，它表明它之后的所有小页，都是大页的一部分。这通过
PageCompound(page)检查函数来检查，我们把Compound页称为复合页。

在历史上，内核通过一个全局数组memmap[]保存所有的页的属性（比如上面这个Compound
属性等），alloc_pages()分配一个页，返回的就是这个数据的一个数组项的内容。这就
叫struct page。为了定位这个数组的下标，引入一个概念，pfn，page frame number，
它和物理地址线性相关，所以，我们很容易从物理地址得到pfn，然后从pfn直接查表得到
map。

这样，我们就有两个“页”的概念了，一个是struct page，一个是这个page本身表示的物
理内存。前者是后者的索引。我们常常混用这两个概念，但我们必须知道，这里有两个不
同的实体。当我们需要强调我们说的是索引，我们用struct page这个名字。

在支持稀疏的物理内存分布后，物理空间由多个section组成，memmap也被分布到每个
section（struct mem_section）上，叫section_mem_map。这本质是一个页表一样的
radix结构，我们从物理地址先定位section，然后从section定位section_mem_map，从而
用pfn确定page。这也解释了为什么需要限制memblock的最小大小，因为这被section的大
小影响了。这种情况下，pfn不是简单的section_mem_map的下标，而是一个全局的page表
示，可以通过mem_section和section_mem_map定位page的位置。

.. note::

   section还被另一个要素影响：它需要大于alloc_pages()的最大order表达的范围
   （MAX_ORDER_NR_PAGES）。

mem_map是基于最小页的，对于Compound页来说，这对应多个page。这对使用者很不友好。
所以最近的内核引入了另一个概念：folio。它表示一般意义的页，而不是最小页。这个
概念在数据结构上和struct page是重叠的。也就是说，如果这是一个普通的最小page，
它的数据结构实际上就是struct page。但如果它是一个复合页，它的数据接口会延伸到
后续的struct page上，但如果你拿到后面的page的指针，你也能有办法确定这是一个复
合页的一部分，同时能通过指针值得得到这个复合页的folio的指针。

所以，在概念上，我们用page表示最小页，而用folio表示硬件页表意义上的“页”。

alloc_pages()分配的是page，folio_alloc()分配的是folio，两者其实是可以换用的，
因为你完全可以用folio->page来得到page，也可以用page_folio(folio)得到page。

page和folio通过引用记数管理生命周期，alloc_pages()得到的页，可以通过put_page()
释放，可以通过get_page()增加生命周期。对应也有folio_get/put()函数。

但要注意，这种管理是作用在单个页上的，不是成组的页。也就是说，你只能对
alloc_page()分配的页做这种引用计数。如果你调用alloc_pages()而order不是0，那么
你得到成组的页，这些页不会每个都有引用计数，这种情况下，你只能用free_pages()释
放。或者，你也可以用split_pages把这组页（也称为“高阶页”）分成单个struct page，
这样你就可以一个个管理了。

在线性区分配的页，可以用page_address(page)转化为线性地址，这个转换过程是线性变
换，速度很快。同样page_to_pfn(page)和page_to_phys(page)，分别把page转换为pfn或
者pa，这些转换都是很快的。但如果不在线性区，这种转换需要特别的算法（内核没有固
定的接口做这种转换），所以一般情况内核模块分配空间都用GPF_KERNEL属性，保证总在
线性区进行内存分配。ZONE_HIGHMEM不到极端情形基本上是不会用的。


ZONE_MOVABLE
============

如前所述，在64位系统中，内核线性区已经足够覆盖所有内存了。但由于内存热插拔的需
求的存在（这个需求现在变得很普遍，就算不考虑热插拔的硬件，在虚拟机里面根据需要
动态增加内存的场景也非常普遍），这又造成了另一个ZONE的需求：ZONE_MOVABLE。在这
个区域内的内存可以被移动到其他地方，这样，如果所在的物理地址需要热插拔，上面的
内存可以被迁移到其他区，这样这个区内的Block就可以整个offline。

ZONE_MOVABLE的语义是：这部分空间不分配给GFP_KERNEL（虽然它的物理地址仍可以在线
性区），这样内核肯定不会使用它（实际上ZONE_MOVABLE允许内核用特殊的方法使用，这
个后面再展开），而用户态的内存(又叫LRU内存，LRU是Least Recently Used的缩写，这
是用户态页调度算法的名字）总是可以迁移的，在需要热拔这边内存的时候就可以移走这
些内存。

请注意：ZONE_MOVABLE的内存可以处于线性区，只是它不用于内核，所以不会有内核应用
使用它，所以可以迁移而已。

内核通过如下参数控制不同物理空间的内存，哪些属于ZONE_MOVABLE：

* kernelcore：这个参数决定有多少内存属于KERNEL ZONE（如前所述，这是个虚拟概念，
  表示ZONE_MOVABLE之外的空间有多少）

* movablecore：这个参数决定有多少内存用于ZONE_MOVABLE，这是换一个角度定义
  KERNEL ZONE的内存数量。

* movable_zone：这个参数决定把所有热插入的内存都看作MOVABLE的。

对于热插拔的内存，在/sys/bus/memory/devices/memoryXXX中有一个online的文件，写
入不同的参数可以把这片内存online到不同的zone。这可以动态改变启动的时候预设的参
数。（注：通常我们不会直接操作这些文件，而是通过chmem命令操作memblock，但当前
的chmem版本不支持选择如何加入online文件，所以，这种功能需要直接操作这些文件。）

内存如果加入movable_zone，基本上内核就不会使用它了，只用于用户态的分配。由于
LRU不是线性映射的，物理空间移动到其他地方，只要重新映射就可以了。

内核不能直接使用ZONE_MOVABLE的内存，因为内核使用线性映射，如果直接也迁移了，va
也需要改变，这会导致用户态的应用工作不正常。但内核程序可以在显式知道这一点的情
况下使用它。方法类似这样：::

  struct page *p_movable= alloc_page(GFP_HIGHUSER_MOVABLE);
  lock_page(p_movable);
  __SetPageMovable(p_movable, &movable_mops);
  unlock_page(p_movable);
  
核心就是你必须为这一页提供移动时的回掉函数，从而内核程序主动认知这个地址是会改
变的。如果这个迁移过程失败，这片memblock就不能offline。

如果出现迁移失败，内核会输出失败的页的信息，如果开启了page_owner调试功能，这可
以输出具体是什么地方分配的页导致的迁移失败，这对于定位这部分功能非常有用。

ZONE_DEVICE
===========

ZONE_DEVICE是个占位符，表示这片ZONE用于设备映射，不能用于内存分配。这个ZONE和
内存分配是无关的，就是一个简单的物理地址空间预留。

Slab
====

Slab内存是在页之上进行二次管理的算法，一种用法是用kmem_cache_create()建立一个
固定大小的分配器，以后基于这个分配器分配固定大小的object就可以实现“不够的时候
分配更多的页，整页用完释放整页”。它还能实现一些对象的管理，比如在临时释放的对
象中保留一些信息，下次分配的时候就不需要初始化了，但根本就是一种把页打零的管理
方法。

kmem_cache_create()是针对大量使用固定大小内存的模块的，有些模块只是用少数内存，
可以让所有模块共享一组分配器，这就构成kmalloc()结构。

以上两个概念，结合/proc/slabinfo的具体形式就很容易建立概念：::

  # name            <active_objs> <num_objs> <objsize> <objperslab> <pagesperslab> : tunables <limit> <batchcount> <sharedfactor> : slabdata <active_slabs> <num_slabs> <sharedavail>
  ext4_groupinfo_1k     23     23    176   23    1 : tunables    0    0    0 : slabdata      1      1      0
  p9_req_t               0      0    160   25    1 : tunables    0    0    0 : slabdata      0      0      0
  ip6-frags              0      0    184   22    1 : tunables    0    0    0 : slabdata      0      0      0
  RAWv6                 26     26   1216   26    8 : tunables    0    0    0 : slabdata      1      1      0
  UDPv6                  0      0   1344   24    8 : tunables    0    0    0 : slabdata      0      0      0
  tw_sock_TCPv6          0      0    248   33    2 : tunables    0    0    0 : slabdata      0      0      0
  request_sock_TCPv6      0      0    312   26    2 : tunables    0    0    0 : slabdata      0      0      0
  TCPv6                  0      0   2496   13    8 : tunables    0    0    0 : slabdata      0      0      0
  nf_conntrack_expect      0      0    208   39    2 : tunables    0    0    0 : slabdata      0      0      0
  nf_conntrack           0      0    256   32    2 : tunables    0    0    0 : slabdata      0      0      0
  ...
  kmalloc-8k            20     20   8192    4    8 : tunables    0    0    0 : slabdata      5      5      0
  kmalloc-4k            72     72   4096    8    8 : tunables    0    0    0 : slabdata      9      9      0
  kmalloc-2k           176    176   2048   16    8 : tunables    0    0    0 : slabdata     11     11      0
  kmalloc-1k           566    576   1024   32    8 : tunables    0    0    0 : slabdata     18     18      0
  kmalloc-512          603    672    512   32    4 : tunables    0    0    0 : slabdata     21     21      0
  kmalloc-256          667    736    256   32    2 : tunables    0    0    0 : slabdata     23     23      0
  kmalloc-128          576    576    128   32    1 : tunables    0    0    0 : slabdata     18     18      0
  ...

这个列表前半段就是每个模块各自的slab，后半段就是kmalloc给各个模块公共的slab，
概念是一目了然的。
