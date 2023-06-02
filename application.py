from website import create_app
from flask import redirect, request

application = create_app()
@application.before_request
def redirect_to_https():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


if __name__ == '__main__':
    application.run(debug=True)
