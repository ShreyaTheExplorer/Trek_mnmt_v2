import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from config import Config
from extensions import db
from models import User
from auth import api_response

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )
    app.config.from_object(config_class)

    # Ensure required export directories exist
    os.makedirs(app.config.get('EXPORTS_DIR', os.path.join(os.path.dirname(__file__), 'exports')), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints safely if available
    try:
        from routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        pass

    try:
        from routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)
    except ImportError:
        pass

    try:
        from routes.staff_routes import staff_bp
        app.register_blueprint(staff_bp)
    except ImportError:
        pass

    try:
        from routes.user_routes import user_bp
        app.register_blueprint(user_bp)
    except ImportError:
        pass

    # Programmatic database initialization & admin seeding
    with app.app_context():
        # Programmatic schema creation
        db.create_all()

        # Ensure column migrations for existing SQLite tables
        try:
            with db.engine.connect() as conn:
                cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(treks);").fetchall()]
                if 'is_started' not in cols:
                    conn.exec_driver_sql("ALTER TABLE treks ADD COLUMN is_started BOOLEAN DEFAULT 0;")
                    conn.commit()
        except Exception:
            pass

        # Seed exactly one admin if no admin exists
        existing_admin = User.query.filter_by(role='admin').first()
        if not existing_admin:
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@tma.com')
            admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
            admin_name = app.config.get('ADMIN_NAME', 'System Administrator')

            admin = User(
                name=admin_name,
                email=admin_email,
                role='admin',
                status='active'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"[TMA Seeder] Programmatically seeded initial admin: {admin_email}")

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return api_response(
            True,
            "TMA API is healthy.",
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            },
            200
        )

    # Single entry point: serves templates/index.html at "/"
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/'):
            return api_response(False, f"API endpoint '/{path}' not found.", None, 404)
        return render_template('index.html')

    # Global JSON error handlers for API
    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith('/api/'):
            return api_response(False, "API resource not found.", None, 404)
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        return api_response(False, "Internal server error.", None, 500)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
