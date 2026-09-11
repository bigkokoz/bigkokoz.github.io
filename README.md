# Taller-Interfaces-UAI

Portafolio estático de Jose (Taller Interfaces UAI). El sitio lee `data/projects.json`
y renderiza la home y el detalle de cada proyecto — **no hay que tocar HTML** para
agregar, editar u ocultar un proyecto.

Sitio publicado: `https://bigkokoz.github.io/`

## Estructura

```text
/
├── index.html          # shell mínima
├── css/styles.css       # estilos
├── js/app.js             # fetch del JSON, render de grid/modal, routing
├── data/projects.json    # única fuente de verdad de los proyectos
└── assets/projects/<id>/ # imágenes de cada proyecto (thumb.png, hero.png)
```

## Cómo agregar un proyecto (sin código)

1. En GitHub, entra al repo → **Add file → Upload files** y sube las imágenes a
   `assets/projects/<tu-id>/thumb.png` y `assets/projects/<tu-id>/hero.png`
   (usa el mismo `<tu-id>` que vas a poner en el JSON). Si no subes imágenes,
   la tarjeta muestra automáticamente un color con las iniciales del título —
   no queda un ícono roto.
2. Abre `data/projects.json` → **Edit** (ícono de lápiz) y copia un bloque de
   proyecto existente dentro del array `projects`, por ejemplo:

   ```json
   {
     "id": "nombre-del-proyecto",
     "order": 4,
     "published": true,
     "title": "Título del proyecto",
     "subtitle": "Subtítulo corto",
     "cardExcerpt": "Una línea para la tarjeta (máx. ~120 caracteres).",
     "description": "Párrafo largo para el detalle.",
     "year": 2026,
     "tags": ["tag1", "tag2"],
     "role": "Tu rol en el proyecto",
     "thumb": "assets/projects/nombre-del-proyecto/thumb.png",
     "hero": "assets/projects/nombre-del-proyecto/hero.png",
     "links": [{ "label": "Ver más", "url": "https://..." }]
   }
   ```

3. Ajusta los campos:
   - `id`: único, en minúsculas y con guiones (sin espacios ni tildes).
   - `order`: número que define la posición en la grilla (menor = primero).
   - `published`: `true` para que se vea en el sitio público, `false` para
     dejarlo como borrador (Jose lo ve en el JSON pero el visitante no).
   - `cardExcerpt` y `description` son obligatorios si `published` es `true`.
4. Haz **Commit changes** directo a `main`.
5. Espera 1–2 minutos a que GitHub Pages actualice y abre la URL pública.

### Checklist antes de publicar

- [ ] `id` único y no repetido con otro proyecto.
- [ ] Rutas de `thumb`/`hero` apuntan a la carpeta correcta en `assets/projects/`.
- [ ] `cardExcerpt` (tarjeta) y `description` (detalle) completos.
- [ ] `order` correcto respecto a los demás proyectos.
- [ ] `published: true` solo cuando el contenido esté listo.

### Datos del sitio (encabezado y contacto)

Al principio de `data/projects.json` está el bloque `site`:

```json
"site": {
  "title": "Mis Proyectos",
  "ownerName": "Jose",
  "tagline": "Diseño de interfaces · Taller UAI",
  "contactEmail": "",
  "contactLinkedIn": ""
}
```

Completa `contactEmail` y/o `contactLinkedIn` para que aparezca un botón de
contacto al final de cada proyecto.

## Pendiente: imagen del proyecto "Interfaz impresora"

El proyecto `interfaz-impresora` ya está publicado con su texto real, pero
todavía no tiene imagen. En `data/projects.json` sus rutas ya están
declaradas:

- `assets/projects/interfaz-impresora/thumb.png`
- `assets/projects/interfaz-impresora/hero.png`

Mientras esos archivos no existan, el sitio muestra automáticamente un
color con las iniciales ("II") en vez de un ícono roto. Para agregar el
diagrama real, sube el PNG a esa misma ruta (ver pasos arriba) — no hace
falta tocar el JSON.

## GitHub Pages

Ya está activo (Settings → Pages → Deploy from a branch → `main` → `/root`).
El repo se llama `bigkokoz.github.io`, así que Pages lo sirve como sitio de
usuario, directo en la raíz: `https://bigkokoz.github.io/` (sin sufijo del
nombre del repo). Cualquier commit a `main` se refleja ahí en 1–2 minutos.

## Desarrollo local

Es un sitio estático sin build. Para probarlo localmente hace falta
servirlo por HTTP (el `fetch` de `data/projects.json` no funciona abriendo
`index.html` directo con `file://`). Por ejemplo:

```bash
npx serve .
# o
python -m http.server 8080
```
