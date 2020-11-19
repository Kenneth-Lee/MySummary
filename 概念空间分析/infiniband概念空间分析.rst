.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

infiniband概念空间分析
**********************

文档概要
========

最近在考虑把我们的加速器方案扩展到infiniband（以下简称ib）的概念空间中，所以解
构一下它的概念空间，看看这样做的可能性有多少。

由于本文需要给几位合作伙伴分享，所以在中间版本就对外公开，这里做一个简单的版本
管理：

V0.1.20181125
        Kenneth Lee 完成初步概念构建，只对了代码，还没有编程验证，待进一步细化

V0.2.20181126
        Kenneth Lee 补充MR相关的更多语义过，重新组织了结论的表述方式（但不改变
        结论）

V0.3.20181130
        Kenneth Lee 补充处于安全区加速器的讨论


IB是跨平台的，但本文仅分析Linux的实现，分析基于当前最新的Linux Kernel版本
4.20-rc1和rdma-core stable-v15


基础概念空间
============

我原来做我们的加速器方案的时候，很多共享地址空间相关的方案都参考过InfiniBand的
umem的方案，我们自己也有RDMA的硬件解决方案，但我从来没有考虑过要把加速器集成到
InfiniBand中，因为这个名字和它使用的场合就让人想到这是个通讯方案，是和远程的另
一个实体进行合作用的，所以，我也没有深入去看过verbs的整个设计理念。

但实际上，虽然IB根植于通讯解决方案，它的verbs理念其实确实可以和通讯完全独立的。

IB的基础理念是这样的：我有一个程序，要和另一个程序（可能在另一台机器上）进行互
相协助，这种协助可以被抽象为：

1. 程序A和程序B建立一个双工管道QP（Queue Pair，包含两个CQ，一个Send Complete
   Queue和一个Receive Complete Queue），一方要求另一个干什么，只要把请求WR（
   Work Request)，写到对应的CQ中，另一方对这种请求进行响应，这个模型就可以建立
   起来了

2. WR可以说明请求是什么，这种请求被抽象为特定的原语（称为verb），verb中可以索引
   内存，这种被索引的内存称为MR（Memory Region），verb可以更新对方的MR，实现远
   程进程的内存更新，这称为RDMA

这个概念我们用下面这幅图来表达：

        .. figure:: _static/ib1.jpg

在实现理念上，IB心目中的Application可以在用户态，也可以在内核态（统称Client），
但为了保证效率，IB认为，这个通讯是直接和硬件沟通的，不经过第三方的软件代理。也
就是说，如果你的应用在用户态，向对端发送verb或者更新对方的MR，不需要经过内核。
QP是直接mmap到用户态的，MR也是直接暴露为实际的内存，直接被硬件同步到另一端的。
他们都不经过用户态和内核态的通讯过程。

为了实现QP和对端通讯的细节，QP中包含了不少和通讯有关的语义，这个我们下一步分析
。我们先理解一下verbs这一层封装了什么逻辑，其实verbs的核心逻辑主要就三个：

1. WR send/receive

2. MR RDMA Read/Write

3. Atomic Operation

所以，如果抛开通信细节相关的东西，这是个完全和远程通讯或者具体业务无关的概念模
型。要用于具体的某个业务，你可以基于这个通讯层，实现需要的语义逻辑。这个高一层
的业务抽象，称为ULP（Upper Layer Protocol），现在常用的ULP包括：

1. SDP：Socket Direct Protocol

2. SRP：SCSI RDMA Protocoli

3. SER：iSCSI Extension for RDMA

4. IPoIB: IP over IBNFS-RDMA

5. RDS: Reliable Datagram Socket

6. MPI：Message Passing Interface

这样，这些通讯方就构成这样一个协议栈了：

        .. figure:: _static/ib2.jpg

下层的通讯栈可以根据不同的通讯协议承载在不同的协议上的，最常见的协议当然是
Mellanox的Infiniband协议了，这也是它总造成误会的原因。IB软件框架和IB通讯协议，
是重名的。但其实那是可以换掉的。Linux的IB协议中，有一个模块叫RXE，这个东西基于
Socket实现了一个Transport Layer，下面根本就没有那些层次，但仍可以支持上面的大部
分的verbs（只是性能不高就是了）。

