#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket, select
import Queue
import yaml

confile = open('agent_check.yaml')
conf = yaml.load(confile)
epoll = select.epoll()
message_queues = {}
timeout = 1
socket_pool = {}
socket_type = {}
fd_to_socket = {}
status = {}
oldstatus = {}


 
for pool in conf:
  print conf[pool]
  status[pool] = "up"
  oldstatus[pool] = "up"
  for type in conf[pool]:
    host = conf[pool][type]['host']
    port = conf[pool][type]['port']
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr = (host, port)
    s.bind(addr)
    s.listen(1)
    print  "服务器启动成功，监听IP：" , addr
    s.setblocking(0)
    epoll.register(s.fileno(), select.EPOLLIN)
    socket_pool[s.fileno()] = pool
    socket_type[s.fileno()] = type
    fd_to_socket[s.fileno()] = s

while True:
  print "等待活动连接......"
  events = epoll.poll(timeout)
  if not events:
     print "epoll超时无活动连接，重新轮询......"
     continue
  print "有" , len(events), "个新事件，开始处理......"
  for fd, event in events:
    socket = fd_to_socket[fd]
    if event & select.EPOLLIN:
      if socket_type[fd] == 'check':
        connection, address = socket.accept()
        print "新连接：" , address
        connection.setblocking(0)
        connection.send(status[socket_pool[fd]]+"\n")
        connection.close()
      elif socket_type[fd] == 'manage':
        connection, address = socket.accept()
        print "新连接：" , address
        connection.setblocking(0)
        epoll.register(connection.fileno(), select.EPOLLIN)
        socket_pool[connection.fileno()] = socket_pool[fd]
        socket_type[connection.fileno()] = ""
        fd_to_socket[connection.fileno()] = connection
        message_queues[connection]  = Queue.Queue()
      else:
        try:
          data = socket.recv(1024)
          if  data.strip('\n') in ["ready","up","maint","drain","down"]:
            print "收到数据：" , data , "客户端：" , socket.getpeername()
            oldstatus[socket_pool[fd]] = status[socket_pool[fd]]
            status[socket_pool[fd]] = data.strip('\n')
            message_queues[socket].put("changed from " + oldstatus[socket_pool[fd]] + " to " + status[socket_pool[fd]] + "\n")
            epoll.modify(fd, select.EPOLLOUT)
          else:
            socket.close()
            del socket_type[fd]
            del socket_pool[fd]
            epoll.unregister(fd)
        except socket.error:
          socket.close()
          del socket_type[fd]
          del socket_pool[fd]
          epoll.unregister(fd)
    elif event & select.EPOLLOUT:
      try:
        msg = message_queues[socket].get_nowait()
      except Queue.Empty:
        print socket.getpeername() , " queue empty"
        epoll.modify(fd, select.EPOLLIN)
      else :
        print "发送数据：" , data , "客户端：" , socket.getpeername()
        socket.send(msg)
    elif event & select.EPOLLHUP:
      epoll.unregister(fd)
      fd_to_socket[fd].close()
      del socket_type[fd]
      del socket_pool[fd]
      del fd_to_socket[fd]

for s in socket_type:
  epoll.unregister(s.fileno())
epoll.close()
for s in socket_type:
  s.close()

