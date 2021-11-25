.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-11-25
:Status: Draft

释放页表页补丁分析
******************

本文分析这个补丁：
https://lore.kernel.org/lkml/20211110105428.32458-1-zhengqi.arch@bytedance.com/
。

它的Idea是：页表包括Sparse的多个页面用来分段放PTE，当这个页的所有PTE都清掉了，
这些页没有释放，所以需要释放这些页。

补丁来自字节跳动，具体的问题是服务器进程mmap大量内存后，靠MADV_DONTNEED释放PTE
，但释放不了也表本身，导致他们的进程590G RES却有110G VmPTE，所以值得修改。修改
方法是在pte中放一个pte_refcount进行数量统计，减到0就把这个pte对着的pmd页面释放
了。修改后性能下降大概1%。

Redhat的David Hildenbrand提出正在做的另一个方案：不用MADV_DONTNEED，而用
MADV_PUNCH_HOLE，或者MADV_CLEANUP_PGTABLE，这样把这个事情变成一锤子买卖，就不影
响性能了，而且也不用修改那么多地方，我觉得后面这个思路好。
