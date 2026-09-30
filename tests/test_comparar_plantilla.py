import os

import pytest

from sprites_lib import comparar_plantilla as cp


@pytest.mark.skipif(not os.path.exists(cp.REF_HUESOS), reason="referencia LPC no descargada (referencias/ no se versiona)")
def test_caminar_lpc_sigue_a_la_referencia():
    r = cp.medir()
    texto = cp.resumen(r)
    assert r["ok"], texto
