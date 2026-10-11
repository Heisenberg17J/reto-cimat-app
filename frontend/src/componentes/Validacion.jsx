// Validación del modelo contra la segmentación del radiólogo (resultado.evaluacion del núcleo):
// métricas oficiales de BraTS, posición del caso entre los 285 pacientes del estudio y pronóstico con
// las dos máscaras.
import { urlArchivo } from "../api.js";

const REGIONES = [
  { id: "WT", nombre: "Tumor completo (WT)" },
  { id: "TC", nombre: "Núcleo (TC)" },
  { id: "ET", nombre: "Realce (ET)" },
];

const fmt = (x, d = 3) => (x == null ? "—" : Number(x).toFixed(d));

function difPorc(modelo, ref) {
  if (!ref) return "—";
  const d = (100 * (modelo - ref)) / ref;
  return `${d > 0 ? "+" : ""}${d.toFixed(1)} %`;
}

// Histograma del Dice de los 285 pacientes (fuera de fold) con el caso marcado.
function Histograma({ region, estudio, dice }) {
  const r = estudio.regiones[region];
  const bordes = estudio.bordes_dice;
  const conteo = r.histograma_dice;
  const max = Math.max(...conteo, 1);
  const W = 300, H = 120, izq = 6, der = 6, arriba = 22, abajo = 20;
  const ancho = (W - izq - der) / conteo.length;
  const x = (v) => izq + v * (W - izq - der);
  const y = (n) => arriba + (H - arriba - abajo) * (1 - n / max);
  const binCaso = Math.min(conteo.length - 1, Math.floor(dice * conteo.length));
  const xCaso = x(Math.min(Math.max(dice, 0), 1));
  const anclaCaso = dice > 0.75 ? "end" : dice < 0.25 ? "start" : "middle";

  return (
    <figure className="histograma">
      <figcaption>
        <strong>{region}</strong> · mejor o igual que el {Math.round(r.percentil_dice)} % del estudio
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
           aria-label={`Dice ${region}: este caso ${fmt(dice)}, mediana del estudio ${fmt(r.dice_mediana)}`}>
        <line x1={izq} x2={W - der} y1={H - abajo} y2={H - abajo} className="eje" />
        {conteo.map((n, i) => {
          const alto = H - abajo - y(n);
          return (
            <g key={i}>
              {n > 0 && (
                <rect x={x(bordes[i]) + 1} y={y(n)} width={ancho - 2} height={alto} rx={Math.min(2, alto / 2)}
                      className={i === binCaso ? "barra barra-caso" : "barra"} />
              )}
              <rect x={x(bordes[i])} y={arriba} width={ancho} height={H - arriba - abajo} className="zona-hover">
                <title>{`Dice ${bordes[i].toFixed(2)}–${bordes[i + 1].toFixed(2)}: ${n} pacientes`}</title>
              </rect>
            </g>
          );
        })}
        <line x1={x(r.dice_mediana)} x2={x(r.dice_mediana)} y1={arriba - 4} y2={H - abajo} className="mediana" />
        <line x1={xCaso} x2={xCaso} y1={arriba - 6} y2={H - abajo} className="marca-caso" />
        <text x={xCaso} y={arriba - 10} textAnchor={anclaCaso} className="texto-caso">
          este caso {fmt(dice)}
        </text>
        {[0, 0.5, 1].map((v) => (
          <text key={v} x={x(v)} y={H - 5} textAnchor={v === 0 ? "start" : v === 1 ? "end" : "middle"}
                className="texto-eje">
            {v}
          </text>
        ))}
      </svg>
    </figure>
  );
}

function PronosticoMascara({ titulo, p }) {
  return (
    <div>
      <span className="pista">{titulo}</span>
      {p.aplica ? (
        <>
          <span className="vol">{p.clase.split(" ")[0]}</span>
          <span>~{Math.round(p.dias_mediana_estimada)} días · riesgo {p.riesgo >= 0 ? "+" : ""}{fmt(p.riesgo)}</span>
        </>
      ) : (
        <>
          <span className="vol">no aplica</span>
          <span className="pista">{p.motivo.split(".")[0]}.</span>
        </>
      )}
    </div>
  );
}

