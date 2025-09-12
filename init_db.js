const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('motel.db');

db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS habitaciones (
    id INTEGER PRIMARY KEY,
    estado TEXT,
    inicio DATETIME,
    fin DATETIME,
    total INTEGER
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    stock INTEGER,
    precio INTEGER
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY,
    tipo TEXT,
    monto INTEGER,
    descripcion TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // Inicializar 22 habitaciones
  for (let i = 1; i <= 22; i++) {
    db.run(`INSERT OR IGNORE INTO habitaciones (id, estado) VALUES (?, 'libre')`, [i]);
  }
});

db.close();
