import { useEffect, useState } from "react";
import Inicio from "./componentes/Inicio.jsx";
import Carga from "./componentes/Carga.jsx";
import Progreso from "./componentes/Progreso.jsx";
import Resultados from "./componentes/Resultados.jsx";
import { borrarAnalisis, estadoPesos } from "./api.js";

const AVISO =
  "Prototipo de investigación. No es una herramienta clínica ni sustituye el criterio médico. " +
  "El pronóstico depende casi solo de la edad.";

export default function App() {
  const [fase, setFase] = useState("inicio"); // inicio | carga | progreso | resultados
  const [analisisId, setAnalisisId] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [pesos, setPesos] = useState(null);

  useEffect(() => {
    estadoPesos().then(setPesos).catch(() => {});
  }, []);

  function reiniciar() {
    if (analisisId) borrarAnalisis(analisisId).catch(() => {});
    setAnalisisId(null);
    setResultado(null);
    setError(null);
    setFase("inicio");
  }

  return (
    <div className="app">
      <header className="aviso" role="alert">
        <strong>Prototipo de investigación.</strong> {AVISO.replace("Prototipo de investigación. ", "")}
      </header>

      <main>
        {fase === "inicio" && (
          <Inicio onEmpezar={() => setFase("carga")} pesos={pesos} setPesos={setPesos} />
        )}

        {fase === "carga" && (
          <Carga
            pesos={pesos}
            onIniciado={(id) => {
              setAnalisisId(id);
              setError(null);
              setFase("progreso");
            }}
            onCancelar={reiniciar}
          />
        )}

        {fase === "progreso" && (
          <Progreso
            id={analisisId}
            onTerminado={(res) => {
              setResultado(res);
              setFase("resultados");
            }}
            onError={(msg) => {
              setError(msg);
              setFase("carga");
            }}
          />
        )}

        {fase === "resultados" && (
          <Resultados id={analisisId} resultado={resultado} onNuevo={reiniciar} />
        )}

        {error && fase === "carga" && (
          <p className="error">No se pudo completar: {error}</p>
        )}
      </main>

      <footer className="pie">
        reto-cimat-app · BraTS 2018 · c-index 0.62 (≈ la edad sola). Las imágenes no salen de este equipo.
      </footer>
    </div>
  );
}