export default function Validacion({ id, resultado }) {
  const ev = resultado.evaluacion;
  const v = resultado.volumen_cm3;
  const vr = ev.volumen_ref_cm3;
  const caso = ev.caso_del_estudio;
  const p = resultado.pronostico;
  const pr = ev.pronostico_ref;

  return (
    <>
      <div className="tarjeta validacion">
        <h2>Validación frente al radiólogo</h2>
        <p className="pista">
          Segmentación de nuestro modelo comparada con la del radiólogo, con las métricas oficiales de BraTS
          (Bakas et al. 2018), calculadas igual que en el estudio.
        </p>
        <div className="tabla-desplazable">
          <table className="tabla-metricas">
            <thead>
              <tr>
                <th>Región</th>
                <th title="Solapamiento: 1 = idénticas">Dice</th>
                <th title="Distancia de Hausdorff 95: error de borde en mm (menor es mejor)">HD95 (mm)</th>
                <th title="Fracción del tumor del radiólogo que el modelo encontró">Sensibilidad</th>
                <th>Especificidad</th>
                <th>Vol. modelo (cm³)</th>
                <th>Vol. radiólogo (cm³)</th>
                <th>Diferencia</th>
              </tr>
            </thead>
            <tbody>
              {REGIONES.map(({ id: r, nombre }) => {
                const m = ev.metricas[r];
                return (
                  <tr key={r}>
                    <th>{nombre}</th>
                    <td><strong>{fmt(m.dice)}</strong></td>
                    <td>{fmt(m.hd95_mm, 1)}</td>
                    <td>{fmt(m.sensibilidad)}</td>
                    <td>{fmt(m.especificidad, 4)}</td>
                    <td>{v[r].toFixed(2)}</td>
                    <td>{vr[r].toFixed(2)}</td>
                    <td>{difPorc(v[r], vr[r])}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="pista">
          Dice: 1 = las dos máscaras coinciden por completo, 0 = no se tocan. HD95: distancia (mm) dentro de la
          que queda el 95 % del borde. Si una región falta en una sola máscara, Dice 0 y HD95 373,13 mm
          (convención de BraTS).
        </p>

        <h3>En el estudio ({ev.estudio.n_pacientes} pacientes, fuera de fold)</h3>
        <p className="pista">
          Distribución del Dice de nuestro modelo en BraTS 2018, cada paciente segmentado por el modelo que no lo
          vio. Línea discontinua: mediana del estudio (WT {fmt(ev.estudio.regiones.WT.dice_mediana)} · TC{" "}
          {fmt(ev.estudio.regiones.TC.dice_mediana)} · ET {fmt(ev.estudio.regiones.ET.dice_mediana)}). Pase el
          cursor sobre una barra para ver cuántos pacientes tiene.
        </p>
        <div className="histogramas">
          {REGIONES.map(({ id: r }) => (
            <Histograma key={r} region={r} estudio={ev.estudio} dice={ev.metricas[r].dice} />
          ))}
        </div>
        {caso && (
          <p className="nota">
            <strong>{caso.paciente_id}</strong> es un paciente del estudio (fold {caso.fold}). Su segmentación viene
            del modelo que no lo vio en el entrenamiento, así que la comparación es honesta; el paciente también
            está dentro de la distribución de arriba.
          </p>
        )}

        <h3>Pronóstico con cada máscara</h3>
        <div className="volumenes">
          <PronosticoMascara titulo="Con la máscara del modelo" p={p} />
          <PronosticoMascara titulo="Con la máscara del radiólogo" p={pr} />
        </div>
        {p.aplica && pr.aplica && (
          <p className="pista">
            Diferencia de riesgo: {fmt(p.riesgo - pr.riesgo)}.{" "}
            {p.clase_id === pr.clase_id ? "La clase no cambia." : "La clase cambia."} En el estudio, el 82 % de
            las características radiómicas conservó el orden de los pacientes entre máscaras manuales y predichas
            (Spearman ≥ 0,85), y el modelo depende casi solo de la edad.
          </p>
        )}
      </div>

      <div className="tarjeta">
        <h2>Contornos: modelo frente a radiólogo</h2>
        <img className="vista-control" src={urlArchivo(id, "comparacion.png")} alt="contornos del modelo y del radiólogo" />
      </div>
    </>
  );
}
