"""Cinemática inversa de dos huesos (cadera→rodilla→tobillo, hombro→codo→mano)."""
import math


def ik(a, b, l1, l2, bend):
    """Articulación intermedia entre a y b en 2D (y hacia abajo).
    bend=+1 dobla hacia x+ (rodilla adelante), -1 hacia x- (codo atrás)."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    k = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0, l1 * l1 - k * k))
    ux, uy = dx / d, dy / d
    px, py = ax + ux * k, ay + uy * k
    c1 = (px - uy * h, py + ux * h)
    c2 = (px + uy * h, py - ux * h)
    return max(c1, c2, key=lambda c: c[0] * bend)
