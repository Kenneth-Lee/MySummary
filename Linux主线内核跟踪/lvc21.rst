.. Kenneth Lee 版权所有 2021

:Authors: Kenneth Lee
:Version: 1.0

Linaro Virtual Connect 2021
*****************************

介绍
====
Linaro Connect的跟踪不是Linux内核跟踪的一部分，但相关性其实很大，也不知道为这个
跟踪开一个新的主题，所以就写在这里了。

这个跟踪主要是把所有的主题看一遍（在\ `这里`_\ ），把其中感兴趣的主题突出描述出
来。

.. _`这里`: https://connect.linaro.org/resources/lvc21/

主题遍历
=========

300K1：ARM SystemReady
-----------------------
ARM扩展ServerReady的新概念（看来是收益不错，做上瘾了？），在SR的基础上扩展IR（
IoT），ES（边缘服务器），和LS（Linux Group Server）结构也和ServerReady类似：硬
件要求，BIOS要求加兼容性测试套。

IR的要素包括：UEFI子集+DTS，uboot，TF-A，Yocto。32/64bit。

ES的要素包括：UEFI全集+ACPI+SMBUS，64bit。

LS估计还在设计中，没有详细提。

300K2：Trusted Substrate Panel
--------------------------------
讨论会，没有胶片。



301：True Story: How Rust for AArch64 Linux became a Tier-1 target platform
----------------------------------------------------------------------------
1. Rust意图统一高层和底层编码的需要

2. 演讲花了大量的篇幅介绍Rust是什么，和做广告。老实说，我的英语不好，没有听明白
   广告具体的技术点。

3. Rust定义的Tier X层次挺有参考价值：

   * T1： “保证能工作”，有官方二进制支持，有自动测试，有文档说明

   * T2：“保证能编译”，也有官方二进制支持，但不是每个测试都能通过，库可能有缺失

   * T3：“理论上能工作”

4. ARM实现T1支持主要是靠双方联合团队实现的，用Ampere@Packet作为硬件开发平台。CI
   用github actions，加Rust自己的用例，自动上Packet云完成。

总的来说，我觉得这是一个广告，广告的内容，就是：ARM是Rust的Tier-1支持平台。

302：Integration Arm SPE in Perf for Memory Profiling
--------------------------------------------------------
SPE是Stastistical Profile Extension，A8.2开始支持，主要目的是不但跟踪内存发生的
地点，同时记录被访问内存的位置（两种位置：内存地址，Cache Line层级）。最后用于
支持perf c2c命令。

具体的工作原理，我觉得现场没有说清楚，这个演讲提取SPE和c2c两个关键字就差不多了。

作为参考，下面是SPE记录的内容：::

        0.      (Address)       Virtual PC of the load instruction.
        1.      (Type)          Load instruction.
        2.      (Counter)       Number of cycles spent waiting for the
                                instruction to be issued.
        3.      (Address)       Virtual address accessed by the instruction.
        4.      (Counter)       Number of cycles spent executing the instruction.
        5.      (Counter)       Number of cycles spent translating the address.
        6.      (Address)       Physical address accessed by the instruction.
        7.      (Source)        Where in the system the data was returned from.
        8.      (Events)        E.g. Missed in level 1 data cache and TLB.
        9.      (End)           End of record, optionally containing a timestamp
                                for the instruction

303： Secure Partition Manager(Armv8.4 Secure EL2)
---------------------------------------------------
Secure EL2是8.4的重要特性，我是一直没有搞明白这个需求是怎么来的，安全区连虚拟化
都支持，这个安全区功能也太强大了，还能安全吗？

todo
