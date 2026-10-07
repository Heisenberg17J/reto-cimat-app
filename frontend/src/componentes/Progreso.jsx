import { useEffect, useRef, useState } from "react";
import { estadoAnalisis } from "../api.js";

const ETAPAS = ["entrada", "segmentacion", "radiomica", "pronostico", "salida"];
const TEXTO = {
  entrada: "Leyendo las resonancias",
  segmentacion: "Segmentando el tumor (puede tardar minutos en CPU)",
  radiomica: "Calculando la radiómica",
  pronostico: "Estimando el pronóstico",
  salida: "Preparando los resultados",
};

export default function Progreso({ id, onTerminado, onError }) {
  const [etapa, setEtapa] = useState(null);
  const [fraccion, setFraccion] = useState(0);
  const [segundos, setSegundos] = useState(0);
  const vivo = useRef(true);

  useEffect(() => {
    vivo.current = true;
    const inicio = Date.now();
    const reloj = setInterval(() => setSegundos(Math.floor((Date.now() - inicio) / 1000)), 1000);

    async function sondear() {
      if (!vivo.current) return;
      try {
        const e = await estadoAnalisis(id);
        if (!vivo.current) return;
        setEtapa(e.etapa);
        setFraccion(e.fraccion || 0);
        if (e.estado === "terminado") return onTerminado(e.resultado);
        if (e.estado === "error") return onError(e.error);
        setTimeout(sondear, 1000);
      } catch (err) {
        if (vivo.current) onError(err.message);
      }
    }
    sondear();

    return () => {
      vivo.current = false;
      clearInterval(reloj);
    };
  }, [id]);

  const indice = ETAPAS.indexOf(etapa);
  const global = indice < 0 ? 0 : (indice + fraccion) / ETAPAS.length;
  const mm = String(Math.floor(segundos / 60)).padStart(2, "0");
  const ss = String(segundos % 60).padStart(2, "0");

  return (
    <section className="tarjeta progreso">
      <h2>Analizando…</h2>
      <p className="etapa-actual">{etapa ? TEXTO[etapa] : "En cola…"}</p>
      <progress max="1" value={global} />
      <p className="pista">
        Transcurrido: {mm}:{ss}. Puede dejar esta ventana abierta; el análisis sigue en este equipo.
      </p>
      <ol className="etapas">
        {ETAPAS.map((e, i) => (
          <li key={e} className={i < indice ? "hecha" : i === indice ? "activa" : ""}>
            {TEXTO[e]}
          </li>
        ))}
      </ol>
    </section>
  );
}
