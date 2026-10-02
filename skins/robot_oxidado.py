import os, sys; sys.path.insert(0, os.getcwd())
from sprites_lib import skins
skins.desde_colores({
  "piel":"#9a9a90","pelo":"#6f6f66","remera":"#b45a2a","pantalon":"#5a5a55",
  "calzado":"#3a3a38","iris":"#ff5a2a","mangas":"cortas",
}, "skins/robot_oxidado.png")
print(skins.continuidad("skins/robot_oxidado.png"))
