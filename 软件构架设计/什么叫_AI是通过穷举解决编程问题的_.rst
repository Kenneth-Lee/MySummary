.. Kenneth Lee 版权所有 2026

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2026-07-15
:Status: Draft

什么叫“AI是通过穷举解决编程问题的”
**********************************

这个问题其实我觉得对程序员都不用解释，但无奈和我讨论的人中有些是是没入门的，对
于“可能性空间穷举”没有任何认识，所以我还是补一个AI的思维过程，来说明这句话是什
么意思。下面是我在一段通过AI编码的时候，AI思维过程的截屏：::

 我觉得方案 1 更合理。但我倾向于让约束更清晰：Node 创建后，要么全部用 AddCaller（逐个），要么用一次 AddCallers（批量），不能混合。

 但这样的话，如果先用了 AddCaller，再想用 AddCallers，应该也禁止。这需要一个标志来区分"未锁定"、"单个模式"、"批量模式"。

 不过，让我再想一下用户的原意。用户说："AddCallers是独占的，针对一个Node只能用一次。前后不能再增加其他Caller了。"
 这明确说了"前后"都不能再增加。也就是说：
 - 用了 AddCallers 后：不能再 AddCaller 或 AddCallers
 - 用 AddCaller 后：是否不能再 AddCallers？用户说的是"AddCallers 是独占的"，可能只限制 AddCallers 本身。

 为了简洁，我认为最好的方案是：AddCallers 设置一个锁定标志，之后任何 add（AddCaller 或 AddCallers）都 assert 失败。而对于 AddCaller 后再
 AddCallers 的情况，也可以用同样的标志来检测——如果 node 上已经有 caller 了，AddCallers 就 assert 失败。

 但"node 上已经有 caller"的检测需要计数或检查 libgqm 的 caller 数量。libgqm 可能有这个信息...

 实际上，让我看看更简单的方案。redisGqm 已经有 caller_sm 字段。我可以加一个 caller_mode 枚举：

 ```c
   enum {
       GQM_CALLER_MODE_NONE,    // 未加 caller
       GQM_CALLER_MODE_SINGLE,  // 用了 AddCaller
       GQM_CALLER_MODE_BATCH,   // 用了 AddCallers
   } caller_mode;
 ```

 - AddCaller：如果 caller_mode == BATCH，assert 失败；否则设为 SINGLE
 - AddCallers：如果 caller_mode != NONE，assert 失败；否则设为 BATCH

 这样就完全锁定了，不能混合使用。

 不过这增加了一个枚举字段。或者更简单——用两个 bool 或直接用 caller_sm 的状态？

 其实，让我重新审视。用户的问题核心是：caller_sm 只有一个槽，混合使用会导致内存管理错误。

 最简单的修复：AddCallers 在 caller_sm != NULL 时 assert 失败（防止重复调用）。AddCaller 在 caller_sm != NULL 时也 assert
 失败（防止批量后再加单个）。但 AddCallers 在已经有 AddCaller 创建的 caller 时怎么办？这需要检测 libgqm 的 caller 数量。

 让我看看 libgqm 是否有获取 caller 数量的接口...

 实际上，我觉得最干净的方案是方案 1 的严格版本：Node 一旦被"定型"，就不能再用另一种方式加 caller。用一个 caller_mode 枚举实现。

 但等等，用户说的是"AddCallers是独占的，针对一个Node只能用一次。前后不能再增加其他Caller了"。这句话的重点是 AddCallers 之后不能再加。它没有说
 AddCaller 之后不能再用 AddCallers。

 所以最简单的实现就是：
 - AddCallers 之后设置一个标志 batch_done = true
 - AddCaller 和 AddCallers 在 batch_done == true 时 assert 失败

 但如果先用了 AddCaller 再用 AddCallers，这个场景需要处理吗？如果 caller_sm == NULL（没有用 AddCallers），AddCallers 仍然可以执行。这时 node
 上既有 AddCaller 的独立 caller（各自有 peer_sm），又有 AddCallers 的批量 caller（共享 peer_sm）。这种混合在内存管理上没有问题——独立的各自
 munmap，共享的由 Close munmap。

 所以实际上唯一的问题是：AddCallers 不能调用两次（caller_sm 会被覆盖，第一次的 mapping 泄漏）。

 让我重新分析：
 - AddCaller 后 AddCallers：OK，独立 caller 各自管 peer_sm，批量 caller 共享 caller_sm
 - AddCallers 后 AddCaller：OK？批量 caller 共享 caller_sm，独立 caller 各自管 peer_sm。好像也 OK
 - AddCallers 后 AddCallers：caller_sm 被覆盖，第一次的 mapping 泄漏

 所以唯一真正的问题是重复 AddCallers。但这在 benchmark 场景不会发生（每个 thread 只创建一次）。

 不过用户说"容易用错"。从防御性编程的角度，应该阻止混合使用。

 我倾向于方案 1（独占模式），因为：
 1. 简单清晰
 2. 当前没有混合使用的场景
 3. 避免未来误用

 让我提出这个方案，用 caller_mode 枚举实现。

 但其实，我觉得最干净的表述是：

 ```c
   /* 一个 Node 只能用一种 caller 模式：
    * - 单个模式：反复调用 AddCaller（gossip 场景）
    * - 批量模式：调用一次 AddCallers（benchmark 场景）
    * 两种模式不能混合。 */
 ```

 实现上，在 redisGqm 中加一个字段：

 ```c
   int batch_mode;  /* 1 = batch callers created, no more adds allowed */
 ```

 或者更语义化的枚举。让我选择最简单的。

 我觉得用一个 bool/int 标志就够了。AddCallers 时检查并设置。AddCaller 时检查。

