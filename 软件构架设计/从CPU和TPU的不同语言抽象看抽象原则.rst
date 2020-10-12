.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

从CPU和TPU的不同语言抽象看抽象原则
***********************************

最近和人讨论CPU和TPU的语言抽象，把一些总结整理在这里。

CPU的语言是个时间模型，我随便拷贝一段Linux的代码来作为例子：::

	static __always_inline long __get_user_pages_locked(struct task_struct *tsk,
							struct mm_struct *mm,
							unsigned long start,
							unsigned long nr_pages,
							struct page **pages,
							struct vm_area_struct **vmas,
							int *locked,
							unsigned int flags)
	{
		long ret, pages_done;
		bool lock_dropped;

		if (locked) {
			/* if VM_FAULT_RETRY can be returned, vmas become invalid */
			BUG_ON(vmas);
			/* check caller initialized locked */
			BUG_ON(*locked != 1);
		}

		if (pages)
			flags |= FOLL_GET;

		pages_done = 0;
		lock_dropped = false;
		for (;;) {
			ret = __get_user_pages(tsk, mm, start, nr_pages, flags, pages,
					       vmas, locked);
			if (!locked)
				/* VM_FAULT_RETRY couldn't trigger, bypass */
				return ret;

			/* VM_FAULT_RETRY cannot return errors */
			if (!*locked) {
				BUG_ON(ret < 0);
				BUG_ON(ret >= nr_pages);
			}

			if (!pages)
				/* If it's a prefault don't insist harder */
				return ret;

			if (ret > 0) {
				nr_pages -= ret;
				pages_done += ret;
				if (!nr_pages)
					break;
			}
			if (*locked) {
				/*
				 * VM_FAULT_RETRY didn't trigger or it was a
				 * FOLL_NOWAIT.
				 */
				if (!pages_done)
					pages_done = ret;
				break;
			}
			/* VM_FAULT_RETRY triggered, so seek to the faulting offset */
			pages += ret;
			start += ret << PAGE_SHIFT;

			/*
			 * Repeat on the address that fired VM_FAULT_RETRY
			 * without FAULT_FLAG_ALLOW_RETRY but with
			 * FAULT_FLAG_TRIED.
			 */
			*locked = 1;
			lock_dropped = true;
			down_read(&mm->mmap_sem);
			ret = __get_user_pages(tsk, mm, start, 1, flags | FOLL_TRIED,
					       pages, NULL, NULL);
			if (ret != 1) {
				BUG_ON(ret > 1);
				if (!pages_done)
					pages_done = ret;
				break;
			}
			nr_pages--;
			pages_done++;
			if (!nr_pages)
				break;
			pages++;
			start += PAGE_SIZE;
		}
		if (lock_dropped && *locked) {
			/*
			 * We must let the caller know we temporarily dropped the lock
			 * and so the critical section protected by it was lost.
			 */
			up_read(&mm->mmap_sem);
			*locked = 0;
		}
		return pages_done;
	}

可以看到，这种“CPU代码”，语句上的相关性是极强的：我取一个页，如果取不到，就告诉
用户失败，取到了，对这个页里面的几个域进行赋值，如果是情况A，给这个值。如果是情
况B，给那个值。所以，“CPU代码”，你给我10个乘法器，这东西是没有什么意义的，反正
我大部分时候都是在做判断，前一个判断没有做完前，反正我也不能做下一个判断。而且
这恰恰是人类理性思考的特征，我能给你的明确控制就是这样的，这个东西改变不了。人
的理智永远不能思考“下意识”：看见红的东西，感受到了温度，想起自己正在锅炉房里面
，手想都不想就可以缩回来，这个用人脑是做不到的，下意识怎么做到的，人脑是想不清
楚的。

所以，编译器对CPU代码的调度。主要是调度寄存器：我有32个寄存器，你要做一组连续的
控制，我也就能保证你少数几条不相关的指令，不会因为有限的寄存器而产生互相依赖。
我只能保证我把你内存中的数据（因为要在CPU中执行）尽量地分开给你的寄存器，保证没
有依赖的两个指令，可以被独立的执行部件来执行。至于这些部件的利用效率，其实我是
不怎么在乎的，因为这没啥意义。

限制CPU执行并行度提升的不是CPU的结构，而是人脑。我给你的就是连续的，有依赖的执
行序列，你要完全满足我的要求，你就只能一步步走，速度只取决于你每步的速度，增加
执行部件于事无补。C语言也是基于这个逻辑来设计的，它左右了你的并行度提升。它能实
施的主要提升并行度的手段，更多是线程，线程本质也是线性依赖的，只是在内存一级组
织出多个独立实体来，从而执行更多，线程不能带来寄存器使用效率的提升。

TPU则不同，比如它里面有100个卷积计算器，它的整个目的就是认为你会有100个同步并行
的卷积运算可以同时进行。那么在语义上，你就得能给出这100个卷积，编译器才有可能调
度TPU里面的缓存或者寄存器，实现所有执行部件的高效。

