.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

Multiprocess Support for Linux IOMMU driver
*******************************************

Most of IOMMU, or so called DMAR, is implemented supporting multiple processes.
For example, the ASID or PCI PASID in ARM SMMU architecture is used as the
sub-stream id to index the Context Descriptor table so more than one page
tables can be assigned to the same IOMMU unit.

But the current Linux kernel (4.12) cannot make use of this facility. The Linux
kernel use the iommu_group to represent a group of devices which share the same
IOMMU hardware. And a virtual space, which is defined by a set of page table,
is represented as iommu_domain.

The iommu_group can get only one domain attached according to its definition: ::

        struct iommu_group {
                struct kobject kobj;
                struct kobject *devices_kobj;
                struct list_head devices;
                struct mutex mutex;
                struct blocking_notifier_head notifier;
                void *iommu_data;
                void (*iommu_data_release)(void *iommu_data);
                char *name;
                int id;
                struct iommu_domain *default_domain;
                struct iommu_domain *domain;
        };

The member, domain, is referred as the iommu_domain attached to it. If another
domain is attached, for example, an application create a new domain via the
VFIO_GROUP_SET_CONTAINER interface, the previous one will be detached first.
The Linux kernel assumes the iommu_group is assigned to a VM as a whole.

The iommu_group->default_domain is used for kernel DMA when no other domain is
attached. It is not another domain that can be applied with the
iommu_group->domain at the same time.


Most of the iommu driver also takes this as a design assumption. The
arm-smmu-v3.c attaches a new asid to the domain when the domain is attached to
the device (in arm_smmu_attach_dev()). But it detaches the previous one if it
exists. Same strategy is adopted by the other drivers, such as intel-iommu.c.


It looks reasonable. A VM will never share its VF with another VM. But it is
not reasonable for the vfio-mdev device (mdev in short for this blog). Mdev is
a virtual device created by a physical device (called parent device, or pdev in
short for this blog). There is a SMMU hardware attaching to the pdev. But all
its mdevs share the same.

Mdev can be taken as a Virtual Function (VF) without separated IOMMU device
identity., such as stream ID in ARM SMMU specification. But the device
identities is expensive, you cannot have many for a single physical device. To
some hardware such as hardwre accelerator, mdev is necessary.

Mdev make use of a virtual iommu_group if you do not have one for it, and you
don't in most cases, because it is your original intention to get a separated
iommu_group particularly for your process.

But the virtual mdev_bus_type is not attached with any iommu_ops, so it cannot
get the advantage of the hardware facility from IOMMU/DMAR. This can be done by
revising the vfio_drv->attach_group() procedure, such as
vfio_iommu_type1_attach_group(). When it detect the bus type is mdev_bus_type,
it can iommu_domain_alloc() with the parent device's bus.

After the hardware-enabled iommu_group is attached to the group. The dma
request can then reach the hardware driver. If we can upgrade the driver to
accept more than one domain. The problem, at lease from the vfio perspective,
is solved.

The remained problem is on the device driver itself. If the hardware can
support multiple asid/pasid, it has to know the asid. So the hardware drive
need to know the asid. But currently, the asid is a private data with the SMMU
driver. It should be made public for the driver to access.
