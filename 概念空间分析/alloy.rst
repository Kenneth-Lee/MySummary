.. Kenneth Lee 版权所有 2022

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2022-10-19
:Status: Draft

alloy
*****

介绍
====

分析Alloy主要有两个目的：

1. 本身要用这个工具，完成初步的学习自然要对它的整个逻辑建一次模。
2. 学习这个东西对理解
   :doc:`维特根斯坦的理论 <../逻辑哲学论分析/README>`
   很有帮助，写出来可以作为那边的一个参考。

Alloy是一个建模工具，它的主页在这里：
`Alloy <https://www.csail.mit.edu/research/alloy>`_
。

它可以做很多纯逻辑模型的分析，比如Spetre/Meltdown的攻击模型，内存序模型等等。
RISC-V的内存序就是用这种方法进行的分析。

Alloy有Mac的Native版本，其他平台是java的，可以用java -jar运行，没有额外的依赖，
代码在github上开源：
`Alloy Source <https://github.com/AlloyTools/org.alloytools.alloy/releases>`_

作者为这个工具写了一本书，叫《\ *Software Abstractions*\ 》，详细介绍了这个工具
的用法。但如果不熟悉相关概念，纯从程序员的角度去理解它，很容易把自己绕晕。本文
会通过澄清一些基本的概念来避免这个问题，澄清这些基本概念，也有助于我们理解前面
提到的逻辑哲学论的基本概念。

一阶谓词逻辑
============

Alloy的语法基础是一阶谓词逻辑。我们不用因为听到这种哲学名词就被吓着了，实际上这
个学科的基础知识大部分理科生都或多或少有理解，而我们也不需要非常高深的理解去认
知Alloy。

一阶谓词逻辑的英文是First Order Logic，或者Predicate Logic，又或者
Quantification logic，又或者First Order Predicate Calculus。把它的英文名提出来，
有利于我们理解这个专业领域到底是研究什么问题的。

我们平时说的逻辑，通常是不包含变量的，称为“命题逻辑”（Prepersition Logic）。比
如我们说：

1. 卡拉是条狗
2. 狗有四条腿
3. 所以卡拉有四条腿

请注意了，这个逻辑的所有感知，都在描述上，没有数学（集合）的成分在其中。1和2定
义了两个集合，但这个集合是什么呢？需要我们从语义上理解出来，然后我们才能得到第
三个结论。

要把这个东西转化为数学，我们要明确定义这个集合，这样就引入了谓词逻辑（Predicate
Logic），它强调的是“谓语”对集合的定义作用：把卡拉看作一个集合x，这个集合的范围
定义由它的谓语f决定。那么，整个命题就可以定义为f(x)。使命题为真的x的集合，就是
这个命题的解。

