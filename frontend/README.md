# frontend · interfaz del reto CIMAT (React + Vite + NiiVue)

Interfaz web en español, sin tecnicismos. La sirve el backend FastAPI (`backend/`) desde `frontend/dist`.
**Prototipo de investigación, no clínico.**

## Pantallas (`src/componentes/`)

- **Inicio** — qué hace la app y el aviso "no clínico".
- **Carga** — arrastrar los 4 archivos, una carpeta o un `.zip`; reconoce las modalidades por el nombre (igual que
  `nucleo/entrada.py`) o se asignan a mano. Edad opcional. Opción avanzada: subir una segmentación.
- **Progreso** — etapas (entrada → segmentación → radiómica → pronóstico → salida) con barra y tiempo.
- **Resultados** — visor **NiiVue** (modalidad, opacidad de la máscara, colores BraTS: rojo necrosis, verde edema,
  amarillo realce), volúmenes, pronóstico (o "no aplica" con el motivo y la referencia según la edad), vista de control
  e informe PDF (`window.print()`).

## Desarrollo

```bash
npm install
# Backend aparte, en otra terminal:
reto-cimat-servidor --puerto 8000 --sin-navegador
npm run dev        # http://127.0.0.1:5173 ; Vite manda /api -> 127.0.0.1:8000
```

## Compilar (lo que sirve el backend)

```bash
npm run build      # genera frontend/dist/
```

Con `frontend/dist/` presente, `reto-cimat-servidor` lo sirve en `/` (si no existe, usa la página mínima de
`backend/estatico/`). `node_modules/` y `dist/` no se versionan.
