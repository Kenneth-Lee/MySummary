.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

推演一个Buffer分配的语法设计
****************************

问题：有一个向量处理器，核内有一片Buffer，大小为X，可以基于它进行向量/张量计算
，令操作符为opX，多个操作组合成一系列连续操作可以表述为opX(N)。

opX的操作数（无论输入还是输出），都在Buffer中，我们称为一个Tensor（张量），
Tensor表示Buffer中的首地址和长度。某些opX可以把数据从核外的内存搬移到Buffer中来
。

opX之间没有complete-start关系（简称NCS，Non-Complete-Start），也就是说op1完成前
，op2可以被投入运行，处理器有原语可以主动保证opX之间的依赖，这个问题不在本问题
的考虑范围内，我们只保证：“可以主动建立任何两个opX之间的CS关系”。

现在的问题是：用什么语法来表述Tensor在Buffer中的分配？


为了更容易理解问题，我们举一个典型的场景，看看程序员要面对什么问题大概是什么样
的。比如程序要要完成一组计算，他的行为可能是这样的：::

        LoadDataToTensor()
        Barrier()
        opX(N)
        Barrier()
        LoadDataToTensor()
        Barrier()
        opX(N)

但这样的效率是很低的，因为在Load的时候opX的执行部件就会全部闲着。更好的办法是把
它们交叉起来：::

        loadTensor(Tensor1)
        loadTensor(Tensor2)
        Barrier(Tensor1)
        opX(N)(Tensor1)
        Barrier(Tensor1)  #等opX(N)对Tensor1的处理完成
        loadTensor(Tensor1)
        Barrier(Tensor2)
        opX(N)(Tensor2)
        Barrier(Tensor2)
        LoadTensor(Tensor2)
        ...

Tensor3、4明显可以复用前面1、2的空间。

我们可以把这个行为归结为这样的语法：::

        for i in range(x) pipeline(depth=2):
          t = AllocTensor()
            loadTensor(t)
              opXWithBarrier(N)
                Free(t) 

这样我们可以构造一个深度为2的流水线，我们需要两个t，发射完两个序列后，我们等其
中一个完成，然后我们让t复用它的Buffer，然后才投入运行第三个循环。我们如果要支持
这样的语法，Tensor对Buffer的分配关系，应该提供什么样的语义才能提供最利于程序员
选择的编程接口？（当然，这只是其中一种典型场景）。


方案1：Alloc/Free

Tensor通过Alloc分配，Free释放。分配后即可以被投入使用。这种方案明显会导致Buffer
利用不充分，Alloc, Free方式是用于“充裕内存”的场景的，很多时候容忍一定程度的浪费
，作为处理器内部Buffer的分配算法，显然不适合，这个方案首先抛弃。


方案2：基于名称空间的主动分配和释放

我们把for里面的opX(N)看做是一个名称空间，Nested的for看做是一个子名称空间，用
Tensor(size)这个定义来实现一次Buffer分配，保证Tensor在离开它定义的名称空间时自
动被释放。

这个方案本质上是方案1的收缩自由度后的变体，程序员不能对Buffer的利用进行控制，就
会产生碎片，如前所述，对于处理器内部Buffer，碎片不可原谅。

这个方案其实还有另一个问题：基于Tensor来进行运算，依赖可以做在Tensor上，如果op1
和op2使用相同的Tensor，我们就可以建立op1和op2之间的CS依赖。Buffer空间的分配和释
放本身并没有Tensor依赖，那么我们就不得不等待Nested的空间全部计算结束，否则就可
以导致后续计算没有空间继续。这个让程序员失去控制的机会，可能导致性能瓶颈。

方案3：半静态Buffer规划

上面那个流水线语义的核心是，要把Buffer根据流水线平分使用，为此，我们引入一个
Tensor别名的设计，你可以把Tensor切出多块出来单独使用，比如你有一个Tensor：::

        Tensor A(shape=(2,3)) #这个用动态分配来分配出来，离开名称空间就释放，但我们预期你根本不会释放它

我们可以在这个Buffer的原位放另一个Tensor层叠上去：::

        Tensor A1(shape=3) alias A[0, :]

        Tensor A2(shape=3) alias A[1, :]

A1和A2复用A的内存，但使用了另一个语义进行解释。当我们进入一个流水线的时候，我们
让流水线来处理这个分配，这个语法就会变成这样：::

        for i in [n, m] with t in Tensor1[0:2]:
          loadTensor(t, i)
            opXWithBarrier(N)(t) 

这个语义表达的是：把Tensor1的第一维分成两份，每份产生一个别名t，我们先完成两次
循环的发射，然后等第一个循环的结束，再投入下一次的发射。这样，程序员始终知道整
个Buffer的规划，在循环内部他还可以把t再通过别名再分解过多个独立的Tensor，这样，
整个控制力就比较强了。


方案4：全静态Buffer规划

这个方案是前一个方案的改进。既然Tensor别名是另一个Tensor的叠加，我们就根本不需
要Tensor别名的概念了，我们可以让Tensor就是原来的Tensor别名。然后把系统的所有
Buffer定义为一个根Tensor就可以了。这样Tensor的定义语法是这样的：::

        Tensor A(shape=(2,3)) from ROOT_TENSOR[0:7]
        ...
        Tensor B(shape=(6,10)) from ROOT_TENSOR[7:68]
        for i in [n, m] with t in A[0:2]:
              ...


方案5：基于Tensor的动态分配

这个方案是3,4方案上的一个addon，响应有人要求的：某些情况下，我的Buffer真得是充
足，你随便帮我分就好了。

那么，我们就给Tensor本身提供一个动态分配的Slice模式。以方案4为例，假如我们已经
有一个Tensor A了（A可以是ROOT_TENSOR本身）

我可以这样定义一个要求在A上动态分配的空间：::

        B(shape=(2, 3)) from A[auto]

一旦你这样定义了，A的空间进入动态调配模式，B会在A上分配一个合适的空间。等你一段
代码过后，你整个A要另做它用，你可以直接定义一个普通的Tensor：::

        X(shape=(2,3)) from A[0:7]

这样我们可以继续用原来的模式来使用最初的功能。

我暂时能想到的最优方案是方案3和4了，具体用哪个看具体情形（看起来4更好），其实要
组合起来用也是可以的。有人有更喜欢的应用模式吗？
