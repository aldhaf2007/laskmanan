import os
import datetime
from flask import Flask, render_template
from config import Config
from db import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.permanent_session_lifetime = datetime.timedelta(days=7)
    
    # Initialize DB schema & seed if needed
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"Warning: DB init check encountered: {e}")

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.faculty import faculty_bp
    from routes.attendance import attendance_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)

    @app.context_processor
    def inject_globals():
        return {
            'now': datetime.datetime.now(),
            'current_year': datetime.datetime.now().year
        }

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