这样以后，我们通过定义x这个集合的数量来描述命题的解的特征，比如我们常见的证明题：
“存在多个自然数x，而且x>10而且，x<13”。这个描述集合大小的形容词，就成为这个谓词
的解的范围的描述符了。这称为谓词逻辑的”量词“，所以，这种逻辑也称为“量词逻辑
(Quantification Logic）”。

谓词逻辑的基础就是这个，更复杂的反正我也不懂，它是一个抽象谓词形式描述的系统的
规律的系统，但要理解Alloy，我们只需要理解每个具体的具像，所以，我们理解到这个地
步就够了。

再理解一下什么是“阶（Order）”。按定义，如果量词可以用于谓词（本质就是谓词可以成
为谓词函数的参数），这个体系就称为Higher Order Logic。能叠加一层就是二阶谓词逻
辑，能叠加两层就是三阶谓词逻辑。所以，一阶谓词逻辑很特别，它的集合和它的谓词函
数是严格分离的，“卡拉是条狗”和“‘x是条狗'这句话有道理”中，‘x是条狗’是个独立的解，
不能用作谓词。所以，它和”卡拉是条狗“这个定义是没有任何关系的（当然，你可以去定义
它们的关系，但那个是额外定义出来的，不是因为有是条狗这个描述）。

这个概念有助于我们理解逻辑哲学论中的Can be said clearly和Must be passed over in
silence是什么。谓词就是Can be said clearly的，因为它是明确的集合，是可以运算的
东西，任何时候都有一个集合的结果。而解本身是只能意会的，我们说不清楚狗是什么，
除了被抽象出来的部分，其他部分你说那是狗它就是狗，反正没法说。你可以多补充一些
信息，那些信息会被加入到谓词定义中，但你总有一些东西是Must be passed over in
silence的。

谓词逻辑用到的符号我们其实很熟悉的：

* Quantifier：For Every（\ :math:`\forall`\ ），
  There exists（\ :math:`\exists`\ ）
* Connection：交集（conjunction，.），并集（disjunction，+），补集（~），推出
  （imply，->），等价（充要，<->）
* variable：用小写字母表示
* 括号：大中小括号都可以用

优先级是补，逻辑，Quantifier，Imply。

非逻辑符号用于表示谓词，函数和常数。通常用f_n表示函数，用P_n表示谓词。

针对某个问题的全部非逻辑符号称为signature，也就是我们前面提到的“解”的集合。它可
以有限，无限，空，甚至不可数。

如果变量被规定了quantify，那么它是绑定的，否则它就是free的。比如下面这个命题：

.. math::

   {\forall a | P(a, b)}

那么a是bound的，b是free的。这个概念本质上说明某个命题的成立和某个signature的选
择是不是有关系。很多推理过程会影响变量的bound和free属性。

谓词逻辑一个最重要的定理是德.摩根定理，它的集合本质是：

1. :math:`A \bigvee B = !A \bigwedge !B`
2. :math:`A \bigwedge B = !A \bigvee !B`

在谓词逻辑中它的表达是：

.. math::

   (1) {\forall x | P(x)} \equiv {!\exists x | !P(x)}

.. math::

   (2) {\exists x | P(x) } \equiv {!\forall x | !P(x)}

所以，它又称为反演律。

.. note::

  考察这个逻辑：存在x，使P(x)成立。这能否认为是两个集合的运算呢？其实是不行的，
  存在x是对P(x)的修饰。如果把X看作是x的所有可能取值的全集，P(x)其实X的一个子集，
  但存在x是这个属性的一个结论：它说明P(x)是结果是否是空集。也就是说：存在x，使
  P(x)成立在集合上应该表示为P(x)对x的限制为非空。而对所有x，P(x)成立在集合上表
  示P(x)对x的限制范围是X。

通过例子理解Alloy的原理
=======================

例子
----

谓词逻辑太抽象，我们还是用具体的Alloy代码来类比去理解会跟深刻一点。这个小节我们
通过《\ *Software Abstractions*\ 》中的一个例子来展开介绍Alloy的语法和用途。

下面这个模型定义建模“我是我自己的爷爷（或者外公）”这个命题的可能性：

.. code-block:: none

  abstract sig Person {
    father: lone Man,
    mother: lone Woman
  }
  sig Man extends Person {
    wife: lone Woman
  }
  sig Woman extends Person {
    husband: lone Man
  }
  fact Biology {
    no p: Person | p in p.^(mother + father)
  }
  fact Terminology {
    wife = ~husband
  }
  fact SocialConvention {
    no (wife + husband) & ^(mother + father)
  }
  assert NoSelfFather {
    no m: Man | m = m.father
  }
  check NoSelfFather
  fun grandpas (p: Person): set Person {
    let parent = mother + father + father.wife +mother.husband | p.parent.parent & Man
  }
  pred ownGrandpa (p: Man) {
    p in grandpas [p]
  }
  run ownGrandpa for 4

这里用的保留字几乎全部都是谓词逻辑直接继承过来的。其中sig就是signature。pred就
是predicate。在我们这个“世界”里，只有两种“解”（在Alloy中称为Atom）：Man, Woman。

signature
---------

signature定义了这个世界的所有解的全集的范围。比如上面的例子中：

.. code-block:: none

  abstract sig Person {
    father: lone Man,
    mother: lone Woman
  }
  sig Man extends Person {
    wife: lone Woman
  }
  sig Woman extends Person {
    husband: lone Man
  }

这里定义了Person，Man，Woman三个sig，这个世界中只由这三个sig的Atom们组成。

我这里想特别强调如下几点：

1. Atom是sig的实例，不是sig本身，sig是Man，那么它的Atom可能就是{John，Peter，
   Kenneth}，Man是这个集合的总称。
2. {John, Peter, Kenneth}是Man的其中一个解，Man可以有更多的解，每个解都是其中一
   个“平行世界”。这就是维特根斯坦说的World的概念（Alloy叫Universe，宇宙）。他的
   World，是由Can be said clearly的所有Signature的Atom组成的。你认为世界是这样
   的，那这个世界就会有那么多的atom，atom间有关系，但atom不从属于任何东西而存在。
   所有的“从属”，只是一种概念上的“关系”。请仔细想明白这个问题，A认为世界上只有
   {John, Peter和Kenneth}三个男人，B认为只有{John, Peter}两个男人，这是两个独立
   的“平行世界”，他们的“世界”并不相同。
3. 所以，定义signature，是定义一个所有解的一个范围，是一个解的集合，而Alloy的作
   用，是帮你把这个解找出来。
4. 注意，在这个定义中，所有signature的集合都是有限的。这就是为什么维特根斯坦说
   没有无限的世界。世界是有限的，所有我们对无限的理解，只是一个“最初如何，若n如
   何，则n-1如何”的有限认知，人脑根本就处理不了无限。

所以，Man和Woman都定义了我们世界中的两个正交的Atom的集合，而Person是它们的合集。
也就是说，如果：

1. Man = {John, Peter, Kenneth}
2. Woman = {Rose, Marry}

这里Person是Abstract的，所以Peron没有Man和Woman之外的成员，Person = Man + Woman。
如果这里我们不把Person定义成Abstract的，那么我们的World里面，就会允许一个Billy，它
是一个Person，但不是Man，也不是Woman，那个也是我们世界的一个解。

那么

3. Person = {John, Peter, Kenneth, Rose, Marry}

这其实也是这个世界里面全部的sig成员了。Alloy中用univ（Universal）表示。这是
Alloy两大常数之一，另一个常数是一个关联：iden = univ->univ。

然则，Person里面的father是什么呢？它不是组成这个世界的一阶Atom，而是一种定义Atom
间关系的Atom。如果John是Peter是父亲，Peter是Rose的父亲，那么

father = {(Peter, John) (Rose, Peter)}

这也是这个世界的其中一个解（的组成部分）。

所以，father也是集合，只是集合的成员是有关系的多个一阶Atom组成的向量而已。这种
集合，在Alloy中称为Relation。Sigangure可以认为是一个一维的Relation，又叫Unary，
二维的Relation称为Binary，而三维的称为Ternary。

这些都是集合运算，我们不要把这个当作编程语言中那种内存和作用域的关系，这些其实
都是集合而已。所以，作为一阶谓词逻辑，father可以被直接访问，不需要像编程语言那
样用Person.father来访问的。所有的Atom，也是无条件的值，Peter就是Peter，整个世界，
就只有一个Peter，没有Marry的丈夫Peter和，Rose的丈夫Peter这种说法。如果这个Atom
叫Peter，那么无论在哪里看到Peter，那就是那个Peter，不是其他Peter。

这就是维特根斯坦理论中说的：如果两个对象的同名或者属性完全相同，它们就是同一个
对象，如果你确认要认为它们是不同的对象，那么它们唯一有区别的属性是：“它们是不同
的”。这说起来很绕，本质原因是我们的“世界”是一个抽象，有很多Must be passed over
in silence的东西并没有被加入到世界中。

.. note::

   其实认真想想这里的Relation的概念，你会发现，所有的属性，其实不过是sig的关联，
   这也是为什么维特根斯坦的理论可以用关联图来表示所有的逻辑，而且声称“世界是五
   色的”，颜色只是sig，而某种对象有颜色，我们只是认为这个颜色和那个对象有关联而
   已。

   想明白这一点，不但有助于我们理解维特根斯坦，也有助于我们想明白怎么用Alloy去
   建模现实的模型。

fact
----

如果没有其他约束，那么我们的世界只受限于signature和它们在定义上的集合关系。
Alloy中通过fact收窄世界可以取的解的范围。上面的例子中，它定义了三个fact：

.. code-block:: none

  fact Biology {
    no p: Person | p in p.^(mother + father)
  }
  fact Terminology {
    wife = ~husband
  }
  fact SocialConvention {
    no (wife + husband) & ^(mother + father)
  }

第一fact Biology从“生物性”上约束我们的集合，它定义：不存在p（“不存在”是量词），使
p属于集合p.^(mother + father)，这里涉及三个操作符：

第一个是join（“.”），a.b表示用a集合的成员作为输入，求b relation集合的解。比如：

已知：

1. Man = {John, Peter, Kenneth}
2. father = {(Peter, John), (Rose, Peter)}

那么我们有

Man.father = {John}

father定义了Peter的输出是John，Rose的输出是Peter，然则，输入John, Peter，
Kenneth，得到的就只有John了。

^是关联性操作符，如果：

father = {(Peter, John), (John, Kenneth)}

那么我们有：

^father = {(Peter, John), (John, Kenneth), (Peter, Kenneth)}

在father中，Peter和John有关联，John和Kenneth有关联，那么我们认为Peter和Kenneth
也有关联。

最后是+，这是并集。

所以Biology这个fact约束的范围是：不存在一个属于Person的p，使得p是p的祖先。

同理，Terminology（用语）定义的是：所有妻子关系是丈夫关系的转置。~是什么意思我
们应该可以猜到了。

SocialConvention（社会习惯）定义的是：没有人和自己的祖先是夫妻关系。

这样定义以后，就把很多解排除到范围之外了。

其实想想这个模型，我们定义的这些条件是不是完全和现实一致呢？显然不是，甚至不说
一些违反条件的特例了。就算完全符合条件，我们也有很多条件没有引进来，比如“同一个
father的两人不能是夫妻”。

我强调这一点，是想说：

1. 不能认为模型就代表你建模的那个对象了。
2. 我们对世界的认识其实本质也是这样一个模型，Can be said clearly的东西也只是Can
   be said而已，不代表事实。

Assert
------

断言和谓词是Alloy的核心。前面的signature和fact定义世界的基本边界，而assert是让
Alloy尝试在这个定义的世界的所有自由解中，找到一个符合要求的解，让assert不成立。

Assert的语法像下面这样：

.. code-block:: none

  assert NoSelfFather {
    no m: Man | m = m.father
  }
  check NoSelfFather

这里检查：在前面的条件下，是否我们可以认为“没人会成为自己的父亲”。Alloy尝试找一
个反例，让它符合前面的所有要求，但不满足assert定义的范围。

Predicate
---------

check找反例，而run负责找正例，找一个满足条件的解。语法像下面这样：

.. code-block:: none

  fun grandpas (p: Person): set Person {
    let parent = mother + father + father.wife +mother.husband | p.parent.parent & Man
  }
  pred ownGrandpa (p: Man) {
    p in grandpas [p]
  }
  run ownGrandpa for 4

其中fun只是一个辅助设施，用来生成某个集合以便计算。set关键字是量词，这样的量词包括：

* one： 一个
* lone：0个或者一个
* set：0个或者多个
* some：一个或者多个
* all：全部

这里的fun定义了一个以p为索引的集合，成员由p的父母的父母和Man的交集组成（就是p的
爷爷或者外公）。有了这个基础设施，它定义的谓词是：对于某个属于Man集合的p，它符
合p是p的爷爷或者外公这个条件。

run表示开始寻找一个符合条件的解，后面那个4用于指定查找多大的范围，4本身表示每个
signature最多产生4个atom。

Join的计算符的进一步探讨
------------------------

Alloy这个Join操作符的设计很有意思，它一定程度说明白了集合角度的成员引用和数组下
标的本质。我们深入探讨一下这里的概念。

当我们定义Person() { father: lone Person }这个概念的时候，我们定义了一个sig和一个
relation。后者本质是Person->Person。如果Person和father是独立存放的，那么，我们
说某个Person的father是谁怎么找呢？那当然应该是：

  one p: Person | p in ThisPerson.father[1]

这样一来，p.father恰恰就是这个世界所有father的relation中，p的father了。所以，在
语义上，虽然join是个查表，但它同样符合p的father这个语义的，这个认识让我们更大程
度上理解“某某的某某”到底本质上是什么。

在Alloy中，p.father还可以写成：father[p]。这是个数组的表达，它的语义似乎可以理
解为：所有father中，主语是p的对象组成的集合。最终它还是表示p的father。

所以，对泛化的集合来说，对象关系本质就是数组查找关系。

小结
----

我觉得这个例子基本上可以说明整个Alloy的原理了。但可能不容易联想怎么建模一个动态
的过程。比如前面这个模型中，如果模拟新生一个小孩会怎么样？这个我们后面用RISCV的
模型来解释。但现在可以先简单解释一下：

所谓动态变化的一个过程，其实本质就是时间上的两个集合，比如你的Man组成一个时刻的
所有男人的集合，那么Man'就是下一个时刻的集合，你说明这两个集合的关系就可以了。
在逻辑的世界里，根本没有时间，时间只是关联（这也是维特根斯坦的定义）。

RISCV的内存模型
===============

最后我们看一个复杂一点的实用模型来完成对这个工具的理解。

前面提到的RISCV的内存模型建模开源在这里：
`riscv-memory-model <https://github.com/daniellustig/riscv-memory-model>`_
。

它定义了两个世界，一个是riscv.als定义的RVWMO（弱内存序）世界，和基于这个世界衍
生的TSO（强内存序）世界，定义在ztso.als中。后者的内容不多，只是前者的一点补充，
我们这里只讨论riscv.als。

.. note::

   注：RISCV的这个模型在最新的Alloy 6上是不能运行的，必须用旧的5或者更低的版本。

内存序是这样一个问题：当一段代码交给一个执行体（比如CPU核，RISCV中叫Hart）的时
候，会形成一个代码作者意图中的序列，这叫程序序。但CPU让这个结果生效需要时间，这
个先后时间有可能会导致在程序序后面的指令先于前面的指令起作用。

这种先后顺序主要体现在内存上，因为指令对计算机的影响只有寄存器和内存，寄存器是
HART内部的，依赖关系在硬件上就能保证。而这种计算上的依赖关系，是我们判断指令顺
序的唯一依据。内存就不一样了，它不但是多个Hart共享的，而且经过总线和Cache系统才
实际生效。即使是同一个Hart的写出和读入的顺序都很难保证。

为了简化问题，很多研究都把问题化简为：系统只有Hart的程序序和内存子系统的生效序。
我们忽略了内存子系统作为一个分布式的多Cache系统会给不同Hart呈现不同的顺序，我们
认为内存子系统可以为所有人保证这个序。这样，整个模型就变成：内存子系统有一个虚
拟的switch，它按特定的规则接通其中一个Hart，这段时间内，Hart用它的内存序更新内
存子系统，然后switch再选择下一个Hart，做那个Hart内存序操作。

.. note::

   在Vijay等人的《A Primer on Memory Consistency and Cache Coherence （2nd
   Edition）》中，把内存序模型分成两种：

   1. Consistency-agnostic coherence
   2. Consistency-directed coherence

   前者常见于CPU，后者常见于GPU。我们这里讨论的模型是前一个模型。

很多研究都用一个称为SEQUENTIAL CONSISTENCY的模型（简称SC）来作为设计基准。SC模
型中，程序序等于内存序。这是效率最低的一个模型，但也最容易理解。其他模型（比如
RISCV支持的RVWMO和TSO）都在一定程度上放松这个限制，它们会规定什么样的指令是必然
保序的，而有些指令不一定。也就是说，在这些模型上，只要约束不存在，程序序上后面
的指令在内存序可以发生在前面的指令前面。

这样就带来一个问题了：这些定义有没有可能是自相矛盾的？比如说，我们说a会发生在b
前面，但另一个规则却说a必须发生在b的后面？

为了理解这个推理的具像我们还是简单理解一下TSO和WMO到底是什么样的规则。

我们知道，SC的规则是程序序就是内存序。如果细分一下，可以认为有四条规则：

* LL，Load后Load是保序的
* SS，Store后Store是保序的
* LS，Load后Store是保序的
* SL，Store后Load是保序的

这个规则有一个效果：如果A核写x读y，B核写y读x，那么无论怎么组合，不可能读出来的x
和y都等于初值。考虑下面这个程序：::

   x, y是内存地址，初值为0
          A核              |            B核
       store x, 1          |          store y, 1
       load y, r1          |          load x, r1

如果是SC，因为内存序和程序序总是一致的，两个核只有这些组合：::

  (x, y初值为0）
           A:store x, 1 | A:store x, 1 | A:store x, 1 | B:store y, 1 | B:store y, 1
           A:load y, r1 | B:store y, 1 | B:store y, 1 | A:store x, 1 | B:load x, r1
           B:store y, 1 | A:load y, r1 | B:load x, r1 | B:load x, r1 | A:store x, 1
           B:load x, r1 | B:load x, r1 | A:load y, r1 | A:load y, r1 | A:load y, r1
  (A.r1,B.r1)= (0,1)    |    (1,1)     |     (1,1)    |     (1,1)    |     (1,0)   

没有两者都是0的组合。但其实软件很少需要做这种通讯的，所以TSO放松了其中一个要求，
它不保证SL。之所以叫Total Store Order，是因为它用了叫Write Buffer的FIFO队列来保
存写到内存去的队列，如果读的内容在读列中，就从队列读，否则才到内存系统上去排队。
这样一组合，你会发现，LL和LS是在内存上排队的，自然可以保证，SS是在FIFO中排队后
到内存上排队的，也可以保证，只有SL是无法保证的。但核间通讯的大部分场景是A核SS，
B核LL的（A核写数据再写flag，B核读flag，在flag变化以后读数据），不保证这一点大部
分时候并没有问题。不保证SC那个交叉访问得到(0, 0）几乎不会遇到什么问题。实在要用，
就用Fence去强制FIFO刷新，也能达成目的。

而WMO放得更松，它认为，很多其他约束其实也是不必要的，比如你写10个数据在设置一个
flag，那是个数据也不需要in-order啊（SS规则）。你可以简单认为WMO的WB不是FIFO的，
而是随机发射出去的。当然它也不是只有这一种实现方法，但无论是什么方法，它大部分
内存序都是靠fence刷中间状态来保序的，反正不论玩什么妖蛾子，一旦刷到内存子系统上，
内存子系统（比如CC总线），就自然保证了顺序了。

但WMO还是有一些特殊的保序要求的，比如对于同一个地址的操作，它必须保序，否则它自
己的程序逻辑就没法保证了。想象你在一个核中写一地址，然后从这个地址读回来，结果
读发生在写的前面，这你也要求这个核要加fence，这个程序会很难写。

除此以外，为了配合很多语言的核间通讯协议，很多平台又增加更多的保序指令，比如典
型的用于C++内存模式的LR/SC（Load Reserved / Store Conditional，又称为Load
Reserved在有些地方也称为Load Linked，Load Link或者Load Locked）。它支持一对指令，
先向一个地址中写，后面根据这个地址是否被其他核修改过决定是否修改。这对指令就是
有顺序要求的。

还有原子操作（比如RISCV中的AMO），常常是对内存有多个操作的，这些操作必须同时起
作用（比如读-判断-写指令），这也会产生顺序要求。

每个指令制造各自的顺序要求，那么组合起来，他们的那些独立的承诺还能够成立吗？这
就是对这个问题建模的目的。

那么这个模型应该怎么建呢？程序序是程序员指定的，这是一个完全的自由度，我们称为
po，program order。RISCV的语法约束是RISCV构架承诺的，这是另一个自由度，我们称为
ppo，Preserved Program Order。最终反映出来的顺序都出现在内存上，这个我们称为gmo，
Global Memory Order。这就是这个模型的基础，我们要表达当程序员写成一个po的时候，
无论是什么样的组合（世界），在我们额外的约束ppo下，是否能兑现最终呈现在gmo上的
承诺。

RV的Alloy模型（下面简称rv.als）这样定义这种顺序关系：在一个Hart上的一个操作，定
义为一个Event，Hart->start关联第一个Event，Event->po定义这个Event在po上的下一个
Event的，这样就构成一个连续的某个Hart上的po序列了。

有内存属性的Event定义为MemoryEvent，MemoryEvent->gmo定义这个事件的gmo。po的属性
是one，而gmo的属性是set，也就是说，gmo在MemoryEvent的声明上不是一个序列，在声明
上我们只保证它在谁的前面。

但gmo在全局上是一个序列，所以它用这种方法来约束它：::

  pred acyclic[rel: Event->Event] { no iden & ^rel }
  pred total[rel: Event->Event, bag: Event] {
    all disj e, e': bag | e->e' in rel + ~rel
    acyclic[rel]
  }
  fact { total[^gmo, MemoryEvent] }

这个定义是这个意思：任选两个内存事件e和e'（无论它们是否在同一个Hart中），它们必
然在gmo上被定义了顺序：要不e在e'前面，要不e'在e的前面，而且，不可能出现循环。

这里有几个值得注意的Alloy定义技巧：

1. 当我们人为定义一个顺序的时候（比如gmo），它的所有两两关系可以通过^gmo这种形
   式构成一个顺序的全集。这样我们很容易通过判断某个其他定义的顺序关系和这个关系
   的集合关系来判断两者是否相容。

对于所有可能的gmo定义的先后关系（^gmo），任何两个内存操作，必然
有一个先后关系，而不会有循环的依赖。

定义这种时间上的关系，总是把每个状态看作是一个sig的成员，顺序是sig之间的关
系。所以RISCV的基础模型是这样的：

1. 所有操作，包括内存操作，都是sig Event，不同的操作就叫不同的子sig。比如内存操作
   就是一个MemoryEvent（继承Event）。Event带属性po，这个关联表示它们的程序序。
   （注意Event不是指令，而是指令的执行行为，同一个指令不同时空执行是不同的Event）。
2. 如果你承诺了其他顺序，在MemoryEvent上在放起来属性（也是Event），这样可以建立
   更多的顺序的承诺。address也是MemoryEvent的属性，用于控制那些对于相同内存的行
   为的承诺。
3. Hart定义为另一种sig，它在这个问题上的本质是对所有po的区分（成为不同的线程），
   所以它就一个start属性，而且只有一个。当我们构造世界的时候，为每个构造的Hart
   构造唯一的一个开始Event，这个Hart上的后续Event就由这个Event的po决定了。这样
   所有的po就有唯一的线程根源了。

在这个基础上它建立了一组子集，比如所有的AMO指令，所有的LoadNormail，StoreNormal
执行等等。然后补充明显的fact，比如这个：::

  //gmo是MemoryEvent的属性，和po一样，定义内存序，这里不看它的定义
  pred acyclic[rel: Event->Event] { no iden & ^rel }
  pred total[rel: Event->Event, bag: Event] {
    all disj e, e': bag | e->e' in rel + ~rel
    acyclic[rel]
  }
  fact { total[^gmo, MemoryEvent] } // gmo is a total order over all MemoryEvents


在定义中，我们严格区分了两个集合：gmo的集合和MemoryEvents的集合。两个集合在其他
地方都是独立定义的。但我们无论你怎么定义，我把你说好的两个内存操作拿出来，在gmo
的定义中找到它们，它们比如在gmo的某个顺序中可以找到。这就是我们对gmo的基础要求。

之后你可以继续补充其他的不同内存事件类型，说明什么事情下的gmo要求是什么样的，但
那些要求不能导致gmo的这个约束逻辑不成立。

我们再看看它的ppo是怎么定义和使用的：::

  // Preserved Program Order
  fun ppo : Event->Event {
    // same-address ordering
    po_loc :> Store
    + (AMO + StoreConditional) <: rfi
    + rdw
  
    // explicit synchronization
    + ppo_fence
    + Acquire <: ^po :> MemoryEvent
    + MemoryEvent <: ^po :> Release
    + RCsc <: ^po :> RCsc
    + pair
  
    // syntactic dependencies
    + addrdep
    + datadep
    + ctrldep :> Store
  
    // pipeline dependencies
    + (addrdep+datadep).rfi
    + addrdep.^po :> Store
  }
  
  // the global memory order respects preserved program order
  fact { ppo in ^gmo }

ppo的定义原则就是：我承诺了什么，我就加到集合中，然后我保证：ppo承诺的顺序，在
gmo里面也承诺。

我们打开其中一个子集看，比如这个same-address ordering，它包括几个要素：

1. 同一个地址是的Store，承诺保序。
2. AMO和SC指令，如果属于rfi（从写中读），承诺保序。
3. rdw（同一个地址的两个读），承诺保序。

其实可以看到，这些约束只是建模者自己能找到的所有观察事实，它不见得都在指令
Specification中（但大部分在），你不能认为有了这个模型，整个定义就万无一失了。

有了这些定义以后，就会有类似这样的一些测试了：::

  // 给定一个内存事件，求gmo和po都在它前面的同地址写
  fun candidates[r: MemoryEvent] : set MemoryEvent {
    (r.~^gmo & Store & same_addr[r])
    + (r.^~po & Store & same_addr[r])
  }

  // 给定一个event集合，求每个事件gmo在它前面的集合
  fun latest_among[s: set Event] : Event { s - s.~^gmo }
  
  // 一对写读操作，如果符合read-from的条件，那么写在gmo和po上都在读前面。
  // 反之依然：如果写gmo和po都在读前面，那么它必然符合read-from的条件。
  pred LoadValue {
    all w: Store | all r: Load |
      w->r in rf <=> w = latest_among[candidates[r]]
  }
  
  // 对于Store的LR操作，没有同地址的另一个Hart的Store，使得这个Store是一个Read-From
  // 同时，
  pred Atomicity {
    all r: Store.~pair |            // starting from the lr,
      no x: Store & same_addr[r] |  // there is no store x to the same addr
        x not in same_hart[r]       // such that x is from a different hart,
        and x in r.~rf.^gmo         // x follows (the store r reads from) in gmo,
        and r.pair in x.^gmo        // and r follows x in gmo
  }

  run MP {
    some disj a, b, c, d : MemoryEvent, disj x, y: Address |
      a in Store & x.~address and
      b in Store & y.~address and
      c in Load & y.~address and
      d in Load & x.~address and
      a->b + c->d in ppo and
      b->c in rf and
      d->a in fr and
      RISCV_mm
  } for 8

todo：未写完。


附录
====

Alloy集合操作符速查
-------------------

* p->q：关联操作，求p，q两个集合的所有对应关系。想象p，q是男女的集合，p->q是所
  有婚姻的组合可能。
* p.q：join操作，用关联p的值域对消q的定义域生成新的关联。想象q是p的属性关联，
  p.q是求所有属性的集合。
* []：数组关系，join的另一个写法
* ~p：转置，p的值域和定义域对掉
* ^p：可达性闭包，求关联中的所有可达的对应关系。想象一张连通图上，所有可以经过
  其他节点关联起来的两个节点都对应起来。
* \*p：反身转换闭包，就是^p + iden。即加上自己到自己的关联。
* p <: q：定义域过滤，把q的定义域限制在p的范围内
* p :> q：值域过滤，把p的值域限制在q的范围内
* p ++ q：重载，用q中定义域和p相同的记录替换p中的记录，想象q是p的斟误表。
* p + q：合集
* p - q：删除子集
* p & q：交集

这些操作有一些常见的组合套路：

* p.~p：p中所有值相同的输入。设想p是一个名字到地址关系的地址本，p.~p就是所有住
  在一起的人的组合。如果p.~p in iden，就说明映射是单调的，不同的输入没有相同的
  输出。
* p.^~e：发生在p之前的所有事件。Alloy常常用同一个sig的关联表示时间上的关系。比
  如一个线程的一系列事件，或者一个程序在操作前和操作后的状态。如果把这个事件定
  义为p，后面的时间定义为它的属性e（关联），那么p.^~e是发生在p前的所有事件，而
  p.^e是发生在它之后的所有事件。如果这些操作中把^换成\*，那就包括p自己。
