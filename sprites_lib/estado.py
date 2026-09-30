"""Estado de artefactos aprobados: hash de la fuente, fecha y detección de deriva."""
import glob
import hashlib
import json
import os
from datetime import datetime


def canonico(obj):
    """Serialización canónica de un objeto (claves ordenadas) para que el hash sea estable."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))


def hash_obj(obj):
    """Hash `sha256:` de un objeto JSON-serializable, independiente del orden de las claves."""
    return "sha256:" + hashlib.sha256(canonico(obj).encode()).hexdigest()


def hash_archivo(ruta):
    """Hash `sha256:` de los bytes de un archivo; `sha256:falta` si no existe."""
    if not os.path.exists(ruta):
        return "sha256:falta"
    with open(ruta, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


def escribir(carpeta, artefacto, fuentes, metricas, nota=None):
    """Congela un artefacto aprobado: escribe `<carpeta>/estado.json` y devuelve su ruta.

    `fuentes` es {clave: hash}, `metricas` el nombre del archivo de métricas del gate y `nota` el
    motivo de una excepción (si hubo).
    """
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "estado.json")
    datos = {"artefacto": artefacto, "fuentes": fuentes, "metricas": metricas,
             "fecha": datetime.now().isoformat(timespec="seconds"), "aprobado_por": "usuario", "nota": nota}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta


def leer(carpeta):
    """Carga `<carpeta>/estado.json`, o `None` si el artefacto no está aprobado."""
    ruta = os.path.join(carpeta, "estado.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def deriva(estado_dict, fuentes):
    """Claves con hash distinto o ausentes de cualquiera de los dos lados (simétrico), ordenadas."""
    guardadas = estado_dict.get("fuentes", {})
    claves = set(guardadas) ^ set(fuentes)
    claves |= {k for k in guardadas.keys() & fuentes.keys() if guardadas[k] != fuentes[k]}
    return sorted(claves)


def listar(raiz):
    """Lista los artefactos aprobados bajo `raiz` (nombre, estilo, carpeta y estado), ordenados.

    Recorre `raiz/<nombre>/<estilo>/estado.json` o, para skins, `raiz/<nombre>/estado.json` (con estilo=None).
    """
    encontrados = []
    for patron in ("*/estado.json", "*/*/estado.json"):
        for ruta in glob.glob(os.path.join(raiz, patron)):
            carpeta = os.path.dirname(ruta)
            partes = os.path.relpath(carpeta, raiz).split(os.sep)
            datos = leer(carpeta)
            if datos is None:
                continue
            encontrados.append({"nombre": partes[0], "estilo": partes[1] if len(partes) > 1 else None,
                                "carpeta": carpeta, "estado": datos})
    return sorted(encontrados, key=lambda x: (x["nombre"], x["estilo"] or ""))
