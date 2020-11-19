.. MySummary documentation master file, created by
   sphinx-quickstart on Sat Nov  2 07:53:59 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Kenneth Lee的工作和生活总结
===========================

本工程原本是知乎上的三个专栏，为了更好维护和备份，迁移为一个git工程，其中包括如
下三个主题：

   道德经直译

   花朵的温室

   软件构架设计

我现在已经不再给知乎写东西了，所以除了迁移的内容，新的心得会分散放入这些专栏中，
但写法就不再是针对特定的读者来写了，纯以自己写给自己来组织内容。git不是一个好的
讨论平台，如果有幸有读者有所赐教，不妨发我的email：Kenneth-Lee-2012@qq.com。

在自行维护的过程中，我开始加入新的主题，现在放入的新主题包括：

除此以外，我开始把一个Linux主线内核跟踪的工作也放到这个地方来，所以整个项目会增
加这个主题：

Linux主线内核跟踪
        跟踪Linux内核主线的升级变化

概念空间分析
        这个主题用于收集对各种软件或者其他领域的概念空间的分析

本工程用Python Sphinx进行管理，所有的文本都是reStructuredText文档，这是一种文字
安排有特殊设置的文本文件，可以被很多git托管服务所解释，所以阅读者可以在如gitee
，github这样的代码托管服务上直接阅读每个独立的文件。但如果文档之间有相互引用，
这种引用是看不到的。为此我不定期会对文档进行编译，把epub版本作为本项目的二进制
发布，读者可以在这里下载阅读：

        https://gitee.com/Kenneth-Lee-2012/MySummary/releases

另外，2020底，我开始把道德经直译转化为一本书，项目在这里：

        https://gitee.com/Kenneth-Lee-2012/daodejing_translation

所以，本项目的“道德经直译”目录中翻译的部分不再进行内容修正，但我仍会使用该目录
补充我关于《道德经》的心得。

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   道德经直译/README
   花朵的温室/README
   软件构架设计/README
   Linux主线内核跟踪/README
   概念空间分析/README

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
