from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth"
login_manager.login_message = "Авторизуйтесь, чтобы получить доступ к странице"


