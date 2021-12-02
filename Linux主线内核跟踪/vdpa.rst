.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-12-02
:Status: Draft

vDAP概念空间分析
****************

本文分析一下vDAP的概念原理。

用法
====

我们先用Redhat的这个基本介绍博文：
`Hands on vDPA <https://www.redhat.com/en/blog/hands-vdpa-what-do-you-do-when-you-aint-got-hardware>`_
，来理解一下它的用法：


关于vhost和virtio
-----------------

vDAP有两种用法，一种是作为一个vhost设备，一种是作为virtio设备。这两个概念很容易
让人晕掉，我们先来理解一下：

我们用virtio来模拟设备，比如我们在guest中需要有一张virtio的网卡，我们需要在qemu
中为这张网卡创建一个后端（backend），然后用靠这个后端和host的网络机制通讯（比如
TAP/TUN等）。

这样的模型，guest中需要一个virtio-net驱动，qemu中需要一个virtio-net设备（比如
qemu -netdev type=virtio-net-pci...），最后我们需要在内核中有一个TAP/TUN实例去
相应这个设备的请求，这样一个通讯过程，需要从虚拟机到qemu到内核，通讯两次。

那更好的办法是把TAP/TUN直接换成一个virtio接口的vqueue接口，让guest那个驱动直接
和host中的设备通讯。这样host内核中就需要一个vhost-net设备，qemu仅仅管理上向这个
设备申请资源(比如：qemu -netdev type=vhost-user），然后把它的vqueue交给guest OS
中的virtio-net驱动，这样guest OS中的virtio-net驱动写到host OS的vhost-net设备上，
只通讯一次就行了。

后面这种方法的缺点是你就无法在qemu里面直接实现两个网卡之间的通讯了。

总结起来，两种方法都是virtio的virtqueue的通讯手段实现的Guest-Host通讯，只是一个
用于Guest Kernel - Host Qemu，一个用于Guest Kernel - Host Kernel。两者使用一样
的Guest驱动和不同位置的Backend驱动。前者适合在一个qemu内部互相通讯，也更灵活，
后者适合直接对外通讯，但需要在Host上完成各种配置，再连到qemu中。

vhost用法
---------

要通过vhost使用，你先要在host上创建vhost设备，这需要：::

  modprobe vpda
  modprobe vhost-vpda
  modprobe 支持vhost的硬件   （作为验证，可以用vdpa_sim，它是一个基于loopback写的软件模拟网卡）

这样我们就有了一个或者多个vdpa设备了。比如，如果这里用的是vpda_sim，它会注册一
个vdpa设备：/sys/devices/vdpa0。这个设备bind到vhost-vpda上，我们就有了一个host可见，可以被qemu
访问的vdpa设备，比如/dev/vhost-vdpa-0。

然后让qemu和这个设备关联起来：::

  qemu -netdev type=vhost-vdpa,vhostdev=/dev/vhost-vdpa-0...

这样guest中多了一个网络设备，可以用virtio-net访问，对它访问直接被转到host的设备
中。

virtio用法
----------

virtio用法类似传统的SR-IOV的用法，首先你是机器上有一个VF（这个如果没有硬件仍可
以通过modprobe vpda_sim来模拟），然后你需要unbind你原来的driver，然后重新bind
virtio_vdpa驱动（为此需要modprobe virtio-vpda），从而得到一个virtio设备。

还是用vdpa_sim为例，前面它bind到vhost-vdpa上了，如果我们unbind
/sys/devices/vdpa0的vhost-vdpa驱动，然后rebind virtio-vpda驱动，现在，我们没有
了/dev/vhost-vpda-0，得到了/sys/bus/vdpa/vdpa0。

这个/sys/bus/vdpa/vdpa0设备，就是可以在qemu里面通过vfio接口来访问的。

这个地方注意和传统的vfio设备区分一下，传统vfio，如果我们要得到一个网卡，我们是
在host端用virtio_net驱动去bind一个virtio设备，然后在qemu中用virtio类型的netdev
去访问它。而使用vdpa，我们是bind一个vdpa设备，然后用vdpa类型的netdev去访问它。
样的驱动上）。

说起来，这两个不同用法仅仅就是接口不同，qemu都是知道这下面是一个vdpa接口，通过
让guest中的vritio-net驱动直接访问host给定的共享内存来访问virtqueue的。

实现
====

所以，vdpa实际上是driver/vdpa.c和driver/vhost/vdpa.c两个驱动，对应以上的两个接
口。

virtio的驱动是个总线接口，除了提供总线匹配，还提供一个管理设备回调，可以在特性
类型的设备注册上来的时候进行特殊的设置。

vhost的驱动是个vhost总线的驱动本身，bind到这个总线上后，它可以给你创建一个misc
设备作用用户态访问的基础。

其他都是virtio本身的适配了，和架构无关，我不再深入进去了。
