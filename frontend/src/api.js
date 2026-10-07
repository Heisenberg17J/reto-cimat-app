// Llamadas al backend FastAPI local. Todo pasa por /api (mismo origen que el frontend).

export async function crearAnalisis(formData) {
  const r = await fetch("/api/analisis", { method: "POST", body: formData });
  if (!r.ok) {
    let detalle = "no se pudo iniciar el análisis";
    try {
      detalle = (await r.json()).detail || detalle;
    } catch {
      /* respuesta sin JSON */
    }
    throw new Error(detalle);
  }
  return r.json();
}

export async function estadoAnalisis(id) {
  const r = await fetch(`/api/analisis/${id}`);
  if (!r.ok) throw new Error("no se encontró el análisis");
  return r.json();
}

export async function borrarAnalisis(id) {
  await fetch(`/api/analisis/${id}`, { method: "DELETE" });
}

export function urlArchivo(id, nombre) {
  return `/api/analisis/${id}/archivo/${nombre}`;
}

export async function estadoPesos() {
  const r = await fetch("/api/pesos");
  if (!r.ok) throw new Error("no se pudo consultar el estado de los modelos");
  return r.json();
}

export async function descargarPesos() {
  const r = await fetch("/api/pesos/descargar", { method: "POST" });
  return r.json();
}

export async function listarEjemplos() {
  const r = await fetch("/api/ejemplos");
  if (!r.ok) return [];
  return r.json();
}

export async function analizarEjemplo(id) {
  const r = await fetch(`/api/ejemplos/${id}`, { method: "POST" });
  if (!r.ok) throw new Error((await r.json()).detail || "no se pudo iniciar el ejemplo");
  return r.json();
}
