from database import SessionLocal, engine
import models
from main import get_password_hash

def init_db():
    # Asegurar que las tablas existan
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if client user exists
    client_user = db.query(models.User).filter(models.User.username == "cliente").first()
    if not client_user:
        client_user = models.User(
            username="cliente",
            password_hash=get_password_hash("1234"),
            role=models.UserRole.CLIENT
        )
        db.add(client_user)
        print("Usuario 'cliente' creado con clave '1234'")

    # Check if admin user exists
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        admin_user = models.User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role=models.UserRole.ADMIN
        )
        db.add(admin_user)
        print("Usuario 'admin' creado con clave 'admin123'")

    db.commit()
    db.close()
    print("Inicialización de base de datos completada.")

if __name__ == "__main__":
    init_db()
