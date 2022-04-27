.. Kenneth Lee 版权所有 2022

:Authors: Kenneth Lee
:Version: 0.1
:Date: 2022-04-27
:Status: Draft

硬编码Tag方案
*************

这里给做某个实现的同事提供一个在自定义指令中实现硬编码一个Tag的软件实现技巧。

问题是这样的：我需要在一个CPU上增加一个调试指令，以便调用这个指令可以在一个端口
上打一个点，这样我调试初始化代码的时候就可以看到启动的过程了。

问题是现在我不想修改编译器，所以我需要在我的程序中硬编码这段代码，比如汇编上我
可以写：::

  .2byte OPCODE
  .2byte tag

这样我在CPU中译码匹配到这个指令，我就可以把tag输出到某条总线上。现在的问题是，
这个代码怎么写?我才能实现这样的代码效果？：::

  ...
  debug_reach(tag);
  ...

这肯定不能是个函数，因为tag必须硬编码到指令中。那就只能让它是个宏了，是个宏，那
我的汇编就只能是嵌入式汇编了。所以应该这样弄：

.. code-block:: c

  #define OPCODE 0xdeb0
  
  #define stringify(str) #str
  #define debug_reach(TAG) asm( \
		  "	.4byte " stringfy(OPCODE) "\n" \
		  "	.4byte " stringfy(TAG) "\n")
  
  int test(void) {
          ... 
	  debug_reach(0x1111);
          ...  
  }

这样，就可以在启动代码中大量打点，而不需要动态传递参数到指令中。
