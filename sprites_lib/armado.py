"""Armado: ficha → lista de componentes (cuerpo base + los de la ficha) → escena → cuadros renderizados."""
from dataclasses import dataclass

from .componentes import REGISTRO, Contexto
from .cuerpo import anatomia, anclas_ausentes, posar
from .escala import celda
from .estilos import ESTILOS, crear_camara
from .paleta import paleta_estilo
from .poses import POSES, ancho as anchura, cuadros
from .render3d import Escena

BASE_HUMANO = [("cabeza_humana", "cabeza"), ("ojos", "cara"), ("torso_humano", "torso"),
               ("brazo_humano", "brazo_izquierdo"), ("brazo_humano", "brazo_derecho"),
               ("pierna_humana", "pierna_izquierda"), ("pierna_humana", "pierna_derecha")]
# muñeco con skin (sprites_lib/skins.py): mismas piezas, el color sale del PNG de la skin
BASE_SKIN = [("cabeza_skin", "cabeza"), ("ojos", "cara"), ("torso_skin", "torso"),
             ("brazo_skin", "brazo_izquierdo"), ("brazo_skin", "brazo_derecho"),
             ("pierna_skin", "pierna_izquierda"), ("pierna_skin", "pierna_derecha")]


def _lista(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def expandir(ficha):
    """Specs finales, una por (tipo, ancla): cuerpo base (salvo sustituciones o componentes propios del mismo
    tipo y ancla) + componentes de la ficha. Cada spec lleva id, material, parámetros completos y pieza_base."""
    cu = ficha.get("cuerpo", {})
    propios = [{**c, "ancla": an} for c in ficha.get("componentes", []) for an in _lista(c["ancla"])]
    ocupadas = {(p["tipo"], p["ancla"]) for p in propios}
    sustituidas = set((cu.get("sustituciones") or {}).keys())
    base = []
    con_skin = cu.get("base") == "skin"
    for tipo, an in BASE_SKIN if con_skin else BASE_HUMANO:
        if an in sustituidas or (tipo, an) in ocupadas:
            continue
        b = {"tipo": tipo, "ancla": an}
        if tipo == "cabeza_humana":
            b["parametros"] = {"cabello": cu.get("cabello", "corto")}
        elif con_skin:
            b["parametros"] = {"iris": "iris"} if tipo == "ojos" else {"skin": cu["skin"]}
        base.append(b)
    specs = []
    for i, s in enumerate(base + propios):
        comp = REGISTRO[s["tipo"]]
        specs.append(dict(
            tipo=s["tipo"], ancla=s["ancla"], material=s.get("material") or comp.material_defecto,
            parametros={**comp.params_defecto, **(s.get("parametros") or {})},
            reglas=list(s.get("reglas") or []), id=f'{s["tipo"]}@{s["ancla"]}', pieza_base=(i + 1) * 10,
            por_que=s.get("por_que", ""),
        ))
    return specs


@dataclass
class Cuadro:
    img: object
    buf: dict
    anclas_px: dict
    specs: list
    mira: str
    pose: str
    indice: int
    cam: object
    anat: object
    escala: float
    bob: int


def render_cuadro(ficha, estilo, pose, p, mira, ancho=None):
    cu = ficha["cuerpo"]
    clase = cu.get("clase_altura", "adulto")
    anat = anatomia(estilo, clase, cu.get("complexion", "normal"))
    cam = crear_camara(estilo, mira, celda(estilo, clase, ancho or anchura(pose, estilo)))
    est = ESTILOS[estilo]
    pal = paleta_estilo(ficha["paleta"], est)
    ps = cuadros(pose)[p]
    if cu.get("brazo_activo") == "derecho" and "mano_b" in POSES[pose]:
        # animación asimétrica (golpear): el ciclo está escrito para el brazo izquierdo; se espeja el lado activo
        ps = {**ps, "mano_a": ps["mano_b"], "mano_b": ps["mano_a"], "pie_a": ps["pie_b"], "pie_b": ps["pie_a"],
              "ang_a": ps["ang_b"], "ang_b": ps["ang_a"]}
    a = posar(anat, ps, cam.cam_local, mira)
    aus = frozenset(anclas_ausentes(cu.get("ausentes")))
    esc = Escena(cam, pal)
    specs = expandir(ficha)
    for s in specs:
        ctx = Contexto(anat=anat, a=a, ps=ps, estilo=estilo, est=est, cam_local=cam.cam_local, paleta=pal,
                       mira=mira, ausentes=aus, pieza_base=s["pieza_base"], cuadro=ps["cuadro"])
        REGISTRO[s["tipo"]].dibujar(esc, ctx, s)
    img, buf = esc.render(estilo=est["render"], buffers=True)
    anclas_px = {k: tuple(float(x) for x in cam.proyectar(val)) for k, val in a.items()}
    return Cuadro(img=img, buf=buf, anclas_px=anclas_px, specs=specs, mira=mira, pose=pose, indice=p, cam=cam,
                  anat=anat, escala=anat.H / 28.0, bob=ps["bob"])


def render_todo(ficha, estilo, poses=("neutra", "quieto")):
    out = {}
    for pn in poses:
        for mira in ESTILOS[estilo]["direcciones"]:
            out[(pn, mira)] = [render_cuadro(ficha, estilo, pn, p, mira) for p in range(len(cuadros(pn)))]
    return out


FICHA_MINIMA = {"cuerpo": {"base": "humano", "clase_altura": "adulto", "complexion": "normal", "cabello": "calvo"},
                 "paleta": {"piel": {"base": "#f9d5ba"}}, "componentes": []}


def pivote(estilo, clase_altura="adulto", pose="quieto"):
    """Punto de los pies (piso) dentro de la celda: el mismo para cualquier pose/dirección/personaje de ese
    estilo (el ancla 'suelo' es el origen del mundo, no se mueve con la pose). Para el JSON de exportación."""
    f = {**FICHA_MINIMA, "cuerpo": {**FICHA_MINIMA["cuerpo"], "clase_altura": clase_altura}}
    mira = ESTILOS[estilo]["direcciones"][0]
    c = render_cuadro(f, estilo, pose, 0, mira)
    x, y, _ = c.anclas_px["suelo"]
    return round(x), round(y)
