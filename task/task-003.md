# task-003 — Robot oxidado: detalle revertido por romper la costura

**Estado:** pendiente
**Origen:** revisión humana de las 10 skins del experimento con modelos free (2026-10-02).

## Problema

En `skins/robot_oxidado.py` el intento de óxido rompía la costura (`[('cabeza', 1)]`) y quedó la base
sin detalle.

## Fix propuesto

Repintar simétrico y regenerar.

## Criterio de aceptación

Detalle de óxido visible, costura correcta y tests del archivo en verde.
