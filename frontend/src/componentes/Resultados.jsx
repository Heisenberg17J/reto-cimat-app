import VisorNiiVue from "./VisorNiiVue.jsx";
import { urlArchivo } from "../api.js";

const REF_CON_EDAD = "segun_edad (referencia)";
const REF_SIN_EDAD = "solo_referencia_segun_edad (NO es una prediccion)";

// desempeno_esperado es {edad:{cindex,...}, coxnet:{cindex,...}} (c-index en validación cruzada).
function desempenoTexto(d) {
  if (!d) return "";
  if (typeof d === "string") return d;
  const modelo = d.coxnet?.cindex;
  const edad = d.edad?.cindex;
  if (modelo && edad) return `c-index ${modelo} (modelo) ≈ ${edad} (edad sola)`;
  return JSON.stringify(d);
}

function TablaReferencia({ referencia, titulo }) {
  const edades = Object.keys(referencia);
  if (!edades.length) return null;
  return (
    <div className="referencia">
      <p className="pista">{titulo}</p>
      <table>
        <thead>
          <tr>
            <th>Edad</th>
            {edades.map((e) => (
              <th key={e}>{e}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>Supervivencia</th>
            {edades.map((e) => (
              <td key={e}>
                {referencia[e].clase.split(" ")[0]}
                <br />
                <span className="pista">~{Math.round(referencia[e].dias_mediana_estimada)} d</span>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function Pronostico({ p }) {
  if (p.aplica) {
    return (
      <>
        <p className="destacado">
          Supervivencia estimada: <strong>{p.clase}</strong> (~{Math.round(p.dias_mediana_estimada)} días).
        </p>
        <p className="pista">
          Desempeño esperado: {desempenoTexto(p.desempeno_esperado)}. El modelo depende casi solo de la edad.
        </p>
        <TablaReferencia referencia={p[REF_CON_EDAD] || {}} titulo="Cómo cambiaría según la edad:" />
      </>
    );
  }
  return (
    <>
      <p className="destacado">No aplica.</p>
      <p>{p.motivo}</p>
      {p[REF_SIN_EDAD] && (
        <TablaReferencia
          referencia={p[REF_SIN_EDAD]}
          titulo="Solo como referencia (NO es una predicción), según la edad:"
        />
      )}
      {p.desempeno_esperado && (
        <p className="pista">Desempeño esperado: {desempenoTexto(p.desempeno_esperado)}.</p>
      )}
    </>
  );
}

export default function Resultados({ id, resultado, onNuevo }) {
  const v = resultado.volumen_cm3;
  const avisos = resultado.avisos_formato || [];

  return (
    <section className="resultados">
      <div className="acciones no-imprimir">
        <button className="secundario" onClick={onNuevo}>
          Nuevo análisis
        </button>
        <button className="secundario" onClick={() => window.print()}>
          Guardar informe (PDF)
        </button>
      </div>

      <div className="tarjeta tarjeta-visor no-imprimir">
        <h2>Visor 3D</h2>
        <VisorNiiVue id={id} />
      </div>

      <div className="tarjeta">
        <h2>Volúmenes</h2>
        <div className="volumenes">
          <div>
            <span className="vol">{v.WT.toFixed(2)}</span>
            <span>tumor completo (WT) cm³</span>
          </div>
          <div>
            <span className="vol">{v.TC.toFixed(2)}</span>
            <span>núcleo (TC) cm³</span>
          </div>
          <div>
            <span className="vol">{v.ET.toFixed(2)}</span>
            <span>realce (ET) cm³</span>
          </div>
        </div>
        <p className="pista">Segmentación: {resultado.segmentacion}.</p>
      </div>

      <div className="tarjeta">
        <h2>Pronóstico</h2>
        <Pronostico p={resultado.pronostico} />
      </div>

      {avisos.length > 0 && (
        <div className="tarjeta avisos-formato">
          <h3>Avisos de formato</h3>
          <ul>
            {avisos.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="tarjeta">
        <h2>Vista de control (FLAIR + segmentación)</h2>
        <img className="vista-control" src={urlArchivo(id, "vista.png")} alt="vista de control" />
      </div>

      <div className="tarjeta no-imprimir">
        <h3>Descargas</h3>
        <p>
          <a href={urlArchivo(id, "segmentacion.nii.gz")}>segmentacion.nii.gz</a> ·{" "}
          <a href={urlArchivo(id, "caracteristicas.csv")}>caracteristicas.csv</a> ·{" "}
          <a href={urlArchivo(id, "resultado.json")}>resultado.json</a>
        </p>
      </div>
    </section>
  );
}
