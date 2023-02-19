.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 1.0

:index:`binfmt`

binfmt概念空间建模
******************

准备要做一种新的二进制格式，本文对Linux二进制格式，特别是这个格式和它的执行单元
直接的关系做一个概念建模。

本分析基于5.5主线内核。

Linux对每种二进制格式进行抽象，抽象的接口叫linux_binfmt（以下简称binfmt），通过
register_binfmt()进行注册，注册时提供的数据结构中，关键是三个函数：::

        int (*load_binary)(struct linux_binprm *);
        int (*load_shlib)(struct file *);
        int (*core_dump)(struct coredump_params *cprm);

后面两个都是辅助的，从概念关联的角度，我们只需要关心第一个就可以了。这个回调作
用在do_execve()阶段，也就是，进程已经fork了，有了和这个进程相关所有管理信息，比
如vma，files，sig_handler这些机制，然后我们清空它的vma，用load_binary重新填充这
些vma（具体用哪个load_binary()可以通过一个个注册的binfmt去试，代码在
search_binary_handler()中），最后调用这个binfmt的start_thread函数（这个函数通常
针对这种binfmt或者针对这个binfmt要使用的硬件，例如CPU Arch，专门设计），修改
current的当前PC等信息，最后进入调度，剩下就是调度器的问题了。

这个结构保证binfmt这个静态的程序概念和process这个动态的运行概念相对独立，仅在
start_thread这个位置上进行关联。当一个程序的binary占据这个进程的vma后，它投入调
度这件事，就完全是调度器的问题。而调度器的调度目标是CPU。然则，如果我有一个GPU
用来执行这个binfmt，我的binfmt投入执行后，仍是CPU在看见这个进程，它被
start_thread()后，我们从OS的管理设施上将看到的是一个“等待GPU完成”的“CPU进程”，
它的files，pid，smaps，cgroup等信息，都是我在CPU一侧当初看到的对应信息。如果我
认为GPU执行在用户态，那么GPU做系统调用进入内核，仍可以使用这些files和pid，只要
保证系统接口可以请求过来就可以了。

这种情况，如果我对这个GPU的进程做GDB，和GPU程序在一起的gdbserver把进程trap in到
内核中，内核读GPU的状态，把数据送回到gdbserver中，gdbserver可以把相关信息全部封
装在gpu stub和gdb client之间，和用于调度的程序没有关系。

这个情形比较怪异的地方在于，调度器这时认为这个进程正在调度在这个CPU上，这个CPU
不能给其他进程使用，实际上这时CPU闲着。这看来有两个解决方案：其一是暂时把CPU挂
起来，别让它动，等GPU算完了再继续调度，这个有点浪费资源。这种模式我们称为“同步
模式”。其二是骗调度器说这个进程没在运行，让GPU干GPU的，CPU干CPU的，GPU要做系统
调用等行为，再通过中断来激活CPU进行这个进程有关的处理。这个产生了一个新的语义：
一个没有被调度的进程，也可以产生系统调用（但我们可以认为这不是系统调用，而是一
种“外部中断”）。而且，我们需要有额外的手段监控这些管理之外的进程的资源分配（对
GPU资源的调度和平衡）。这种模式我们称为“异步模式”。

这种情形下，如果我们让GPU（以下称为“异构CPU”）分时使用，一个异构进程或者线程的
时间片用完了，同步模式是最简单的，因为我们实际是按一般的方法调度一个task进来运
行，这个task是同构的，就用同构CPU执行，是异构的，就用异构CPU来执行。这完全看不
出差别来。但如果是异步的，我们会需要一个异构的调度器对这些异构task进行单独的调
度。

我们再构想一种更极端的情形：如果这个不是GPU，而是一个嵌在CPU核内的TPU。那么这个
进程的两个线程就需要涉及了两个CPU的占据，对应上面两个情形，似乎所有条件仍可以成
立。所以，这种情形我们的全部逻辑都是成立的。

暂时看来，风险不大，概念空间是自恰的。
