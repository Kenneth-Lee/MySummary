.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

Linux net和net-next分支的维护策略
**********************************

有同学愿意“准确”地描述“事实”，不想“不精确”你进行抽象。这在工作展开阶段只会阻碍
事情推进。我来代劳一下吧。

我们这里就解决一个问题：决定我们开发的网络的特性（各种Bugfixing，Feature-Patch
等）如何上传给Linux主线。

Linux主线是这个：

    https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

我们假设读者都知道这个Open Windows, rc1-n, release的维护过程。

为了传到这个主线，网络子系统的维护者David Miller自己又维护了两个分支。根据

        https://www.kernel.org/doc/Documentation/networking/netdev-FAQ.txt

David Miller的分支是：

        https://git.kernel.org/pub/scm/linux/kernel/git/davem/net.git
        https://git.kernel.org/pub/scm/linux/kernel/git/davem/net-next.git

下级维护者不能直接上传Linux主线，必须通过这两个分支代理。

David维护这两个分支的逻辑如下：

net-next基于主线某个版本创建，之后开发者可以提交新特性在Linux主线的Open Window
打开的时候，net-next关闭，里面的内容全部作为pull-request发给主线，net分支以这个
关闭时刻的net-next来创建。在这个阶段，开发者不能提交任何特性到net-next，只能提
交bugfix到net中David基于net版本和主线的rc过程沟通，修改主线rc遇到的问题，直到主
线releasenet-next rebase到最新的主线release，重新open，开发者可以继续提交新特性
。但net还会保留，用于修复主线其他问题。直到进入下一个Linux主线发布循环。

所以，

如果你现在发现了一个Bug，你需要提交到net如果你开发一个新特性，你需要提交到
net-next如果你的新特性同时修复一个要立即修复的Bug，如果这个Bugfix可以独立存在，
就仅合入net，因为下次rebase的时候它会过来的，如果它不能独立存在，你两头都要合，
到rebase的时候，根据David的要求修Conflict就好了。

不要老去想自己要怎么样，闭着眼睛就死向前冲，输出一堆不知所谓的代码，先看懂别人
的要求再想怎么配合好吧？
