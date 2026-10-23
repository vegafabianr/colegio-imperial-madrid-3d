# El Colegio Imperial de Madrid en 3D

Modelo 3D del antiguo Colegio Imperial de la Compañía de Jesús de Madrid, hoy **Instituto San Isidro** (calle de Toledo 39) y **Real Colegiata de San Isidro** (calle de Toledo 37), tal como está hoy. No es una reconstrucción histórica.

*3D model of the former Colegio Imperial (Jesuit college) in Madrid as it stands today, built only from open data. The site and the notes are in Spanish; code comments are in English.*

**Ver el modelo:** https://vegafabianr.github.io/colegio-imperial-madrid-3d/

Versión preliminar (0.1, octubre de 2026).

## Cómo se hizo

1. **Planta.** Huellas de los edificios del Catastro (INSPIRE), en ETRS89 / UTM 30N (EPSG:25830). En Blender el origen local es x = 440000, y = 4473700, z = 640.
2. **Alturas y cubiertas.** Nube de puntos 2023 del Ayuntamiento de Madrid (fotogramétrica, ~100 puntos/m²). Cada cubierta se ajusta crujía por crujía (plana, a un agua o a dos aguas).
3. **Torres, cúpula y linterna.** Cortes de la nube cada 0,5 m; en cada nivel se mide el contorno (octógono o cuadrado achaflanado).
4. **Fachadas.** Fotos con licencia abierta (Wikimedia Commons, Mapillary), rectificadas y escaladas con las alturas de la nube. Las medidas de cada tramo quedan en tablas CSV editables (`data/fachadas/`, `data/volumenes/`). Lo que no se pudo medir lleva la marca `[ESTIMADO]`.
5. **Materiales.** Colores tomados de las fotos abiertas y de la ortofoto 2023; texturas generadas por script.
6. **Control.** Las cubiertas se comparan con la capa municipal de alturas (diferencia mediana absoluta: 0,44 m; 81 % de los cuerpos dentro de ±1 m) y el modelo entero con la malla 3D texturizada del Ayuntamiento (2024), que se usa solo como referencia.

## Contenido

- `index.html`: la página con el visor 3D ([model-viewer](https://modelviewer.dev/)).
- `blender/colegio_imperial_lod3.glb` y `.blend`: el modelo final.
- `renders/`: vistas del modelo.
- `scripts/`: cuadernos de Jupyter, en orden (`01_catastro` … `19_control_malla`), y scripts que corren dentro de Blender (`meshes_to_blender.py`, `render_*.py`, `vistas_malla.py`, `malla_distancias.py`).
- `data/`: datos de trabajo: la manzana catastral (`catastro_manzana.gpkg`), el recorte de la nube de puntos (`nube_manzana_2023.laz`), las tablas de fachadas, volúmenes y materiales, y las texturas.
- `sources/SOURCES.md`: todas las fuentes, con fecha de consulta, licencia y qué aporta cada una.

## Cómo regenerarlo

Hace falta Python 3.13 (geopandas, shapely, pyproj, pandas, numpy, scipy, laspy con lazrs, requests, Pillow, Jupyter) y Blender 5.2 (la ruta está en la primera celda de cada cuaderno). Los cuadernos se corren desde `scripts/`.

- Orden completo: `01` → `19`.
- Solo el modelo final: `05` → `10` → `15` → `17` → `14` → `16` (control automático; revisar los `AVISO` de `data/control/informe_control.csv`) → `19`.
- `08_mapillary` necesita un token de Mapillary en un archivo `.env` (`MAPILLARY_TOKEN=...`), que no se sube.

## Qué falta

- Medir sobre fotos las fachadas de las calles de los Estudios, de la Colegiata y del Duque de Alba, y las de los patios (hoy, huecos estimados).
- Detalles de la cúpula (base de cinc, marcos del tambor), buhardillas y chimeneas.
- Confirmar que la parcela `0139423VK4703G` (calle de los Estudios 1) forma parte del instituto.

## Cómo citar

Vega, Fabián R. (2026). *El Colegio Imperial de Madrid en 3D* [modelo 3D, versión preliminar 0.1]. GitHub. https://github.com/vegafabianr/colegio-imperial-madrid-3d

## Licencias

- Código (`scripts/`, `index.html`): MIT (`LICENSE`).
- Modelo (`blender/`), vistas (`renders/`) y tablas de medidas (`data/`): CC BY 4.0 (`LICENSE-MODEL`).
- Los datos de base conservan sus condiciones: Catastro (Dirección General del Catastro, reutilización con cita de la fuente) y Ayuntamiento de Madrid (nube de puntos 2023, ortofoto 2023, alturas de edificios; reutilización citando origen y fecha). Las fotos de Wikimedia Commons y Mapillary no se incluyen; sus autores y licencias están en `sources/SOURCES.md`.
