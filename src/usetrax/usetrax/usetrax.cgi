#!/bin/env python

import cgi
import cgitb
cgitb.enable()
import commands
import random
import socket
import sys

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
tail = """
  </form>
</body>
</html>
"""

if params.has_key('server'):

  server = params.getfirst('server')
  if server.find(':') < 0:
    server += ':7734'
  form = form.replace('name="server"', 'name="server" value="%s"' % server)

  # Open a connection to the usetrax daemon
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  (addr, port) = server.split(':', 1)
  try:
    sock.connect((addr, int(port)))
  except Exception, x:
    print head
    print "Connection to %s failed" % server
    print tail
    sys.exit(0)
  send(sock, 'GETRES')
  reply = recv(sock)
  sock.close()

  if reply.startswith('OK '):
    for resource in reply[3:].split(','):
      option = '<option>%s</option>' % resource
      form = form.replace('name="resource">', 'name="resource">\n%s' % option)

  if params.has_key('resource'):

    resource = params.getfirst('resource')
    form = form.replace(
      'option>%s' % resource, 'option selected="1">%s' % resource
    )

    end = '-0'
    start = '0'
    step = 0
    sumby = 'Host'

    if params.has_key('end'):
      end = params.getfirst('end')
    if params.has_key('start'):
      start = params.getfirst('start')
    if params.has_key('step'):
      step = params.getfirst('step')
    if params.has_key('sumby'):
      sumby = params.getfirst('sumby')

    form = form.replace('name="start"/>', 'name="start" value="%s"/>' % start)
    form = form.replace('name="end"/>', 'name="end" value="%s"/>' % end)
    form = form.replace('name="step"/>', 'name="step" value="%s"/>' % step)
    form = form.replace('option>%s' % sumby, 'option selected="1">%s' % sumby)

    command = \
      './usetrax --server=%s --resource=%s --start=%s --end=%s --sum=%s --step=%s' % \
      (server, resource, start, end, sumby, step)
    form += '%s<br/>' % command
    output = commands.getoutput(command)

    colorsPerConsumer = { }
    colorsPerConsumer['Others'] = (
      random.randrange(64, 256),
      random.randrange(64, 256),
      random.randrange(64, 256)
    )
    totalPerStepPerAttr = { }
    usagePerStepPerAttrPerConsumer = { }

    for line in output.split("\n"):

      pieces = line.split()
      if len(pieces) < 2:
        continue
      step = pieces[0]
      consumer = pieces[1]

      if not totalPerStepPerAttr.has_key(step):
        totalPerStepPerAttr[step] = { }
      if not usagePerStepPerAttrPerConsumer.has_key(step):
        usagePerStepPerAttrPerConsumer[step] = { }
      if not colorsPerConsumer.has_key(consumer):
        colorsPerConsumer[consumer] = (
          random.randrange(64, 256),
          random.randrange(64, 256),
          random.randrange(64, 256)
        )

      for i in range(3, len(pieces), 2):
        attr = pieces[i - 1]
        usage = int(pieces[i])
        if not totalPerStepPerAttr[step].has_key(attr):
          totalPerStepPerAttr[step][attr] = 0
          usagePerStepPerAttrPerConsumer[step][attr] = { }
        totalPerStepPerAttr[step][attr] += usage
        usagePerStepPerAttrPerConsumer[step][attr][consumer] = usage

    maxTotalPerAttr = { }

    steps = totalPerStepPerAttr.keys()
    steps.sort(key=lambda s: s.rjust(10))

    for step in steps:
      for attr in totalPerStepPerAttr[step]:
        if not maxTotalPerAttr.has_key(attr) or \
               totalPerStepPerAttr[step][attr] > maxTotalPerAttr[attr]:
          maxTotalPerAttr[attr] = totalPerStepPerAttr[step][attr]

    attrs = maxTotalPerAttr.keys()
    attrs.sort()
    for attr in attrs:

      form += '<h2>%s</h2>' % attr
      legendPerConsumer = { }

      for step in steps:

        pctPerConsumer = {'Others':0}
   
        for consumer in usagePerStepPerAttrPerConsumer[step][attr]:
          pct = 100.0 * usagePerStepPerAttrPerConsumer[step][attr][consumer] / \
                maxTotalPerAttr[attr]
          if pct < 2:
            pctPerConsumer['Others'] += pct
            legendPerConsumer['Others'] = colorsPerConsumer['Others']
          else:
            pctPerConsumer[consumer] = pct
            legendPerConsumer[consumer] = colorsPerConsumer[consumer]

        form += '<table border="1" width="100%"><tr align="center">\n'
        form += '<th width="5%%">%s</th>' % step

        consumers = pctPerConsumer.keys()
        consumers.sort()
        for consumer in consumers:
          pct = int(pctPerConsumer[consumer] + 0.5)
          width = int(pct * 0.9 + 0.5)
          color = colorsPerConsumer[consumer]
          if pct >= 2:
            form += '<td width="%d%%" bgcolor="%02X%02X%02X">%d%%</td>\n' % \
                    (width, color[0], color[1], color[2], pct)
          else:
            form += '<td width="1%%" bgcolor="%02X%02X%02X">&nbsp;</td>\n' % \
                    (color[0], color[1], color[2])
        form += '<td align="left">%s</td>' % totalPerStepPerAttr[step][attr]
        form += '</tr></table>\n'

      legend = '<br/><table border="1">\n'
      consumers = legendPerConsumer.keys()
      consumers.sort()
      for consumer in consumers:
        color = legendPerConsumer[consumer]
        legend += \
          '<tr><td bgcolor="%02X%02X%02X">&nbsp;</td><td>%s</td></tr>\n' % \
          (color[0], color[1], color[2], consumer)
      legend += '</table><br/>\n'
      form += legend

print head
print form
print tail
