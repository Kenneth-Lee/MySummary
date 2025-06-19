.. Kenneth Lee 版权所有 2020-2025

:Authors: Kenneth Lee
:Version: 1.0

CPU模拟
*******

CPU对象
=======

和其他设备一样，CPU也是一种QoM，继承树是：::

        TYPE_DEVICE <- TYPE_CPU <- TYPE_MY_CPU

CPU有自己的as，mr，如果是全系统模拟，这当然就是system_as这些东西了。

CPU对象的模拟使用不同的算法，在CPU的概念中称为一种加速器，Accelerator。TCG，KVM
都是Accelerator。

CPU的状态定义在它的QoM的State中，由加速器在模拟的过程中进行同步修改，但这种修改
不是实时的。

就现在来说，无论是哪种加速器，Qemu都创建了一个本地线程去匹配它，所以我们可以简
单认为每个虚拟的CPU就是Host上的一个线程，在这个线程之内的调用，都是串行的，只有
访问CPU间的数据结构才需要上锁保护。

TCG
===

TCG，Tiny Code Generator，是Qemu最基本的模拟加速器，它是一个纯软件的模拟器，可
以在任何qemu支持的平台上，模拟任何其他硬件平台。

和很多解释型的CPU模拟系统不同，TCG不是通过一条条指令解释执行的，而是先把Guest的
指令翻译成Qemu中间代码，进行中间代码优化，然后再把中间代码翻译成Host代码，才投
入执行的（这相当于是个JIT）。所以，在TCG的概念空间中，target不是qemu中那个被模
拟的系统的概念，而是翻译结果的概念，而这个翻译结果是本地平台的指令，刚好和qemu
的target相反。比如你在x86上模拟RISCV，qemu的target是RISCV，但tcg的target是x86，
而RISCV，则称为Guest。

TCG target组织成多个Translate Buffer，简称TB。它把Guest的代码分成多个小块，一次
连续翻译多条指令到这个TB中，然后跳进去执行，执行完了，再翻译一个TB。这些TB作为
Cache存在，如果指令跳回到到翻译过的地方，可以直接复用这些Cache（TB）。这个算法
大幅提升了Qemu的模拟效率，是qemu最初被称为“Quick EMUlator”的原因。

.. note::

        如果运气好（实际上很容易发生），每段代码在Qemu中都只会被翻译一次，之后
        基本上Qemu就在TB之间流转，而不再进入翻译。这在实际应用中，可以成百倍提
        高Qemu的模拟速度。

我们Review一下前面这个过程，这里其实有三个程序上下文：

1. Guest的执行上下文，我们简称G。
2. Qemu自身的执行上下文，我们简称Q。
3. TB的执行上下文，我们简称T。

比如在ARM上执行riscv的jal指令，jal是guest的期望，jal表现的行为就是G上下文，Qemu
的程序负责把jal翻译到TB中，这个执行翻译的程序属于Q上下文。而TB中的动态代码需要
负责修改Qemu中定义的那些表示CPU状态的数据结构，这些动态代码，就在运行T上下文。

本质上，Q和T是同一个上下文，但在使用感受上是有区别的，这主要体现为三点：

1. 如果你用gdb去跟踪qemu，你只能看到Q上下文，T上下文对gdb是黑盒，因为T是动态生
   成的，gdb并没没有它的信息。

2. T上下文理论上可以调用qemu的任何代码，但TCG做这个链接的时候只使用TCGv变量和
   helper函数，所以T上下文看不见qemu中的全部符号。

