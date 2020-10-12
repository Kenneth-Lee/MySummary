.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 1.0

cond/mutex模型
**************

本文给一位同学快速介绍一下pthread cond/mutex模型，作为他进行另一个设计的参考。

pthread_cond用于实现提供者-消耗者模型。示意如下：

        .. figure:: _static/cond_mutex模型1.jpg

这个图一画，你就发现这个破绽是非常明显的，因为可以发生这样的问题：

        .. figure:: _static/cond_mutex模型2.jpg

pthread_cond的解决方案是再加一重保证，让signal发生在wait之后：

        .. figure:: _static/cond_mutex模型3.jpg

这个实际复杂了很多，它要处理两种情形：

提供者先抢到mutex，消费者就进不去，等有数据，发完signal，而且unlock了，才轮到消
费者，这时消费者要立即检查数据，有数据就不能wait了。

第二种情况是消费者先拿到锁，提供者就一定进不去，这时如果消费者确定没有数据了，
就用cond wait去等待，这个wait会产生一个unlock，解锁提供者，提供者这时准备数据然
后signal消费者，就必然是有效的。

所以，其实用这种cond的方式提供等待是很复杂的，不要指望靠简单硬件加速可以搞定。
