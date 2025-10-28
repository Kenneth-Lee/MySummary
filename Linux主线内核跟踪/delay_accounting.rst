.. Kenneth Lee 版权所有 2025

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2025-10-28
:Status: Draft

delay_accounting
****************

这个特性的文档在accounting/delay-accounting.rst中。

所谓delay-accounting是一种跟踪任务因为资源不可用而等待了多久的日志（Accounting，
也许应该译作“记账”）机制。它需要配置两个参数：::

	CONFIG_TASK_DELAY_ACCT=y
	CONFIG_TASKSTATS=y

包括内核命令行参数：delayacct。

可以通过命令行工具getdelays/delaytop去读记账结果。这些工具的代码在内核代码树中：
tools/accounting，输出大致是这样的（摘自内核文档）：::

	bash-4.4# ./getdelays -d -t 242
	print delayacct stats ON
	TGID    242
	CPU         count     real total  virtual total    delay total  delay average      delay max      delay min
	               39      156000000      156576579        2111069          0.054ms     0.212296ms     0.031307ms
	IO          count    delay total  delay average      delay max      delay min
	                0              0          0.000ms     0.000000ms     0.000000ms
	SWAP        count    delay total  delay average      delay max      delay min
	                0              0          0.000ms     0.000000ms     0.000000ms
	RECLAIM     count    delay total  delay average      delay max      delay min
	                0              0          0.000ms     0.000000ms     0.000000ms

这个accounting机制是根植任务的统计机制的，不是一种通用的延迟接口，就是针对任务
的，实现在kernel/delayacct.c中，用户态程序通过NETLINK和这个统计机制接口。统计
类别也是写死的：::

	UPDATE_DELAY(blkio);
	UPDATE_DELAY(swapin);
	UPDATE_DELAY(freepages);
	UPDATE_DELAY(thrashing);
	UPDATE_DELAY(compact);
	UPDATE_DELAY(wpcopy);
	UPDATE_DELAY(irq);
  
所以不是做任务模块本身的维护，用来看系统的运行情况就好了，自己要做延迟统计也不
用指望靠它。
