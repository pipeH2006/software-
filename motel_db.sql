use motel_db;
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT 0
);

CREATE TABLE habitaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero INT UNIQUE NOT NULL,
    estado VARCHAR(50) NOT NULL, -- disponible, ocupada, limpieza
    horas_reservadas INT DEFAULT 0
);

CREATE TABLE inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(100) UNIQUE NOT NULL,
    cantidad INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL
);

CREATE TABLE cargocargoshabitacion_ids (
    id INT AUTO_INCREMENT PRIMARY KEY,
    habitacion_id INT NOT NULL,
    producto_id INT NOT NULL,
    fecha DATETIME NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    cantidad INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    documento VARCHAR(255),
    anulado BOOLEAN DEFAULT 0,
    FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id),
    FOREIGN KEY (producto_id) REFERENCES inventario(id)
);

CREATE TABLE pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    habitacion_id INT NOT NULL,
    fecha DATETIME NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    tipo_pago VARCHAR(50) NOT NULL,
    documento VARCHAR(255),
    FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id)
);

CREATE TABLE movimientos_caja (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- ingreso, egreso
    valor DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(255)
);
