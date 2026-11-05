# bigkokoz.github.io

Portafolio de José — https://bigkokoz.github.io/

La portada lee `data/projects.json`: para agregar o editar un proyecto no hay que tocar HTML.

## Estructura

```text
/
├── index.html              # portada (destacados + otros proyectos)
├── css/site.css            # sistema visual común (portada, páginas de proyecto y apps)
├── js/app.js               # arma la portada desde el JSON
├── data/projects.json      # única fuente de verdad de los proyectos
├── assets/projects/<id>/   # imagen de cada tarjeta (thumb, 16:10)
├── lampara/                # Lámpara reactiva al sonido
│   ├── index.html          # página del proyecto (proceso, decisiones, uso)
│   ├── app.html            # app web: Web Serial + audio + simulador
│   ├── lamina.html         # lámina A3 para presentar (imprimible)
│   ├── firmware/           # .ino del Arduino y script de avisos de Claude
│   └── archivos/           # STL, STEP y modelo paramétrico
└── controla-flow/          # CONTROLA FLOW (groovebox con Arduino)
```

## Campos de un proyecto (`data/projects.json`)

| Campo | Para qué |
|---|---|
| `id` | Único, minúsculas y guiones. |
| `order` | Posición (menor = primero). |
| `published` | `true` para mostrarlo. |
| `featured` | `true` lo muestra grande en "Destacados". |
| `title`, `subtitle`, `year` | Título, línea corta y año. |
| `cardExcerpt` | Texto de la tarjeta. |
| `description`, `role`, `tags` | Detalle (se ve en el modal si no hay página). |
| `thumb` | Imagen 16:10. Si falta, se muestra un color con iniciales. |
| `page` | Página propia del proyecto (botón "Ver proyecto"). |
| `app` | App que se puede abrir (botón "Abrir app"). |
| `links` | Enlaces extra para el modal. |

Pendiente: subir la imagen `assets/projects/interfaz-impresora/thumb.png`.

## Probar localmente

```bash
python -m http.server 8080
```

Las apps con Web Serial funcionan en Chrome o Edge de escritorio.
