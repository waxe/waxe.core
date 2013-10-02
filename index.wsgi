activate_this = '/home/waxe/environment/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
from pyramid.paster import get_app, setup_logging

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
os.environ['LANG'] = 'en_US.UTF8'
os.environ['PYTHONIOENCODING'] = 'UTF-8'

here = os.path.dirname(os.path.abspath(__file__))
conf = os.path.join(here, 'development.ini')
print conf
setup_logging(conf)
application = get_app(conf, 'main')
