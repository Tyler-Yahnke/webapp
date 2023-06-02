from website import create_app
from flask import redirect, request

application = create_app()


if __name__ == '__main__':
    application.run(debug=True)