我也不解释这个问题具体是什么样的，你就看看它的思维模式就行了：它就是组合几个条
件，得到一个结果，再组合几个条件，又得到一个结果，然后把相同结果的条件组合到一
个大的分类中：先AddCaller再AddCallers（注意复数），情形如何？先AddCallers再
AddCaller，情形如何？先AddCallers然后有AddCallers情形又如何？……然后发现
AddCaller/AddCallers后做AddCallers，后者面对的条件是一样的，所以这两种情况就可
以合并为一种情况去处理。

程序员大部分时候就是在做这种穷举和合并，能用越少的条件得到一样的设想中的结果，
这个程序就越“干净”，因为可能性空间少。可能性空间隔得越碎，这个程序就越难维护，
结果也越加无法控制，因为根本没有考虑过遇到那种情况会怎么样。

我们常常说，程序的test-to-pass流程只占50%以下的代码，剩下的的全是异常流程
（test-to-fail），就是这个意思。如果用户只用设想好的可能性，按这个可能性空间写
程序，代码量比正常的程序小得多。严肃的产品，大部分代码是解决预期之外的情形：黑
客来攻击怎么办？用户输错了怎么办？用户的流程走了一半离开了，后来重新开始怎么
办？……把这些可能性全部穷举了，每种都有办法处理，这才是个严肃的程序。这种程序，
用来处理异常情况的代码超过全部代码的50%。所以严肃代码成本才高。

我们经常看到那些外行写的程序，让你在网站上填个表，中间出个错，你就再也填不了了，
要人为在后台给你做清理，或者你从停车场出来，第一次交费不成功，你的车后退一下再
想出去，它说你已经出场了，但死活不给你开闸……这些全都是那些劣质程序员没有推理异
常情形给你弄出来的。

程序员这样思考问题，AI也不是像那些不看代码的所谓“Vibe Coding”人员想象的那样，
把所有信息一堆，马上就能告诉你结果的啊。AI也是这样一个可能性空间，一个可能性空
间这样穷举出来的啊，如果空间太多，AI一样会像那些劣质程序员那样，在可能性没有全
部枚举完就给你出结论啊，你怎么会想到“以后上下文够长了，这个问题自然就能解决了”
的呢？就凭你看不懂代码吗？

顺便在说说AI上面那个推理，最终我是怎么回答它的。我的回答是：::

  你这个推理最终还是增加了一个标记，但我推理似乎不需要这个标记，让我推一下给你
  看：首先，如果Node中没有caller，无论这是有人加过还是加了以后删除，这时都可以
  AddCallers，因为里面本来就不会冲突，反之，就必然不能AddCallers()。如果加过
  AddCallers，那么peer_sm就必然有内容，这时就不允许AddCallers/AddCaller()。这
  样，综合“有没有callers”和“有没有peer_sm”这两个条件，我们就足够处理所有的可能
  性了，为什么还要加一个标记呢？

给它提示了这个以后，它也是通过穷举来确认的：::

 你说得对，让我推一遍验证你的推理。

 ┌───┬─────────────┬─────────────┬────────────────────────┬────────────┬─────────────┐
 │ # │ 有 callers? │ 有 peer_sm? │ 场景                   │ AddCaller? │ AddCallers? │
 ├───┼─────────────┼─────────────┼────────────────────────┼────────────┼─────────────┤
 │ 1 │ 否          │ 否          │ 新 Node                │ ✅         │ ✅          │
 ├───┼─────────────┼─────────────┼────────────────────────┼────────────┼─────────────┤
 │ 2 │ 是          │ 否          │ 独立 callers（gossip） │ ✅         │ ❌          │
 ├───┼─────────────┼─────────────┼────────────────────────┼────────────┼─────────────┤
 │ 3 │ 是          │ 是          │ 批量 callers 存在      │ ❌         │ ❌          │
 ├───┼─────────────┼─────────────┼────────────────────────┼────────────┼─────────────┤
 │ 4 │ 否          │ 是          │ 批量 callers 全删了    │ ❌         │ ❌          │
 └───┴─────────────┴─────────────┴────────────────────────┴────────────┴─────────────┘

 推导：
 - AddCaller：只需 peer_sm == NULL（挡住 case 3/4）
 - AddCallers：需要 caller_count == 0（挡住 case 2）且 peer_sm == NULL（挡住 case 3/4）

 确实不需要 batch_locked。peer_sm != NULL 本身就是"批量模式用过"的证据。唯一缺少的信息是 caller 数量——需要从 node 查询。

你看，这就是我说的：AI通常在“抓主要矛盾和矛盾的主要方面”上不如人。我这里这个分
类方法就和它不同，我穷举的可能性空间比它少。最终我的程序的可能性空间就少了，因
为我用现有的状态就足够得到结论了。而AI的方法，如果没有我这个控制，它就会为这个
程序增加一个状态，新的状态乘上程序中已有的状态，它未来要穷举的空间就更大了。这
种程序这样维护下去，后面它就怎么都穷举不完了。

这种问题AI会成长吗？我觉得不会，因为这里其实不完全是对程序逻辑的认识，而是对事
实的认识，我脑中其实不但有代码的约束，我还有现实世界的约束，在我严重，Caller和
Callee不仅仅是代码表达的那些逻辑，我还有我对“调用”本身在客观世界如何用的这件事
的认识，AI广度太大，它很难把注意力集中到这种问题上的，这个问题人如果有一样的广
度，注意力也没法聚焦。这一点，没有颠覆性的发展，是不可能解决的。
