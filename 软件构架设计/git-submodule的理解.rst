git submodule的理解
********************

今天和人讨论在某个方案中到底应该用Google的repo（Android中引入的那个）还是直接用
git原生的submodule管理多个项目，我想对方可能并不理解submodule的设计逻辑是什么，
这里为他建一个概念空间。

本文假设读者对一般的git的revision和branch管理已经有基本的认识和实际操作经验。

很多时候，我们需要做“组合”项目，比如我们做一个解决方案，做了一块嵌入式单板，这
个单板的解决方案会包括gcc，kernel，uclibc, busybox，还有这块单板专用的一些软件
，比如robot_control。这些软件每个都有自己的git历史管理，但为了在这块单板上运行
，我们需要把它们“组合”成一个解决方案，最后编译出一个board_firmware，用来烧到单
板的flash中，控制单板的运行。

如果直接把用到的那些版本的部件的源代码都拷贝在一起，这样我们就丢失这些源代码的
历史记录了，也很难从上游rebase，把一些新的开发成功同步过来。

submodule解决的就是这样一个问题，你可以创建一个新的叫board的git tree，里面是生
成board_firmware的脚本，同时把其他依赖的项目通过git submodule add的方式加进来，
构成一个组合项目，那些原始的submodule还是用原来的方式管理。

submodule最容易让人误会的是，组合submodule的那个项目不包含submodule，它只是
submodule的一个索引。比如你在board项目中add gcc作为一个submodule，在board项目中
，你只是增加了两个东西：

1. 在board项目的根目录下增加了一个.gitmodule文件，里面包含了这个submodule的路径
   在board项目的对象存储结构的根目录中

2. 增加了一个叫gcc的类型是commit的成员，记录gcc的HEAD sha1的对象索引

这两个信息合起来其实就是支持你在这下面运行clone+checkout两个命令的全部信息。

下面是add命令后board master分支的对象树的结构：::

    kenny@kllt09:~/work/board$ git ls-tree master
    100644 blob 31dbbaf60a542b4faf13582b770526ae37b0c094    .gitmodules
    040000 tree fd44ee11cfbd6d111c918010c2206ff383a6bdcd    docs
    160000 commit 60a6d6357708bd570c2fc3f27b5b27e8dab1befc  gcc
    100644 blob 259b24152b284e29e86afadf714ddc3c2aa8dfe8    README

读者可以看到，这个gcc既不是一个tree（目录），也不是一个blob（文件），而是一个
commit，它的sha就是我们加gcc的时候的HEAD。

也就是说，board的存储结构中，仅仅包含了gcc的git树所在的位置，以及我们引用它的那
个具体的版本。之后你可以在board中随意修改你自己的内容，或者调整gcc对上游的索引
，这都不影响gcc的上游，你修改的仅仅是board里面的内容。

假如你进入gcc submodule，更新了版本，这时有两个东西发生了改变：

1. 你的本地gcc submodule的HEAD发生了改变

2. 你的board项目对象树中那个叫gcc的commit（的sha1）发生了改变（需要你主动在本地
   commit，在这之前仅仅是index发生了更改）

如果你push了你的board到主线，但没有push gcc到主线。那么其他人clone你的board主线
，那里会索引到一个新的gcc revision，但这个revision不在gcc的主线上，那么他就无法
更新这个submodule了。

从这个角度来说，我觉得submodule其实比repo更适合用来管理组合项目，因为他确实就聚
焦到组合这个主题上，而且和git的语义空间是无缝组合的。

-------------------------

补充1：关于subtree

评论中有人提到subtree，这里补充两句。subtree和submodule的功能很相似，但和本文提
到的需求是不一样的。subtree是完全把子项目拉到本项目中一起管理的，两个项目的提交
也是合并在一起的。这基本上就是一个项目了（但因为有subtree的记录，可以用
push/pull和上游同步）。你事后也可以重新split这个目录（无论之前是否用subtree add
加进去的）为一个git分支(git subtree split -P subtree-name -b branch-name)，但这
只是重新从当前项目中分解提交记录而已（如果某些提交记录包含其他目录，这些记录也
会加进来）。

这起的不是“组合”多个项目的作用，这起的是“合并”多个项目的作用。

补充2：关于monorepo

评论中另外有人提到monorepo。老实说，我是第一次听到这个说法，查了一下wiki，发现
这不是一个软件，而是一种管理策略，简单定义如下：::

    a software development strategy where code for many projects is stored in the same repository.

我说明一下，我这里说的repo不是这个泛化的概念，而就是指AOSP（Android Open Source
Poroject）中用到的repo脚本。但确实这个repo脚本是一种monorepo。
