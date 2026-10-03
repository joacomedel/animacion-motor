"""Motor de sprites isométricos con volumen: muñeco 3D de primitivas "fotografiado" en pixel art.

Ejes LOCALES del personaje: f = adelante, l = izquierda del personaje, u = arriba (unidades ≈ px).
Ejes de MUNDO en el piso isométrico: a = sudeste, b = noreste, u = arriba.
La dirección a la que mira el personaje rota (f, l) dentro de (a, b); la cámara y la luz son fijas en el mundo,
así las 8 direcciones quedan iluminadas de forma coherente (como en un juego).

Flujo: Escena(camara) → primitivas (esfera, elipsoide, cápsula, faldón) con material y pieza → render().
El render hace z-buffer, 3 tonos por material según la luz, contorno interior (entre piezas y por salto de
profundidad), detalles de 1 px visibles y contorno exterior.
"""

import functools
import math

import numpy as np
from PIL import Image, ImageDraw

DIRECCIONES = {
    "SE": 0,
    "E": 45,
    "NE": 90,
    "N": 135,
    "NW": 180,
    "W": 225,
    "SW": 270,
    "S": 315,
}


def v(f, l, u):
    return np.array([f, l, u], float)


class Camara:
    def __init__(
        self,
        mira="SE",
        cw=56,
        ch=60,
        gx=26,
        gy=52,
        sc=0.78,
        uz=0.92,
        luz=(0.4, -0.45, 0.8),
    ):
        phi = math.radians(DIRECCIONES[mira] if isinstance(mira, str) else mira)
        self.c, self.s = math.cos(phi), math.sin(phi)
        self.cw, self.ch, self.gx, self.gy, self.sc, self.uz = cw, ch, gx, gy, sc, uz
        cam = np.array([1.0, -1.0, sc / uz])
        self.cam = cam / np.linalg.norm(cam)  # hacia la cámara (mundo)
        L = np.array(luz, float)
        self.luz = L / np.linalg.norm(L)  # hacia la luz (mundo)
        # vector "hacia la cámara" expresado en ejes locales (para ubicar detalles del lado visible)
        a, b, u = self.cam
        self.cam_local = np.array(
            [a * self.c + b * self.s, -a * self.s + b * self.c, u]
        )

    def a_mundo(self, p):
        p = np.asarray(p, float)
        f, l, u = p[..., 0], p[..., 1], p[..., 2]
        return np.stack([f * self.c - l * self.s, f * self.s + l * self.c, u], -1)

    def proyectar(self, p_local):
        w = self.a_mundo(p_local)
        a, b, u = w[..., 0], w[..., 1], w[..., 2]
        return (
            self.gx + self.sc * (a + b),
            self.gy + self.sc * 0.5 * (a - b) - self.uz * u,
            w @ self.cam,
        )


_D = 0.7071067811865476
DIRECCIONES_CENITAL = {
    "S": (0, 1),
    "E": (1, 0),
    "N": (0, -1),
    "W": (-1, 0),
    "SE": (_D, _D),
    "NE": (_D, -_D),
    "NW": (-_D, -_D),
    "SW": (-_D, _D),
}


class CamaraCenital:
    """Vista cenital 3/4 (top-down tipo Stardew Valley/Zelda): piso de grilla cuadrada, 4 direcciones.
    Mundo: X = este (derecha en pantalla), Y = sur (hacia la cámara), u = arriba."""

    def __init__(
        self,
        mira="S",
        cw=16,
        ch=32,
        gx=8,
        gy=29,
        ky=0.5,
        kz=0.92,
        luz=(-0.35, 0.55, 0.8),
    ):
        fx, fy = DIRECCIONES_CENITAL[mira]
        self.f = np.array([fx, fy], float)
        self.l = np.array([fy, -fx], float)  # izquierda del personaje
        self.cw, self.ch, self.gx, self.gy, self.ky, self.kz = cw, ch, gx, gy, ky, kz
        cam = np.array([0.0, kz, ky])
        self.cam = cam / np.linalg.norm(cam)
        L = np.array(luz, float)
        self.luz = L / np.linalg.norm(L)
        X, Y, u = self.cam
        self.cam_local = np.array(
            [X * self.f[0] + Y * self.f[1], X * self.l[0] + Y * self.l[1], u]
        )

    def a_mundo(self, p):
        p = np.asarray(p, float)
        f, l, u = p[..., 0], p[..., 1], p[..., 2]
        return np.stack(
            [f * self.f[0] + l * self.l[0], f * self.f[1] + l * self.l[1], u], -1
        )

    def proyectar(self, p_local):
        w = self.a_mundo(p_local)
        X, Y, u = w[..., 0], w[..., 1], w[..., 2]
        return self.gx + X, self.gy + self.ky * Y - self.kz * u, w @ self.cam


