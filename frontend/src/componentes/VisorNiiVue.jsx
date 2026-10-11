import { useEffect, useRef, useState } from "react";
import { Niivue, SLICE_TYPE, MULTIPLANAR_TYPE } from "@niivue/niivue";
import { urlArchivo } from "../api.js";
import { MODALIDADES, ETIQUETA } from "../modalidades.js";

// Etiquetas BraTS en colores: 1 necrosis/no realzado (rojo), 2 edema (verde), 4 realce (amarillo).
const CMAP_BRATS = {
  R: [0, 230, 40, 255],
  G: [0, 30, 200, 215],
  B: [0, 30, 60, 0],
  A: [0, 255, 255, 255],
  I: [0, 1, 2, 4],
  labels: ["fondo", "necrosis / no realzado", "edema", "realce (ET)"],
};

// Diferencias en el tumor completo (WT): 1 acuerdo (gris), 2 solo el modelo (cian), 3 solo el radiólogo (magenta).
const CMAP_DIFERENCIAS = {
  R: [0, 200, 0, 255],
  G: [0, 200, 208, 61],
  B: [0, 200, 255, 245],
  A: [0, 255, 255, 255],
  I: [0, 1, 2, 3],
  labels: ["fondo", "acuerdo", "solo el modelo", "solo el radiólogo"],
};

const CAPAS = {
  modelo: { archivo: "segmentacion.nii.gz", cmap: CMAP_BRATS, texto: "Modelo" },
  radiologo: { archivo: "referencia.nii.gz", cmap: CMAP_BRATS, texto: "Radiólogo" },
  diferencias: { archivo: "diferencias.nii.gz", cmap: CMAP_DIFERENCIAS, texto: "Diferencias (WT)" },
};

export default function VisorNiiVue({ id, conReferencia = false }) {
  const lienzoRef = useRef(null);
  const nvRef = useRef(null);
  const [modalidad, setModalidad] = useState("flair");
  const [opacidad, setOpacidad] = useState(0.5);
  const [capa, setCapa] = useState("modelo");
  const [fallo, setFallo] = useState(false);

  async function cargar(mod, op, c = "modelo") {
    const nv = nvRef.current;
    if (!nv) return;
    await nv.loadVolumes([
      { url: urlArchivo(id, `${mod}.nii.gz`) },
      { url: urlArchivo(id, CAPAS[c].archivo), opacity: op },
    ]);
    const seg = nv.volumes[1];
    if (seg?.setColormapLabel) {
      seg.setColormapLabel(CAPAS[c].cmap);
      nv.updateGLVolume();
    }
  }

  useEffect(() => {
    let cancelado = false;
    const nv = new Niivue({
      backColor: [0, 0, 0, 1],
      fontColor: [1, 1, 1, 1], // etiquetas de orientación en blanco (fondo negro)
      crosshairColor: [1, 0.7, 0, 1], // cruz naranja, visible sobre negro
      textHeight: 0.05, // texto algo más grande para que se lea
      show3Dcrosshair: true,
      isColorbar: false,
      multiplanarLayout: MULTIPLANAR_TYPE.GRID, // 2x2 alineado
      multiplanarForceRender: true, // render 3D en la 4ª celda del grid
    });
    nvRef.current = nv;
    (async () => {
      try {
        await nv.attachToCanvas(lienzoRef.current);
        nv.setSliceType(SLICE_TYPE.MULTIPLANAR);
        await cargar("flair", 0.5);
      } catch {
        if (!cancelado) setFallo(true);
      }
    })();
    return () => {
      cancelado = true;
      nvRef.current = null;
    };
  }, [id]);

  function cambiarModalidad(e) {
    setModalidad(e.target.value);
    cargar(e.target.value, opacidad, capa).catch(() => setFallo(true));
  }

  function cambiarCapa(e) {
    setCapa(e.target.value);
    cargar(modalidad, opacidad, e.target.value).catch(() => setFallo(true));
  }

  function cambiarOpacidad(e) {
    const op = Number(e.target.value);
    setOpacidad(op);
    nvRef.current?.setOpacity(1, op);
  }

  return (
    <div className="visor">
      <div className="controles-visor">
        <label>
          Modalidad
          <select value={modalidad} onChange={cambiarModalidad}>
            {MODALIDADES.map((m) => (
              <option key={m} value={m}>
                {ETIQUETA[m]}
              </option>
            ))}
          </select>
        </label>
        {conReferencia && (
          <label>
            Máscara
            <select value={capa} onChange={cambiarCapa}>
              {Object.entries(CAPAS).map(([k, c]) => (
                <option key={k} value={k}>
                  {c.texto}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Opacidad de la máscara: {Math.round(opacidad * 100)}%
          <input type="range" min="0" max="1" step="0.05" value={opacidad} onChange={cambiarOpacidad} />
        </label>
      </div>

      <canvas ref={lienzoRef} className="lienzo" />

      {capa === "diferencias" ? (
        <div className="leyenda">
          <span><i style={{ background: "rgb(200,200,200)" }} /> acuerdo</span>
          <span><i style={{ background: "rgb(0,208,255)" }} /> solo el modelo (de más)</span>
          <span><i style={{ background: "rgb(255,61,245)" }} /> solo el radiólogo (no detectado)</span>
        </div>
      ) : (
        <div className="leyenda">
          <span><i style={{ background: "rgb(230,30,30)" }} /> necrosis / no realzado</span>
          <span><i style={{ background: "rgb(40,200,60)" }} /> edema</span>
          <span><i style={{ background: "rgb(255,215,0)" }} /> realce (ET)</span>
        </div>
      )}

      {fallo && (
        <p className="error">
          No se pudo iniciar el visor 3D (WebGL) en este navegador. La vista de control (imagen) sigue
          disponible más abajo.
        </p>
      )}
    </div>
  );
}
