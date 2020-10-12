.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

Is retpoline really safe?
**************************

retpoline is a solution from Google for Spectre BTB Injection attack.

BTB Injection is a method cheating the Branch Target Buffer in the CPU
pipeline. The Branch Target Buffer is a cache used by the CPU instruction fetch
module. When a branch instruction is fetched and assumed taken, the next
instruction will be fetched from the BTB for speculative execution.

The index of BTB is mapped to the PC of the instruction. But some CPU may not
check the whole PC for the BTB entry. So different PC may reuse the same BTB
entry. This is called BTB alias. And it gives the user application the chance
to train the BTB entry which is also used by the kernel. For example, it can
make the CPU use its own code for speculative execution. So it can update the
cache status with kernel data and make up a cache timing side channel.

The retpoline solution replace the indirect branch with ret by recompile the
attackee's code. Because the ret instruction use RSB rather than BTB for
speculative execution. So the BTB injection does not work on it.

But is retpoline really safe on all platform? As a general concept, BTB can
store not only absolution address, but also relative one. If the attacker train
a relative address and make it refer to some code inside the attackee space, we
will face the same attack as Spectre Bound Check Bypass. And this time, there
is no way to check the code pattern.
