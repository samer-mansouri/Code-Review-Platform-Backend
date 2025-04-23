swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "User Management API",
        "description": "API for user registration, login, JWT auth, etc.",
        "version": "1.0.0"
    },
    "basePath": "/api",
    "schemes": ["http"]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'swagger',
            "route": '/apidocs/swagger.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"
}