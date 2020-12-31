.. Kenneth Lee 版权所有 2020

:Authors: Kenneth Lee
:Version: 1.0

glib
*****

事件循环
=========

glib的事件循环用于处理事件的收集和分发。它包含这样一些概念：

Source
        事件源，比如文件句柄。可以被attach到Context

Context
        用于一个线程的上下文。CMainContext

GMainLoop
        事件循环，对应一个Context

原理就是创建一个GMainLoop，装上Context，加入Source，然后调用run等消息出来然后
处理就行了。

举个例子，你创建一个线程，在线程中顺序要处理各种各样的事件，你可以这样：::

        //创建context，并用它创建mainloop
        context = g_main_context_new(...);
        mainloop = g_main_loop_new(context, ...);

        //创建source1，然后attach到context
        source1 = g_io_create_watch(...);
        g_source_set_callback(source1, callback...);
        g_source_attach(source1, context);
        g_source_unref(source1);

        //创建source2，然后attach到context
        source2 = g_timeout_source_new(...);
        g_source_set_callback(source2, callback...);
        g_source_attach(source2, context);
        g_source_unref(source2);

        //可以创建更多的source并加上callback，然后attach

        //进入调度，进入不同的回调。直到线程内或外有人调用g_main_context_quit()
        g_main_loop_run(mainloop);

        //释放context
        g_main_loop_unref(context);

这东西有Python的封装。
