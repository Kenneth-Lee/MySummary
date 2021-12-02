.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-12-01
:Status: Draft

perf bench的各个测试用例分析
****************************

perf bench最近加了不少测试用例，我分析一下代码，看看它具体测试了什么。

这个分析基于5.10。

* sched

  * message: 创建多个线程或者进程，成对建立UNIT socket或者pipe，发送100字节为单
    位的数据，没有其他work load了。

  * pipe: 同上，但只用pipe做int的pingpong，调度要求更激烈。

* syscall: 就是循环调用getpid
* mem: 就是调用不同优化程度的memcpy等函数而已，连多线程的测试都没有的那种
* numa: 跨不同的节点做memset
* futex: 创建一组线程，等齐了，同时执行futex相关阐述，看完成的数量，对于
  lock/unlock，中间会做短时休眠，usleep(1)，但应该可以用足够数量的线程填满。
* epoll: 通过一个链式的epollfd数组（后一个epoll instance监控前一个epollfd，测试
  epoll的性能）
* internals：调用perf自己内部的一些执行流程，这都和当前运行属于有关，不能作为跨
  环境的测试对比。
  * synthesis: 对当前事件进行综合
  * kallsyms-parse：分析/proc/kallsyms
  * inject-build-id: 
                                               
这些代码的风格我个人是不喜欢的，它几乎每个测试例都是独立的，有更多重复代码，我
不明白有什么必要，当然，对于这样的测试来说无伤大雅就是了。
