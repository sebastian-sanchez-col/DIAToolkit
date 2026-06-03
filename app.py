from flask import Flask, jsonify
from api.routes import api_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def health_check():
        return jsonify({
            "status": "success",
            "message": "Flask API is running"
        })

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
