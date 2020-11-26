.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 0.1

Sail概念空间分析
****************

介绍
====
本文分析一下Sail（主要是针对现在最新的Sail2）的概念空间，主要聚焦到它的语法能力
设计思路和发展方向，而不是详细的编程方法。在文档版本不超过1.0的时候，本文还处于
初步的归纳阶段，部分判断可能不那么可靠，请读者注意。

Sail是一个针对指令行为定义的编程语言开源项目，项目主页在这里：

        https://github.com/rems-project/sail.git

在本文写作的时候，它的最新版本不在master分支上，而在sail2分支上，本文的分析针对
sail2分支，其中不少例子都来自该分支的manual.pdf中的，但该手册中的例子不少有语法
错误，或者需要依赖其他头文件，本文都经过修改，如果顺序一路加进去，基本上都可以
直接编译通过的。

        | Sail的文档很弱，很多语法根本连提都没有提，作者大部分时候
        | 是通过看它的测试用例去判断它支持的语法是什么样的。

本文使用的例子是递进式的，不适合进行跳跃式阅读。

Sail介绍
========
Sail是一个编译器，可以对Sail语法的程序进行编译，编译的结果可以根据需要有多种，
比如生成芯片验证模型（比如HOL，Isabelle等），也可以是芯片的功能模型（类似Qemu这
样的模拟器。可以预先生成.c文件，然后编译出模拟器），还可以生成latex文档。甚至可
以没有结果，仅仅进行语法检查。Sail代码的目的是定义指令集的行为——虽然和它的语法
无关，但它设计的一般目标是：可以针对每条指令，大体定义两个函数：

decode
        决定遇到一条指令的时候如何解码它的行为

execute
        决定特定解码的指令的实际行为

这样，如果指令的定义是用Sail的语法写的，我们就有一种标准的方法去理解它确切的行
为，同时，我们可以用标准的方法去生成验证模型，判断这个指令的“承诺”是否是逻辑自
恰的，也可以生成功能模型，直接用这个语义空间去验证软件是否可以在上面正常运行。

但当然了，Sail语言本身和这两个函数并没有什么关系。

Sail现在还是一个学术性的项目，所以文档很不完整，语法也在不断改进。但它又是非常
先进的方向，已经有很多的平台，开始转向Sail的描述，比如它是RISCV的标准指令提交格
式，而ARM64的所有ASL定义也提供了标准的工具可以转化为Sail语法，其他的指令平台也
都在向这个方向迁移。它的发展前景是可预期的。


Sail语法分析
============

综述
----
Sail本身基于OCAML编写，虽然它和OCAML不是同一种语言，但它在很多地方都借鉴了OCAML
的语法，所以，读者可以考虑先去简单学习一下OCAML的基本概念，特别是对于函数式编程
没有概念的读者，会容易很多，但如果你希望立即解决问题，不看也没有什么大不了的。

但Sail比OCAML简单得多。OCAML是向通用编程语言的角度发展的，而Sail是用于定义指令
的行为的，后者需要的表达能力简单得多，甚至不需要是图灵自恰的。Sail也不支持动态
资源分配，不支持High Order Function等等一般编程必须的功能。

但Sail本身也确实是函数式程序的语法，作为函数式编程语法，读者可能需要很注意它的
表述什么部分是编译态的指令，什么部分是运行态的指令。总的来说，前者用于各种类型
匹配，后者用于实际的运行逻辑。

类型
-----
编程语言中的类型用于决定编译器的行为，比如同是对于a=a+1，如果a是一个整数，编译
器需要把指令翻译为一个整数加法，如果a是一个浮点数，则需要翻译为一个浮点数加法。
更复杂一点来说，我们可以通过类似C++ template这样的语法，让同一段代码生成不同的
二进制版本，从而避免我们为不同的类型生成完全一样的逻辑。这部分判断类型然后生成
不同的代码的过程，是源代码提供给编译器的计算要求（对比提供给Target的计算要求）。

Sail把这种能力再推进了一步，它支持类型变体：Type Variable。这个名字其实直译可能
应该叫类型变量，但这听起来好像说这是一个有类型的变量，而不是说这个类型本身是可
以变的。类型变体本身是一个类型，但这个类型可以带有参数（我们后面称为超参），这
有点像函数式编程中的函数一样。在函数式编程语法中，函数可以被咖喱化过程逐步去参
数化，最后变成一个固定的值。在Sail中，类型也可以被从类型变体咖喱化为一个固定的
类型，甚至简单变成一个值。而这个过程都在编译阶段完成，如果完成不了，编译就会失
败。

