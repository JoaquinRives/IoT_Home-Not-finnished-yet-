from app.application import create_app
# from flask_basicauth import BasicAuth

application = create_app()



# # Basic Authentication
# basic_auth = BasicAuth(flask_app)



if __name__ == '__main__':
    application.run(host='0.0.0.0', port=80, debug=True)