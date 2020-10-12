.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

WarpDrive as a General Heterogeneous Platform
**********************************************

More and more heterogeneous systems are introduced into the industries these
days. Because CPU is indeed a good way to control rather than compute.

OpenCL is considered a general way to access the heterogeneous system (aka.
device in this document. it can be TPU, NPU, CPU, GPU, or any accelerator). But
many developers still prefer native interface, such as CUDA. I think one of the
reasons is that OpenCL standardizes the device interface but not simplify
anything. It does not even hide the difference of the device configuration in
revision deviation. So there is not much benefit to adopted it while native
interface provides faster update and specific optimization.

We introduce WarpDrive as a general platform for heterogeneous system from
another perspective. It standardizes only the memory model and solve the
problem most of the solutions can not ignore: The device must be used by
application in use space.

If you have a bunch of data in the user space, and you need your device program
to take care of it, you will need to share the user address space with the
device. IOMMU is the only way for the protection without heavy kernel
interaction. WarpDrive manages IOMMU for you to share the address space between
the application and the device. If the application open an WarpDrive-enabled
device, it is bound to the device and share its addresses space to the device.
You can have your device program (and data) ready in the memory and add a
request to the device fd (via ioctl or direct mmio doorbell). So The device can
get it accordingly. The program can refer to the same addresses as the user
application (in CPU side) does. With proper setup, you can access the hardware
without any syscall in the data path.

WarpDrive does not care how the program is generated. And it does not care the
device memory. The device memory is the problem of the device. it should be
left to the device itself. It is the device program's problem if it wants to
copy the data from the main memory. The CPU just give its input in the main
memory and it have to take it back from the the main memory too. How the device
make use of its own buffer/memory should be scheduled by the device or device
program compiler according to the device's configuration.

The concept of WarpDrive is simple but it guild the evolution of IOMMU
subsystem, such as:

Multiple process support (via ASID/PASID)Page fault from device (SVM or SVA)Two
stages page tables support (for use it in a VM)

WarpDrive can also be used as a support technology of other solution such as
OpenCL or CUDA.

WarpDrive is still in RFC stage for mainline Linux Kernel. Please join us to
make it better.


The mailing list for the kernel topic:
https://lists.ozlabs.org/listinfo/linux-accelerators

The kernel branch with Hisilicon Hi1620 accelerator and two dummy test drivers:
https://github.com/Kenneth-Lee/linux-kernel-warpdrive

The user space framework: https://github.com/Kenneth-Lee/warpdrive

And here is a qemu branch with dummy warpdrive device for you to test the
feature without real hardware: Kenneth-Lee/qemu-warpdrive

For more information, please see the document in:

https://github.com/Kenneth-Lee/linux-kernel-warpdrive/blob/master/Documentation/warpdrive/warpdrive.rst
