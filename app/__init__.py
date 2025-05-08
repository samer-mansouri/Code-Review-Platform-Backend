from flask import Flask, jsonify
from app.extensions import db, jwt, ma
from config import Config
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from app.utils.errors import register_error_handlers
from flasgger import Swagger
from app.docs.swagger_config import swagger_template, swagger_config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    CORS(app)
    Swagger(app, template=swagger_template, config=swagger_config)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from app.routes.gitlab_token_routes import gitlab_token_bp
    app.register_blueprint(gitlab_token_bp, url_prefix="/api/gitlab-token")

    from app.routes.gitlab_project_routes import gitlab_project_bp
    app.register_blueprint(gitlab_project_bp, url_prefix='/api/gitlab-project')

    from app.routes.gitlab_merge_request_routes import mr_bp
    app.register_blueprint(mr_bp, url_prefix="/api/gitlab-merge-requests")

    from app.routes.github_token_routes import github_token_bp
    app.register_blueprint(github_token_bp, url_prefix="/api/github-token")

    from app.routes.github_project_routes import github_repo_bp
    app.register_blueprint(github_repo_bp, url_prefix="/api/github-repo")


    swaggerui_blueprint = get_swaggerui_blueprint(
        '/api/docs', '/apidocs/swagger.json', config={'app_name': "User Auth API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix='/api/docs')

    register_error_handlers(app)

    return app