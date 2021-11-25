.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-11-25
:Status: Draft

用Uncache写清除页面内容
***********************

本文是对这个补丁的一个分析：
https://lwn.net/ml/linux-kernel/20211020170305.376118-1-ankur.a.arora@oracle.com/
。

这个补丁的idea从标题就能看出来的，就是对页面清零的时候把页变成uncached的，反正
这把这些0留在cache中也没什么用，关键是它的效果：

1. 它要求是大页（例子中是2M，估计更大的，比如以G算的），说明小页是不值得的。按
   Patch的解释，这是因为Uncached就是比cache慢，只有足够大（大到超过cache的大小
   ），才在体现出不需要走两步的优势。

2. 在AMD和Intel上的效果是快272%和161%，这个提升很有看头（当然，这是单点的提升，
   不是系统级的提升）。

实现方法不是依靠修改页属性来实现的，而是利用了Movnt和Clzero等带有cache hint的指
令实现的。所谓NT，是Non-Temporal，“不是临时的”，也就是说，尽量别用Cache，这样不
会让一堆的0清掉整个Cache。Clzero是AMD版本的实现。

但不是简单用这两个指令就可以了，因为这些指令是弱内存序的，这会导致清完以后
SetPageUptodate和它们顺序交叉（深入是为什么，我也没有分析），这需要补一个fence
，这可能会影响性能。

代码具体修改了：

1. memset_movnt，clear_page_movnt，clear_page_clzero的汇编实现。
2. 检查movnt特性是否有效。
3. 封装clear_page_uncached，以便调用不同的汇编实现。
4. 设置调uncached还是cache版本的门限。
5. 修改对应的clear_huge_page调用。
6. 对Uncached写入导致的异常进行特殊处理，增加一种新的FOLL，FAULT_FLAG_UNCACHED
   （主要对应IOMMU的GUP处理，为什么要这个对应，我没有深入分析，应该是为了保证
   外设访问和CPU访问的访问顺序问题）
7. 把性能没有提升的Skylate_x排除出去。
