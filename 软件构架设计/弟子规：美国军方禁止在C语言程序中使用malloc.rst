.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

弟子规：美国军方禁止在C语言程序中使用malloc
********************************************

今天有朋友分享了一个今日头条文档，标题是这样的：《为了更加安全稳定，美国军方禁
止在C语言中使用malloc》。

这种标题一看就是知道是胡说八道，我都没有兴趣打开看。但联系最近的一些别的讨论，
我就借题发挥，讨论关于“动脑”的问题。

为什么我说这种标题我一看就是“胡说八道”？——因为没有任何一个靠谱的架构师会去定缺
乏逻辑支持的“断言”的。如果美国军方能出发出这样的断言，美国就真的没落了。但另一
方面说，国内还真有企业或者组织敢出这样的东西的，这是我们的差距。就不说企业吧。
我们的网络上充斥着这种智障文字，我可没在老美的技术论坛上看过。

如果你打开这个“头条”来看，就会发现，这个作者的的逻辑链是这样的：动态分配内存是
巴拉巴拉-->在safety-critical的嵌入式C语言开发中，动态内存分配被认为是禁忌-->又
：美国军方按照DO-178B标准，在safety-critical的嵌入式航空电子设备代码中禁止动态
内存分配-->所以，我们来讨论为什么美国军方禁止使用malloc和free……

这真是一个极好的反面教材，因为它的每个逻辑推理都是断裂的。

动态分配内存可以代理为malloc吗？DO-178B标准可以代理为美国军方要求吗？禁止嵌入式
航空电子设备代码中使用动态内存分配可以代理为美国军方禁止使用malloc吗？……为什么
这样的逻辑可以在我们的行业中大行其道的？

DO-178B是什么？我一时也看不完（关键是这个文本好像不是可以公开下载的），但这是人
家的文档体系：

        .. figure:: _static/do178b.jpg

它可是从开发流程开始定义整个策略的。这也符合我对美国整个技术体系的认识，我看过
的大部分美国标准，都是这样从大问题开始分解，从流程，到方法，到部件的具体要求，
到数学证明，都是连续的逻辑。这些逻辑不一定是A必然导致B的关系，但必然有具体的因
果关系来决定增加约束的目的，并保证约束必然是在条件下发挥作用的。

实际上，就算我不去查这个标准的具体文本，我都能猜到这里的不许使用动态资源分配的
原因是什么。因为很多需要进行形式化验证的关键部件都不允许使用动态资源分配，因为
这样很容易导致状态机的状态数量失控，这可不仅仅是不允许malloc，它其实不允许任何
意义的动态资源分配。但这和美国军方禁不禁止malloc十万八千里。——每件事情都是有范
围的，多一个条件结论是会反过来的。只有不动脑子的才会认为美国军方禁止使用malloc
。

这个事情让我想起最近知乎老来推送的《弟子规》话题，我发现很多为《弟子规》辩护的
人的逻辑也是类似的。比如他们会说，“父母呼，应勿缓”，这有错吗？“物虽小，勿私藏”
，这不是劝人向善吗？——这个压根儿就不是有没有错的问题，这整个玩意儿就是教你不要
动脑，它是一组断言——反正你是个傻逼，脑子就不要动了，按规矩办就是了。所以，弟子
规的问题简单说就是傻逼要出来刷存在感，它是无解的，你无法给一个傻逼证明他们是傻
逼。

而那些在极高的抽象上让人：不要用goto，不能使用魔鬼数字，一个函数中必须完成上锁
和解锁的整个过程，不要使用malloc和free。也是一样的问题。出这种主意的人要离他们
远一点，傻逼是会传染的。

当然，最怕的是你的领导让你背这种弟子规，那你就只好自求多福了，主要看看他给多少
钱吧，记得算上青春损失费什么的。


补充1.20190617：谢谢有读者私信我这个“头条”的英文原文是出自哪里的：
http://mil-embedded.com/articles/justifiably-apis-militaryaerospace-embedded-code/
。他可能觉得该“头条”可能仅仅是个“标题党”，从内容上说，这位读者认为“至少美国军方
禁止在嵌入式航空电子设备代码中使用动态内存分配”。

这个观点值得讨论，因为这是我在本文中要讨论的关键问题。

我在原文中反复使用“代理为”这种提法，这个概念来自Amzon的CEO Jeff Bezos（参考：
What Is Jeff Bezos's "Day 1" Philosophy?））的Resist Proxies。他认为大公司很容
易出现的一个问题就是代理，比如业绩好不好，不去分析业绩的方方面面，就“代理”为一
个指标：销售额。开发效率高不高，不去看客户的反应和收益，“代理”为“日产代码量”。
这样让决策简单，让管理者有everything under control的快感，但这离实际的情况越来
越远。

