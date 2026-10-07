import AvisoPesos from "./AvisoPesos.jsx";

export default function Inicio({ onEmpezar, pesos, setPesos }) {
  return (
    <>
      <AvisoPesos pesos={pesos} setPesos={setPesos} />
      <section className="tarjeta inicio">
        <h1>Análisis de glioma</h1>
      <p>
        Esta aplicación analiza las resonancias de un paciente con glioma: <strong>segmenta</strong> el tumor
        (edema, necrosis y realce), calcula sus <strong>volúmenes</strong> y estima la <strong>supervivencia</strong>{" "}
        (corta, media o larga).
      </p>
      <p>
        Usa <strong>nuestros modelos</strong> —los que entrenó el <strong>Team Camacho</strong> en el proyecto{" "}
        <em>reto-CIMAT</em> (BraTS 2018)— tanto para la segmentación como para el pronóstico.
      </p>
      <ul>
        <li>Necesita las 4 resonancias en <strong>formato BraTS</strong> (NIfTI): t1, t1ce, t2 y flair.</li>
        <li>La <strong>edad</strong> es opcional, pero sin ella no hay pronóstico.</li>
        <li>Todo se procesa <strong>en este equipo</strong>; las imágenes no se suben a internet.</li>
      </ul>
      <p className="nota">
        Recuerde: es un <strong>prototipo de investigación</strong>, no una herramienta clínica. El modelo de
        pronóstico depende casi solo de la edad (c-index 0.62, prácticamente igual a la edad sola).
      </p>
        <button className="principal" onClick={onEmpezar}>
          Analizar un paciente
        </button>
      </section>

      <section className="tarjeta creditos">
        <img
          className="logo-uniajc"
          src="logo-uniajc.png"
          alt="Universidad Antonio José Camacho (UNIAJC)"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
        <div>
          <p className="uni">Universidad Antonio José Camacho (UNIAJC)</p>
          <p>
            <strong>Team Camacho</strong> — semilleros AppliScience y SEMOSIMA
          </p>
          <p className="autores">
            Hejembert Jaramillo · Daniel León · Karen Arroyave · Dylan Cuervo · Nikol López
          </p>
        </div>
      </section>
    </>
  );
}