所以，TPU的调度，无论你怎么设计，离不开对执行体和缓冲区的调度。你不能离开这一个
特点来给TPU提供描述。但对TPU来说，执行体的数量和缓冲区的大小，必然是会升级的。
把这一层信息给开发者，就相当于告诉别人不要升级了。就算你要你说你可以分两层，先
给一个C语言层，然后再给一个高层语言调度为C语言，这也没有意义，因为C语言那一层没
有人会写程序，真要写的要不是汇编，要不是高层语言。一个可以被生成的语言，对开发
者是没有意义的。所以，做一个类似CPU的表述层，这件事本身对TPU来说没有意义。

然后我们考虑第二个问题，我们是通过提供一组向量计算的方式让编译器进行调度呢？还
是提供一组线程来给TPU OS（或者叫Runtime也行）进行调度呢？

如前所述，线程的前提是在内存使用上把每个独立的线性计算过程Hash开，用户是认知内
存的使用的。如果我们依靠线程来提供服务，开发者必然是认知内存的分配的。由于TPU的
缓存区在TPU内部，也就是开发者必须认知这个缓存区的大小。这违背了我们前面说的，缓
冲区的大小，跨代肯定是不同的。

你看，我们简单这样推演一下，你就会发现，其实从我们确定了TPU要解决的问题的时候，
无论你用什么技巧，你的选择就只剩下一个：让用户把整片的，需要进行向量计算的要求
，整体提供给你的编译器，让它重排到你的TPU上。这个过程当然要对大量的用户实例进行
分析，基于这个来确定语法乃至决定TPU的硬件配置。但无论如何，其他路是一定不通的，
根本没有必要走。

抽象，通常就是这么个东西，所有东西都是可变的，我们要抓住主要矛盾和矛盾的主要方
面，所以抽象的中心是需求，而不是现在的硬件做成什么样。


补充1：我们再拉高一层来想这个问题：如果我们把编译器定义在CPU和TPU之上，能否获得
更多的优势？也就是说，你让我编译，我知道我的程序有可能选择运行在CPU上，也可能运
行在TPU上，让编译器根据代码的实际情况来调配两边的资源，这样能否提升执行效率？

这个问题，其实就是问：一段语义（计算要求）表述，是否有可能微妙到人无法直接简单
判断它是并行计算还是逻辑的串行判断？

我想不出这种场景，除非你说你的TPU有部分计算根本就没法做，需要用CPU来模拟。我简
单判断：拉高这一层的价值不大。


补充2：简单推演一下我们的整个计算要求可以怎么下（我对这个还没有深入的分析，完全
靠YY来想一种场景，请读者指正。后面也会根据案例分析的深入对此进行修正）：

比如我们就做一个简单的三层全关联卷积，用Sigmoid做激活函数（Sigmoid不会是个计算
单元，但我姑且认为是吧），输入一开始肯定得在内存中，我们有

第一层A(shape=[100])

第二层B(shape=[100, 10]）

第三层C（shape=[10,4]）

我们也不放偏置。TPU的计算缓冲假定是统一的，可以支持300个计算值，包含10个卷积计算单元，每次计算的向量长度是32。那我们排指令估计得这样排：

    | Load A的32个值到计算缓冲（寄存器也行，反正总得取进来才能处理）
    | Load B.weight的32个值到计算缓冲
    | 发起卷积计算（但不等待）
    | Load A的下32个值到计算缓冲
    | Load B.weight的下32个值到计算缓冲中
    | 发起卷积计算（但不等待）
    | 如此类推，直到用完卷积计算单元，流水线或者缓冲……
    | 同步等待计算完成
    | 调度Sigmoid计算单元做下一步向量计算（但不等待）
    | Load A的下32个值到计算缓冲中……（如此类推）
    | 等待计算完成，回写计算缓冲到内存，让出的计算缓冲用于下一步计算……

这样，我们可能会这样来定义TPU编译器应该提供的语法：::

        define_external(A, int14, [100], program.v1);  #假设是CPU负责准备数据，进入TPU程序后，根据特定的语法获得对应数据的指针
        define_external(B, int14, [100, 10], program.v2)
        define_external(C, int14, [10, 4], program.v3)
        define_internal(tmp1, int14, [100], program.v4)
        define_external(D, int14, [4], program.v5)

        for i in [0, 9]:
          tmp[i] = matmul(A, B[i])
          tmp[i] = sigmoid(tmp[i])
        for i in [0, 3]:
          D[i] = matmul(tmp, C[i])

        return;

这样，我们就有一组内存对象，计算的时候根据硬件能力调度到内部buffer中，只要内部内存还够，我们就不同步出去，这样编译器才会有足够的余量来对流水线进行优化。



版本控制
========

V1：完成了初稿，把骨干架起来了，其他细节待补。

V2：加了两个补充讨论，设想一下TPU的可能语法会是什么样的。
