
import os
import sys


# Change working directory so relative paths (and template lookup) work again
sys.path.append('/home/go')
os.chdir(os.path.dirname(__file__))

# ... build or import your bottle application here ...
import bottle
import go

application = bottle.default_app()
