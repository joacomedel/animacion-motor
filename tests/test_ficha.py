import copy

import pytest

from sprites_lib.componentes import Componente, registrar, REGISTRO
from sprites_lib.ficha import FichaInvalida, cargar, validar

if "_prueba_muneca" not in REGISTRO:
    @registrar
    class _PruebaMuneca(Componente):
        tipo = "_prueba_muneca"
        anclas_validas = ("muneca_derecha", "muneca_izquierda")
        estilos = ("stardew",)
        material_defecto = "piel"
        params_defecto = {"grosor": 1.0}

        def dibujar(self, esc, ctx, spec):
            pass

BASE = {
    "identidad": {"nombre": "Prueba", "concepto": "humano de prueba", "silueta_clave": "ninguna"},
    "cuerpo": {"base": "humano", "clase_altura": "adulto", "cabello": "corto"},
    "paleta": {"piel": {"base": "#c89070"}, "pelo": {"base": "#302018"}},
    "componentes": [{"tipo": "_prueba_muneca", "ancla": "muneca_derecha", "por_que": "prueba"}],
}


def f(**cambios):
    x = copy.deepcopy(BASE)
    for ruta, valor in cambios.items():
        d = x
        partes = ruta.split("__")
        for p in partes[:-1]:
            d = d[int(p)] if isinstance(d, list) else d[p]
        d[int(partes[-1]) if isinstance(d, list) else partes[-1]] = valor
    return x


def errores(ficha, **kw):
    return "\n".join(validar(ficha, **kw))


def test_ficha_valida():
    assert validar(BASE, estilos=["stardew"]) == []


def test_falta_seccion():
    x = copy.deepcopy(BASE); del x["paleta"]
    assert "falta la sección 'paleta'" in errores(x)


def test_ancla_mal_escrita_sugiere():
    e = errores(f(componentes__0__ancla="muneca_derecho"), estilos=["stardew"])
    assert "no existe" in e and "muneca_derecha" in e


def test_ancla_con_enie_sugiere():
    assert "muneca_derecha" in errores(f(componentes__0__ancla="muñeca_derecha"), estilos=["stardew"])


def test_componente_inexistente_sugiere():
    e = errores(f(componentes__0__tipo="_prueba_munecca"))
    assert "no existe" in e and "_prueba_muneca" in e


def test_ancla_no_valida_para_el_componente():
    assert "no se puede poner en 'cabeza'" in errores(f(componentes__0__ancla="cabeza"), estilos=["stardew"])


def test_accesorio_en_parte_ausente():
    x = f(cuerpo__ausentes=["antebrazo_derecho"])
    assert "está ausente" in errores(x, estilos=["stardew"])


def test_estilo_no_soportado():
    assert "no soporta el estilo 'lateral'" in errores(BASE, estilos=["lateral"])


def test_material_no_definido():
    assert "material 'oro' no está en la paleta" in errores(f(componentes__0__material="oro"), estilos=["stardew"])


def test_parametro_desconocido():
    e = errores(f(componentes__0__parametros={"grosro": 2}), estilos=["stardew"])
    assert "parámetro desconocido 'grosro'" in e and "grosor" in e


def test_color_invalido():
    assert "#rrggbb" in errores(f(paleta__piel={"base": "rosado"}), estilos=["stardew"])


def test_regla_desconocida():
    assert "regla desconocida" in errores(f(componentes__0__reglas=["visible_siempre"]), estilos=["stardew"])


def test_falta_por_que():
    x = copy.deepcopy(BASE); del x["componentes"][0]["por_que"]
    assert "falta 'por_que'" in errores(x, estilos=["stardew"])


def test_sustitucion_sin_componente():
    assert "no hay un componente" in errores(f(cuerpo__sustituciones={"brazo_derecho": "brazo_humano"}),
                                             estilos=["stardew"])


def test_excepcion_de_componente_inexistente():
    x = f(excepciones=[{"regla": "visible_si_ancla_visible", "componente": "pulsera", "direcciones": ["W"],
                        "motivo": "x"}])
    assert "excepción sobre 'pulsera'" in errores(x, estilos=["stardew"])


def test_falta_pelo_con_cabello_corto():
    x = copy.deepcopy(BASE); del x["paleta"]["pelo"]
    assert "falta 'pelo'" in errores(x, estilos=["stardew"])


def test_cargar_inexistente():
    with pytest.raises(FileNotFoundError, match="no existe la ficha"):
        cargar("nadie_se_llama_asi")


def test_cargar_yaml_mal_formado(tmp_path):
    ruta = tmp_path / "rota.yaml"
    ruta.write_text("identidad: [sin cerrar\n", encoding="utf-8")
    with pytest.raises(FichaInvalida, match="YAML mal formado"):
        cargar(str(ruta))
