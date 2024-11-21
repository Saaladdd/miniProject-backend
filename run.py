from app import db,app
from sqlalchemy import text


if __name__ == "__main__":
    with app.app_context():
        
        with db.engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys = ON"))
        db.create_all()
    app.run(debug=True)
