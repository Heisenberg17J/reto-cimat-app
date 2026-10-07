// Guía rápida dentro de la app (modal). Se abre con el botón flotante "? Guía".
const GUIA_COMPLETA =
  "https://github.com/Heisenberg17J/reto-cimat-app/blob/main/docs/GUIA_USUARIO.md";
const BRATS_TOOLKIT = "https://brats-toolkit.readthedocs.io";

export default function Guia({ onCerrar }) {
  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Guía de uso">
        <button className="modal-cerrar" onClick={onCerrar} aria-label="Cerrar">×</button>
        <h2>Guía rápida</h2>

        <p className="pista">
          Prototipo de investigación, <strong>no es una herramienta clínica</strong>. El pronóstico depende casi solo
          de la edad.
        </p>

        <h3>Qué hace</h3>
        <p>
          A partir de las 4 resonancias de un paciente con glioma (y, si se conoce, la edad): segmenta el tumor,
          calcula sus volúmenes y estima la supervivencia (corta / media / larga).
        </p>

        <h3>Qué necesita</h3>
        <ul>
          <li>Las <strong>4 resonancias</strong> en <strong>formato BraTS</strong> (NIfTI): <code>t1</code>,
            <code> t1ce</code>, <code>t2</code> y <code>flair</code>.</li>
          <li>La <strong>edad</strong> es opcional (sin ella no hay pronóstico).</li>
          <li>Todo se procesa <strong>en este equipo</strong>; las imágenes no salen de aquí.</li>
        </ul>

        <h3>Pasos</h3>
        <ol>
          <li>Pulse <strong>“Analizar un paciente”</strong>.</li>
          <li><strong>Cargue</strong> los 4 archivos (o una carpeta o un <code>.zip</code>).</li>
          <li>Escriba la <strong>edad</strong> si la conoce.</li>
          <li>Elija el modo de segmentación: <strong>Rápido</strong> (~2 min) o <strong>Completo</strong> (~12 min).</li>
          <li>Pulse <strong>“Analizar paciente”</strong> y espere las etapas.</li>
        </ol>

        <h3>Resultados</h3>
        <ul>
          <li><strong>Visor 3D</strong>: máscara en colores (rojo necrosis, verde edema, amarillo realce).</li>
          <li><strong>Volúmenes</strong> (cm³) y <strong>pronóstico</strong> (o “no aplica” si falta la edad o el realce).</li>
          <li>Botón para <strong>guardar un informe en PDF</strong>.</li>
        </ul>

        <h3>¿No tienes las imágenes en formato BraTS?</h3>
        <p>
          Una resonancia clínica normal (DICOM del hospital) <strong>no</strong> viene en formato BraTS (sin cráneo,
          co-registrada y de 240×240×155). Convertirla requiere un preprocesamiento aparte (DICOM→NIfTI, registro,
          extracción de cráneo) que esta app <strong>no</strong> incluye. Herramientas de referencia (requieren
          instalación y conocimientos técnicos):{" "}
          <a href={BRATS_TOOLKIT} target="_blank" rel="noreferrer">BraTS Toolkit / BrainLes</a>.
        </p>

        <p className="pista">
          Guía completa: <a href={GUIA_COMPLETA} target="_blank" rel="noreferrer">docs/GUIA_USUARIO.md</a>.
        </p>
      </div>
    </div>
  );
}
