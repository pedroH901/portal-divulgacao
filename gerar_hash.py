from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
senha_plana = 'senha123'
hash_gerado = bcrypt.generate_password_hash(senha_plana).decode('utf-8')
print("\n--- SEU NOVO HASH SEGURO ---")
print(hash_gerado)
print("----------------------------\n")