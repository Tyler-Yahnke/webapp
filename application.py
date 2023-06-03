from website import create_app

application = create_app()

#adding comment
if __name__ == '__main__':
    application.run(debug=False)
