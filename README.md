# Hackathon-Gambooza-Carnicos

Solución del Grupo 9 para el Hackathon «Semana del Descubrir» organizado por la UFV.

## Reproducción

Ejecutar desde la raíz del repositorio y en este orden:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/01_motion_crop.py
python src/02_extract_features.py
python src/03_train_temporal.py
```

Los clips, embeddings y CSV de entrada (`train.csv` y `test.csv`) deben estar disponibles bajo
`data/`. Estos ficheros no se versionan porque son pesados.

## Entregables

Los documentos finales se guardan en `entregables/`:

- Presentación.
- Business Model Canvas.
- Memoria breve de viabilidad.
- Arquitectura C4.

## Resultados

Los resultados reproducibles se guardan en `resultados/`, incluyendo las predicciones, el registro
de experimentos y la matriz de confusión.
