# Kenneth Lee的工作和生活总结

本工程原本是知乎上的三个专栏，为了更好维护和备份，迁移为一个git工程，用
python3-sphinx管理。

sphinx基于reStructured Markdown语言(rst)写成，和md格式一样，它也是文本文件，所
以可以直接用文本编辑器打开阅读。在gitee或者github等网站上，甚至可以解释其中部
分的格式。但如果文档之间有相互引用，或者文档中使用了数学公式，用这种方法阅读都
是看不到的。我为此申请了readthedocs的自动生成服务，读者可以直接在这里阅读生成
后的版本：[MySummary](https://mysummary.readthedocs.io/zh/latest/index.html)。

但如果要得到完整的格式支持，需要通过：

```bash
make html
make epub
```

等方式编译成html或者epub等格式。

项目原来包含一个道德经翻译的子目录。2020底，我开始这个翻译转化为一本书，项目在
这里：

* [道德经直译@gitee](https://gitee.com/Kenneth-Lee-2012/daodejing_translation)

* [道德经直译@github](https://github.com/Kenneth-Lee-2012/daodejing_translation)

所以，本项目的“道德经直译”目录中翻译的部分不再进行内容修正，但我仍会使用该目录
补充我关于《道德经》的一些建模心得。

当前我用了两个git托管服务，路径分别是：

1. git@github.com:Kenneth-Lee/MySummary.git

2. git@gitee.com:Kenneth-Lee-2012/MySummary.git

读者可以根据需要选择就近的服务器下载整个项目的源代码。其中gitee网站使用非常粗
暴的敏感词过滤系统，所以经常把项目中的部分文件标识为“有敏感内容”，其实这里讨论
的都是技术问题，根本就没有什么敏感内容。有直接在网站上阅读的读者经常问怎么获得
对应的内容，这有很多解决方法：

1. 可以下载文件后自己编译

2. 直接下载我定时编译的Released版本：
   [Release](https://gitee.com/Kenneth-Lee-2012/MySummary/releases)

3. 在github上阅读

4. 在readthedocs上的版本：
   [MySummary](https://mysummary.readthedocs.io/zh/latest/index.html)
