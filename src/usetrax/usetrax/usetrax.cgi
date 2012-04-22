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
<table>
<tr align="left"><th>Server</th><td><input type="text" name="server"/></td></tr>
<tr align="left"><th>Resource</th><td><select name="resource">
</select></td></tr>
<tr align="left"><th>Start Time</th><td><input type="text" name="start"/></td></tr>
<tr align="left"><th>End Time</th><td><input type="text" name="end"/></td></tr>
<tr align="left"><th>Step</th><td><input type="text" name="step"/></td></tr>
<tr align="left"><th>Sum By</th><td><select name="sumby">
<option>Host</option>
<option>Job</option>
<option>User</option>
</select></td></tr>
<tr align="left"><th></th><td><input type="submit" value="Refresh"/></td></tr>
</table><br/><br/>
'''
debug = ''

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
  sock.close()

  if reply.startswith('OK '):
    for resource in reply[3:].split(','):
      option = '<option>%s</option>' % resource
      form = form.replace('name="resource">', 'name="resource">\n%s' % option)

  if params.has_key('resource'):

    end = '-0'
    resource = params.getfirst('resource')
    start = '0'
    step = None
    sumby = 'Host'

    if params.has_key('end'):
      end = params.getfirst('end')
    if params.has_key('start'):
      start = params.getfirst('start')
    if params.has_key('step'):
      step = int(params.getfirst('step'))
    if params.has_key('sumby'):
      sumby = params.getfirst('sumby')

    form = form.replace(
      'option>%s' % resource, 'option selected="1">%s' % resource
    )
    form = form.replace('name="start"/>', 'name="start" value="%s"/>' % start)
    form = form.replace('name="end"/>', 'name="end" value="%s"/>' % end)
    form = form.replace('name="step"/>', 'name="step" value="%s"/>' % step)
    form = form.replace('option>%s' % sumby, 'option selected="1">%s' % sumby)

    command = \
      './usetrax --server=%s --resource=%s --start=%s --end=%s --sum=%s' % \
      (server, resource, start, end, sumby)
    if step:
      command += ' --step=%s' % step
    form += '%s<br/>' % command
    output = commands.getoutput(command)

    colorsPerConsumer = { }
    lastColor = colorsPerConsumer['Others'] = (
      random.randrange(0,256), random.randrange(0,256), random.randrange(0,256)
    )
    totalsPerStep = { }
    usagePerStepPerConsumer = { }

    for line in output.split("\n"):

      pieces = line.split()
      if len(pieces) < 2:
        continue
      step = int(pieces[0])
      consumer = pieces[1]

      if not totalsPerStep.has_key(step):
        totalsPerStep[step] = { }
      if not usagePerStepPerConsumer.has_key(step):
        usagePerStepPerConsumer[step] = { }
      if not usagePerStepPerConsumer[step].has_key(consumer):
        usagePerStepPerConsumer[step][consumer] = { }
      if not colorsPerConsumer.has_key(consumer):
        lastColor = colorsPerConsumer[consumer] = (
          random.randrange(0, 256),
          random.randrange(0, 256),
          random.randrange(0, 256)
        )

      usagePerAttr = { }
      for i in range(3, len(pieces), 2):
        attr = pieces[i - 1]
        usage = int(pieces[i])
        usagePerAttr[attr] = usage
        if not totalsPerStep[step].has_key(attr):
          totalsPerStep[step][attr] = 0
        totalsPerStep[step][attr] += usage
      usagePerStepPerConsumer[step][consumer] = usagePerAttr

    highestTotalsPerAttr = { }

    steps = usagePerStepPerConsumer.keys()
    steps.sort()
    for step in steps:
      for attr in totalsPerStep[step]:
        if not highestTotalsPerAttr.has_key(attr) or \
               totalsPerStep[step][attr] > highestTotalsPerAttr[attr]:
          highestTotalsPerAttr[attr] = totalsPerStep[step][attr]

    consumersInAnyStep = {}

    for step in steps:

      pctsPerConsumer = { }
      pctsPerConsumer['Others'] = { }
   
      for consumer in usagePerStepPerConsumer[step]:
        for attr in usagePerStepPerConsumer[step][consumer]:
          pct = 100.0 * usagePerStepPerConsumer[step][consumer][attr] / \
                highestTotalsPerAttr[attr]
          if pct < 2:
            if not pctsPerConsumer['Others'].has_key(attr):
              pctsPerConsumer['Others'][attr] = 0
            pctsPerConsumer['Others'][attr] += pct
            consumersInAnyStep['Others'] = 1
          else:
            if not pctsPerConsumer.has_key(consumer):
              pctsPerConsumer[consumer] = { }
            pctsPerConsumer[consumer][attr] = pct
            consumersInAnyStep[consumer] = 1

      form += '<table border="1" width="100%"><tr align="center">\n'
      form += '<th width="5%%">%s</th>' % step
      consumers = pctsPerConsumer.keys()
      consumers.sort()
      for consumer in consumers:
        if pctsPerConsumer[consumer].has_key('totalBytes'):
          pct = int(pctsPerConsumer[consumer]['totalBytes'] + 0.5)
          color = colorsPerConsumer[consumer]
          if pct >= 2:
            form += '<td width="%d%%" bgcolor="%02X%02X%02X">%d%%</td>\n' % \
                    (pct, color[0], color[1], color[2], pct)
          else:
            form += '<td width="1%%" bgcolor="%02X%02X%02X">&nbsp;</td>\n' % \
                    (color[0], color[1], color[2])
      form += '<td align="left">%s</td>' % totalsPerStep[step]['totalBytes']
      form += '</tr></table>\n'

    legend = '<br/><table border="1">\n'
    consumers = consumersInAnyStep.keys()
    consumers.sort()
    for consumer in consumers:
      color = colorsPerConsumer[consumer]
      legend += \
        '<tr><td bgcolor="%02X%02X%02X">&nbsp;</td><td>%s</td></tr>\n' % \
        (color[0], color[1], color[2], consumer)
    legend += '</table><br/>\n'
    form += legend

print head
print form
print debug
print tail
