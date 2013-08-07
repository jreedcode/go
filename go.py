"""http://go

A simple tinyurl.
"""

import sys
import syslog
import smtplib
from bottle import route
from bottle import post
from bottle import get
from bottle import static_file
from bottle import redirect
from bottle import template
from bottle import request
from bottle_sqlite import SQLitePlugin

install(SQLitePlugin(dbfile=DB))
# globals
DB = '/home/go/db/go.db'
RESERVED_NAMES = ['faq', 'support', 'credits', 'links', 'created', 'feedback']
ADMIN_MAILBOXES = []
SMTP_SERVER = ''
DOMAIN_EMAIL = ''
# these may come in useful
#from bottle import debug
#debug(True)


@route('/static/<filename>')
def StaticStuff(filename):
  """Serve static content files."""
  return static_file(filename, root='static')


def LogUserVisit(db, page):
  """Log the user's visit to sqlite.

  Args:
    db: A connection instance of sqlite3.
    page: A string of the page being visited.
  """
  client_ip = request.environ.get('REMOTE_ADDR')
  db.execute('select ipAddress from stats where ipAddress = ?', (client_ip,))
  result = db.fetchone()
  if result is None:
    # new visitor
    if page == 'home':
      db.execute('insert into stats (ipAddress, homeHits, goHits) '
                'values(?, 1, 0)', (client_ip,))
    else:
      db.execute('insert into stats (ipAddress, homeHits, goHits) '
                 'values(?, 0, 1)', (client_ip,))
  else:
    #returning visitor
    if page == 'home':
      db.execute('update stats set homeHits=homeHits + 1 where ipAddress = ?',
                 (client_ip,))
    else:
      db.execute('update stats set goHits=goHits + 1 where ipAddress = ?',
                 (client_ip,))
  return


@get('/')
def GoHome():
  """Serve the GO home page."""
  LogUserVisit('home')
  return static_file('index.html', root='static')


@post('/created')
def ShowCreate(db):
  """Show the result of a user submission.

  Args:
    db: A connection instance of sqlite3.
  """
  go_name = request.forms.get('go_name')
  dest = request.forms.get('destination')
  user_name = request.forms.get('user_name')
  comment = request.forms.get('comment')
 
  # clean up the go name
  go_name = go_name.strip()
  go_name = go_name.split('/')[-1]
  go_name = ''.join(go_name.split())
  # we cannot lowercase urls for things like wiki pages that are case sensitive
  # go_name = go_name.lower()
  # clean up the landing page
  dest = dest.strip()
  dest = ''.join(dest.split())
  dest = dest.lower()

  dest_url_matcher = ['http://', 'https://', 'ftp://']
  match = False
  for matcher in dest_url_matcher:
    if dest.startswith(matcher):
      match = True
  if match is False:
    return static_file('invalid_dest.html', root='static')
 
  # check if its already being used
  db.execute('select * from redirects where source = ?', (go_name,))
  result = db.fetchone()

  if result is None:
    db.execute('insert into redirects (source, destination, user, comment, '
               'goHits) values(?, ?, ?, ?, ?)', (go_name, dest, user_name,
                                                 comment, 0))
    short_dest = '%s ...' % dest[:45]
    output = template('created', go_name=go_name, dest=short_dest)
  elif str(result[0]) in RESERVED_NAMES:
    output = template('create_failed', go_name=go_name)
  else:
    output = template('create_failed', go_name=go_name)
  return output


@get('/support')
def ShowSupport():
  """Show the support page."""
  return static_file('support.html', root='static')


@post('/feedback')
def ShowFeedback():
  comments = request.forms.get('comments')
  message = []
  message.append(comments)
  SendEmail(ADMIN_MAILBOXES, 'infrastructure-team', 'http-go', 'http://go',
            message, 'Support Request')
  output = static_file('feedback.html', root='static')
  return output


@route('/faq')
def ShowFaq():
  """Show the FAQ page."""
  return static_file('faq.html', root='static')


@route('/credits')
def ShowCredits():
  """Show the credits page."""
  return static_file('credits.html', root='static')


@route('/links')
def ShowDb(db):
  """Display the GO database.

  Args:
    db: A connection instance of sqlite3.
  """
  db.execute('select * from redirects')
  result = db.fetchall()
  output = template('links', rows=result)
  return output


@route('/<go_name>')
def GoRedirect(db, go_name):
  """Redirect the user.

  Args:
    db: A connection instance of sqlite3.
  """
  if go_name != 'favicon.ico':
    LogUserVisit('go_link')

  go_name = go_name.lower()
  db.execute('select destination from redirects where source = ?', (go_name,))
  result = db.fetchone()
  if result is None:
    output = template('oops')
    return output + """<meta http-equiv="REFRESH" content="3;url=http://go">'"""
  else:
    go_destination = str(result[0])
    db.execute('update redirects set goHits=goHits + 1 where source = ?',
               (go_name,))
    redirect(go_destination)


def WriteToSyslog(message):
  """Write a message to syslog.

  Args:
    message: A string of text to send to syslog.
  """
  syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
  syslog.syslog(syslog.LOG_ERR, '%s' % message)
  syslog.closelog()
  return


def SendEmail(to, pseudo_to, from_name, subject, message, boolean_status=''):
  """Email a status.

  Args:
    to: A list of email addresses to send this message to.
    pseudo_to: A masked string of the name in the To field.
    from_name: A string of the username to represent.
    subject: A string of the email subject.
    message: A list of messages collected to form the body.
    boolean_status: A string indicating 'success' or 'failure'. 
  """
  subject = '%s: %s' % (subject, boolean_status)
  from_addr = '%s@%s' % (from_name, DOMAIN_EMAIL)
  header = ('From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n' % (from_addr,
                                                           pseudo_to,
                                                           subject))
  full_body = '\n'.join(message)
  header_and_body = header + '\n\n' + full_body
  try:
    mail_server = smtplib.SMTP(SMTP_SERVER)
    mail_server.sendmail(from_addr, to, header_and_body)
    mail_server.quit()
  except Exception, err:
    WriteToSyslog('failed to send email: %s' % str(err))
  else:
    WriteToSyslog('Email sent')
