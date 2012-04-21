#!/bin/env python

import cgi
import cgitb
cgitb.enable()
import commands
import os
import random
import socket
import sys
import time

def recv(sock):
  """
  A convenience method for receiving a message from the usetrax daemon.
  """
  result = ''
  while not result.endswith("\n"):
    chunk = sock.recv(2560)
    if chunk == '':
      result = None
      break 
    result += chunk
  if not result:
    sys.stderr.write('usetrax daemon closed connection\n')
    sys.exit(1)
  elif not result.startswith('OK '):
    sys.stderr.write('Garbled message "%s" from usetrax daemon\n' % result)
    sys.exit(1)
  return result.strip()
    
def send(sock, message):
  """
  A convenience method for sending a message to the usetrax daemon.
  """
  sock.send(message + "\n")

params = cgi.FieldStorage();

head = """Content-type: text/html\n
<html>
<head>
<title>Usetrax Graph</title>
</head>
<body bgcolor="wheat">
  <h1>Usetrax Graph</h1>
  <form action="http://triton-44.sdsc.edu/~diag/cgi-bin/usetrax.cgi">
"""
tail = """
  </form>
</body>
</html>
"""

form = '''
Server: <input type="text" name="server"/><br/>
Resource: <select name="resource">
</select><br/>
Start Time: <input type="text" name="start"/><br/>
End Time: <input type="text" name="end"/><br/>
Sum By: <select name="sumby">
<option>None</option>
<option>Job</option>
<option>User</option>
</select><br/>
'''

if params.has_key('server'):

  # Open a connection to the usetrax daemon
  server = params.getfirst('server')
  if server.find(':') < 0:
    server += ':7734'
  (addr, port) = server.split(':', 1)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sock.connect((addr, int(port)))
  except Exception, x:
    print head
    print "Connection to %s failed" % server
    print tail
    sys.exit(0)

  form = form.replace('name="server"', 'name="server" value="%s"' % server)

  send(sock, 'GETRES')
  reply = recv(sock)
  if reply.startswith('OK '):
    for resource in reply[3:].split(','):
      option = '<option>%s</option>' % resource
      form = form.replace('name="resource">', 'name="resource">\n%s' % option)

  if params.has_key('resource'):

    end = '-0'
    resource = params.getfirst('resource')
    start = '0'
    step = None
    sumby = 'None'

    if params.has_key('end'):
      end = params.getfirst('end')
    if params.has_key('start'):
      start = params.getfirst('start')
    if params.has_key('step'):
      step = int(params.getfirst('step'))
    if params.has_key('sumby'):
      sumby = params.getfirst('sumby')

    form = form.replace('option>%s' % resource, 'option selected="1">%s' % resource)
    form = form.replace('name="start"/>', 'name="start" value="%s"/>' % start)
    form = form.replace('name="end"/>', 'name="end" value="%s"/>' % end)
    form = form.replace('option>%s' % sumby, 'option selected="1">%s' % sumby)

    command = \
      './usetrax --server=%s --resource=%s --start=%s --end=%s --sum=%s' % \
      (server, resource, start, end, sumby)
    usagePerConsumer = { }
    usageTotals = { }
    for line in commands.getoutput(command).split("\n"):
      pieces = line.split()
      if len(pieces) < 2:
        continue
      usagePerAttr = { }
      for i in range(3, len(pieces), 2):
        attr = pieces[i - 1]
        usage = int(pieces[i])
        usagePerAttr[attr] = usage
        if not usageTotals.has_key(attr):
          usageTotals[attr] = 0
        usageTotals[attr] += usage
      usagePerConsumer[pieces[1]] = usagePerAttr

    pctPerConsumer = { }
    pctPerConsumer['Others'] = { }
    colorsPerConsumer = { }
    lastColor = colorsPerConsumer['Others'] = (
      random.randrange(0,256), random.randrange(0,256), random.randrange(0,256)
    )
   
    for consumer in usagePerConsumer.keys():
      for attr in usagePerConsumer[consumer]:
        pct = 100.0 * usagePerConsumer[consumer][attr] / usageTotals[attr]
        if pct < 2:
          if not pctPerConsumer['Others'].has_key(attr):
            pctPerConsumer['Others'][attr] = 0
          pctPerConsumer['Others'][attr] += pct
        else:
          if not pctPerConsumer.has_key(consumer):
            pctPerConsumer[consumer] = { }
            lastColor = colorsPerConsumer[consumer] = (
              (lastColor[0] + random.randrange(0, 256)) % 255,
              (lastColor[1] + random.randrange(0, 256)) % 255,
              (lastColor[2] + random.randrange(0, 256)) % 255
          )
          pctPerConsumer[consumer][attr] = pct

    form += '<table border="1" width="100%"><tr align="center">\n'
    legend = '<table border="1">\n'
    consumers = pctPerConsumer.keys()
    consumers.sort()
    for consumer in consumers:
      if pctPerConsumer[consumer].has_key('totalBytes'):
        color = colorsPerConsumer[consumer]
        pct = int(pctPerConsumer[consumer]['totalBytes'] + 0.5)
        form += '<td width="%d%%" bgcolor="%02X%02X%02X">%d%%</td>\n' % \
                (pct, color[0], color[1], color[2], pct)
        legend += '<tr><td bgcolor="%02X%02X%02X">&nbsp;</td><td>%s</td></tr>\n' % \
                  (color[0], color[1], color[2], consumer)
    form += '</tr></table><br/>\n'
    legend += '</table><br/>\n'
    form += legend

  sock.close()

form += '<input type="submit"/>'

print head
print form
print tail
