.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

Accelerator vs. Co-processor
*****************************

This blog explains the intention of WarpDrive / uacce ([PATCH 0/2] A General
Accelerator Framework, WarpDrive).

Von Neumann processor is not good at general data manipulation. It is designed
for control-bound rather than data-bound application. The latter need less
control path facility and more/specific ALUs. So there are more and more
heterogeneous processors, such as encryption/decryption accelerators, TPUs, or
EDGE (Explicated Data Graph Execution) processors, introduced to gain better
performance or power efficiency for particular applications these days.

There are generally two ways to make use of these heterogeneous processors. The
first is to make them co-processors, just like FPU. This is good for some
application but it has its own cons:

1. It changes the ISA set permanently.

2. You must save all state elements when the process is switched out. 

3. But most data-bound processors have a huge set of state elements. 

4. It makes the kernel scheduler more complex

Accelerator is the alternative to solve these problems. It is taken as a IO
device from the CPU's point of view (but it need not to be physically). The
process, running on CPU, hold a context of the accelerator and send
instructions to it as if it calls a function or thread running with FPU. The
context is bound with the processor itself. So the state elements remain in the
hardware context until the context is released.

We believe this is the core feature of an "Accelerator" vs. Co-processor or
other heterogeneous processors.

The intention of WarpDrive is to provide the basic facility to backup this
scenario. Its first step is to make sure the accelerator and process can share
the same address space. So the accelerator ISA can directly address any data
structure of the main CPU. This differs from the data sharing between CPU and
IO device, which share data content rather than address. So it is different
comparing to the other DMA libraries.

In the future, we may add more facility to support linking accelerator library
to the main application, or managing the accelerator context as special thread.
But no matter how, this can be a solid start point for new processor to be used
as an "accelerator" as this is the essential requirement.