DIRECCIONES_LATERAL = ("E", "W")


class CamaraLateral(CamaraCenital):
    """Vista de costado ortográfica (plataformas): sin inclinación; x = adelante, y = −arriba.
    Es una cámara cenital con ky = 0: la profundidad es el eje sur (el lado derecho del personaje queda más
    cerca mirando al E)."""

    def __init__(
        self, mira="E", cw=40, ch=40, gx=20, gy=38, kz=1.0, luz=(-0.35, 0.55, 0.8)
    ):
        if mira not in DIRECCIONES_LATERAL:
            raise ValueError(f"la vista lateral solo admite E o W, no {mira!r}")
        super().__init__(mira, cw=cw, ch=ch, gx=gx, gy=gy, ky=0.0, kz=kz, luz=luz)


def _oscurecer(c, k):
    return tuple(int(v * k) for v in c)


def _snap_tonos(col, tonos):
    """Acerca cada color a uno de los 3 tonos del material (sombra/base/luz) para que el
    especular y la textura no introduzcan colores fuera de la paleta fija del estilo."""
    t = np.array(tonos, float)
    d = ((col[:, None, :] - t[None, :, :]) ** 2).sum(-1)
    return t[d.argmin(1)]


def _specular(N_mundo, luz, cam, especular, rugosidad):
    """Highlight especular: devuelve (N,) float con la intensidad del brillo.

    N_mundo: normal en ejes de mundo (N, 3) float.
    luz: vector hacia la luz (mundo).
    cam: vector hacia la cámara (mundo).
    especular: 0..1 (0 = sin brillo, 1 = brillo máximo).
    rugosidad: 0..1 (0 = espejo, 1 = difuso).
    """
    if especular <= 0:
        return np.zeros(N_mundo.shape[0])
    H = luz + cam
    H /= np.linalg.norm(H) + 1e-9
    N = N_mundo / (np.linalg.norm(N_mundo, axis=-1, keepdims=True) + 1e-9)
    spec = np.clip(N @ H, 0, 1) ** (1.0 - rugosidad * 0.95)
    return spec * especular


def _textura_mod(nombre, shape):
    """Modulación de textura: devuelve (shape) float en [0.85, 1.15] para modular el color.

    Patrones disponibles: 'ruido' (ruido suave), 'lineas' (líneas verticales), 'puntos' (trama de puntos).
    """
    import numpy as np

    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    if nombre == "ruido":
        rng = np.random.RandomState(42)
        return 1.0 + (rng.rand(h, w) - 0.5) * 0.3
    elif nombre == "lineas":
        return 1.0 + 0.15 * np.sin(xx * 0.8)
    elif nombre == "puntos":
        return 1.0 + 0.15 * ((xx + yy) % 2)
    return np.ones((h, w))


def _mover(a, dy, dx, relleno):
    """Desplaza un array sin "dar la vuelta" (np.roll mete el borde opuesto: los pies aparecían arriba)."""
    out = np.full_like(a, relleno)
    H, W = a.shape[:2]
    ys, yd = (
        (slice(0, H - dy), slice(dy, H))
        if dy >= 0
        else (slice(-dy, H), slice(0, H + dy))
    )
    xs, xd = (
        (slice(0, W - dx), slice(dx, W))
        if dx >= 0
        else (slice(-dx, W), slice(0, W + dx))
    )
    out[yd, xd] = a[ys, xs]
    return out


def _esfera_dirs(r, paso=0.3):
    return _dirs_n(max(8, int(2 * math.pi * r / paso)))


