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

我个人不喜欢知乎的氛围，所以知乎的帐号已经删除，以后正式的写作总结，我都改写到
这里。我写东西的主要目的是为了对某些复杂的信息进行建模。既然是建模，就意味着我
有可能有错误的观察（写出来就是为了更容易看到我观察到的是什么，并判断这种观察有
没有错）。我想还有很多人也有这种观察的需要，所以这些观察我也分享到这里来了，但
git不是一个好的讨论平台，如果有幸有读者有所赐教，不妨发我的
email：Kenneth-Lee-2012@qq.com。

在自行维护的过程中，我开始加入新的主题，现在放入的新主题包括：

Linux主线内核跟踪
        这个主题主要用于跟踪Linux内核主线的升级变化。

概念空间分析
        这个主题用于整理对各种软件或者其他领域的概念空间的分析。

逻辑哲学论分析
        这个主题就是文字表面的意思。

本工程用Python Sphinx进行管理，所有的文本都是reStructuredText文档，这是一种文字
安排有特殊设置的文本文件，可以被很多git托管服务所解释，所以阅读者可以在如gitee
，github这样的代码托管服务上直接阅读每个独立的文件。但如果文档之间有相互引用，
或者文档中使用了数学公式，用这种方法阅读都是看不到的。我为此申请了readthedocs
的自动生成服务，读者可以直接在这里阅读生成后的版本：

        `MySummary <https://mysummary.readthedocs.io/zh/latest/index.html>`_

另外，2020底，我开始把道德经直译转化为一本书，项目在这里：

        https://gitee.com/Kenneth-Lee-2012/daodejing_translation

所以，本项目的“道德经直译”目录中翻译的部分不再进行内容修正，但我仍会使用该目录
补充我关于《道德经》的一些建模心得。

当前我用了两个git托管服务，路径分别是：

1. git@github.com:Kenneth-Lee/MySummary.git

2. git@gitee.com:Kenneth-Lee-2012/MySummary.git

读者可以根据需要选择就近的服务器下载整个项目的源代码。

.. toctree::
   :maxdepth: 2
   :numbered:
   :caption: 独立专栏：

   道德经直译/README
   花朵的温室/README
   软件构架设计/README
   Linux主线内核跟踪/README
   概念空间分析/README
   逻辑哲学论分析/README
   分类索引

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