从这个角度来看，比如你做了一个压缩引擎的加速器，你完全可以把这个加速引擎本身作
为一个通讯方构成这样的一个构架：

        .. figure:: _static/ib3.jpg

这是不考虑通讯本身的语义的情况，但如前所述，实际上IB是从通讯发展起来的（实际上
主要就是发明了支持上层做verb和rdma语义的专用硬件），所以它的QP在一定程度上是认
知下面的通讯层的。所以，我们还需要认知在这个语义空间中，有CA，HCA，TCA，Switch
，Channel这个概念（图片来自IBTA）：

        .. figure:: _static/ib4.jpg

但大部分时候我们都用不上，但我们可以知道的是CA就是Channel Adapter，指那个支持通
讯的设备，TCA和HCA是target和Host CA。Channel是连接TCA和HCA的一条通道（连接），
Channel和CA的对应叫一个Port。

SA(Subnet Administration)是网络管理相关命令，有如下子概念：mad（management
diagram）是sa的管理报文，pr（path record）是路由管理接口，mc group(multicast
group)是多播管理接口。

cm（connection management）管理连接（找到对端），有如下子概念：mra（message
received acknowledgement），sid（service id）

上帝保佑，暂时不要让我碰到它们，反正我暂时不需要“对端”。


verbs名称空间的进一步理解
=========================

现在对qp和verbs的名称空间做进一步的理解。如前所述，ib的应用，可以在内核态，也可
以在用户态，两者只是API接口不同，语义是类似的（但内核用ib_register_client()的概
念代替用户态的context），所以我们只从用户态的接口来考量一下这些概念。

qp的名称空间基本上可以从libibverbs/verbs.h上看出来

首先我们得有提供qp的设备，这个称为dev，通过ibv_get_device_list()来获得，然后通
过设备名称来匹配自己需要的那个设备，基于设备建立context，基于context建立pd，基
于pd建立cq，基于cq建立qp。

综合起来这个过程大概是这样的：::

        dev = find_a_matched_device(ibv_get_device_list());
        ctx =  ibv_open_device(dev)
        pd =  ibv_alloc_pd(context)
        send_cq = ibv_create_cq(ctx, ...);
        recv_cq = ibv_create_cq(ctx, ...);
        qp = ibv_create_qp(pd, qp_attr(send_cq, recv_cq, ...));
        ibv_modify_qp(qp, attr, attr_mask);

然后就可以用ibv_post_send()和ibv_post_recv()来进行verb的收发了。

这里有几个新概念：

ctx，这相当于一个client

pd，protection domain，这个用来隔离多对qp和mr。如果下面是个真正的通讯层，相关端
口，地址（IB的地址叫id）等，可以通过ah（address handle）、channel等概念在创建cq
的时候作为参数提供给相关的用户态驱动，让负责发送的驱动来处理）

ibv_modify_qp主要是用于通讯的相关细节的设置，ibv_create_qp仅仅分配了资源，要通
过这个modify来让硬件进入工作状态。

ibv_post_send和recv用于发送verb，verb承载在一个称为ibv_send_wr或者ibv_recv_wr的
数据结构中，里面是verb类型和mr的相关细节。verb的类型包括：::

        enum ibv_wr_opcode { 
                IBV_WR_RDMA_WRITE,  
                IBV_WR_RDMA_WRITE_WITH_IMM, 
                IBV_WR_SEND,
                IBV_WR_SEND_WITH_IMM,
                IBV_WR_RDMA_READ,
                IBV_WR_ATOMIC_CMP_AND_SWP,
                IBV_WR_ATOMIC_FETCH_AND_ADD, 
                IBV_WR_LOCAL_INV, 
                IBV_WR_BIND_MW,
                IBV_WR_SEND_WITH_INV,
                IBV_WR_TSO,
        };

ULP层的消息都可以通过IBV_WR_SEND_XXXX来封装，其他的就是在IB层就可以处理的RDMA操
作和原子操作。

mr名称空间的进一步理解
======================

mr基于ctx创建，通过verb进行分享和更新。先看看mr的创建方法：::

        mr = ibv_reg_mr(pd, addr, length, access);

基本上是直接给定一个虚拟地址，ib负责帮你创建一个句柄，创建的mr中包含一个lkey和
一个rkey，前者用于本地索引，后者用于远程索引。

mr还有一些扩展概念：

