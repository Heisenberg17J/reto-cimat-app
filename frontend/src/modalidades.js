// Reconocer cada resonancia por su nombre, igual que el backend (nucleo/entrada.py):
// acepta "t1.nii.gz" o "<id>_t1.nii.gz", sin confundir t1 con t1ce.

export const MODALIDADES = ["t1", "t1ce", "t2", "flair"];

export const ETIQUETA = {
  t1: "T1",
  t1ce: "T1 con contraste (T1ce)",
  t2: "T2",
  flair: "FLAIR",
};

function base(nombre) {
  return nombre.split(".")[0].toLowerCase();
}

export function esZip(archivo) {
  return archivo.name.toLowerCase().endsWith(".zip");
}

export function esNifti(archivo) {
  const n = archivo.name.toLowerCase();
  return n.endsWith(".nii") || n.endsWith(".nii.gz");
}

// Devuelve { t1: File|null, ... } reconociendo por nombre; deja null lo ambiguo o ausente.
export function reconocer(archivos) {
  const asignacion = Object.fromEntries(MODALIDADES.map((m) => [m, null]));
  for (const mod of MODALIDADES) {
    const candidatos = archivos.filter((f) => {
      const b = base(f.name);
      return b === mod || b.endsWith(`_${mod}`);
    });
    if (candidatos.length === 1) asignacion[mod] = candidatos[0];
  }
  return asignacion;
}

// Segmentación del radiólogo en formato BraTS: "<id>_seg.nii.gz" o "seg.nii.gz".
export function esMascaraBrats(archivo) {
  const b = base(archivo.name);
  return esNifti(archivo) && (b === "seg" || b.endsWith("_seg"));
}

// Nombre del paciente a partir de "<id>_t1.nii.gz" (null si el archivo se llama solo "t1.nii.gz").
export function idDelCaso(archivoT1) {
  if (!archivoT1) return null;
  const b = archivoT1.name.split(".")[0];
  return b.toLowerCase().endsWith("_t1") ? b.slice(0, -3) : null;
}
