.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

用户态DMA的问题
****************

Linux的安全模型分两层，用户和内核，用户是不可信任的，内核是可信任的。像这样：

        .. figure:: _static/OS隔间1.png

这种分层模型其实已经比较落后了（但也比较实用），现在更推崇的模式是分隔（而不是
分层），一个身份访问一个隔间，这样不会导致“只要你获得root权限，就可以对系统为所
欲为”。

        .. figure:: _static/OS隔间2.png

但分隔技术灵活性太高，不容易有共识，所以到现在为止，这种方法也不成熟。只是作为
分层技术的补充。

隔间的一大技术是微内核化。这里“微内核”的含义和它的最初定义不完全一致。更多的是
指把内核的功能移到用户态，让每个用户态的程序使用独立的权限。这样，虽然内核仍具
有最高的权限。但因为大部分操作不需要在内核中进行，我们就可以把权限控制聚集在一
个或者一组进程的内部了。

        .. figure:: _static/OS隔间3.png

用户态驱动因此成为其中一个需求了。通过用户态驱动，我们可以把一个设备（或者这个
设备的其中一部分）分配给一个进程，这样，对这个设备的控制就可以完全限制在这个进
程的内部了。

用户态进程也可以在一定程度上提高设备访问的效率。想象一下，原来你需要把用户空间
的内存拷贝到内核，然后再从内核拷贝到设备上，现在让你直接从用户空间拷贝的设备上
，这个效率岂不是可以大大提高？：

        .. figure:: _static/OS隔间4.png

本文要讨论的问题是：怎么才能从用户一侧对设备发起DMA？

所谓DMA，本质上就是设备访问内存。让设备访问内存，我们有如下要求：

1. 提供设备可以认知的内存地址。可以是物理地址（这个物理地址必须在设备可以访问的
   范围内，如果设备地址比CPU地址短，CPU就必须把地址拷贝到设备可以认知的地址内，
   这是Linux DMA_ZONE和Bouncing Buffer解决的问题），也可以是虚拟地址（后者需要
   设备有IOMMU支持，即设备可以做虚拟地址翻译）

2. 物理内存必须在位（考虑到虚拟内存可能被交换到磁盘上的情况）

3. CPU对内存的更新必须对设备可见（考虑到CPU的Cache系统和设备的Cache不一定互相认
   知）

无论我们在内核态做DMA还是在用户态做DMA，这三个要求都是必须的。但内核做起来比较
容易，因为Linux内核可以分配“必然在位”的内存，也可以任意进行cache操作，保证CPU的
更新必然对设备可见。但用户态就不一定了。

Cache问题是个死问题，要让CPU对内存的更改对设备可见，我们要不做一次系统调用（这
个有软件性能成本），强刷过去。要不就让设备和CPU间实现Cache-Coherent（这个有硬件
性能成本）。所以，这个没有什么可说的。

地址范围这个问题也是一样的。所以，这两个问题我更看好的思路是让硬件直接支持IOMMU
和CC总线，这样这两个问题就不存在了。

现在比较麻烦是虚拟内存的问题。如果内存不在位，设备访问的时候就会缺页，设备又不
知道这个缺掉的页应该怎么补（这是Linux内核handle_mm_fault负责管理的），现在的解
决思路是SVM（Shared Virtual Memory）：让设备产生一个缺页中断给CPU，CPU通过
handle_mm_fault来补上这个页，在这期间设备就只能等着。很容易想象，这样的设计在不
同的场景上有利有弊——但这恰恰反映了它是值得做的（因为特定的场景有利）。

SVM的问题是现在Linux的主线只有Intel平台支持，而且——没有用户！也就是说，Intel自
己都不一定用，所以这个方法到底是有益还是无益，其实这得看发展。

更成熟的方法是直接在内核中分配物理内存，然后让用户态驱动直接填到这个内存中。很
多GPU驱动都是用这种方法，但这些方法大部分都上不了Linux主线。因为这样基本上是把
Linux做成一个专用系统了。按Linux的设计理念，专用系统你在家里用就好了，没有必要
上传上来。