首先是fmr，fast mr，用法如下：::

        fmr = ib_alloc_fmr(pd, flags, attr);
        ib_map_phys_fmr(fmr, page_list, list_len, iova);

这个概念仅在内核有效，其实就是mem_pool版本的mr，个人认为不影响整个概念空间。

第二个概念是sge，这表示scatter gather element，它用于指定不连续的内存块给mr做二
次组织（这说起来是个优势，进程中不连续的虚拟地址，在设备上都可以是连续的）

第三个概念是mw，memory window ，用法如下：::

        wm = ibv_alloc_wm(pd, type);
        ibv_bind_mw(qp, mw, mw_bind)

其中的mw_bind用来指定一个mr内的区域的读写属性，其实就是在mr中割一段空间出来，指
定它的权限。这个功能在当前的rdma-core的代码中没有看到用户。

如果把通讯的一方称为A，另一方称为B。A有一片内存要B更新，可以从A发出一个verb，把
自己的rkey和地址发给B。B先在自己的内存中完成修改，然后用这个内存创建一个MR，然
后用 IBV_WR_RDMA_WRITE一类的verb，里面指定A的rkey和地址，就可以远程更新到A的mr
上了。

这些概念如果匹配到加速器上，把B看做是加速器，就是要求B直接更新到A指定下来的MR上
，这个语义，接受了这么多的IB的RDMA语义后，得到的收获，和我直接对设备驱动做一个
ioctl，几乎没有任何区别。IB辛辛苦苦做了这么多工作，就是为了越过内核，把对另一端
的内存更新请求，直接发到硬件上（而不是经过一个软件代理），但加速器的数据本来就
在本端，我真正要解决的问题是，让设备和CPU看到相同的地址空间，那我增加这么多复杂
度，最终的结果是拿着MR，把物理地址弄下来，交给设备，让它按这个物理地址给我填？
IB在这里提供的增值仅仅是gup加上dma_map，这不是所有dma操作本来就要干的吗？

而IOMMU的SVA/SVM能力，也不是IB需要的，因为PD和MR的存在，就已经意味这通讯的两端
是两个实体。而把进程的空间整体共享给设备，让设备来帮助完成特定的计算操作，这种
场景只有加速器才会发生，RDMA并不会这样用，换句话说，把另一台服务器某个进程的空
间全部交给另一台服务器的进程进行操控，这样的行为没有什么ULP会用到。

而IB的ODP（On Demand Page）虽然可以成为SVA/SVM的封装，允许创建MR的时候不gup MR
的内存，但它并不需要SVA的共享页表能力。


安全区问题
===========

上面这个讨论建立在非安全区的加速器上，但我们还常常遇到安全区加速器的问题。比如
你有一段内存需要解密，对应的密钥在安全区，这种情况下使用IB框架就是合理的了。这
时我们可以复用所有的IB概念，但这种情况，也不需要对IB做额外的改变来解决问题了。

小结
====

让我把前面的几个理由重新组织一下：

IB提供的语义是：应用程序可以通过verb，对处于另一侧的一个通讯实体进行服务请求，
另一端实体可以对所请求的远程mr提供更新操作，而这些操作封装为直接的硬件语义，由
应用驱动，在不经过任何软件代理（比如内核）的情况下，转化为对硬件空间的直接读写
，从来保证“对远端MR进行更新”这个语义被以最大性能的方式进行实现。

而加速器需要的语义是：应用程序可以通过verb，对挂接在同一个内存系统中设备进行服
务请求，设备可以直接对提供的内存直接进行更新，从而实现服务的最快提供。

对于后者，MR的封装是多余的，因为双方的依赖是OS对page的直接定义，并没有这层虚拟
的语义。因此verb上被认知的rmda和原子操作也是多余的。失去这这两个需求，IB的所有
优势，在加速器场景上会成为负担。

所以分析到现在为止，我的初步结论是IB的名称空间不适合加速器。加速器并不是一个远
端设备，它看见的内存和CPU看见的内存是同一片内存，和IB的MR概念中的内存是不同的，
后者更像是一个内存的镜像，让内存在多台设备之间同步，而加速器，需要是的CPU和加速
器围在一起吃火锅，你下一筷子，我下一筷子，然后大家都吃个饱。强行把这两者合在一
起，只会增加应用的复杂度。