比如下面是一个类型变体的定义：::

        type bits ('n : Int) = bitvector('n, dec)

这里定义了类型bits，它有一个Int的超参'n，当'n固定下来的的时候，bits就是一个固定
长度的位向量

        | dec是bitvector的一个类型参数，用于表示高位的方向的，
        | 只有两个取值：dec和inc。这不是关键问题，本文不讨论这类问题。

也就是说bits最终是什么类型，在它在程序中被引用的时候才会决定的，比如：::

        type xlen : Int = 64
        type xlenbits = bits(xlen)
        register PC : xlenbits

这里又定义了两个类型，xlen和xlenbit。前者被咖喱化为常数了，引用xlen，就是引用64
。而后者咖喱化为一个固定长度（64）的bitvector，所以，xlenbit，就是一个定义64位
向量的类型。而PC，就是一个64位的寄存器。

像大部分函数式编程语言一样，Sail也通过匹配确定标识符的类型，从而确定实际编译成
目标代码的时候具体如何安排逻辑。匹配本身是核心代码的一部分，比如这样：::

        let aa1=3
        let aa2 : int = match aa1 {
                0 => 1,
                1 => 2,
                _ => 3
        }

这里的match语法对aa1进行匹配，针对aa1的不同取值决定aa2的取值，这看起来是一个运
行态的逻辑，但编译器可以为此组织出针对性的逻辑来生成代码。对于这一点，下面这个
例子会更加明显一点： ::

        val sail_zero_extend = "zero_extend" : forall 'n 'm. (bits('n), int('m)) -> bits('m)
        val test2 = {ocaml: "test2ml", tt: "test2tt"} : 
          forall ('n 'm: Int), ('n >= 1 & 'm >= 1). 
          (bits('n), bits('m), bits('n)) -> bits(4)

        val my_map : int <-> bits(4)
        mapping my_map = {
                0 <-> 0b1000,
                1 <-> 0b1001,
                2 <-> 0b1010
        }

        function test2 x = match x {
                (a, b, c) => sail_zero_extend(a, 4),
                _ => my_map(0)
        }

我们先忽略其他语法，就看最后那个match，当x被匹配到一个(a, b, c)的向量的时候，编
译器可以直接解开这个x，把里面的内容分解为a, b, c三个子参数，然后做后面的运算。
解这个动作不是编译器干的，但编译器可以在满足条件的场景中，把动态的数据按这个规
则来布置解开的代码，从而支持源程序的逻辑得到满足。这也就是前面说的，类型是决定
编译器行为的关键要素。

函数
----
现在我们开始看函数的结构。和很多函数式编程语言一样，Sail的函数包括两个部分：签
名和实现。签名就是函数的类型定义，也可以理解为C语言的函数“声明”。如果你索引一个
函数，只要保证有签名，编译就可以通过，而不需要有实现。本文举的例子，很多时候，
我们用到一个第三方的函数，我们都不需要写它怎么实现的，就给出它的签名就可以了，
如果仅仅要做语法逻辑验证，这已经足够了。

下面是一个简单的例子：::

        val test: int -> int
        function test a = a

第一句是签名，说明test是一个把int转化为int的的函数，第二句是实现，表示调用
test(a)，就返回a。由于前面签名已经规定了a是int，所以这里的a就可以被匹配为int，

两者也可以写在一起：::

        function test a:int->int = a

由于类型都是在使用的时候决定的，这我们很容易实现函数的多态，比如你有两个不同的
签名，你可以把它们合并为一个名字，像这样：::

        val test1: int -> bits(4)
        val test2: bits(4) -> int
        overload test {test1, test2}

这种情况下，你调用test(int)，匹配上的就是test1，如果你调用的是test(bits(4))，实
际匹配的就是test2。

Sail的很多语法糖都是通过这种方法实现的，比如我们可以把函数转化为一种类型变量的
读写：::

        val test11 : int->unit
        val test12 : unit->int
        overload test112 = {test11, test12}
        let test112=1
        let test112v = test112

注意最后overload出来的test112，后面我们用let对它读写的时候，变成了对应的两个函
数调用，我们可以在里面发起一系列的动作。行为就好像处理器的某个IO寄存器被访问的
情形。后面我们会看到更多比如访问向量成员等行为，都会以来这种匹配特定函数来实现
语法糖的。

到此为止，表面上看来是没有什么特别的。我们先说明Sail函数的一个限制：它只能有一
个参数。所以，如果你有两个参数，你只能作为一个tuple一起送进去：::

        val test: (int, int) -> int
        function test (a, b) = a

这就能看出特别了，因为test的参数并没有写作一个独立的表示(int, int)的x，而是写成
了(a, b)。这又制作了一个匹配，由编译器把a, b匹配为两个int变量，并输出a这个int。
如果这样写可能就更清楚了：::

        val test: (int, int) -> int
        val operator + : (int, int) -> int
        function test a = match a {
                (b, c) => b+c,
                _ => 10
        }

这里test的签名是把包含两个int的tuple转化为int，在实现上a就是一个(int, int)，
然后我们用match把它匹配为两种情况，一种是符合要求的(b, c)，分别把两个输入解释
为b和c，然后我们用b+c来完成这个计算。

        | 默认的Sail并不认识int+int这个函数，
        | 所以例子中我们用val定义了加法的签名，
        | 这倒和这里的例子无关。

这里的各种匹配，都是编译阶段的控制。更完整的函数匹配控制是这样的：::

        val test = { c : "c_test", _ : "test" }: 
                forall ('n 'm: Int), ('n >= 1 & 'm >= 1). 
                (bits('n), bits('m)) -> bits('n+'m)

这个签名分了三行，第一行定义函数名，后面可以补充一个={...}，我觉得功能是用来制
定实际匹配到对应的编译目标的时候，实际的函数名是什么的。比如这个例子中用c:
"c_test"，表示输出为c代码的时候，函数名叫c_test。这行以冒号分隔后面的部分。

        | 一般来说，如果只是要检查语法，我们不需要那个补充列表

第二行定义超参，它以逗号分成两段，第一段是超参本身的定义，第二段是超参的取值范
围。例子中定义了超参'n, 'm，并要求范围是大于等于1，你还可以要求'n>'m这样同时卷
入两者的定义，反正这是编译器负责解释的。

超参的名字必须用'打头，类型和普通参数的类型也是不同的，一般用大写开头，暂时看到
可用的取值是Int，Type等，前者是整数，后者是某种类型。

最后第三行定义函数的具体形式，这个定义就可以包含超参。还可以通过effect关键字
声明函数的边界效应，比如这样：::

        val test: forall ('n 'm: Int), 
                ('n >= 1 & 'm >= 1). 
                (bits('n), bits('m)) -> unit effect {rreg, wreg}

这本身是用来生成其他代码的hint，本身并没有什么实际的意思。这里的unit和ocaml里的
unit的语义一样，作用和void差不多。可选的effect是预定义的，可选的有：

        rreg, wreg, wmem, rmem, escape, barr, eamem, exmem, rmemt,
        undef, wmv, wmvt...

如果都不是，可以写pure：::

        val stall: xlenbits -> int effect pure

函数实现部分相对简单，就是实现签名给定的计算过程，模式是：

        function 名称 参数 = 结果

结果是个表达式，前面的例子中我们用match语句，你也可以用多个let或者分号连起来
：::

        val operator + : (int, int) -> int
        function test5 (a : int) -> int = let ax1=2 in let ax2=ax1+1 in a+ax2
        function test6 (a : int) -> int = {ax1=2; ax2=ax1+1; a+ax2}
        function test7 (a : int) -> unit= {ax1=2; ax2=ax1+1; ()}
        function test8 (a : int) -> unit= ()

反正整体能计算出一个结果就行。你还可以在里面使用超参：::

        val __size : forall ('a : Int). bits('a) -> int
        val test9 : forall ('a : Int), 'a>0. bits('a) -> int
        function test9 a = 'a

这里的test9用一个bits来计算它的长度，我们使用了签名中的超参'a，但为了在计算上可
实现，就需要有一个__size来支撑这个计算，Sail自己搞不定，你需要你来弄，最终就是
你给另一个签名为__size的函数来完成这个功能，至于__size怎么实现，那是你的问题了
。从这里我们可以看出Sail作为一种“接口定义语言”是如何看待这些实现的。


register
---------
register是个独立的语法，和哪个独立的逻辑都不太搭，这个我们快速看一看，这有助于
看懂后面其他的例子。

register是Sail中少数可以被全局定义的“变量”（因为CPU中除了寄存器也不能有别的东西
可以当变量了），下面是一个例子：::

        default Order dec

        register X0 : bits(8)
        register X1 : bits(8)
        register X2 : bits(8)

        let X : vector(3, dec, register(bits(8))) = [ref X2, ref X1, ref X0]

        function main() : unit -> unit = {
                X0 = 0xFF;
                (*X[0]) = 0x11;
        }

        | 这个地方作为ref Xn，其实只要3个bit就可以完成索引了，
        | 但实际测试发现，这里vector的定义必须和Xn的定义一致，
        | 看起来是把整个内容都放进去了，我个人觉得这是实现上的方便。
        | （因为这本来就不是真的代码，它只是要说明这必须作为索引来
        | 解释，记录目标的类型被记录如何存储它更有意义）

第一句是定义vector默认Order的东西，我们暂时忽略。后面是具体的register变量，后面
定义了一个vector，索引到这些register。后面的main函数对寄存器和寄存器索引进行赋
值。

这里值得探讨的是X0和X到底有什么区别：X是个变量，它是Sail程序本身控制的一部分，
它改变的是程序的逻辑，而X0是一个寄存器，是目标机器的一部分。这是表面的不同，但
说起来，寄存器对软件本身也是黑盒的一部分，只是暴露为状态的变化。所以严格来说，
我觉得以现在的语法来看，register和普通的变量其实没有本质的区别，也许仅仅为了
Sail生成模型的方便。

type, val和let
---------------

type，val和let的语法和用法非常接近，我们统一辨析一下。

type定义的是类型，可以用来匹配一个变量的行为，val用来定义签名，可以是函数或者其
他如mapping等机制的类型声明，而let用于设定变量（通常是中间变量）::

        type 名字 超参声明 = 含超参的类型定义
        val 名字=属性表: 超参声明. 含超参的函数声明     //函数
        val 名字=类型1 <-> 类型2                        //mapping
        let 名字 = 表达式 in 子域

这里不举例子，反正在其他例子中总是少不了要用这些定义的。

operator
---------
operator是语法糖的一部分，本质是标识符，只是用特殊的字符做的标识符，比如
+-\*/:<>这些，这种标识符后面可以再加一个_开头的后缀，比如+_u。每个操作符
有自己结合方法
和优先级，通过infix, infixl, infixr来定义，比如：::

        infixr 3 .|.
        type operator .|. ('n : Int, 'm : Int) = range('n, 'm)
        let x : 3 .|. 5 = 4

        | _一般用来对operator做补充说明，比如+_u就可以表示无符号加法。
        | 手册没说，但后缀实际是什么Sail编译的时候其实是有要求的，
        | 我还没有看出这个规律是什么，只知道_u是可以的，但用_ua就不行了。

这里.|.就是我们定义的标识符，被定义为一个函数，然后我们当作函数那样去用它就好了
了。


常用类型
---------

下面通过例子快速浏览一下Sail支持的常见类型和语法：

整数，real，string
```````````````````
::
        let i1 : int = 1
        let i2 : nat = 2
        let i3 : range(2, 4) = 3
        let s : string = "test"
        let r : real = 1.0

其他没有什么可解释的，整数这里比较有趣，它可以有三种类型：

* int：所有整数

* nat：自然数

* range：范围


vector和list
`````````````

vector的语法是vector(个数，顺序，单元类型），下面是一个例子：::

        val vector_access : forall ('n : Int) ('a : Type).
            (vector('n, dec, 'a), int) -> 'a

        let v : vector(4, dec, int) = [1,2,3,4]
        let v1 = v[0]

向量用v[i]的方式访问，为了支持这个访问，需要定义vector_access函数，我们在这个例
子中已经给出这个函数的签名了，具体如何实现，就看具体的平台自己怎么弄了。

bitvector是bit版本的vector：::

        default Order dec
        let bv: bitvector(4, dec) = 0b1111

我们还可以用with子句去索引vector中的成员：::

        val gen_bit : unit -> bit
        val vector_update : forall 'n. (bits('n), int, bit) -> bits('n)
        let cc1 : bits(4) = 0xF
        let cc3 = [cc1 with 2 = gen_bit() ]
        let cc4 = [cc1]

这里我们用cc1生成cc3，同时把其中的成员2修改了一下，为了支持这个修改，需要
vector_update函数的支持。

list和vector很接近，但一般用来做合并和分解，例子如下：::

        val append : forall ('a:Type). (list('a),list('a)) -> list('a)
        let l1 : list(int) = 1::2::[|3,4|]
        let l2 : list(int) = 1::2::[|3,4|]
        let l  : list(int) = l1 @ l2
        let v2 : int = match l {
                a::rest => a,
                _ => 1
        }

注意其中的::和@操作符的用法，以及match如何把list分解开。list现在没有看到有访问
单个单元的方法，它的用法就是这里的match的方法进行分解。

mapping
````````
mapping定义两种类型之间的映射关系，它需要签名，模式如下：

        val 名称 : 类型1 <-> 类型2

        mapping 名称 = { pattern1 <-> pattern2, ... }2, ... }

下面是一个例子：::

        val my_map : int <-> bits(4)
        mapping my_map = {
                0 <-> 0b1000,
                1 <-> 0b1001,
                2 <-> 0b1010
        }

        function test2 x = match x {
                (a, b, c) => sail_zero_extend(a, 4),
                _ => my_map(0)
        }

它可以像函数一样使用：mapping_name(patternN)可以得到映射的patternM的值。

union和struct
``````````````
::

        struct Struct = {
                sa : bits(8),
                sb : int,
                sc : range(0, 9)
        }

        union Union ('a : Int) = {
          Ua : bits('a),
          None : unit
        }

        val operator == : forall ('a : Type). ('a, 'a) -> bool
        function test_assert() : unit -> unit = {
                t1 : Struct = struct {sa=sail_zero_extend(0b1, 8), sb=2, sc=3};
                t2 : Union(3) = None();
                t1.sa = 0x77;
                X0 = 0xFF;
                assert(X0 == 0xFF);

                t3 : int = match t2 {
                        Ua(0b111) : Union(3) => 1,
                        _ => 2
                };

        }

这两者，一个是多选一，一个是多选多，也没有特别的了。

bitfield
`````````
bitfield是个语法糖，语法大概是这样的：::

        val vector_subrange : forall ('n : Int) ('m : Int) ('o : Int),
                'o <= 'm <= 'n.
                (bits('n), int('m), int('o)) -> bits('m - 'o + 1)

        bitfield Ctr_reg : bits(8) =
        {
          AV : 6..5,
          IMO : 4,
          FMO : 3,
          PTW : 2,
          SWIO : 1..0,
        }
        register HCR_EL2 : Ctr_reg
        let bf : Ctr_reg = 0xFF
        let a : bit(2) = bf.AV()

但这个需要vector_subrange函数的支持，我上面给出的签名会导致编译失败，而且没有给
出原因，我估计是个Bug，但暂时我无法分析它。

从语法上说，你调用bf.AV()，其实就是调用vector_subrange(bf, 6, 5)，或者
bf[5 ..  6]。


scatted和clause
````````````````
这是定义指令是另一个语法糖，用于聚合多个函数，union，mapping之类的东西，下面是
一个具体应用利用这个语法糖定义指令execute例子：::

        scattered union ast('datasize : Int, 'destsize : Int, 'regsize : Int)

        val execute : forall ('datasize : Int) ('destsize : Int) ('regsize : Int).
          ast('datasize, 'destsize, 'regsize) -> unit

        scattered function execute

        union clause ast = the_test : (vector(8, dec, bit), vector('regsize, dec, bit))

        function clause execute the_test(x, y) = return(())

        union clause ast = the_test2 : int

        function clause execute the_test2(_) = return(())

        end execute
        end ast

这里我们用scattered xxxx和end xxxx控制了一个范围，这个范围中scattered的函数或者
union可以被分成多段进行定义，每段加上clause，定义匹配的其中一部分，完整合起来，
才是一个完整的定义。所以这叫scattered定义。

        | 我暂时猜不到这个好处在哪里，也许可以让多个定义互相应用吧。


计算过程控制
-------------
从前面的例子我们已经看到了，大部分的计算，其实都需要自己定义操作符的行为。这些
行为最后，很多时候都不是靠Sail来实现的，而是让下面的模型一类的东西来实现的。
Sail语法本身不是用来写计算逻辑，而是用来说明什么情形下触发什么行为。

所以，各种match是Sail最重要的特征。但它也支持一些基本的控制要素，比如这些：::

        val operator < : (int, int) -> bool
        function test10 n : int -> int = {
                i : int = 0;
                j : int = 0;
                while i < n do {
                        j = j + 1
                };
                if j < 100 then j else 10
        }

注意while和if语法的语法，加法我们前面定义过了，这里就不再定义一次了。


小结
====
没啥感觉，觉得这个东西还挺简陋的，还需要发展一段时间吧，可以边用边改。不过这个
项目的文档实在太烂了，很多新特性，比如as，implicte之类的东西，根本连提都没提，
啥打算都不太容易判断，感觉非得派人加到项目中才有可能控制得住方向吧。
