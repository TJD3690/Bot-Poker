"""Análisis de la mesa (flop) y detección de proyectos, según FLOP.docx.

Los umbrales marcados como PROVISIONAL no están en el documento: validarlos con el equipo.
"""
from math import comb

PALOS = range(4)
RANGOS = range(2, 15)


def _hay_escalera(rangos):
    s = set(rangos)
    if 14 in s:
        s.add(1)
    return any(all(r in s for r in range(alto - 4, alto + 1)) for alto in range(5, 15))


def _hay_color(cartas):
    return any(sum(1 for c in cartas if c['palo'] == p) >= 5 for p in PALOS)


def analizar_mesa(mesa):
    """Los 5 datos que pide FLOP.docx sobre las cartas comunitarias del flop."""
    flop = mesa[:3]
    if len(flop) < 3:
        return None
    rangos = sorted(c['rango'] for c in flop)
    palos = max(sum(1 for c in flop if c['palo'] == p) for p in PALOS)
    bajo = sorted(1 if r == 14 else r for r in rangos)
    separacion = min(rangos[-1] - rangos[0], bajo[-1] - bajo[0])
    if separacion <= 4:        # PROVISIONAL
        conectividad = 'muy'
    elif separacion <= 6:      # PROVISIONAL
        conectividad = 'parcial'
    else:
        conectividad = 'poco'
    repetidas = max(rangos.count(r) for r in set(rangos))
    emparejada = {1: 'ninguna', 2: 'pareja', 3: 'trio'}[repetidas]
    color = palos == 3
    escalera = conectividad == 'muy' and len(set(rangos)) == 3
    amenazas = 'ambas' if color and escalera else 'color' if color else 'escalera' if escalera else 'ninguna'
    return {'palos_iguales': palos, 'conectividad': conectividad, 'emparejada': emparejada,
            'carta_alta': rangos[-1], 'amenazas': amenazas}


def prob_completar(outs):
    """Probabilidad de completar hasta el river con 'outs' cartas (tabla de FLOP.docx: 9 -> 35.0 %)."""
    if outs <= 0:
        return 0.0
    return 1 - comb(47 - outs, 2) / comb(47, 2)


def proyectos(cartas, mesa):
    """Proyectos de color, escalera y backdoor con 2 cartas propias y 3 de mesa."""
    vacio = {'color': False, 'escalera': None, 'backdoor': False, 'outs': 0, 'prob': 0.0}
    flop = mesa[:3]
    if len(cartas) != 2 or len(flop) < 3:
        return vacio
    conocidas = cartas + flop
    rangos = [c['rango'] for c in conocidas]
    if _hay_escalera(rangos) or _hay_color(conocidas):
        return vacio                      # ya está hecha: no es un proyecto
    por_palo = {p: [c for c in conocidas if c['palo'] == p] for p in PALOS}
    color = any(len(v) == 4 and any(c in cartas for c in v) for v in por_palo.values())
    backdoor = not color and any(len(v) == 3 and any(c in cartas for c in v) for v in por_palo.values())
    vistas = {(c['rango'], c['palo']) for c in conocidas}
    outs_total = outs_escalera = 0
    for r in RANGOS:
        for p in PALOS:
            if (r, p) in vistas:
                continue
            nueva = conocidas + [{'rango': r, 'palo': p}]
            hace_esc = _hay_escalera([c['rango'] for c in nueva])
            hace_col = _hay_color(nueva)
            outs_escalera += hace_esc
            outs_total += hace_esc or hace_col
    escalera = None if outs_escalera == 0 else ('abierta' if outs_escalera >= 8 else 'interna')
    return {'color': color, 'escalera': escalera, 'backdoor': backdoor,
            'outs': outs_total, 'prob': prob_completar(outs_total)}
