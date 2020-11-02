import gettext
import os

__current_dir = os.path.abspath(os.path.dirname(__file__))
gettext.bindtextdomain('myapplication', os.path.join(__current_dir, "locale"))
gettext.textdomain('myapplication')
_ = gettext.gettext
