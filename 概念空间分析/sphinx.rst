.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0
:Date: 2021-06-27
:Status: Draft

Sphinx概念空间分析
************************

:index:`sphinx`

介绍
======

本文剖析一下Python3\ [#n1]_\ 的Sphinx文档系统的概念空间。

Shpinx是一个文档系统，用于生成各种用户手册。当然，你也不见得非要写成用户手册，
用来写什么都可以。这种文档的样式，看看Sphinx自己的手册就知道了：

        http://sphinxsearch.com/docs/sphinx3.html

.. note::

   本文其实也是用Sphinx写的，只是它只是整个工程中的其中一个子文档。

在写作的时候，原始的Sphinx文档用.rst格式写，这是一种类似Markdown的格式化文本文
件。Sphinx负责把这些原始的Sphinx文件全部组合在一起，变成一本书的样子，最终可以
生成html，pdf等其他格式。

这有点类似Latex的理念：写作内容的聚焦写作内容，排版的聚焦排版。不需要在写内容的
时候老去想“这段文字用红色背景好看还是蓝色背景好看？”这种问题。但Latex过于灵活了
，也发展得太早了，用Latex还是很让人痛苦的一件事。Sphinx则提供了较为简单的构架，
对于只想写一本漂亮的手册，不想想那么多稀奇古怪问题的人来说，这是一个理想的选择。

Latex对中文的处理一直是一个麻烦的地方，Python3全面支持UTF-8，所以基本上很少中文
问题，你无论直接在Python3代码中直接写中文，还是在源rst代码中写中文，都可以无缝
处理。至于最后显示的时候具体怎么用字体，这是后端生成器的问题。我个人经常是直接
生成html或者epub。这些格式使用浏览器的字体，所以基本上不会有问题，如果需要pdf，
只要把html在浏览器中打印出来就可以了，也不会有字体的问题。

.. note::

   rst还有两个常见的中文问题。

   其一是默认会把换行替换成空格（英文下这是合理行为），这会让目标文档不好看。这
   个问题可以很容易通过后端处理解决掉。这个后面会介绍。

   其二是中文搜索功能还不完善，这个可以解决，但本文不是介绍用法，这里不提。

本文是概念空间分析，我们只关心架构，不关心具体的用法，但本文作者建议读者先对
Sphinx的用法作一定理解，这样会比较容易看懂本文。

Sphinx的使用接口概念空间
=================================

.. sidebar:: docutils的顶级模块概念

   parser
        源代码扫描器，当前就只有rst这一个扫描器。

   reader
        封装parser和读入功能的对象。

   transform
        封装对doctree进行处理的对象。

   writer
        把doctree写出去对象。

   publisher
        组合上述概念最终构成一个应用的对象。

类似源代码，用于生成目标的书的所有文本（.rst文件）组成一个工程，Sphinx负责编译
这个工作，最终生成要求的目标格式。

一个Sphinx工程包括一组rst文件和一个conf.py作为配置文件，conf.py是一个纯python的
源代码文件，sphinx执行的时候先运行这个文件，设置一组参数，然后基于这些参数，编
译其中的master_doc参数指定的rst文件，最终生成指定的目标格式。

master_doc是整本书的入口，它的标题就是全书的标题，它里面通过toctree定义的目录树
就是书中的第一级目录。这个目录树的项目指向其他rst文件，那些rst文件就是书的内容
，如果那些文件中也定义了doctree，那么那些目录就是书中那个章节的子目录……如此递归
，就构成了整本书的全部内容。

rst文件结构在sphinx中的表示
====================================

Sphinx基于rst，而Python基于docutils库来访问rst。docutils用于处理单个的rst文件。
它可以读入一个rst文件，生成一棵docutils.nodes.Node树。Node有很多类型，其中一个
rst文件的根的类型是docutils.nodes.Document，文档中的每个章节，段落，列表，都是
这个对象的子对象，或者子对象的子对象……如此类推。

每个Node都有自己的属性。比如下面这个文档：::

        我的文章
        =========

        第一章
        ----------
        现在我们来介绍一下第一章的内容

        section 2
        ----------
        第二章的情况是这样的：
        1. 首先，这样这样
            * 深入一点说呢，是这样
            * 另外补充一点：是那样
        2. 然后，那样那样

生成的Document树的结构是这样的：::

  document( ids(['id1']) classes names(['我的文章']) dupnames backrefs source(<string>) title(我的文章)):
    title( ids classes names dupnames backrefs):
      Text: 我的文章
    section( ids(['id2']) classes names(['第一章介绍']) dupnames backrefs):
      title( ids classes names dupnames backrefs):
        Text: 第一章介绍
      paragraph( ids classes names dupnames backrefs):
        Text: 现在我们来介绍一下第一章的内容
    section( ids(['id3']) classes names(['第二章深入探讨']) dupnames backrefs):
      title( ids classes names dupnames backrefs):
        Text: 第二章深入探讨
      paragraph( ids classes names dupnames backrefs):
        Text: 第二章的情况是这样的：
      enumerated_list( ids classes names dupnames backrefs enumtype(arabic) prefix suffix(.)):
        list_item( ids classes names dupnames backrefs):
          paragraph( ids classes names dupnames backrefs):
            emphasis( ids classes names dupnames backrefs):
              Text: 首先
            Text: ，这样这样
          block_quote( ids classes names dupnames backrefs):
            bullet_list( ids classes names dupnames backrefs bullet(*)):
              list_item( ids classes names dupnames backrefs):
                paragraph( ids classes names dupnames backrefs):
                  Text: 深入一点说呢，是这样
              list_item( ids classes names dupnames backrefs):
                paragraph( ids classes names dupnames backrefs):
                  Text: 另外补充一点：是那样
        list_item( ids classes names dupnames backrefs):
          paragraph( ids classes names dupnames backrefs):
            Text: 然后，那样那样

我们可以用docutils.core.publish_XXXX()函数从一个rst中生成一个document对象，然后
我们就可以根据需要处理这个Node树了。

Node的属性可以通过Node['attrname']来访问，或者直接从Node.attributes获得，Node的
子结点可以通过Node[node_index]访问，或者直接从Node.children获得。有了这两个成员，
可以很容易可以查找，增加，删除树里的Node。比如，你可以找到某个paragraph的Node，用
replace_self()函数，把它的所有子结点换成你加入的其他Node，最后通过
publish_from_doctree()把文档最终生成目标文档。

总结起来说，docutils负责把静态的一个文档解释为一颗动态的文档树，然后在靠不同的
后端，根据这个文档书，把这个文档生成html，pdf这些目标格式。这样整个文档工作就分成
了写作内容和决定输出两个部分了。

sphinx工程对docutils的组织
====================================

sphinx用docutils对工程中的每个rst进行遍历，然后把结果保存在临时的cache中，之后
根据指定的translator对结果进行第二次处理，最后根据你指定的输出格式，用对应的
Writer对象把它们根据需要写成那种格式的目标文件。

所以，一个Writer怎么使用这个document，这完全是那个Writer决定的，它可以根据Node
的名字，title，ids，下面有多少子Node，在目标文件中写不同的内容。这并没有一定的
标准，所以，你只能根据现在的实现，尽量在修改的时候符合现在的样式，这样目标
Writer按默认方式来处理你的Node，你就可以得到预期的结果。

.. note::

   从架构的角度来说，sphinx现在比Latex更有竞争力，就是因为它并不依靠定义完美的
   标准，而是提供了一个“可以运行”的框架，让人可以不断把结果“试出来”。我个人在架
   构设计上很反对“试试能跑就上线”的开发方法，因为这样会导致部分异常流程没有考虑
   到，但这种模式特别适合非关键模块（所谓枝叶模块），因为它是快速开发的基础。只
   是那种模块没有什么架构设计的需要而已。

   换句话说，我们通过组织历经打磨的中间模块，支持大量可以随便犯错的枝叶模块，就
   可以让整个代码生态可以快速发展。

所以，sphinx的整个工作原理是对document树进行多次pass，每次调整一部分node的内容
，等所有的pass都完成了，最终提供给Writer进行最终的输出。

我们用前面提到的中文问题为例子，看看这种处理的逻辑结构是什么样的。

Sphinx支持插件，方法在conf.py的参数extension中加入一个py文件，在该文件中包含一
个setup函数，这样就可以了。setup函数最常见的功能是在sphinx的pass中加回调。比如
这样：::

        from docutils.nodes import NodeVisitor, Text, TextElement, literal_block

        def setup(app):
            app.connect('doctree-resolved', process_chinese_para)

        def process_chinese_para(app, doctree, docname):
            doctree.walk(ParaVisitor(doctree))

        def _is_asiic_end(text): return bytes(text[-1], 'utf-8')[0] < 128

        def _this_is_asiic(text): return bytes(text[0], 'utf-8')[0] < 128

        def _tran_chinese_text(text):
            secs=text.split('\n')

            out = ''
            last_is_asiic = False
            for sec in secs:
                if not sec:
                    continue

                if last_is_asiic and _this_is_asiic(sec):
                    out += ' '

                out += sec 

                last_is_asiic = _is_asiic_end(sec)

            return out

        class ParaVisitor(NodeVisitor):
            def dispatch_visit(self, node):
                if isinstance(node, TextElement) and not isinstance(node, literal_block):
                    for i in range(len(node.children)):
                        if type(node[i]) == Text:
                            node[i] = Text(_tran_chinese_text(node[i].astext()))

这个扩展处理前面提到的中文换行变空格的问题。它的setup函数在'doctree-resolved'阶
段加入一个回调，process_chinese_para，这个阶段发生在文档被人引用的时候。上面这个
例子在这个阶段遍历了一次文档树，找到所有TextElement节点，然后把里面的Text节点都
作了一个替换，如果是非ASIIC码发生换行，就直接替换成没有换行，这样在后期Writer进
行处理的时候，就根本不出现这个空格问题了。

更多的阶段，可以在python的docutilsh和sphinx目录中找到，或者直接学习其他
extension是怎么写的，反正理解了这个概念的安排，这个就不是问题了。

Sphinx对docutils的扩展
==========================
按前面的逻辑构架，Sphinx把rst文件转化为docutils的document，然后用内置的或者外加
的扩展对document进行多次pass，最后用writer把Document转化成目标文档。

为了保证可以进行扩展，Sphinx允许增加Node的类型，这样就很容易实现对rst的语法的扩展，
并在扩展后对这些Node进行专门的处理。

Directive
---------

最核心的两种Node扩展，反映在rst文件中，是directive和role。它们都是rst文件中特定
格式的文本。其中directive的写法类似这样：

.. code-block:: rst

   .. directive-name:: argument1 argument2...
      :option1: option_value
      :option2: option_value
      :option_without_value:
           
   directive-content

directive可以生成一个叫directive-name的节点，如果这个名字是内置的，那么就生成叫
这个名字的节点。如果不是，开发者可以通过扩展在setup的时候增加自己的：::

        app.add_directive("directive-name", directive_class)

directive_class是docutils.parser.rst.directive的子类（sphinx也提供了自己的封装
，sphinx.util.docutils.SphinxDirective），里面提供一个run函数负责在文档扫描的时
候决定生成什么预期的node。这样就实现了对document树的插入。比如，你可以从这里读
入一个外部的数据库，然后用数据库来生成内容。

另一种情况是你需要先扫描完所有的文档（比如你要收集全文的关键字），这时你可以在
这里先放一个自定义的node作为占位符，到最后再更新它。这时可以在run函数里创建自定
义的node实例。这种自定义的node，可以在setup的时候，用这个函数创建：::

    app.add_node(cnote_node, ...)
        
这些自定义的Node可以在后续的pass中替换成其他Writer认识的node，也可以在add_node
的时候制定Writer的处理函数，自己生成对应Writer的输出。

.. note::

   老实说，在架构上这（在创建Node的时候指定Writer的回调）是个相当恶心的设计，这
   相当于把node的描述逻辑和Writer的逻辑绑定了。如果我来做这个设计，会考虑另外加
   一个Writer Plugin来处理不同的Node。但这个其实影响不大，因为这个关联不算强，
   可以在后续升级的时候再重建这个逻辑，这不影响其他逻辑。

Role
----

Role是简单版本的directive，一般directive用在成段的替代上，而Role用在嵌入的文本上，
类似用::

        我们要**强调**的是：

把“**强调**”嵌入到其他句子中。Role的写法如下：::

        :role-name:`role content`

它的定义函数是这样的：::

        app.add_role('role-name', role_function)

和directive不同的地方是它给定的不是一个类，而是一个函数，但其实本质也没有区别，
用法完全可以和directive一样的。

Event
-----

Event前面介绍过，用于实现回调。它通过app.add_event()添加，app.connect()挂接，
app.emit()发起调用。需要具体知道什么事件在什么时机回调的，全文搜emit的位置就可
以了。

如果是写扩展，最常用的几个事件是：

source-read
        这是读入rst的时机，这里可以访问源代码

doctree-read
        这是把源代码初次转化为document树后的时机，这里可以访问初期的doctree

doctree-resolved
        这是其他文档索引本文档的时机，这时你可以根据这个索引，重新更改本文档的
        内容或者为其他文档提供本文档的信息等。很多后期处理放在这个阶段

Domain
-------

Domain为directive和role提供了一个名称空间，比如在C语言中，你才需要c_function这
个directive，那么我们可以创建一个就叫c:function的directive。默认Domain是可以省
略的，sphinx默认的domain就是rst。所以你平时写的directive，其实都是rst:directive
。

这个概念很容易联想，这里不深入打开了。

config value
------------
配置值就是conf.py中你设置的那些变量，它可以通过：::

        app.add_config_value(name, default, rebuild)

增加，然后在后期用app.config[]访问。其中这个rebuild是重新编译条件，也就是如果这
个配置修改了，什么情形下需要重新编译，是个字符串，最常用的是None或者'html'，前
者不用rebuild，后者表示如果输出html就rebuild。


.. [#n1] Python2也有一样的东西，但本文专注考虑Python3的情况。