3. 我们特别区分Q和T上下文还有一个重要原因是在看北向翻译代码的时候很容易产生错
   觉，需要我们特别区分。比如下面这个代码：::

        TCGv_ptr fpst = tcg_temp_new_ptr();
        int offset = offsetof(CPUARMState, vfp.fp_status[flavour]);
        tcg_gen_addi_ptr(statusptr, tcg_env, offset);
        gen_helper_vfp_muladdh(vd, vn, vm, vd, fpst);

   这个代码是ARM vfm_hp指令翻译的一部分。这4行都是在Q上下文中执行的，而第3，4
   两句都产生了中间代码，这个要求的动作是在T上下文中发生的。翻译程序是完成了整
   个TB的翻译才投入执行的，所以，这里计算offset是个静态行为，它在翻译的时候得
   到一个静态的值，然后在动态执行中间代码的时候要求把tcg_env寄存器加上这个静态
   的值，作为helper函数vfp_muladdh()的参数输入。我们必须很清楚第2行是Q上下文的，
   而3和4所要求的行为是属于T上下文的。两者甚至没有必然的顺序关系，因为如果这个
   TB被翻译过，那么之后再执行就根本不会有这个翻译了。offset的计算只在翻译的时
   候发生了一次，后面反复执行的是中间代码addi_ptr和vfp_muladdh，这个不能说是G
   上下文（因为这是vfm_hp指令里面），那我们就得强调这是T上下文了。

这特别容易误会，因为在helper函数中，你看起来已经可以调用qemu中任何函数了。就函
数本身，你不一定能感受到你是在Q上下文中，还是T上下文中。但在两个上下文中的行为
是不一样的。

.. note::

   如果用User模式运行Qemu模拟程序，并用perf record跟踪这个程序，perf会报告部分
   时间消耗在JIT中，这个JIT就是T上下文消耗的时间。

为了代码更好地复用，TCG把翻译过程分成两步。第一步把G指令翻译成中间指令（我们把
这个称为QOP，Qemu Operation），第二步把中间指令翻译成Target的。这样就不用每个
Guest都要提供一组Target的翻译了。而是分成南北两个实现：

* 北向是Qemu Target，这部分程序负责把Guest指令翻译到TB中（当前代码在
  target/<arch>目录下）。
 
* 南向是TCG Target，这部分程序负责把QOP翻译成TB里面的真实代码（当前代码在
  tcg/<arch>目录下）。

.. note:: 由于QOP从来不需要任何人去“运行”，所以它只是一个放在TB中的记录
   （struct TCGOp），记录操作需要的参数，让南向接口可以根据这个要求去翻译
   Target而已。它并不需要有自己的指令编码。

   当前的代码中，QOP支持的指令可以从tcg-opc.h文件中找到。

这样一来，你要模拟任何Guest系统，只要实现北向接口就可以了。要支持任何Host平台，
只要实现南向接口而已。两个目的是完全独立的。

整个CPU的模拟过程可以总结为这样一个过程的循环：

1. 用北向模块的gen_intermediate_code()把Guest代码翻译成GOP，保存在TB中。
2. 优化中间代码
3. 用南向模块的tcg_out_op()接口生成Host侧代码，保存在TB的运行缓冲中
4. 跳入TB的运行缓冲中执行本地代码

这个跳入的过程对Q上下文来说，就是一个函数调用：::

        tcg_qemu_tb_exec(CPUArchState *env, uint8_t *tb_ptr)

T上下文根据这个调用的要求更新CPU的状态（即CPUArchState对象中相应的内存）就可以
了。

北向模块接口
------------

北向接口完成第一步：从Guest指令到GOP。

Qemu写了一个Python程序基于定义文件自动生成decode程序，以便降低北向模块的写作成
本。它的输入是一个.decode文件，格式在这里有介绍：docs/devel/decodetree.rst。在
qemu的Make文件meson.build中调用decode_tree，可以生成一个.inc文件，里面为每个指
令生成一个decode_xxx函数，你包含这个inc文件，就可以直接调用这个函数直接进行解
码。解码后，inc文件会主动调用对应代码的“trans”为前缀的函数，向TB中填充代码。所
以，一般来说，你只需要写一个translate文件，包含decode产生的decode函数，并在里
面定义所有的trans函数，就可以支持这个Arch的TCG了。