对软件架构师来说，这个问题是一样的，由于信息量摆在那里，我们免不了要使用“代理的
概念”，比如“这是一条广泛承认的原则：不要使用malloc”，这就是一个“代理”。这可以简
化我们很多决策——不然怎么说架构师都是受虐狂呢——没得选择才是架构师的心头所好。因
为没得选，就意味着对手很可能也没得选，你就可以放心地放弃这个角度的劳心劳力了）
。

但理智一点，其实对架构师来说，更可怕的是你给自己上了锁链，但你的对手没有。

“不要使用malloc”？我可没有看见谁敢轻易给自己套上这个枷锁吧？

回到这个“补充问题”本身。这个作者（Steve Graves）看来是一个给美国陆军供货的公司
（主要做In-Memory嵌入式数据库）的CEO，他的标题是：Justifiably taboo: Avoiding
malloc()/free() APIs in military/aerospace embedded code。译成中文大概是：《可
被证明的禁忌：避免在军队/航空器嵌入式代码中使用malloc/free API》。其实他强调的
不是“美国军方不让使用malloc”，而是“我告诉你有什么办法避开美国军方不让用malloc的
障碍”——这个大概率是给自己的数据库算法带盐的。

这个表述和《为了更加安全稳定，美国军方禁止在C语言中使用malloc》并不能互相代理。
后者是个“断言”，前者么，应该说“是一个别有用心的暗示”。

美国军方禁止在C语言中使用malloc的说法，在这个Steve的英文版本是这样表述的：

        | But dynamic allocation is widely considered taboo in 
        | safety-critical embedded software. The use of the C 
        | runtime library’s malloc() and free() APIs, which do 
        | the grunt work of dynamic allocation, can introduce 
        | disastrous side effects such as memory leaks or 
        | fragmentation. Further, malloc() can exhibit wildly
        | unpredictable performance and become a bottleneck in
        | multithreaded programs on multicore systems. Due to 
        | its risk, dynamic memory allocation is forbidden, under
        | the DO-178B standard, in safety-critical embedded avionics
        | code. Due to its risk, dynamic memory allocation is 
        | forbidden, under the DO-178B standard, in safety-critical 
        | embedded avionics code.

首先这个家伙就不是个好鸟，前面他还在说malloc，后面强行代理为了dynamic memory
allocation。而中文版再把这个代理的结果放到标题上。

但根据这里（Dynamic Memory Allocation: Justifiably Taboo?）的引用，DO-178B的表
述是这样的：

        | Software Design Standards should include…constraints 
        | on design, for example, exclusion of recursion, dynamic 
        | objects, data aliases, and compacted expressions.

这个Steve其实是强行把dynamic objects代理为了malloc，然后提出另一个dynamic
object算法，证明：我没有使用malloc，所以我没有使用dynamic object。从而买盐：我
们的数据库可以卖给军方。

他很可能可以卖给军方，但原因恰恰是，DO-178B并没有下很强硬的“断言”，DO-178B使用
了非常技巧的要求：

        | 软件设计标准（前面在定义流程的时候可能要求设计过程需要有标准）
        | 应该在设计中包含……限制，比如禁止使用递归，动态对象，数据别名
        | 和compacted expressions（不知道这是啥）。

注意到了吗？DO-178B并不敢肯定你一定是不能用动态对象的，它只是“建议”你考虑把这样
的要求写入你的编程规范。如果你傻不拉几为了脑子的方便，就把“不得使用malloc，或者
不得使用动态对象分配”写入你的编程规范，你就输给Steve了。

希望这个例子让某些架构师或者“领导”理解，你们那些所谓“一心向好”，“严格要求”，“有
比没有好”，能给竞争力带来多大的伤害。


补充2.20190619：今天回来看到几个讨论，我不知道是我表述得不够清楚，还是他们根本
就是只看了一个标题，所以我更直接地表述一下我的观点：我不反对“美国军方某些人在审
计特定软件的时候看到了malloc会条件反射地拒绝这个软件。”，我在表述的是：把一个复
杂的逻辑代理为一条简单的行为规则，是非常危险的行为。如果你只是负责一个小模块，
一个小产品，这伤害不大，但你上升为一个行业行为，或者一个组织行为，这就非常危险
了。评论区中不少人傲慢的态度，已经证明了我说的现象并非少数，是什么给你们自信，
可以大言不惭地说出“军工行业不用malloc是共识”这样武断的推论来的？。你们说话的时
候用过脑子吗？还是学某些《弟子规》的推广者那样：“让你听父母的话有错吗？”
