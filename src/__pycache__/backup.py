import os
import datetime
import subprocess

# Configuración de conexión
user = "root"
password = "root" 
database = "motel_db"

# Nombre del archivo con fecha
fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = f"backup_{database}_{fecha}.sql"

# Comando mysqldump
comando = f'mysqldump -u {user} -p{password} {database} > "{backup_file}"'

# Ejecutar el comando
try:
    os.system(comando)
    print(f" Backup creado exitosamente: {backup_file}")
except Exception as e:
    print(f" Error al crear el backup: {e}")