trans函数完成guest代码到tcg target的翻译过程，生成TCG中间代码，这通过一系列的
tcg_gen_xxxx()函数来完成。

看一个例子。下面是一个为了说明问题而改进过的riscv的trans_addi翻译算法：

.. code-block:: C 

  static bool trans_addi(DisasContext *ctx, arg_addi *a)
  {
      TCGv tmp = tcg_temp_new();

      tcg_gen_mov_i64(tmp, cpu_gpr[a->rs1]);
      tcg_gen_addi_i64(tmp, tmp, a->imm);
      tcg_gen_mov_i64(cpu_gpr[a->rd], tmp);

      tcg_temp_free(source1);
      return true;
  }

RISCV的原始指令是这样的：::

  addi rd, rs1, imm

解码的时候我们得到的是三个数字rd, rs1和imm。我们用rs1作为下标可以找到代表rs1的
寄存器，这个cpu_gpr数组其实是Q上下文里面的，但Qemu已经把它暴露到G空间了，所以
直接访问并没有问题，这里没有直接对它做加法，而是选择另放了一个中间变量，然后
rs1读进去，用中间变量完成加法后再写到rd要求的寄存器变量中。（这个地方写得有点
冗余是有理由的，因为源和目标可能会是同一个寄存器，读走再写入才能不产生冲突。）

所以，看起来这是翻译成三个GOP：::

  mov_i64 tmp, rs1
  addi_i64 tmp, tmp, imm
  mov_i64 rs1, tmp

不过tcg_gen函数并非总是生成单条指令的，如果用qemu的跟踪功能，你会发现它实际产
生了四条指令：::

   mov_i64 tmp2,x5/t0
   movi_i64 tmp3,imm
   add_i64 tmp2,tmp2,tmp3
   mov_i64 x12/a2,tmp2
  
明显tcg_gen_addi_i64()也申请了一个临时变量，然后先用movi_i64把立即数移进去，然
后做通用的变量加法，实现变量加立即数的效果。

Qemu优化器合并临时变量，和前后的指令一配合（这一点本上下文没有反映出来，读者认
为会发生这种重新优化就行），4条TCG指令优化成2条：::

   movi_i64 tmp2,imm2
   mov_i64 x12/a2,tmp2

