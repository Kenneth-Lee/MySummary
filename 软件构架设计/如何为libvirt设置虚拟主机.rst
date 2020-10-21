.. Kenneth Lee 版权所有 2018-2020

:Authors: Kenneth Lee
:Version: 1.0

如何为libvirt设置虚拟主机
**************************

最近在ARM Server上分析虚拟机的数据压力，其中一种场景类似Docker，要把guest中的端
口映射到host中，类似对Docker Image中做这样的动作：::

        docker run -p 8080:80 my_web_server

但libvirt没有这样的配置，只在手册（Networking - Libvirt Wiki）中这样建议：::

        iptables -I FORWARD -o virbr0 -d  $GUEST_IP \
                -j ACCEPT iptables -t nat -I PREROUTING \
                -p tcp --dport $HOST_PORT \
                -j DNAT --to $GUEST_IP:$GUEST_PORT

但实际上你这样做了，映射根本过不去。

所以，我和Docker的规则对了一下，发现区别在这个地方：

首先，DNAT不仅仅要对PREROUTING链来做，还要对OUTPUT链来做：::

        iptables -t nat -A OUTPUT -p tcp --dport $HOST_PORT 
                -j DNAT --to-destination $GUEST_IP:$GUEST_IP

第二，要给反向的包做SNAT：::

        iptables -t nat -A POSTROUTING -d $GUEST_IP \
                -s $GUEST_IP -p tcp --dport $GUEST_PORT \
                -j MASQUERADE

这样就通了。

深入分析一下，其实第二条是不需要的，因为如果你的机器使用默认的NAT网络，本来就有
这个配置，而且，很多协议并不需要双向连接，没有SNAT并不会引起问题。


而增加第一个配置的原因可以从这个图上看出来（来源：
https://upload.wikimedia.org/wikipedia/commons/3/37/Netfilter-packet-flow.svg）
：

        .. figure:: _static/qemu-iptable.jpg

veth是路由一层的协议，不经过nat链在链路层布下的PREROUTING钩子的，所以如果不在
OUTPUT上做DNAT，就没有DNAT了。


libvirt在这个问题上处理得好的话，应该把这种映射直接做在网络的XML配置中的，不过
libvirt的应用场景和docker不一样，前者通常是用vxlan连接多个跨节点的虚拟机的，不
需要通过本地的Host做防火墙，所以这个功能就没人弄了。但其实做单机测试和验证这个
功能却很常用，希望圈内人士可以把这个功能加进去。