现在在Linux主线更被认可的方法是人工把虚拟地址的物理内存pin在位置上。这样，无论
你用的是什么地址，只要完成了pin的操作，这个地址就可以用于DMA。pin内存对比SVM来
说，可能导致pin了多余的内存部分，但如果是IO密集的场景，这种情况很可能也不存在。

但pin物理内存在Linux的实现上有很多具体的问题要解决。Linux内核提供的pin机制是gup
（参考mm/gup.c），这是get_user_pages系列函数的缩写。它的作用是把某个进程的虚拟
地址进行预缺页，把物理页表分配出来，然后做get_page()，增加这个page的使用计数，
这样这个page就不会被释放，设备就可以一直访问这个物理页了。

但gup是有严格限制的，在gup.c中，你可以看到这个表述：::

        /*
         *...
         * Must be called with mmap_sem held for read or write.
         *
         * get_user_pages walks a process's page tables and takes a reference to
         * each struct page that each user address corresponds to at a given
         * instant. That is, it takes the page that would be accessed if a user
         * thread accesses the given user virtual address at that instant.
         *
         * This does not guarantee that the page exists in the user mappings when
         * get_user_pages returns, and there may even be a completely different
         * page there in some cases (eg. if mmapped pagecache has been invalidated
         * and subsequently re faulted). However it does guarantee that the page
         * won't be freed completely. And mostly callers simply care that the page
         * contains data that was valid *at some point in time*. Typically, an IO
         * or similar operation cannot guarantee anything stronger anyway because
         * locks can't be held over the syscall boundary.
         *...
        */

请注意这个函数的使用要求，他必须在mmap_sem锁住的范围内使用，换句话说，你必须做
一个系统调用，然后在这个系统锁住mmap_sem，然后才调用gup，接着做你的DMA，并且，
必须等待这个DMA完成，然后你通过put_page()释放gup，并对mmap_sem解锁，然后才能从
系统调用中返回——我能做这么复杂的动作，我还pin毛啊？

gup限制这么大，核心原因在于，gup只是把page pin住了，可没有把vma pin住。参考下面
这幅图：

        .. figure:: _static/OS隔间5.png
        
gup做了两个动作，第一是分配了一个page（如果没有的话）给进程，让进程的vma指向这
个page（这会导致这个页的索引加1）。第二是gup自己也给这个page的索引加1。这样，这
个page一般情况下就释放不了了，设备可以很安全地对这个内存进行读写。

问题是，这个动作并没有保证进程的vma必须一直指向这个page啊，假设系统觉得内存效率
不够，需要清理一下内存。它可以把这个vma的页放弃，这样这个物理页的索引会减1（不
会引起释放，因为还是gup本身的索引），同时vma的指针没了。等你设备完成操作了，通
知进程可以使用物理页中的数据，进程再访问这个虚拟地址（会使用这个vma），这时发生
缺页，系统会重新分配一个页给这进程，你就根本拿不到设备返回的数据了：

        .. figure:: _static/OS隔间6.png

所以，正如我在前面一个文档（Linux Socket 0拷贝特性）中说的，如果你只是发送，这
是没有问题的，因为你的用户进程根本不需要访问原来的页，但如果你还要收，这就有问
题了。

我做了一个例子程序（等我有空把Patch发出来），让一个进程通过系统调用gup一片内存
，然后对这片内存做madvise(MADV_DONTNEED)，通知系统我暂时不需要这片内存了，然后
我再通知内核在gup的页里填东西，之后我访问这片内存，就拿不到内核提供的数据了。

