"""
organizar_clips.py
Ordena los videos del reto en carpetas:

    <salida>/train/<bar>/<incidencia>/<clip_id>.mp4
    <salida>/test/<bar>/<clip_id>.mp4          (test no trae etiqueta, asi que no hay nivel de incidencia)

Los datos salen de train.csv (clip_id, bar, ..., label) y test.csv (clip_id, bar, ...).
Busca los .mp4 dentro de la carpeta de videos, tambien en subcarpetas.

Estructura esperada (todo al mismo nivel, en la carpeta --base):
    <base>/train.csv
    <base>/test.csv
    <base>/clips_public/   (los .mp4)
y se crea <base>/clips_ordenados/.

Uso (ejemplo en Mac, desde la carpeta que contiene train.csv, test.csv y clips_public):
  cd ~/Desktop/mi_carpeta
  python3 /ruta/a/organizar_clips.py --dry-run     # primero en seco, sin tocar nada
  python3 /ruta/a/organizar_clips.py

  # o indicando la carpeta sin hacer cd:
  python3 organizar_clips.py --base ~/Desktop/mi_carpeta

Si algo esta en otro sitio, se puede indicar con --clips, --train, --test y --salida.

--modo controla que se hace con cada video:
  enlace  (por defecto) enlace duro: aparece en la carpeta nueva sin ocupar espacio extra y el
          original sigue donde estaba. Si no es posible (otro disco), copia.
  copiar  copia el video (ocupa el doble de espacio)
  mover   lo mueve (el original desaparece de su sitio)
Es seguro repetirlo: lo que ya esta colocado se salta.
"""
import argparse
import csv
import os
import shutil
import sys
from collections import Counter
from pathlib import Path


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        sys.exit(f"{ruta} esta vacio")
    for col in ("clip_id", "bar"):
        if col not in filas[0]:
            sys.exit(f"{ruta} no tiene la columna '{col}'. Columnas: {list(filas[0])}")
    return filas


def limpio(nombre):
    """Nombre seguro para carpeta (por si alguna etiqueta trae barras o espacios raros)."""
    return str(nombre).strip().replace("/", "_").replace("\\", "_") or "sin_etiqueta"


def colocar(origen, destino, modo):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        return "ya_estaba"
    if modo == "mover":
        shutil.move(str(origen), str(destino))
        return "movido"
    if modo == "copiar":
        shutil.copy2(origen, destino)
        return "copiado"
    try:  # enlace
        os.link(origen, destino)
        return "enlazado"
    except OSError:
        shutil.copy2(origen, destino)
        return "copiado"


def main():
    ap = argparse.ArgumentParser(description="Ordena los clips en train|test / bar / incidencia")
    ap.add_argument("--base", default=".", help="carpeta con train.csv, test.csv y clips_public (por defecto, la actual)")
    ap.add_argument("--clips", help="carpeta con los .mp4 (por defecto <base>/clips_public)")
    ap.add_argument("--train", help="train.csv (por defecto <base>/train.csv)")
    ap.add_argument("--test", help="test.csv (por defecto <base>/test.csv, si existe)")
    ap.add_argument("--salida", help="carpeta de salida (por defecto <base>/clips_ordenados)")
    ap.add_argument("--modo", choices=["enlace", "copiar", "mover"], default="enlace")
    ap.add_argument("--dry-run", action="store_true", help="solo muestra lo que haria")
    a = ap.parse_args()

    base = Path(a.base).expanduser().resolve()
    clips_dir = Path(a.clips).expanduser() if a.clips else base / "clips_public"
    salida = Path(a.salida).expanduser() if a.salida else base / "clips_ordenados"
    train_csv = Path(a.train).expanduser() if a.train else base / "train.csv"
    test_csv = Path(a.test).expanduser() if a.test else base / "test.csv"
    if not train_csv.is_file():
        sys.exit(f"No encuentro {train_csv}. Ejecuta el script desde la carpeta que contiene train.csv o usa --base")
    if not clips_dir.is_dir():
        sys.exit(f"No existe la carpeta de videos: {clips_dir}")

    # indice clip_id -> ruta del video
    videos = {p.stem: p for p in clips_dir.rglob("*.mp4")}
    print(f"{len(videos)} videos encontrados en {clips_dir}")
    if not videos:
        sys.exit("No hay ningun .mp4: revisa la ruta de --clips")

    trabajo = []  # (clip_id, subconjunto, bar, incidencia, destino)
    for fila in leer_csv(train_csv):
        inc = limpio(fila.get("label", "sin_etiqueta"))
        trabajo.append((fila["clip_id"], "train", fila["bar"], inc,
                        salida / "train" / limpio(fila["bar"]) / inc / f"{fila['clip_id']}.mp4"))
    if test_csv.is_file():
        for fila in leer_csv(test_csv):
            trabajo.append((fila["clip_id"], "test", fila["bar"], "",
                            salida / "test" / limpio(fila["bar"]) / f"{fila['clip_id']}.mp4"))

    cuenta, faltan, manifiesto = Counter(), [], []
    for clip_id, sub, bar, inc, destino in trabajo:
        origen = videos.get(clip_id)
        if origen is None:
            faltan.append((sub, clip_id))
            continue
        if a.dry_run:
            res = "ya_estaba" if destino.exists() else "se_colocaria"
        else:
            res = colocar(origen, destino, a.modo)
        cuenta[res] += 1
        manifiesto.append([clip_id, sub, bar, inc, str(destino.relative_to(salida))])

    if not a.dry_run:
        salida.mkdir(parents=True, exist_ok=True)
        with open(salida / "manifiesto.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["clip_id", "subconjunto", "bar", "incidencia", "ruta"])
            w.writerows(manifiesto)

    print("\nResumen:", dict(cuenta))
    sin_csv = set(videos) - {t[0] for t in trabajo}
    if faltan:
        print(f"AVISO: {len(faltan)} clips de los CSV no estan en la carpeta de videos "
              f"(ej.: {faltan[0][1]}). Por conjunto: {dict(Counter(s for s, _ in faltan))}")
    if sin_csv:
        print(f"AVISO: {len(sin_csv)} videos de la carpeta no aparecen en ningun CSV y no se han tocado.")
    if a.dry_run:
        print("\n(Prueba en seco: no se ha creado ni movido nada.)")
    else:
        print(f"\nHecho. Estructura en {salida}  (lista completa en manifiesto.csv)")


if __name__ == "__main__":
    main()
