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
RISC-V的内存序就是用这种方法进行的分析，分析模型在这里：
`riscv-memory-model <https://github.com/daniellustig/riscv-memory-model>`_
。

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

todo：分析一个实际的复杂模型的建模逻辑
