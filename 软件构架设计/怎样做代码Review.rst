.. Kenneth Lee 版权所有 2017-2020

:Authors: Kenneth Lee
:Version: 1.0

怎样做代码Review
****************

Review是极为重要的代码质量工艺。本文介绍这个工艺步骤的执行要领。

很多人都说Review很重要，但我们本身是否真的认为这个步骤非常重要呢？我们在生活中
，说某个事情重要，其实有纸面上的，有实践中的。不少同学和同学说话的时候都劝人家
不要玩游戏，自己回家第一件事是打开游戏机。长大了也见不得会更好，老同学聚会劝人
家“少抽点烟，对身体不好”，说完就自己点一支。

Review这个事情一样，说的时候，都说“Review”很重要，实际上，到时间不够的时候，首
先割掉的是Review。甚至，在项目上多给你一个月，你首先也不投在Review上，而宁愿投
在系统测试上。我们得从这个角度看待所谓“Review的重要性”，否则，所谓“Review很重要
”根本就是一句空话。

错误地认可“Review很重要”，不仅仅是个工作量取舍的问题。还是个如何应用Review的问
题。为什么我们宁愿投入更多的时间到测试上，或者增加功能上，而不是代码Review上呢
？因为我们不一定注意到Review能解决多少其实系统测试测试不到的问题。

我们要这样理解这个问题：一本书，或者你自己写一篇博文，不Review一次或者几次。你
对拿出正式出版，有多大信心？我个人是一点信心都没有。Review是唯一保证一段文字是
否正确的手段。

但我们在程序上不是这样认为，因为我们可以运行，程序本质上不是用来看，而是用来运
行。这种情况，为什么还需要Review？我想是因为运行无法穷举，如果你的程序的出入口
很容易穷举，你确实可以用系统测试代替代码Review。其实比如CPU核的验证就是这样的，
我们也信不过肉眼的Review，这种就直接上测试套，随机覆盖，但这种测试都是以月为单
位来做的，你是不是耗得起就要看你这是个什么业务了。

解决无法穷举的基本工艺有两个，一个是Review，一个是UT。这两个解决不同的问题，不
能互相取代。Review主要解决的问题是语义，UT解决的问题主要是流程。

比如你调用了a=malloc(size)，并且允许size=0，那么你就要判断一下你要支持的所有目
标平台，是不是都支持malloc(size)的入口是0，并且，这样分配出来的指针是可以用free
来释放的（不少非posix的平台可不支持这个），这种问题用UT或者系统测试，都测试不出
来。这种问题就是Review的强项。

换过来，比如你做一组malloc()，然后在中间出现错误的时候要退回去。或者做一个多重
循环遍历一个Hash数组并上一个单向链表。这种用人脑就远远不如计算机了，就不应该通
过Review来发现，而应该采用UT。

这样，我们就可以总结出Review的关键了。软件工程之所以是工程，就是重点解决成本问
题。Review就是个工程问题，我们要采用最低成本的方法达成最好的结果。

所以Review的工程要领或者说工艺要求是：

1. 不通过Review发现UT可以发现的问题，不用Review取代UT

2. Review的评审重点是语义逻辑（包括错误的函数语义理解，错误的名称定义，错误的
   Comment，错误的Assert，都是），代码构架（比如是否有冗余，分层是否错误，和上
   级设计是否对应得上等），统计，跟踪，异常等处理逻辑在业务上的正确性，还有缺少
   的功能，可靠性，可维护性，可测试性等“反面理解”的问题。

3. 基于2，所以Review采用广度优先遍历，而不是深度优先遍历（UT才采用深度优先遍历
   ）。也就是说，看完一个函数，再看下一个函数，而不跟随到那个函数的下面。

比如下面这个函数：::

        /**
         *  prot_autoc_read_82599 - Hides MAC differences needed for AUTOC read
         *  @hw: pointer to hardware structure
         *  @locked: Return the if we locked for this read.
         *  @reg_val: Value we read from AUTOC
         *
         *  For this part (82599) we need to wrap read-modify-writes with a possible
         *  FW/SW lock.  It is assumed this lock will be freed with the next
         *  prot_autoc_write_82599().  Note, that locked can only be true in cases
         *  where this function doesn't return an error.
         **/
        static s32 prot_autoc_read_82599(struct ixgbe_hw *hw, bool *locked,
                                         u32 *reg_val)
        {
                s32 ret_val;

                *locked = false;
                /* If LESM is on then we need to hold the SW/FW semaphore. */
                if (ixgbe_verify_lesm_fw_enabled_82599(hw)) {
                        ret_val = hw->mac.ops.acquire_swfw_sync(hw,
                                                IXGBE_GSSR_MAC_CSR_SM);
                        if (ret_val)
                                return IXGBE_ERR_SWFW_SYNC;

                        *locked = true;
                }

                *reg_val = IXGBE_READ_REG(hw, IXGBE_AUTOC);
                return 0;
        }

Review这个代码，很多人看到ixgbe_verify_lesm_fw_enabled_82599(hw)就想着跟过去看
看那个流程有没有问题。但你不是计算机，你执行它干什么？你要做的是，判断这里说
lesm的firmware使能了，你是不是应该acquire它，如果没有使能，你又能不能去读那个寄
存器。这样才会聚焦的到“语义”上。至于穿过去的流程，你的脑子肯定没有计算机好使，
不反对看，但那不是重点。

而且，Review应该对这里描述下来的每句话，包括注释，都要“过眼”。这个函数是不是应
该static的？读寄存器到底应该用s32还是u32返回？为什么？s32, u32, int, size_t,
void * 这种类型选择，如果考虑到代码是可以运行在多个硬件平台上的，基本上都有唯一
选择。

还有注释，我这个例子是在Linux主线代码中随便拷出来的，它的注释就有错。::

        @locked: Return the if we locked for this read.

Return the是什么鬼意思？

无论是Review还是编程，都要基于“语义”，你的程序才具有延续性，仅仅能跑，是无法支
持长远的，这就叫基于“语义”来编程。

最后谈谈组织，我经验比较好的组织方法是这样：

1. 每次选择1000行左右的代码，不包括作者2-3人参与，必须是对相关模块熟识的。

2. 先由作者做一个代码介绍，按广度优先遍历整个代码，全体参与需要5-10个小时

3. （可选）如果代码足够复杂，可以下来再做一次个人Review，时间上我没有经验，而且
   一旦离开会场，这些人看不看难说得很

4. 汇总会议，记录下所有的问题

5. （可选）作者修改代码，然后最后做一次跟踪，时间视问题多寡而定

6. 强调：代码Review必须在UT之前做

