import { useState } from "react";
import { descargarPesos, estadoPesos } from "../api.js";

// Aviso + descarga de los pesos de nnU-Net cuando faltan. Si no hay descarga disponible,
// explica cómo copiarlos a mano.
export default function AvisoPesos({ pesos, setPesos }) {
  const [bajando, setBajando] = useState(false);
  if (!pesos || pesos.instalados) return null;

  const d = pesos.descarga || {};

  async function iniciar() {
    setBajando(true);
    await descargarPesos();
    const sondear = async () => {
      const info = await estadoPesos();
      setPesos(info);
      const est = info.descarga?.estado;
      if (est === "terminado" || est === "error") {
        setBajando(false);
        return;
      }
      setTimeout(sondear, 1500);
    };
    sondear();
  }

  return (
    <div className="tarjeta avisos-formato">
      <h3>Faltan nuestros modelos de segmentación</h3>
      <p>
        Son los que entrenó el Team Camacho (con nnU-Net, sobre BraTS 2018). Sin ellos la app no puede segmentar
        sola; tendrás que subir una segmentación ya hecha en cada análisis (opción avanzada de la pantalla de carga).
      </p>

      {pesos.descarga_disponible ? (
        <>
          {!bajando && d.estado !== "error" && (
            <button className="principal" onClick={iniciar}>
              Descargar modelos (~{pesos.tamano_mb} MB)
            </button>
          )}
          {bajando && (
            <>
              <p className="pista">{d.mensaje || "descargando…"}</p>
              <progress max="1" value={d.fraccion || 0} />
            </>
          )}
          {d.estado === "error" && (
            <p className="error">
              No se pudo: {d.error}{" "}
              <button className="secundario" onClick={iniciar}>
                Reintentar
              </button>
            </p>
          )}
        </>
      ) : (
        <p className="pista">
          Todavía no hay descarga automática. Copia los pesos a mano (ver <code>docs/INICIO_SESION.md</code>) en{" "}
          <code>{pesos.carpeta}</code>, o define la variable <code>NUCLEO_PESOS_URL</code>.
        </p>
      )}
    </div>
  );
}
