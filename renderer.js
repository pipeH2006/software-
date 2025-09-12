import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

function Habitacion({ hab, onStart, onAddHour }) {
  const [tiempoRestante, setTiempoRestante] = useState(null);

  useEffect(() => {
    if (hab.estado === 'ocupada' && hab.fin) {
      const interval = setInterval(() => {
        const diff = new Date(hab.fin) - new Date();
        setTiempoRestante(diff > 0 ? Math.floor(diff / 1000) : 0);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [hab]);

  return (
    <div style={{ border: '1px solid #ccc', margin: 4, padding: 8, width: 180 }}>
      <h4>Habitación {hab.id}</h4>
      <p>Estado: {hab.estado}</p>
      {hab.estado === 'ocupada' && (
        <p>Tiempo restante: {tiempoRestante !== null ? `${Math.floor(tiempoRestante/3600)}h ${Math.floor((tiempoRestante%3600)/60)}m` : ''}</p>
      )}
      {hab.estado === 'libre' && <button onClick={() => onStart(hab.id)}>Iniciar</button>}
      {hab.estado === 'ocupada' && <button onClick={() => onAddHour(hab.id)}>Añadir 1 hora ($9,000)</button>}
    </div>
  );
}

function App() {
  const [habitaciones, setHabitaciones] = useState([]);
  const [inventario, setInventario] = useState([]);
  const [arqueo, setArqueo] = useState([]);

  useEffect(() => {
    window.api.dbQuery('SELECT * FROM habitaciones').then(setHabitaciones);
    window.api.dbQuery('SELECT * FROM inventario').then(setInventario);
    window.api.dbQuery('SELECT * FROM movimientos ORDER BY fecha DESC LIMIT 10').then(setArqueo);
  }, []);

  const iniciarHabitacion = async (id) => {
    const inicio = new Date();
    const fin = new Date(inicio.getTime() + 6 * 60 * 60 * 1000);
    await window.api.dbRun('UPDATE habitaciones SET estado=?, inicio=?, fin=?, total=? WHERE id=?', [
      'ocupada', inicio.toISOString(), fin.toISOString(), 45000, id
    ]);
    await window.api.dbRun('INSERT INTO movimientos (tipo, monto, descripcion) VALUES (?, ?, ?)', [
      'ingreso', 45000, `Inicio habitación ${id}`
    ]);
    setHabitaciones(await window.api.dbQuery('SELECT * FROM habitaciones'));
    setArqueo(await window.api.dbQuery('SELECT * FROM movimientos ORDER BY fecha DESC LIMIT 10'));
  };

  const addHour = async (id) => {
    const hab = habitaciones.find(h => h.id === id);
    const nuevaFin = new Date(new Date(hab.fin).getTime() + 60 * 60 * 1000);
    const nuevoTotal = (hab.total || 0) + 9000;
    await window.api.dbRun('UPDATE habitaciones SET fin=?, total=? WHERE id=?', [
      nuevaFin.toISOString(), nuevoTotal, id
    ]);
    await window.api.dbRun('INSERT INTO movimientos (tipo, monto, descripcion) VALUES (?, ?, ?)', [
      'ingreso', 9000, `Hora extra habitación ${id}`
    ]);
    setHabitaciones(await window.api.dbQuery('SELECT * FROM habitaciones'));
    setArqueo(await window.api.dbQuery('SELECT * FROM movimientos ORDER BY fecha DESC LIMIT 10'));
  };

  return (
    <div>
      <h2>Habitaciones</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>
        {habitaciones.map(hab => (
          <Habitacion key={hab.id} hab={hab} onStart={iniciarHabitacion} onAddHour={addHour} />
        ))}
      </div>
      <h2>Inventario</h2>
      <table>
        <thead>
          <tr><th>Producto</th><th>Stock</th><th>Precio</th></tr>
        </thead>
        <tbody>
          {inventario.map(item => (
            <tr key={item.id}><td>{item.nombre}</td><td>{item.stock}</td><td>{item.precio}</td></tr>
          ))}
        </tbody>
      </table>
      <h2>Arqueo de Caja</h2>
      <table>
        <thead>
          <tr><th>Fecha</th><th>Tipo</th><th>Monto</th><th>Descripción</th></tr>
        </thead>
        <tbody>
          {arqueo.map(mov => (
            <tr key={mov.id}><td>{mov.fecha}</td><td>{mov.tipo}</td><td>{mov.monto}</td><td>{mov.descripcion}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);
