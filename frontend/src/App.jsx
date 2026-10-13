import { useEffect, useState } from "react";
import Inicio from "./componentes/Inicio.jsx";
import Carga from "./componentes/Carga.jsx";
import Progreso from "./componentes/Progreso.jsx";
import Resultados from "./componentes/Resultados.jsx";
import Guia from "./componentes/Guia.jsx";
import AcercaDe from "./componentes/AcercaDe.jsx";
import { analizarEjemplo, borrarAnalisis, estadoPesos, listarEjemplos } from "./api.js";

export default function App() {
  const [fase, setFase] = useState("inicio"); // inicio | carga | progreso | resultados
  const [analisisId, setAnalisisId] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [pesos, setPesos] = useState(null);
  const [ejemplos, setEjemplos] = useState([]);
  const [mostrarGuia, setMostrarGuia] = useState(false);
  const [mostrarAcerca, setMostrarAcerca] = useState(false);

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
    <>
      <header className="barra-superior">
        <div className="barra-interior">
          <div className="marca">
            <img
              className="marca-logo"
              src="logo-uniajc.png"
              alt=""
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
            <span className="marca-uni">UNIAJC</span>
            <span className="marca-separador" aria-hidden="true" />
            <span className="marca-proyecto">reto-CIMAT</span>
          </div>
          <button className="boton-guia" onClick={() => setMostrarGuia(true)} aria-label="Abrir la guía">
            <span aria-hidden="true">?</span> Guía
          </button>
        </div>
      </header>
      {mostrarGuia && <Guia onCerrar={() => setMostrarGuia(false)} />}

      <div className="app">
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
      </div>

      <footer className="pie">
        <div className="pie-interior">
          <div>
            <p className="pie-titulo">Universidad Antonio José Camacho</p>
            <p>
              <strong>Team Camacho</strong> — semilleros AppliScience y SEMOSIMA
            </p>
            <p className="pie-autores">
              Hejembert Jaramillo · Daniel León · Karen Arroyave · Dylan Cuervo · Nikol López
            </p>
          </div>
          <div className="pie-legal">
            <p>Prototipo de investigación · no es una herramienta clínica</p>
            <p>
              BraTS 2018 ·{" "}
              <button className="enlace-pie" onClick={() => setMostrarAcerca(true)}>
                Acerca de
              </button>
            </p>
          </div>
        </div>
      </footer>
      {mostrarAcerca && <AcercaDe onCerrar={() => setMostrarAcerca(false)} />}
    </>
  );
}
