.. Kenneth Lee 版权所有 2019-2020

:Authors: Kenneth Lee
:Version: 1.0

Multiarch概念调查
*****************

由于设计需要，花了一点时间调查了一下Multiarch的概念，作为笔记放在这里。

Multiarch是Debian发型版提出的概念，涉及所有基于Debian实现的发行版，比如Ubuntu。
基础的定义文档在这里：Multiarch - Debian Wiki，用于在一个平台（arch）上安装多个
平台的开发运行库，比如在AMD64的系统上安装i386，ARM64的开发库（包括头文件）。很
明显，这对在本地进行交叉编译会带来很多好处。

交叉编译的包和应用使用GNU三元组表示不同的TARGET，避免名称和目录冲突，例如：
aarch64-linux-gnu，但如果还有其他配置差异，允许增加后缀，例如：
aarch64-linux-gnu_ilp32。这个表达不再称为GNU Triple，而称为Multiarch Tuple。

Debian的本地应用遵循FHS，开发库通常在/lib或者/usr/lib中（以下简称$prefix/lib）
，增加multiarch支持后，库的后面增加Tuple：$prefix/lib/<tuple>。FHS中的/lib32，
/lib64等目录定义，转化为对$prefix/lib/<tuple>的链接。

头文件放在$prefix/include/<tuple>中。

Debian明确说不支持应用，但有一个同时是程序也是库的东西（ld.so）会遵循前面对库的
定义。Ubuntu有一份文档对这个设计有更详细的定义：MultiarchSpec - Ubuntu Wiki，似
乎要尝试支持多平台的包可以混装，但似乎逻辑并没有自恰。

（在没有应用支持的情况下，你的应用需要自行找一个root来安装，然后看用什么翻译器
来运行，比如qemu-aarch64 -L $prefix/lib/<aarch64-linux-gnu/ path_to_my_app这样
。）

简单判断，短期内，这个特性不太能够依靠。要做交叉系统，还是自己围绕工具链建所有
的依赖比较实际。我原来以为它可以借用其他arch的本地编译的包用到本地系统上，看来
是我想多了
