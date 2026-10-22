# Reto Gambooza · malas praxis en la barra — guía para asistentes de código

Este fichero resume el reto para que lo lea un asistente (Claude Code, Cursor, Codex...) o una
persona con prisa. La explicación larga está en `README.md`.

## Objetivo

Clasificar clips de vídeo de una barra de bar en 8 clases: `normal` o uno de 7 tipos de mala
praxis. Entrada: un `.mp4`. Salida: una etiqueta por clip. Entregable: `predictions.csv` con
columnas `clip_id,label`, una fila por clip de `test.csv`, más código y una presentación.

## Ficheros y esquemas

```
clips_public/<clip_id>.mp4        896×512, 15 fps, sin audio, 20–60 s, caras pixeladas
train.csv                         clip_id, bar, weekday, hour, seconds, label     (4970 filas)
test.csv                          clip_id, bar, weekday, hour, seconds            (743 filas, sin label)
classes.csv                       label, descripción                              (8 clases)
embeddings/dinov2s_224/<id>.npy   (T, 384) float16, T = fotogramas a 2 fps
embeddings/dinov2b_224/<id>.npy   (T, 768) float16
embeddings/<tag>_pooled.npz       ids (N,), X (N, dim) media temporal, n_frames (N,)
embeddings/<tag>_index.csv        clip_id, n_frames, dim
baseline.py                       regresión logística sobre la media de embeddings (CPU, segundos)
evaluate.py                       F1 macro por clase, praxis vs normal, desglose por bar (--test)
embed_example.py                  calcula embeddings nuevos: --crop, --size, --pool, --fps, --model, --bar
```

- `bar` es un id anónimo `bar_01`..`bar_14`. Cada bar tiene su cámara fija y su encuadre.
- `weekday` (Mon..Sun), `hour` (0-23) y `seconds` (duración del clip) son metadatos, no señal.
- El evento ocupa unos segundos en el centro del clip, con ~10 s de margen a cada lado.
- Clases desbalanceadas: `normal` es ~70 %; `espuma_tirada` y `cerveza_al_sumidero` son más de
  la mitad de las praxis; `cambio_de_vaso`, `un_vaso_dos_grifos` y `vaso_equivocado` son raras
  y muy concentradas en pocos bares.
- Las etiquetas son anotación humana y puede haber dudosas.

## Comandos

```bash
pip install numpy scikit-learn                      # para baseline y evaluate
python baseline.py --ds . --tag dinov2s_224          # CV dejando bares fuera + predictions_dinov2s_224.csv
python evaluate.py --pred mis_predicciones.csv --labels mis_etiquetas.csv --test train.csv
                                                     # medir sobre una partición propia de train
pip install torch transformers numpy                 # para embeddings nuevos (ffmpeg en PATH)
python embed_example.py --clips clips_public --out emb --ids train.csv --bar bar_09 \
    --model facebook/dinov2-small --size 518 --pool mean --fps 2 --crop 0.1,0.2,0.9,0.9
```

Los embeddings entregados son fotograma a fotograma, fotograma completo aplastado a 224×224,
token CLS, sin información temporal. Son un punto de partida, no una recomendación.

## Plan sugerido

1. Un bar primero: elegir uno con muchas praxis en train, mirar sus clips, recortar a la zona
   de grifos y bandeja, calcular embeddings o entrenar ahí, validar dentro del bar.
2. Modelo general con todos los bares, validado dejando bares enteros fuera (`GroupKFold` por
   `bar`).
3. Ajuste ligero por bar sobre el modelo general (cabeza, umbrales, adaptador). Comparar con y
   sin ajuste.
4. Pensar cómo se adaptaría a un bar que no está en train.

## Restricciones

- Los clips son grabaciones reales de locales clientes: no subirlos a sitios públicos, no
  redistribuirlos, copias de trabajo solo privadas, borrar al terminar el hackathon.
- No modificar `test.csv` ni `train.csv`; crear particiones propias en ficheros nuevos.
- Un sistema que tarde más que el tiempo real por cámara no sirve en producción (Gambooza
  procesa ~150 h de vídeo al día): anotar el coste por hora de vídeo.
- El jurado tiene en cuenta los resultados y también la explicación y el razonamiento: qué se
  probó, por qué funciona o no, y cómo se comportaría en un local nuevo.
