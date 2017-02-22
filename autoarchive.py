import os

from args_parser import args_parser
from application import Application

"""
:type application.Application
"""
app = None

if __name__ == '__main__':
    app = Application(os.path.dirname(__file__), args_parser.parse_args())
    app.exec()