这个实验证明了，gup在离开系统调用后，确实是不安全的。RDMA的人在2014年尝试推一个
特性叫VM_PINNED，但出了一个RFC就没有弄了。我向该作者了解了一下背景，他说主要是
没有时间做。但我看是没有那么简单，这个问题对RDMA是致命的。因为RDMA恰恰需要通过
在用户态提供一个接收内存，等待对端填充它，如果不能把page和vma同时pin住，RDMA驱
动就只能做一次拷贝，性能就很难提上去了。这种情况都不优先搞这个特性，背后有故事
。

这期间其实更值得关注的问题是，Redhat的VFIO接口的DMA操作也是用gup来做pin操作的，
也就是他们也有一样的问题。但VFIO的接口被Linux主线接受了。我问了对应作者怎么看
VM_PINNED的问题，他的答复是：“我经过大量测试，没有遇到这个问题”。哈，所以，我觉
得现在大家是想睁只眼闭只眼，看能不能混过去，一旦混过去了，用户多了，就可以反过
来绑架Linux接受VM_PINNED了。当初VM_PINNED被拦着很大一部分问题在memory
accounting上，说起来其实是不怎么接地气的，但大家都没有空空谈这种东西，而
VM_PINNED这个特性叫得也不够狠，痛的人少，在这种讨论下是很难有结果的。

而我更关注的是，Redhat的观点到底有多大的可靠度。Page的状态，简直就是一堆麻，你
很难那猜到，如果你不主动做madvise()或者numa_move，Linux的页表管理系统到底有没有
可能主动把这个vma的链接断掉。本文最后对这个问题（基于4.11-r1）进行一个分析。

我的分析逻辑是这样的：要断掉vma和page的关联，归根结底必须必须直接操作页表，所以
分析入口肯定在pte最后的invalide上面，这样pte_clear这个操作是少不了的，用这个作
为搜索应该可靠性是比较高的，首先找到的是unmap_page_range()。这个函数的用户有两
个，一个是unmap_vmas()，我们cs find s unmap_vmas：::

        3   2464  mm/mmap.c <<unmap_region>>
                  unmap_vmas(&tlb, vma, start, end);
        4   2963  mm/mmap.c <<exit_mmap>>
                  unmap_vmas(&tlb, vma, 0, -1);

两个都是主动操作。

另一个用户是omm_killer，这个连进程都死了，也不是我们需要担心的。而且，这个
Killer不能处理VM_SHARED页，所以如果用VM_SHARED，这样我们就会更安全了。但要注意
的是VM_SHARED的mapping需要文件系统支持，可不是每个虚拟机都支持哦。比如无名页就
不支持，virtio也不支持。

pte_clear的下一个用户是madvise_free_pte_range，这是madvice系统调用主动发起的操
作（我前面的实验就依赖这个），也是不作死就不会死的情形。

下面是其他的单点使用点（明显没有意义的忽略，比如在初始化，虚拟化，内核页表中用
的）：

1. khugepaged内核线程定期扫描有没有可以合并的大页(__collapse_huge_page_copy)，
   如果是VMA需要重新指到合并的大页上。这是个风险点，不过得花点时间才能构造这种
   场景：一页一页分配内存，最后这些内存能被合并成一个大页。todo

2. ptep_get_and_clear/huge_pte_clear

2.1 mremap系统调用中。这个也是主动的

2.2 vm_unmap_ram，这个是内核内部的


这样看完后，还是觉得不对劲：怎么会没有迁移的相关流程的，跟了一下迁移的流程，发
现迁移是不clear_pte的，而是直接set_pte，把原来的页指针盖掉。这个就只好独立去看
了：

3.1 move_pages系统调用，这个是主动的

3.2 handle_pte_fault->do_numa_pte()，这个是缺页的时候发现是添加了标记引起的，如
果发现是需要迁移，就主动发起迁移。这个是有风险的。


综合起来，风险最大的可能是hugepage的合并流程和迁移流程，有时间可能需要构造一下
这个可能性上的用例。但无论如何吧，做破坏规矩的特性真心心累，就算现在能排除了所
有可能性，但谁知道下个版本会怎么样呢？
