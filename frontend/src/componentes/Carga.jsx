import { useRef, useState } from "react";
import { crearAnalisis } from "../api.js";
import { MODALIDADES, ETIQUETA, reconocer, esZip, esNifti } from "../modalidades.js";

export default function Carga({ onIniciado, onCancelar, pesos }) {
  const sinPesos = pesos && !pesos.instalados;
  const [niftis, setNiftis] = useState([]); // File[] reconocibles
  const [zip, setZip] = useState(null); // File | null
  const [asignacion, setAsignacion] = useState({}); // { t1: File, ... }
  const [edad, setEdad] = useState("");
  const [modo, setModo] = useState("rapido");
  const [segmentacion, setSegmentacion] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [errorLocal, setErrorLocal] = useState(null);
  const carpetaRef = useRef(null);

  function ingerir(fileList) {
    const archivos = Array.from(fileList);
    const unZip = archivos.find(esZip);
    if (unZip) {
      setZip(unZip);
      setNiftis([]);
      setAsignacion({});
      return;
    }
    const soloNii = archivos.filter(esNifti);
    setZip(null);
    setNiftis(soloNii);
    setAsignacion(reconocer(soloNii));
  }

  function alSoltar(e) {
    e.preventDefault();
    if (e.dataTransfer.files?.length) ingerir(e.dataTransfer.files);
  }

  // input de carpeta: webkitdirectory no es estandar, se activa por ref para evitar avisos de React
  function activarCarpeta() {
    const i = carpetaRef.current;
    i.setAttribute("webkitdirectory", "");
    i.setAttribute("directory", "");
    i.click();
  }

  const completo = zip || MODALIDADES.every((m) => asignacion[m]);

  async function enviar(e) {
    e.preventDefault();
    setErrorLocal(null);
    if (edad && (Number(edad) <= 0 || Number(edad) >= 120)) {
      setErrorLocal("La edad debe estar entre 1 y 119 años.");
      return;
    }
    const fd = new FormData();
    if (zip) {
      fd.append("archivos", zip, zip.name);
    } else {
      // Se suben con nombre canónico (t1.nii.gz…) para que el backend las reconozca.
      for (const m of MODALIDADES) fd.append("archivos", asignacion[m], `${m}.nii.gz`);
    }
    if (edad) fd.append("edad", edad);
    fd.append("modo", modo);
    if (segmentacion) fd.append("segmentacion", segmentacion, "segmentacion.nii.gz");

    setEnviando(true);
    try {
      const { id } = await crearAnalisis(fd);
      onIniciado(id);
    } catch (err) {
      setErrorLocal(err.message);
      setEnviando(false);
    }
  }

  return (
    <form className="tarjeta" onSubmit={enviar}>
      <h2>Cargar las resonancias</h2>

      <div
        className="zona-soltar"
        onDrop={alSoltar}
        onDragOver={(e) => e.preventDefault()}
      >
        <p>Arrastre aquí los 4 archivos, una carpeta o un <code>.zip</code>.</p>
        <div className="botones-carga">
          <label className="secundario">
            Elegir archivos
            <input
              type="file"
              multiple
              accept=".nii,.nii.gz,.gz,.zip"
              hidden
              onChange={(e) => ingerir(e.target.files)}
            />
          </label>
          <button type="button" className="secundario" onClick={activarCarpeta}>
            Elegir carpeta
          </button>
          <input
            ref={carpetaRef}
            type="file"
            hidden
            onChange={(e) => ingerir(e.target.files)}
          />
        </div>
      </div>

      {zip && <p className="ok">Archivo comprimido: <strong>{zip.name}</strong></p>}

      {!zip && niftis.length > 0 && (
        <table className="asignacion">
          <tbody>
            {MODALIDADES.map((m) => (
              <tr key={m}>
                <th>{ETIQUETA[m]}</th>
                <td>
                  <select
                    value={asignacion[m]?.name || ""}
                    onChange={(e) =>
                      setAsignacion({
                        ...asignacion,
                        [m]: niftis.find((f) => f.name === e.target.value) || null,
                      })
                    }
                  >
                    <option value="">— sin asignar —</option>
                    {niftis.map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <label className="campo">
        Edad (años) <span className="pista">— opcional. Sin ella no hay pronóstico.</span>
        <input
          type="number"
          min="1"
          max="119"
          step="0.001"
          value={edad}
          onChange={(e) => setEdad(e.target.value)}
          placeholder="p. ej. 62"
        />
      </label>

      <fieldset className="modo" disabled={!!segmentacion || sinPesos}>
        <legend>Segmentación automática (nuestro modelo)</legend>
        {sinPesos && (
          <p className="error">
            No hay modelos instalados: la segmentación automática no está disponible. Sube una segmentación ya
            hecha abajo (opción avanzada).
          </p>
        )}
        <label className="opcion">
          <input type="radio" name="modo" value="rapido" checked={modo === "rapido"}
                 onChange={() => setModo("rapido")} />
          <span><strong>Rápido</strong> — 1 modelo, ~2 min</span>
        </label>
        <label className="opcion">
          <input type="radio" name="modo" value="completo" checked={modo === "completo"}
                 onChange={() => setModo("completo")} />
          <span><strong>Completo</strong> — 5 modelos, ~12 min en CPU, algo más preciso</span>
        </label>
        <p className="pista">Solo aplica si no subes una segmentación. En CPU, el modo completo tarda bastante más.</p>
      </fieldset>

      <details className="avanzado">
        <summary>Opción avanzada: subir una segmentación ya hecha</summary>
        <p className="pista">
          Si no la sube, se segmentará con nuestro modelo (entrenado con nnU-Net sobre BraTS 2018) en este
          equipo (tarda minutos en CPU).
        </p>
        <input
          type="file"
          accept=".nii,.nii.gz,.gz"
          onChange={(e) => setSegmentacion(e.target.files[0] || null)}
        />
      </details>

      {errorLocal && <p className="error">{errorLocal}</p>}

      <div className="acciones">
        <button type="button" className="secundario" onClick={onCancelar} disabled={enviando}>
          Volver
        </button>
        <button type="submit" className="principal" disabled={!completo || enviando}>
          {enviando ? "Iniciando…" : "Analizar paciente"}
        </button>
      </div>
    </form>
  );
}