@functools.lru_cache(maxsize=None)
def _dirs_n(n):
    """Direcciones de una esfera con n meridianos. Cacheado (se pide miles de veces por hoja); solo lectura."""
    th, ph = np.meshgrid(
        np.linspace(0, math.pi, n // 2 + 1),
        np.linspace(0, 2 * math.pi, n, endpoint=False),
    )
    d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
    d.setflags(write=False)
    return d


class Escena:
    """Acumula puntos de superficie (posición, normal, material, pieza, componente) en ejes locales."""

    def __init__(self, camara, paleta):
        self.cam, self.pal = camara, paleta
        self.mats = list(paleta)
        self.P, self.Nn, self.M, self.K, self.C = [], [], [], [], []
        self.pieza = 0  # cambiarlo antes de agregar cada parte: da contorno entre piezas distintas
        self.componente = (
            ""  # qué componente de la ficha está dibujando (buffer de componente)
        )
        self.comp_nombres = [""]
        self.detalles = []  # (punto local, color RGB, componente) de 1 px

    def _cid(self):
        if self.componente not in self.comp_nombres:
            self.comp_nombres.append(self.componente)
        return self.comp_nombres.index(self.componente)

    def _mid(self, mat, shape):
        if isinstance(mat, str):
            return np.full(shape, self.mats.index(mat))
        nombres = np.asarray(mat)
        out = np.zeros(nombres.shape, int)
        for nm in np.unique(nombres):
            out[nombres == nm] = self.mats.index(nm)
        return out

    def _add(self, pts, nrm, mat, mascara=None):
        pts, nrm = pts.reshape(-1, 3), nrm.reshape(-1, 3)
        m = (
            self._mid(mat, pts.shape[:1])
            if isinstance(mat, str)
            else self._mid(mat, None).reshape(-1)
        )
        if mascara is not None:
            k = np.asarray(mascara, bool).reshape(-1)
            pts, nrm, m = pts[k], nrm[k], m[k]
        self.P.append(pts)
        self.Nn.append(nrm)
        self.M.append(m)
        self.K.append(np.full(len(pts), self.pieza))
        self.C.append(np.full(len(pts), self._cid()))

    # -------------------------------------------------------------- primitivas
    def esfera(self, c, r, mat, conservar=None):
        """mat: nombre, o función(dirs)->array de nombres. conservar(dirs)->bool deja solo una parte."""
        d = _esfera_dirs(r)
        self._add(
            np.asarray(c) + r * d,
            d,
            mat if isinstance(mat, str) else mat(d),
            None if conservar is None else conservar(d),
        )

    def elipsoide(self, c, radios, mat, conservar=None):
        radios = np.asarray(radios, float)
        d = _esfera_dirs(radios.max())
        nrm = d / radios
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._add(
            np.asarray(c) + d * radios,
            nrm,
            mat if isinstance(mat, str) else mat(d),
            None if conservar is None else conservar(d),
        )

    def caja(self, c, radios, mat, n=3.0, conservar=None, giro=0.0):
        """Superelipsoide: n=2 es un elipsoide; n=3-4 es una caja redondeada. Las siluetas con lados rectos se
        leen como dibujadas a mano; las esferas perfectas "gritan 3D"."""
        radios = np.asarray(radios, float)
        d = _esfera_dirs(radios.max())
        q = np.sign(d) * np.abs(d) ** (2.0 / n)
        nrm = np.sign(d) * np.abs(d) ** (2.0 - 2.0 / n) / radios
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9
        pts = q * radios
        if giro:  # gira la caja alrededor de la vertical; el material sigue viendo la dirección real (d girada)
            cs, sn = math.cos(giro), math.sin(giro)
            R = np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1.0]])
            pts, nrm, d = pts @ R.T, nrm @ R.T, d @ R.T
        self._add(
            np.asarray(c) + pts,
            nrm,
            mat if isinstance(mat, str) else mat(d),
            None if conservar is None else conservar(d),
        )

    def capsula(self, a, b, r, mat, tapas=True):
        """mat: nombre, o función(dirs, t)->array de nombres (t∈[0,1] de a hacia b; las tapas usan t=0 y t=1)."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        ax = b - a
        L = np.linalg.norm(ax) + 1e-9
        ax /= L
        e1 = np.cross(ax, [0, 0, 1.0])
        if np.linalg.norm(e1) < 1e-3:
            e1 = np.cross(ax, [1.0, 0, 0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(ax, e1)
        t, ang = np.meshgrid(
            np.linspace(0, L, int(L / 0.3) + 2),
            np.linspace(
                0, 2 * math.pi, max(8, int(2 * math.pi * r / 0.3)), endpoint=False
            ),
        )
        d = np.cos(ang)[..., None] * e1 + np.sin(ang)[..., None] * e2
        self._add(
            a + t[..., None] * ax + r * d,
            d,
            mat if isinstance(mat, str) else mat(d, t / L),
        )
        if tapas:
            if isinstance(mat, str):
                self.esfera(a, r, mat)
                self.esfera(b, r, mat)
            else:
                self.esfera(a, r, lambda dd: mat(dd, np.zeros(dd.shape[:-1])))
                self.esfera(b, r, lambda dd: mat(dd, np.ones(dd.shape[:-1])))

    def faldon(
        self,
        arriba,
        abajo,
        r1,
        r2,
        mat,
        conservar=lambda d: d[..., 0] < 0.35,
        recorte=None,
    ):
        """Tronco de cono (túnica, capa, falda). conservar(dirs) decide qué ángulos existen (por defecto abierto
        adelante); recorte(dirs, t) saca partes según la altura t∈[0,1] (jirones, dobladillo irregular)."""
        arriba, abajo = np.asarray(arriba, float), np.asarray(abajo, float)
        t, ang = np.meshgrid(
            np.linspace(0, 1, 26), np.linspace(0, 2 * math.pi, 64, endpoint=False)
        )
        d = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], -1)
        c = arriba + t[..., None] * (abajo - arriba)
        r = (r1 + (r2 - r1) * t)[..., None]
        m = np.asarray(conservar(d), bool)
        if recorte is not None:
            m = m & np.asarray(recorte(d, t), bool)
        nrm = d + np.array([0, 0, 0.35])
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        mats = (
            mat if isinstance(mat, str) else mat(d, t)[m]
        )  # mat(d, t): pliegues por ángulo/altura
        self._add((c + r * d)[m], nrm[m], mats)

    def detalle(self, p, col):
        self._cid()  # un componente que solo aporta detalles también existe en el buffer
        self.detalles.append(
            (np.asarray(p, float), tuple(int(x) for x in col), self.componente)
        )

    # -------------------------------------------------------------- render
    def render(
        self,
        contorno=(16, 10, 24),
        salto=3.2,
        salto_pieza=0.8,
        estilo=None,
        buffers=False,
    ):
        """estilo (ver sprites_lib/estilos.py): umbrales de tonos, contorno 'negro'|'color'
        (el tono más oscuro del material vecino), interior 'negro'|'color'|'ninguno', sombreado 'luz'|'borde'.
        buffers=True devuelve además (depth, mat, pieza, comp, solido, normal, lam, comp_nombres,
        colores_detalle). normal: RGB (ch, cw, 3) uint8 con la normal en ejes de mundo [-1,1] -> [0,255],
        misma dimensión y alineación que el PNG; lam: (ch, cw) float con N·luz clippeado a [0,1]."""
        est = dict(
            umbrales=(0.28, 0.66),
            contorno="negro",
            interior="negro",
            oscurecer=0.55,
            sombreado="luz",
        )
        est.update(estilo or {})
        cw, ch = self.cam.cw, self.cam.ch
        depth = np.full((ch, cw), -1e9)
        mat = np.full((ch, cw), -1)
        pieza = np.full((ch, cw), -1)
        comp = np.full((ch, cw), -1)
        lam = np.zeros((ch, cw))
        normal = np.zeros((ch, cw, 3), np.uint8)
        img = np.zeros((ch, cw, 4), np.uint8)
        colores_detalle = set()
        if self.P:
            P = np.concatenate(self.P)
            Nn = np.concatenate(self.Nn)
            M = np.concatenate(self.M)
            K = np.concatenate(self.K)
            C = np.concatenate(self.C)
            x, y, d = self.cam.proyectar(P)
            xi, yi = np.round(x).astype(int), np.round(y).astype(int)
            ok = (xi >= 0) & (xi < cw) & (yi >= 0) & (yi < ch)
            xi, yi, d, Nn, M, K, C = (arr[ok] for arr in (xi, yi, d, Nn, M, K, C))
            o = np.argsort(
                d, kind="stable"
            )  # lo más cercano a cámara queda último y gana
            xi, yi, d, Nn, M, K, C = (arr[o] for arr in (xi, yi, d, Nn, M, K, C))
            depth[yi, xi] = d
            mat[yi, xi] = M
            pieza[yi, xi] = K
            comp[yi, xi] = C
            N_mundo = self.cam.a_mundo(Nn)
            lam[yi, xi] = np.clip(N_mundo @ self.cam.luz, 0, 1)
            normal[yi, xi] = ((N_mundo + 1) * 127.5).astype(np.uint8)
        nivel = None
        if est["sombreado"] == "borde":
            # como lo haría un artista: tono base plano; luz en el borde superior/izquierdo de cada pieza y
            # sombra en el inferior/derecho (y donde la luz real es muy baja)
            nivel = np.ones((ch, cw), int)
            distinto = lambda dy, dx: _mover(pieza, dy, dx, -1) != pieza
            luz_b = distinto(1, 0) | distinto(
                0, 1
            )  # vecino de arriba o de la izquierda es otra pieza
            som_b = distinto(-1, 0) | distinto(0, -1)
            nivel[luz_b & ~som_b] = 2
            nivel[som_b & ~luz_b] = 0
            nivel[lam < est["umbrales"][0]] = 0
        u1, u2 = est["umbrales"]
        for k, nm in enumerate(self.mats):
            tonos = self.pal[nm]
            mat_obj = self.pal[nm] if hasattr(self.pal[nm], "especular") else None
            especular = getattr(mat_obj, "especular", 0.0) if mat_obj else 0.0
            transmision = getattr(mat_obj, "transmision", 0.0) if mat_obj else 0.0
            textura = getattr(mat_obj, "textura", None) if mat_obj else None
            rugosidad = getattr(mat_obj, "rugosidad", 0.5) if mat_obj else 0.5
            spec_img = None
            if especular > 0:
                spec = _specular(
                    N_mundo, self.cam.luz, self.cam.cam, especular, rugosidad
                )
                spec_img = np.zeros((ch, cw))
                spec_img[yi, xi] = spec
            if nivel is not None:
                for lvl in range(3):
                    mask = (mat == k) & (nivel == lvl)
                    n = int(mask.sum())
                    if n == 0:
                        continue
                    col = np.tile(np.array(tonos[lvl], float), (n, 1))
                    if textura:
                        col = col * _textura_mod(textura, mask.shape)[mask][:, None]
                    if spec_img is not None:
                        col = col + spec_img[mask][:, None] * 255
                    if textura or spec_img is not None:
                        col = _snap_tonos(col, tonos)
                    col = np.clip(col, 0, 255).astype(np.uint8)
                    alpha = int(255 * (1.0 - transmision))
                    img[mask] = np.column_stack([col, np.full(n, alpha)])
                continue
            for lvl, (lo, hi) in enumerate(((-1, u1), (u1, u2), (u2, 2))):
                mask = (mat == k) & (lam > lo) & (lam <= hi)
                n = int(mask.sum())
                if n == 0:
                    continue
                col = np.tile(np.array(tonos[lvl], float), (n, 1))
                if textura:
                    col = col * _textura_mod(textura, mask.shape)[mask][:, None]
                if spec_img is not None:
                    col = col + spec_img[mask][:, None] * 255
                if textura or spec_img is not None:
                    col = _snap_tonos(col, tonos)
                col = np.clip(col, 0, 255).astype(np.uint8)
                alpha = int(255 * (1.0 - transmision))
                img[mask] = np.column_stack([col, np.full(n, alpha)])
        solido = mat >= 0
        interior = np.zeros_like(solido)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nd = _mover(depth, dy, dx, -1e9)
            npz = _mover(pieza, dy, dx, -1)
            interior |= solido & (nd - depth > salto)
            interior |= (
                solido & (npz >= 0) & (npz != pieza) & (nd - depth > salto_pieza)
            )
        if est["interior"] == "negro":
            img[interior] = (*contorno, 255)
        elif (
            est["interior"] == "color"
        ):  # línea con el tono oscuro de la pieza de atrás
            for k, nm in enumerate(self.mats):
                img[interior & (mat == k)] = (*_oscurecer(self.pal[nm][0], 0.8), 255)
        for p, col, cn in self.detalles:
            px, py, pd = self.cam.proyectar(p)
            ix, iy = int(round(float(px))), int(round(float(py)))
            if (
                0 <= ix < cw
                and 0 <= iy < ch
                and solido[iy, ix]
                and pd >= depth[iy, ix] - 1.3
            ):
                img[iy, ix] = (*col, 255)
                comp[iy, ix] = (
                    self.comp_nombres.index(cn)
                    if cn in self.comp_nombres
                    else comp[iy, ix]
                )
                colores_detalle.add(col)
        grow = solido.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            grow |= _mover(solido, dy, dx, False)
        anillo = grow & ~solido
        if (
            est["contorno"] == "color"
        ):  # "selout": cada borde toma el tono oscuro de su material
            vecino = np.full(mat.shape, -1)
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nm_ = _mover(mat, dy, dx, -1)
                vecino = np.where((vecino < 0) & (nm_ >= 0), nm_, vecino)
            for k, nm in enumerate(self.mats):
                img[anillo & (vecino == k)] = (
                    *_oscurecer(self.pal[nm][0], est["oscurecer"]),
                    255,
                )
        else:
            img[anillo] = (*contorno, 255)
        im = Image.fromarray(img, "RGBA")
        if not buffers:
            return im
        return im, dict(
            depth=depth,
            mat=mat,
            pieza=pieza,
            comp=comp,
            solido=solido,
            normal=normal,
            lam=lam,
            comp_nombres=list(self.comp_nombres),
            colores_detalle=colores_detalle,
        )


def ik_sagital(a, b, l1, l2, doblez):
    """IK en el plano (adelante, arriba) del personaje; l se conserva. doblez=+1 rodilla, -1 codo."""
    from .rig import ik

    k = ik((a[0], -a[2]), (b[0], -b[2]), l1, l2, doblez)
    return v(k[0], a[1], -k[1])


def ik_3d(a, b, l1, l2, polo):
    """IK de dos huesos en 3D: la articulación intermedia se dobla hacia 'polo' (p. ej. (1,0,0) rodilla adelante,
    (-1,0,0) codo atrás). A diferencia de ik_sagital, respeta desplazamientos laterales (brazos abiertos)."""
    a, b, polo = np.asarray(a, float), np.asarray(b, float), np.asarray(polo, float)
    eje = b - a
    dist = max(1e-9, float(np.linalg.norm(eje)))
    u = eje / dist
    d = max(1e-3, min(dist, l1 + l2 - 1e-3))
    k = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - k * k))
    p = polo - (polo @ u) * u
    n = np.linalg.norm(p)
    p = p / n if n > 1e-9 else np.array([0.0, 0.0, 0.0])
    return a + u * k + p * h


def sombra(camara, rx=10.0, ry=4.6, col=(10, 8, 18, 210)):
    """Sombra 2:1 con dithering bajo el punto de apoyo."""
    cw, ch = camara.cw, camara.ch
    yy, xx = np.mgrid[0:ch, 0:cw]
    m = (((xx - camara.gx) / rx) ** 2 + ((yy - camara.gy) / ry) ** 2 <= 1) & (
        (xx + yy) % 2 == 0
    )
    a = np.zeros((ch, cw, 4), np.uint8)
    a[m] = col
    return Image.fromarray(a, "RGBA")


def piso_iso(w, h, desplazamiento=0.0, direccion="SE"):
    """Piso de baldosas 32x16 que se desplaza en la dirección de avance (para GIF de escena)."""
    im = Image.new("RGB", (w, h), (28, 26, 40))
    d = ImageDraw.Draw(im)
    phi = math.radians(DIRECCIONES[direccion])
    a, b = math.cos(phi) * desplazamiento, math.sin(phi) * desplazamiento
    ox, oy = -(a + b) * 1.0 % 32, -(a - b) * 0.5 % 16
    for j in range(-2, h // 8 + 3):
        for i in range(-2, w // 32 + 3):
            cx = i * 32 + (j % 2) * 16 + ox
            cy = j * 8 + oy
            col = (44, 40, 64) if (i + j) % 2 else (38, 34, 56)
            d.polygon(
                [(cx, cy - 8), (cx + 16, cy), (cx, cy + 8), (cx - 16, cy)],
                fill=col,
                outline=(56, 52, 80),
            )
    return im
