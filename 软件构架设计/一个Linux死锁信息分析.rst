.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

一个Linux死锁信息分析
*********************

这两天在遇到一个死锁的问题，信息大概是这样的：::

        ======================================================
        WARNING: possible circular locking dependency detected
        ...
        ------------------------------------------------------
        test_dummy/827 is trying to acquire lock:
        (____ptrval____) (kn->count#4){++++}, at: kernfs_remove_by_name_ns+0x5c/0xb8
        but task is already holding lock: 
        (____ptrval____) (xxxxx_mutex){+.+.}, at: xxxxxxxxxx+0x30/0xb8
        which lock already depends on the new lock.
        the existing dependency chain (in reverse order) is:
        -> #2 (xxxxx_mutex){+.+.}:
               lock_acquire+0xd4/0x250
               __mutex_lock+0x8c/0x868
               mutex_lock_nested+0x3c/0x50
        ...
                work_pending+0x8/0x14

        -> #1 (&hw->mutex){+.+.}:
               lock_acquire+0xd4/0x250
               __mutex_lock+0x8c/0x868
        ...
                el0_svc+0x8/0xc

        -> #0 (kn->count#4){++++}:
                __lock_acquire+0x10ac/0x11d0
                lock_acquire+0xd4/0x250
                __kernfs_remove+0x2f4/0x348
                kernfs_remove_by_name_ns+0x5c/0xb8
        ...
                work_pending+0x8/0x14

        other info that might help us debug this:

        Chain exists of:
          kn->count#4 --> &hw->mutex --> xxxxx_mutex

        Possible unsafe locking scenario:
               CPU0                    CPU1
               ----                    ----
          lock(xxxxx_mutex);
                                       lock(&hw->mutex);
                                       lock(xxxxx_mutex);
          lock(kn->count#4);
         *** DEADLOCK ***

        2 locks held by test_dummy/827:
         #0: (____ptrval____) (&hw->mutex){+.+.}, at: xxxxxxxxx+0x34/0x98
         #1: (____ptrval____) (xxxxx_mutex){+.+.}, at: xxxxxxxxxx+0x30/0xb8

这个事情很奇怪，我不觉得它提出来的Possible unsafe locking scenario真的会死锁啊
。

我个人原来一直没有看过Linux的死锁跟踪机制，为了看懂这个问题，我先速成一下，整理
一下笔记。内核代码基于5.2-rc3。

查了一下git历史，这个死锁跟踪功能最初是Ingo Molnar 2006年引入的。网上有人说第一
个版本就解决掉了大部分Linux内核的死锁问题。不过它的设计目标不是用于产品
(release)版本的，对性能有不小的影响，所以一般用于内部测试阶段。

Linux内核的lockdep-design.txt对这个东西有介绍，但我觉得文档写得很烂，前后矛盾，
语焉不详，还不如直接看代码。不过这个代码也很不规整，基本上都是细节，我也耗不起
这个时间。所以我还是聚焦到看个整体，然后重点搞清那个错误输出什么意思。

从文档建立的概念再去对了一下代码，大概的原理是这样的：给每种类型的锁都定义一个
class（相当于锁的类型，比如所有的mutex就是一个class），为每个class定义一组rules
（非抽象概念，都是具体插入的不同代码），然后根据相同class的锁有没有违反rules的
行为（比如A-B, B-A互锁，在上了spinlock的情况下开中断之类的），由此判断锁设计是
否有问题。由于每次上锁解锁的过程都要加上一堆的rules判断，这个对性能的影响是摆在
那里的，但测试阶段能把问题挖出来，到正式产品中出问题的可能性也不大了，所以用于
测试是个很好的方案。

从接口上看，这个功能主要通过在锁初始化代码上加静态定义定义那个class，然后在第一
次使用的时候注册到子系统中。这是默认的情况，如果你要对你的锁做专门处理，也可以
通过lockdep_set_class()自行创建一种新的class。很多复杂的子系统都自己设置自己的
class，比如inode，各种文件系统等。

之后在上锁和解锁的代码里加lock_acquire()和lock_release()，建立那锁类型和
lockdep_map对象的映射，然后就在这些流程里进行死锁Pattern的匹配，检测出有可能的
死锁场景来。

为了增加检测的机会，在部分和锁有关的代码中，还会主动插入might_lock增加检查，这
个本质是主动把lock_acquire和lock_release调一次，就是为了检查而做的。

除了这些基本接口，lockdep还有可以用来检查某个锁肯定已经上了的
lockdep_assert_is_held()，或者确认锁不会被中途释放的lockdep_*pin_lock()等辅助性
的函数。

具体的检查算法都是细节，大概的意思就是判断依赖关系是否有循环（注1），是否重复上
锁和是否在不安全上下文中上安全的锁（比如开着中断上spinlock，这会引起spinlock进
入中断，并在中断中再次spinlock，导致死锁）。我先忽略这些细节，重点解决两个问题
：

第一，错误输出中，每个锁后面{+.+.}是什么意思。从代码上看（吐一句槽：这个代码写
得极其晦涩，看着难受），这是4个上下文的状态标记。上下文分别是：::

        LOCK_USED_IN_HARDIRQ
        LOCK_USED_IN_HARDIRQ_READ
        LOCK_USED_IN_SOFTIRQ
        LOCK_USED_IN_SOFTIRQ_READ

这个标记记录的是上锁的时候是否“曾经”在对应的状态过，具体的标记表示这个上下文当
时的状态：::

        . 状态关，非状态上下文（也可能就没有发生过）
        - 状态关，状态上下文
        + 状态开，非状态上下文
        ? 状态开，状态上下文

“状态”对应上面那四个上下文标记提到的中断状态，比如第一个标记是+，就表示hardirq
开，非hardirq上下文。

而例子中的{+.+.}，表示这个锁“在线程上下文没关软硬中断的情况下上过锁（非读写锁）
”，基本上可以认为全是线程之间的交互。

第二个问题是那个“Chain exists of”打印的是什么东西。这个打印并非打印一个任意长度
的列表，它只打印三个对象：source，parent，target。

source是检查的时候本线程正要上的锁

parent是当前线程上一个拿着的锁

target是发现在本线程中锁住了，但以前曾经依赖过source的锁。

这样，我们就可以面对本文开始的问题了：这个场景为什么会死锁？

我觉得这主要是打印的锅。其实这个死锁场景想表达的是：你在给kn->count#4上锁，但你
已经给xxxxx_mutex上锁了，但之前我们发现过你在上了kn->count#4的情况下，给
xxxxx_mutex上过锁，所以，这有可能是一个循环依赖。

这里报错是没有问题的，代码也应该修改，但lockdep的打印是误导的，基本上可以认为是
个Bug，但如果你能看得懂source, parent，target的意思，这个不影响你使用就是了。

注1：lockdep用的搜索算法叫bfs，我猜了很久都没有搞明白是个什么算法，后来无意中看
了一个Patch，才发现这就是简单的“Breadth-First Search”。
