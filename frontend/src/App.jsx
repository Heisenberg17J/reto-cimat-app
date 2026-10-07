import { useEffect, useState } from "react";
import Inicio from "./componentes/Inicio.jsx";
import Carga from "./componentes/Carga.jsx";
import Progreso from "./componentes/Progreso.jsx";
import Resultados from "./componentes/Resultados.jsx";
import Guia from "./componentes/Guia.jsx";
import { analizarEjemplo, borrarAnalisis, estadoPesos, listarEjemplos } from "./api.js";

export default function App() {
  const [fase, setFase] = useState("inicio"); // inicio | carga | progreso | resultados
  const [analisisId, setAnalisisId] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [pesos, setPesos] = useState(null);
  const [ejemplos, setEjemplos] = useState([]);
  const [mostrarGuia, setMostrarGuia] = useState(false);

  useEffect(() => {
    estadoPesos().then(setPesos).catch(() => {});
    listarEjemplos().then(setEjemplos).catch(() => {});
  }, []);

  async function usarEjemplo(idEjemplo) {
    setError(null);
    try {
      const { id } = await analizarEjemplo(idEjemplo);
      setAnalisisId(id);
      setFase("progreso");
    } catch (e) {
      setError(e.message);
    }
  }

  function reiniciar() {
    if (analisisId) borrarAnalisis(analisisId).catch(() => {});
    setAnalisisId(null);
    setResultado(null);
    setError(null);
    setFase("inicio");
  }

  return (
    <div className="app">
      <button className="boton-guia" onClick={() => setMostrarGuia(true)} aria-label="Abrir la guía">
        <span aria-hidden="true">?</span> Guía
      </button>
      {mostrarGuia && <Guia onCerrar={() => setMostrarGuia(false)} />}

      <main>
        {fase === "inicio" && (
          <Inicio
            onEmpezar={() => setFase("carga")}
            pesos={pesos}
            setPesos={setPesos}
            ejemplos={ejemplos}
            onEjemplo={usarEjemplo}
          />
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
        Prototipo de investigación · no es una herramienta clínica · reto-cimat-app · BraTS 2018
      </footer>
    </div>
  );
}
