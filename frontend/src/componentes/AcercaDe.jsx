// "Acerca de": contexto del reto CIMAT, enfoque, resultados y citas (obligatorias por BraTS).
// Se abre desde el pie de página.
function Enlace({ href, children }) {
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  );
}

export default function AcercaDe({ onCerrar }) {
  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Acerca de">
        <button className="modal-cerrar" onClick={onCerrar} aria-label="Cerrar">×</button>
        <h2>Acerca de</h2>

        <p>
          Prototipo de investigación para el reto del <strong>Centro de Investigación en Matemáticas (CIMAT)</strong>:{" "}
          <em>Evolutionary Machine Learning para la detección de tumores cerebrales y la predicción de la supervivencia
          de pacientes a partir de la caracterización de imágenes médicas</em>.
        </p>
        <p>
          Dado un paciente con sus cuatro modalidades de MRI (T1, T1ce, T2, FLAIR) y su edad, la app segmenta el tumor,
          extrae sus características radiómicas y estima la supervivencia.
        </p>

        <h3>Enfoque</h3>
        <p><strong>Datos:</strong> BraTS 2018, 285 pacientes; 163 con dato de supervivencia.</p>
        <p>
          <strong>Segmentación:</strong> nnU-Net 3D, 5 folds × 100 épocas. Dice fuera de fold: tumor completo 0,907 ·
          núcleo 0,842 · realce 0,769.
        </p>
        <p>
          <strong>Pronóstico:</strong> Cox con selección de características por algoritmo genético, sobre 1.146
          características radiómicas extraídas con PyRadiomics. Comparado contra edad sola y Cox Elastic Net, con
          validación cruzada anidada.
        </p>
        <p>
          Segmentación y pronóstico comparten la misma partición, de modo que la radiómica se calcula sobre máscaras
          predichas fuera de fold: ningún paciente fue visto por el modelo que generó su propia segmentación.
        </p>

        <h3>Resultados</h3>
        <p>
          <strong>La radiómica no supera a la edad.</strong> C-index: edad 0,624 · Elastic Net 0,622 · genético 0,605,
          sin diferencias significativas.
        </p>
        <p>
          El algoritmo genético reporta 0,70 según su criterio interno frente a 0,605 medido sobre pacientes no vistos
          — una brecha de +0,09 que cuantifica su sobreajuste. Las características que selecciona varían casi por
          completo entre folds (estabilidad de Nogueira 0,05).
        </p>
        <p>
          Con 163 pacientes y más de mil características, las diferencias pequeñas no son distinguibles del ruido. Un
          solo centro aporta el 52 % de la cohorte.
        </p>

        <blockquote className="aviso-academico">
          <strong>Prototipo académico. No es un dispositivo médico, no ha sido validado clínicamente y no debe usarse
          para decisiones diagnósticas, pronósticas ni de tratamiento.</strong>
        </blockquote>

        <h3>Artículo</h3>
        <p>En preparación. El enlace se publicará aquí.</p>

        <h3>Citas</h3>
        <p>El uso de BraTS 2018 obliga a citar:</p>
        <ol className="citas">
          <li>
            Menze B. H., et al. “The Multimodal Brain Tumor Image Segmentation Benchmark (BRATS)”. <em>IEEE TMI</em>{" "}
            34(10), 1993–2024 (2015).{" "}
            <Enlace href="https://doi.org/10.1109/TMI.2014.2377694">10.1109/TMI.2014.2377694</Enlace>
          </li>
          <li>
            Bakas S., et al. “Advancing The Cancer Genome Atlas glioma MRI collections with expert segmentation labels
            and radiomic features”. <em>Sci Data</em> 4:170117 (2017).{" "}
            <Enlace href="https://doi.org/10.1038/sdata.2017.117">10.1038/sdata.2017.117</Enlace>
          </li>
          <li>
            Bakas S., et al. “Identifying the Best Machine Learning Algorithms for Brain Tumor Segmentation, Progression
            Assessment, and Overall Survival Prediction in the BRATS Challenge”. arXiv:1811.02629 (2018).{" "}
            <Enlace href="https://arxiv.org/abs/1811.02629">arxiv.org/abs/1811.02629</Enlace>
          </li>
          <li>
            Bakas S., et al. “Segmentation Labels and Radiomic Features for the Pre-operative Scans of the TCGA-GBM
            collection”. <em>TCIA</em> (2017).{" "}
            <Enlace href="https://doi.org/10.7937/K9/TCIA.2017.KLXWJJ1Q">10.7937/K9/TCIA.2017.KLXWJJ1Q</Enlace>
          </li>
          <li>
            Bakas S., et al. “Segmentation Labels and Radiomic Features for the Pre-operative Scans of the TCGA-LGG
            collection”. <em>TCIA</em> (2017).{" "}
            <Enlace href="https://doi.org/10.7937/K9/TCIA.2017.GJQ7R0EF">10.7937/K9/TCIA.2017.GJQ7R0EF</Enlace>
          </li>
        </ol>
        <p className="pista">
          Herramientas: nnU-Net (Isensee et al., <em>Nat Methods</em> 2021) · PyRadiomics (van Griethuysen et al.,{" "}
          <em>Cancer Res</em> 2017) · IBSI (Zwanenburg et al., <em>Radiology</em> 2020).
        </p>

        <h3>Datos de ejemplo</h3>
        <p className="pista">
          Los casos de ejemplo provienen de la colección <strong>UPENN-GBM</strong> (TCIA), bajo licencia{" "}
          <strong>CC BY 4.0</strong>:
        </p>
        <ol className="citas">
          <li>
            Bakas S., Sako C., Akbari H., et al. “The University of Pennsylvania glioblastoma (UPenn-GBM) cohort:
            advanced MRI, clinical, genomics, &amp; radiomics”. <em>Sci Data</em> 9, 453 (2022).{" "}
            <Enlace href="https://doi.org/10.1038/s41597-022-01560-7">10.1038/s41597-022-01560-7</Enlace>
          </li>
          <li>
            UPENN-GBM mpMRI (Version 2) [Data set]. <em>The Cancer Imaging Archive</em> (2021).{" "}
            <Enlace href="https://doi.org/10.7937/TCIA.709X-DN49">10.7937/TCIA.709X-DN49</Enlace>
          </li>
        </ol>
      </div>
    </div>
  );
}
