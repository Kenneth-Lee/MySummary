.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

Linux Socket 0拷贝特性
**********************

Linux Net-next分支这个月刚刚接纳了来自Google的SOCK_ZEROCOPY特性：
http://www.mail-archive.com/netdev@vger.kernel.org/msg180839.html。我对所有拿用
户内存做DMA的行为都有兴趣。本文对这个技术做一个分析。

先看看SOCK_ZEROCOPY这个特性做了什么。

首先从接口上来看，这个特性需要修改Socket的使用方式，大概模式是这样的：::

        setsockopt(socket, SOCK_ZEROCOPY);//从代码上看，现在仅支持IPv4/v6的TCP
        send(socket, buffer, length, MSG_ZEROCOPY);

原理很简单：给socket设一个option flags，发送的时候也要指定相应的flags（理论上其
实没有必要，因为可以从socket上拿到的，本文讨论中有人认为这是为了可以给小包选择
不用zerocopy，我觉得这个很有道理）

这个修改不算太大，真正不同的是，调用完send后，你不能直接释放buffer，因为这个
buffer不一定被读走了，所以必须读一下Socket的错误队列，确定包已经发走了：::

        recvmsg(socket, &message, MSG_ERRORQUEUE);

就这样，只有发端可以用。这样实现后，buffer的内容不需要拷贝到内核内存中。


把整个PatchSet看了一次后（作者还写了一个可能用于演讲的，语焉不详的材料在这里：
https://www.netdevconf.org/2.1/slides/apr6/msgzerocopy-willemdebruijn-20170405.pdf
）。我发现这个特性并不是重新发明的技术，而是依赖早在2011年就已经由Redhat上传的
vhost-net的零拷贝技术来实现的）。所以我们先看看vhost-net是如何实现用户态内存做
DMA的。

vhost-net零拷贝上传的解释说明在这里：Provide a zero-copy method on KVM
virtio-net.。写得也是语焉不详的，但大概可以知道，这个技术主要是用于tap/tun驱动
，用于保证KVM和Xen Guest的虚拟网卡向下发请求的时候，qemu进程内部的内存可以被直
接用于tap和tun驱动的dma。

根据代码（4.12)，这个技术的原理如下：用户进程把要写的数据分段指针填入
msghdr.msg_iov向量中，用send/sendmsg发到tap/tun的socket中。这个模块在
handle_tx()中顺序处理这些请求，调用sock->ops->sendmsg()，进入
tun_sendmsg()->tun_get_user()->zerocopy_sg_from_iter()->zerocopy_sg_from_iter()->get_user_pages_fast()
。

所以，弄到最后，还是gup。


也就是说，这个方案还是会有VMA_PIN陷阱的，如果gup后没有立即做DMA，进程是有一定几
率发生VMA的重新映射，导致用户进程无法获得DMA的返回的。但应用在发送这个功能上，
却没有什么风险，因为进程并不使用这个内存作为返回值，发完只要能回收就够了，但这
不足以用作通用的双向DMA方案。

从这个角度说，其实如果你不复用sendmsg()的buffer，而是直接释放，你是不需要在
MSG_ERRORQUEUE上等待的，因为free只是释放了vma的指针，page已经被gup了，是不影响
内核继续使用这个page的。
