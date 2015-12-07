haproxy的agent-check功能作为辅助健康监测，管理人员可以通过接口动态调整后端服务状态、权重。在上线业务时，先将服务调整为维护状态，然后更新代码、重启服务，服务恢复之后再将服务调整为可用状态。


默认配置文件为 agent_check.yaml , 内容格式如下：
-----------------------------------------
uid_stat:            #定义应用
  check:             #用于haproxy监控
    host: 0.0.0.0    #监听IP
    port: 4201      #端口
  manage:            #管理，仅限更新状态
    host: 0.0.0.0    #监听IP
    port: 4202      #管理端口
----------------------------------------

启动：
 python haproxy_agent.py &>/dev/null &

连接 check端口，默认返回 up 状态。
>> nc 127.0.0.1 4201

操作：
 连接 manage端口，可以修改状态。
>> echo drain | nc 127.0.0.1 4202 
 或者 
>> nc 127.0.0.1 4202 然后输入要切换的状态

在上线代码之前，
修改状态为drain 或 maint ，服务恢复之后修改为ready
或
先修改为 down  , 恢复之后改为 up


haproxy配置中，
server test ip:port check agent-check agent-port 4201