这些中间指令再翻译成ARM指令，就是这样的：::

  0xffff8f41b0d0:  f9001674  str      x20, [x19, #0x28]
  0xffff8f41b0d4:  52820514  movz     w20, imm2
  0xffff8f41b0d8:  f9003274  str      x20, [x19, #0x60]               

这里第一条指令先把前一条指令的结果（x20）更新到CPUState(env)上，然后更新tmp2分
配的寄存器，再把它更新到CPUArchState上。

从这个例子可以看到整个翻译过程包括这些动作：

1. Guest翻译程序使用gen系列函数生成目标TCG程序逻辑。
2. gen系列函数生成QOP。
3. TCG框架对QOP进行优化。
4. 把优化过的代码生成Target代码。

这些过程可以通过qmeu命令的-d参数跟踪。

QOP指令不使用寄存器，而是使用自己的变量来支持各种计算。这些变量称为TCGv，它们被
翻译成T上下文指令的时候，会用Target的寄存器来取代。为了支持这种取代，它们有不同
的类型，每种类型有不同的生命周期，这主要包括：

1. 普通TCG变量：通过tcg_temp_new()等函数创建的临时变量，它们只在一个BB之内有效
   （最近的qemu版本叫EBB，参考TEMP_EBB的定义）。

   BB是TB的一个子集，GOP是支持TB内跳转的（比如tcg_jump, tcg_br，tcg_brcond等），
   一旦发生跳转，就算是离开当前的BB了，这种情况下，普通TCGv就可以被重新分配，
   实现的时候必须在跳转前就释放它。搞这么复杂，主要是因为普通TCGv最后都对应着
   target真实的寄存器，早点释放，寄存器Spill的可能性就低一些。

2. 本地TCG变量：通过tcg_temp_local_new()创建，它在一个TB内有效。

3. 全局TCG变量：这种可以跨越BB和TB，一直有效。这种TCG可以绑定一个外界实体，比如

   1. Target寄存器：你可以把这个TCGv绑定一个Target的寄存器，在TB中，这个寄存器就
      一直这样固定分配了。在现在的实现中，基本上都用它放tcg_qemu_tb_exec(env,
      tb_ptr)的env参数，这样需要同步env的变量，就不需要从内存中读了。

   2. 内存类，这种通过tcg_global_mem_new()创建，用来对应env（在CPUArchState中）
      中的内部变量。在生成代码的时候，每次更新了这种TCGv，就会同步回内存中。

所以，整个QOP的执行原理就是：从全局TCGv中读出输入，用普通或者本地TCGv辅助完
成计算，再把结果写回到全局TCGv中。

正如前面说的，TCG框架会一个指令一个指令调用北向接口要求翻译，QOP指令写在这种北
向接口的回调函数中。每个这样的回调接口就称为一个TCG Function。所以，TCG的设计文
档说，一个Function对应一个TB。因为只要还能够调用这个回调，这个回调中产生的代码
就一定属于一个TB。但一个TB不一定只有一个Function。只是Function的设计者（实现北
向翻译的工程师）不能假定两个Function必然在同一个TB内而已。

所以，写每个Function的时候，如果没有QOP的跳转，就可以认为整个Function都在一个TB
内，里面的TCGv都用普通TCGv就可以了。反之，如果跨越了跳转，就要用本地TCGv。

从Function作者的角度，TCGv是翻译用到的变量，和执行是没有关系的。所以，对于普通
和本地TCGv，都定义为Function的局部变量就可以了。但要使用他们，你就必须用
tcg_temp_new()或者tcg_temp_local_new()在翻译上下文上分配它。所以这个变量其实是
一个运行上下文的指针。

这个说法很绕，让我们换个角度再说一次：翻译的时候TCGv是一个说明运行的时候这个变
量的要求的一个ID（某种意义上的指针，只是不是C语言意义上的）。TCGv的真正要求在
翻译上下文中，等这个QOP翻译成目标代码的时候，南向接口根据这个上下文分配寄存器
去匹配它，那时就没有什么TCGv了，那就是真正的Target寄存器以及根据类型要求对内存
中的数据进行回写。

因此，tcg_global_mem_new()等函数建立的全局TCGv通常可以是普通的全局变量。因为它
们也是固定分配在每个翻译上下文中的固定上下文，它们的值在任何一个翻译上下文中都
是一样的位置，TCGv本身作为指针，是不会变的。

正如我们前面提到的，T上下文其实就是Q上下文的一部分。所以，Function的作者在写QOP
的时候，基本上可以认为自己就在Q上下文中，除了使用一般或者local TCGv进行计算外，
可以用这些计算结果和外面进行互动。这种互动包括（下面的_y后缀通常是字长，_op表示
某个QOP）：

1. 如前所述，通过全局TCG变量访问env（本身就是CPUArchState的一部分）

2. 直接用tcg_gen_ld_y, tcg_gen_st_y, tcg_gen_op_ptr等QOP通过env相对偏移直接访问
   CPUArchState的其他变量，这常用于访问一些没法固定位置的变量，比如某个数组的下
   标。

3. 用tcg_gen_qemu_ld_y，tcg_gen_qemu_st_y访问guest内存。请注意这和前一个方法的
   区别，tcg_gen_ld_y是直接访问Qemu上下文的内存，tcg_gen_qemu_ld_y是访问Guest的
   内存，要经过MR翻译那一套的。

4. 调用helper函数直接进入Q的上下文任意访问Q的变量。这个方法相比前面的访问方法更
   通用，几乎可以无所不为，但有一定的成本。这种成本一方面体现在函数调用本身的成
   本上，同时由于无法预判你在helper中会用到和修改什么CPUArchState的环境，所以调
   用前后所有有可能受影响的绑定（target寄存器和变量的定义关系）需要全部进行同
   步。最基本的，至少PC就必须同步一次，否则在TB执行的过程中，是不会更新PC的
   （实际上，如果更新了PC，一般你需要退出本TB，查找下一个TB了）。

   所以，选择不同的helper flags，可以有效提高helper的模拟效率，比如如果你不写
   CPU状态，加上TCG_CALL_FLAG_WG就能保证生成代码的时候不会恢复这些状态。

Chained TB
----------

Qemu从Q上下文跳到T上下文执行，需要经过TB的prologue和epilogue进行上下文保存，这
需要成本，为了提高执行速度，如果一个TB完成了，下一个TB已经翻译过了，就可以直接
跳转过去，这些TB就可以全部连成一个链条，一直在TB间跳转，而不需要回到Q上下文。

这个技术称为Chained TB，对于那些循环之类的代码，Chained TB可以大幅提高性能。为
此对于跳转指令的翻译，Qemu提供了两个手段进行TB间的关联：

1. tcg_gen_lookup_and_goto_ptr()，这个函数在TB里产生一个跳转代码，这个段跳转代
   码会先调用helper函数查找下一个TB，如果查找成功，就直接跳转到那个TB中。这个效
   率比退出TB高，但因为每次都要查找，而且用绝对跳转，这个效率也有点低。

   这个函数要使用CPU状态中的PC，但PC的更新是在退出TB才做的，所以如果使用这个函
   数，先要主动更新PC。

2. tcg_gen_goto_tb()，这个函数在TB里面产生一个调用桩，第一次设置的时候，它跳到
   epilogue代码中，退出当前tb，但退出以后，Qemu会检查是否有这个桩，有的话，会把
   下一个TB的地址写入这个桩，之后再进入前面那个TB的时候，就不需要退出，直接跳到
   下一个TB了。这个方法显然更快，但它只适合固定跳转，不能动态计算目标地址。Qemu
   提供了两个目标地址供固定关联，用来处理if/else两个固定链接点。

tcg_gen_goto_tb()还涉及另一个Qemu比较复杂的算法：物理地址管理。

本来Qemu的物理地址是不需要管理的，物理地址决定物理地址以后，按ram MR记录的首地
址访问对应的Host虚拟地址就可以了。但因为有这个直接链接TB的功能，我们就要担心这
个TB的代码有没有被修改过了（自修改代码和重新启动进程都可以导致物理地址被修改）。

这样，我们就要监控每个代码修改是否更新过TB涉及的位置了。Qemu用物理Page管理这个
关系，这个数据结构称为PageDesc，如果某个TB是基于某个物理地址修改的，它的
PageDesc中就记录这个TB的相关信息，之后如果这个PageDesc被修改了，影响到的TB也会
被清除掉，这样才能保证代码正常。这也导致了，在跨Page的时候，不能产生goto_tb的代
码，这有时也会影响性能。

.. note::

   从现在的代码（比如我正在看的V7.2.50，但其实更早的代码已经是这样的了）逻辑上
   看，我认为这个跨物理页不能调用goto_tb的要求，已经过时了。现在的版本有页被修
   改以后chained到相关TB的其他TB的invalidate操作，应该是不需要的。我在
   qemu-devel@nongnu.org问了一下，Linaro的Richard Henderson答复我说断点还依靠这
   个检查。我猜有就只剩下这一个地方了，所以，如果你不需要使用调试功能，这个检查
   其实是可以关掉的，不过很多平台的代码具有局部性，很多时候这个对性能影响不大。

南向模块接口
------------

南向模块接口的实现在tcg/<arch>目录中，它主要是提供tcg_target_qemu_prologue()和
tcg_out_op()函数。实际工作就是根据tcg中间指令，决定如何映射成TB中的一段本地代码。

tcg_target_qemu_prologue()用于生成prologue和epilogue，也就是根据
tcg_qemu_tb_exec()这个函数输入，设置生成代码的工作环境，比如保存callee-saved寄
存器，这样就可以让出所有的寄存器给目标代码使用了。

而tcg_out_op()就是一条条tcg指令的映射实现，这完全是个体力活了。

TCG的线程模型
-------------

如前所述，Qemu为每个vcpu创建了一个线程。而main函数所在的线程称为iothread。由于
qemu原来设计是单线程的（称为STTCG，Single-threaded TCG），升级到多线程后（称为
MTTCG，Multi-threaded TCG），很多传统的代码并不能处理多线程。所以Qemu设计了
:ref:`BQL<bql>`
机制：除了vcpu翻译执行和iothread polling，其他处理的进入都是加上BQL的，所以，
vcpu的中断异常处理，一般设备程序的事件处理，都是串行的，不需要额外的锁保护。

iothread机制后来升级了，除了main线程天然是个iothread外，用户可以通过iothread命
令创建更多的io线程。（todo：其他iothread的BQL原理待分析）iothread使用glib的main
loop机制进行事件处理，简单说就是所有的外部事件监控都封装成文件，然后对文件组进
行polling，来一个事件用本线程处理一个事件，相当于所有io行为都在本线程上排队。这
些文件可以是字符设备，socket，eventfd，signalfd等等。

原子操作模拟
------------

如前所述，每个Guest的CPU对应的就是Host的一个线程，所以要模拟Guest CPU的原子操作
，只要用Host的原子访存就可以了。但如果要模拟的平台没有对应的Host原子访存指令怎
么办？比如我们要在没有Transaction Memory的系统上模拟Transcation Memory怎么做？

最粗暴的方法是用锁。但这样效率最低，因为每个访存操作都要上锁，而且你不可能每个
内存单元的锁都独立，这样，只要访存，撞上的机会都会很高。

一种可能的优化是对内存分段上锁，但这个算法成本也很高。

由于\ :ref:`BQL<bql>`\ 的存在，TCG选择了另一个成本更低的算法：互斥区。这个执行
区域通过start_exclusive()和end_exclusive()制造，它通过pthread_cond一类的接口，
等待所有vcpu都离开翻译执行区以后，上锁，不让它们再进入执行，这样，成功进入
start_exclusive()的vcpu就可以在其他vcpu停下的情况下执行了。

所以，当你要翻译一条做原子操作的指令时，你首先可以判断当前翻译的上下文是否原子
的（只有一个翻译线程的时候天然就是原子的），如果是原子的，就直接生成非原子的行
为就可以了，因为不会有其他线程来争抢。这个可以通过在翻译程序中判断当前TB的
CF_PARALLEL来判断。

如果你发现这是并行的，可以gen_helper_exit_atomic()，生成一条异常指令（EXCP_ATOMIC），
执行到这里的时候就会好像发生异常一样离开TB，进入互斥区，互斥去会用
cpu_exec_step_atomic()去重新生成一个只有一条指令的TB，并且去掉其中的
CF_PARALLEL参数，这样你的翻译程序就按非并行的方式生成非原子的TB执行一条指令就
行了，qemu会在互斥区完成所有的执行，然后才回到原来的并行上下文中。

.. warning::

   cpu_exec_step_atomic()方法只支持一条指令，如果需要更多，需要更多的修改才能
   做到。

mmap_lock
---------

（这是一个独立的主题。)

TCG代码中经常用到mmap_lock的概念，它是一个简单的可叠加的锁机制，qemu的代码模拟
通过mmap TB的代码区域让代码生效，但代码准备的时候必须上锁，mmap_lock允许所有这
些操作嵌套调用mmap_lock，直到真的发生冲突的时候再真的上锁。
