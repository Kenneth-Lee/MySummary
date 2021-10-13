.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-10-13
:Status: Draft

RISCV中断方案分析
*****************

写这个文档是因为看别人写的一个RISCV的中断控制器的总结，觉得隔靴搔痒，我通过重新
写一个说明这种分析应该怎么抓要点。

要说明的是，我这是根据那个总结，然后单独看了一两个实现上的具像而写的另一个总结
，重点是要说明如何抓重点，由于看的例子不够，总结不一定是对的。

RISCV现在主要有三个中断控制器方案。一个是Sifive的FU540，FU740用的方案，我根据这
个两个定义：

        https://starfivetech.com/uploads/fu540-c000-manual-v1p4.pdf

        https://www.starfivetech.com/uploads/fu740-c000-manual-v1p2.pdf

来抽象这个方案的特点。

首先这个方案没有定义HART的行为，HART的行为用的是RISCV本身对核的定义。也就是说，
它不管你HART怎么触发这些中断的，他只管“我告诉你有这个中断了”，你Hart内部怎么按
符合RISCV的语义的方式触发这个中断，他管不着。

这个方案在Hart外包含两个中断控制器的实体，一个叫CLINT，Core-Local Interruptor，
用于专核专用的中断，比如IPI和本核的通用定时器时钟。另一个叫PLIC，Platform Level
Interrupt Controller，用于处理外设中断。

这两个实体要分开，我觉得很简单，因为这个方案整个就是硬编码的，哪个中断具体是什
么中断号，什么属性，全部是死的。而CLINT控制的那些中断都是per-hart的（如果有外部
中断报上来，也认为是本Hart唯一的），而PLIC控制的中断都是全系统唯一的。如此而已
，至于系统有多少个CLINT和PLIC的物理实体，其实不重要，因为从软件看来，它们就是唯
一的。

如果要分析通用的中断控制器，这个方案不值得看，因为它根本就不是通用方案。

通用一点看PLIC的定义，在这里：

http://shakti.org.in/docs/plic_user_manual.pdf

这基本上从平台一级看也是一个定制方案，因为它预期PLIC和Hart是绑定选路的，硬件一
开始就选择了某个PLIC到底是报给哪个Hart的。

第二个方案是m-pratform profile默认的中断控制器方案，这个是CLIC+PLIC方案。其中CLIC是
Core Local Interrupt Controller，定义在这里：

https://sifive.cdn.prismic.io/sifive/d1984d2b-c9b9-4c91-8de0-d68a5e64fa0f_sifive-interrupt-cookbook-v1p2.pdf

按这个定义CLIC兼容CLINT，只是升级了一些控制功能，这个其实也可以不看。按这里的介绍：

https://riscv.org/wp-content/uploads/2018/07/DAC-SiFive-Drew-Barbier.pdf

这个方案预期PLIC不直接关联Hart，而是报给CLIC，然后统一从CLIC报到具体的HART上。

最后一个方案是AIA，这是一个相对通用的方案。我看的是这里的定义：

file:///tmp/mozilla_kenny0/riscv-interrupts-026.pdf

它一定程度上可以认为是一个PLIC+CLIC的进一步升级，其中PLIC升级为Advanced PLIC，
它确定不再和Hart接口，而是直接上报消息中断（消息中断是通过标准的总线地址写操作
实现的消息报告方法，区别于传统的通过电平或者电平变化的方法）。

而CLIC升级为IMSIC，Incoming MSI Controller，它变成了CPU的代理，每个CPU一个（类
似ARM GIC里的CPU IF），它接口PLIC或者其他位置发上来的消息请求，从而实现对Hart内
部的中断行为的控制。为此，它提供一个中断文件（interrupt file）的概念，每个中断
file代表一组Hart内的ie和ip的状态，通过控制这个interrupt file，我们就可以对不同
的优先级的中断状态进行管理了。

这是个通用方案，而且逻辑空间相当优美：首先，我不管你有多少传统中断，有的话，你
一概给我转化成消息中断，然后报给对应的Hart的IMSIC，这样，在这一层之外，我们只剩
下消息中断的语义。

这样一来，其他用消息中断的系统（比如PCIe），直接对接这个接口就可以了。

第二，它放弃了硬件路由的概念，你硬件选一条路到某个Hart上，怎么选这个事情不是我
软件告诉你的吗？你额外做了什么“加工”？什么都没有，不如我直接告诉中断源：“你直接
给我报给特定的Hart（所在的MSI地址）就行了。

这样，所有问题都解决了。然后，剩下的问题是你硬件能不能作出效率来的问题了。

你看，这才叫问题建模。把别人的东西看一遍，然后把一样的信息拷贝上来，这不是建模
，这是抄笔记。
