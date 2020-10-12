.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

Progress and confusion of the IOMMU name space
**********************************************

Introduction
=============

We are now working on an accelerator framework based on VFIO. New concepts need
to be added. At the same time, the other developers are adding new ideas too.
The name space here become complex. I try to clear it though in this blog.


The Basic Idea
===============

IOMMU is the facility to separate the DMA space of different devices. This is
illustrated as follow figure: 

        .. figure:: _static/iommu1.png

IOMMU works just like MMU for the CPU. Address request issued by the device
will be translated according to the page table assigned to its IOMMU. In many
cases, every device has its own exclusive one. But sometimes some devices may
share the same unit. In this case, the physical space opened for this IOMMU is
also openned to all devices behind this IOMMU.

In Linux, iommu_group is used as the representative of the group of devices
owned by the same IOMMU. It contains a iommu_domain referring to the status of
the IOMMU currently applied:

        .. figure:: _static/iommu2.png

The iommu_group (along with its iommu_domain) is taken as the security border
for the CPU to control the device. When the CPU enables some address mapping in
the iommu_domain. It assumes the memory is dedicated to the devices within the
iommu_group, and the devices can only access those dedicated memory.

The iommu_group is created by the bus driver when the device is detected. A
default_domain will be created with the group. So the default DMA operation
(say, from the driver) can be taken by it. But the effective domain can be
changed later.


This is good enough for driver-device communication with kernel. But it is not
enough for user application who issues request to one or more than one devices.

VFIO come to help in this situation. It introduces a new concept, container, to
representing the unified DMA space shared by all managed devices.

A container, namely vfio_iommu in the most common vfio driver (aka, type1
driver), contains a set of vfio_domain (wrapper of iommu_domain) and a DMA
address space (managed as a rb_tree).

This can be illustrated as follow:

        .. figure:: _static/iommu3.png

New iommu_groups can be attached to a container, its vfio_group is created and
added to an exist or new created vfio_domain (so as its iommu_domain, and this
new iommu_domain will replace the default_domain as effective domain in the
iommu_group). In the case of new domain created, the dma_map_rbtree will be
replayed on it. So all IOMMUs in this container have the same DMA
space/mapping.


But this is not all. The VFIO framework must ensure the default_domain will not
be used any longer. So the device must be unbound from its original driver and
rebound to a VFIO device driver, e.g. vfio-platform or vfio-pci driver.

VFIO device driver use the VFIO driver API to register itself as a VFIO-ied
device: ::

        int vfio_add_group_dev(struct device *dev,
                const struct vfio_device_ops *ops, void *device_data);
        struct vfio_device *vfio_device_get_from_dev(struct device *dev);
        void *vfio_device_data(struct vfio_device *device);
        void *vfio_del_group_dev(struct device *dev);

With this design, the VFIO framework become a agent of the device. DMA
Operation of the devices can be conducted directly on the container itself.

This is important. It means we cannot simply use any device without make it as
a VFIO-ized device.


PASID Support
==============

A devices may communicate to more than one process. So most IOMMU
implementation support the concept of PASID-ed address mapping. In this case,
the IOMMU can accept more than one address space indexing by the process id
(which is referred as PASID in PCIE standard). The current kernel (up to 4.16)
do not support this feature yet.

Jean Philippe Brucker from ARM is now working on it. He extends the
iommu_domain structure to enable PASID-ed address space. We have tested it in
our hardware (known as D06). It works fine.

The design reuses most of the concept as we mentioned before except for
iommu_domain, which is now referring to more than one address space indexed by
PASID.

To expose the feature to VFIO, Jean also add two new commands,
VFIO_IOMMU_ATTACH and VFIO_IOMMU_BIND, for binding the process to the domain.


Our Requirement
================

We are going to implement an accelerator framework for accelerators, e.g. GPU,
TPU, FPGA, Smart NIC, ZIP/UNZIP engine, RSA engine, etc. We assume the data
flow is stored in the memory and shared among different hardware. The idea is
illustrated as follow:

This scenario exactly the same as what has been done by the VFIO framework.

Except for one thing: We are not going to unbound the device from its old
driver.

Consider this scenario: you have a multi-queue NIC and you are going to use it
as the last device of your data flow. We want to use some of the queues in the
NIC for that purpose. But you still need the original driver for the basic
feature as a netdev, say, set its mac address with ethtool.


VFIO MDEV
==========

VFIO Mdev looks a solution for this. The VFIO mdev is initially introduced by
Nvidia for its virtual GPU, which cannot be taken as a standard SR-IOV VF.

A SR-IOV VF, which is defined by PCIE standard, is a virtual device with its
own request id, which is normally taken as a isolated device by the IOMMU.
Request ID, aka stream ID in SMMU of ARM, is the identity for IOMMU to
distinguish the address request from different devices.

Mdev is used as a light weight VF without its own identify for the IOMMU
system, and so as to the VFIO system.

Mdev is created from an exist device driver with its own iommu_group, and of
course, as a VFIO-ized device. It cannot share the facility as the other device
do. So it uses its own iommu_domain and takes care of all DMA operations by its
own. This change the VFIO framework a little bit: 

        .. figure:: _static/iommu4.png

external_domain list are introduced to maintain the domain which is controlled
directly by the device driver itself. The notifier_chain is used to notify the
external domain to conducted the dma operation.

Currently only dma unmap is notified.

This is almost exactly what we need except that we want to be a good boy, who
need not to be a external_domain. So we can continue to reuse all operations on
the parent device and the dma replay can continue work with it.

So if we can change the vfio code a bit: when it detects the device as such a
good boy, it can merge it with the same iommu_group as its parent. Then all the
problem will be solved.

But this also change to the meaning of iommu_group a bit. There will be some
kinds of virtual iommu_group, which directly share the IOMMU hardware resource
with other iommu_group without telling those exist iommu_group.


WarpDrive with mdev
====================

We call our framework as WarpDrive. When a hardware device is registered as a
WarpDrive device, it will be registered as a mdev. So the system administrator
can create it accordingly. But not like the other mdev device, there is no
hardware resource allocated to this mdev device until the device is opened.
Then everything can be shared the same concept space of VFIO.

Without Jean's patches, the device can be used only by one process. With the
patches, the device can be used by more processes through the VFIO_IOMMU_BIND
interface.

The WrapDrive should also ensure only the PASID allocated to the corespondent
process is assigned to the hardware. 

Conclusion
==========

So here is the conclusion:

1. We should add an attribute to the mdev, making it reuse the parent's
   iommu_group

2. The accelerator driver can expose some function as mdev, so the application
   can make use of it with VFIO interface.

3. For WarpDrive, we can expose the function as mdev but the queue allocated to
   the application can be attached to the fd of the vfio device. It will be
   easier to release when the application exist.
