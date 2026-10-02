from sprites_lib import skins
skins.desde_colores({
  "piel":"#b87a4a","pelo":"#e8b020","remera":"#e08020","pantalon":"#7a4a20",
  "calzado":"#5a3a18","iris":"#ffd060","mangas":"cortas",
}, "skins/guerrero_solar.png")
print("continuidad:", skins.continuidad("skins/guerrero_solar.png"))
