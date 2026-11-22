"""Política inicial PokerFight v0.1: PREFLOP/FLOP del equipo y respaldo provisional.

La política nunca da por supuesta una acción que no figure en acciones_validas.
Los rangos proceden de las matrices visuales del documento PREFLOT.
"""
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import random

from mesa import proyectos

RANGOS = json.loads(Path(__file__).with_name('rangos.json').read_text(encoding='utf-8'))['tablas']
ORDEN = 'AKQJT98765432'
FRECUENCIAS = {'UTG': .40, 'HJ': .45, 'CO': .50, 'BTN': .55, 'SB': .35, 'BB': .40}
PROB_MIN, PROB_MAX = .20, .70
MARGEN_PROYECTO = .05   # PROVISIONAL: colchón al pagar un proyecto con apuesta pendiente

def clase_mano(cartas):
    """De 2 cartas a AA, AKs, AKo, etc., sin importar el orden de entrada."""
    if len(cartas) != 2:
        return None
    ranks = sorted((int(c['rango']) for c in cartas), reverse=True)
    nombres = '23456789TJQKA'
    a, b = (nombres[r - 2] for r in ranks)
    if ranks[0] == ranks[1]:
        return a + b
    return a + b + ('s' if cartas[0]['palo'] == cartas[1]['palo'] else 'o')


def rango_color(posicion, cartas):
    """Verde G, amarillo Y y gris F. Maneja orientación de las 169 clases."""
    mano = clase_mano(cartas)
    if not mano or posicion not in RANGOS:
        return 'F'
    i, j = ORDEN.index(mano[0]), ORDEN.index(mano[1])
    # Encima de diagonal: suited. Debajo: offsuit.
    fila, columna = (min(i, j), max(i, j)) if mano.endswith('s') else (max(i, j), min(i, j))
    return RANGOS[posicion][fila][columna]


def obtener_yo(estado, id_jugador):
    return next((j for j in estado.get('jugadores', []) if j.get('id') == id_jugador), None)


def posicion(estado, id_jugador):
    """Deriva la posición a partir del botón y las sillas ocupadas en la mano."""
    jugadores = [p for p in estado.get('jugadores', []) if p.get('en_mano', p.get('activo', False))]
    if len(jugadores) < 2:
        return None
    boton = estado.get('posicion_boton')
    if not isinstance(boton, int):
        return None
    total_sillas = max(6, max((p.get('posicion_silla', 0) for p in jugadores), default=0) + 1)
    jugadores.sort(key=lambda p: (p.get('posicion_silla', 0) - boton) % total_sillas)
    ids = [p.get('id') for p in jugadores]
    if id_jugador not in ids:
        return None
    n = len(ids)
    # n=6: BTN,SB,BB,UTG,HJ,CO. En 5-max se omite HJ.
    etiquetas = {
        6: ['BTN', 'SB', 'BB', 'UTG', 'HJ', 'CO'],
        5: ['BTN', 'SB', 'BB', 'UTG', 'CO'],
        4: ['BTN', 'SB', 'BB', 'CO'],
        3: ['BTN', 'SB', 'BB'],
        2: ['BTN', 'BB'],
    }.get(n)
    if etiquetas is None:
        return None
    return etiquetas[ids.index(id_jugador)]


def accion_segura(validas):
    if 'check' in validas:
        return {'tipo': 'check'}
    if 'fold' in validas:
        return {'tipo': 'fold'}
    if 'call' in validas:
        return {'tipo': 'call'}
    return {'tipo': validas[0]} if validas else {'tipo': 'fold'}


def intentar_subir(estado, yo, validas, objetivo):
    pendiente = int(estado.get('apuesta_actual', 0)) > int(yo.get('apuesta_ronda', 0))
    tipo = 'raise' if pendiente else 'bet'
    tope = int(yo.get('saldo', 0)) + int(yo.get('apuesta_ronda', 0))
    minimo = int(estado.get('apuesta_actual', 0)) + int(estado.get('subida_minima', 0))
    if tipo not in validas or tope < minimo:
        return None
    # No convertir automáticamente una apuesta moderada en un all-in.
    objetivo = max(minimo, round(objetivo))
    if objetivo >= tope:
        return {'tipo': 'allin'} if 'allin' in validas else None
    return {'tipo': tipo, 'monto': objetivo}


def grupo_preflop(carta):
    """Grupo A-E de PREFLOT (sección 5.2) para una clase de mano como 'AKs'."""
    if carta in ('AA', 'KK'):
        return 'A'
    if carta in ('QQ', 'AKs', 'AKo'):
        return 'B'
    if carta in ('JJ', 'TT', 'AQs', 'AJs', 'KQs'):
        return 'C'
    if carta in ('99', '88', '77', '66', 'ATs', 'KJs', 'QJs', 'JTs', 'T9s', '98s', 'AJo', 'KQo'):
        return 'D'
    return 'E'


def prob_apertura(pos, saldo_bb):
    """P = limitar(P0(pos) + ajuste_fichas, 20 %, 70 %) de PREFLOT (sección 3.2)."""
    base = FRECUENCIAS[pos] - (.10 if saldo_bb <= 40 else 0)
    return min(PROB_MAX, max(PROB_MIN, base))


def tamano_por_relacion(r):
    """Tras nuestra apertura: R = apuesta rival / nuestra apertura (PREFLOT 5.1)."""
    return 'pequena' if r <= 2.5 else ('mediana' if r <= 4 else 'grande')


def tamano_por_bb(apuesta_en_bb):
    """Apertura ajena: se mide la apuesta rival en ciegas grandes."""
    return 'pequena' if apuesta_en_bb <= 3 else ('mediana' if apuesta_en_bb <= 5 else 'grande')


def pagar(validas):
    return {'tipo': 'call'} if 'call' in validas else accion_segura(validas)


def responder_subida(estado, yo, validas, grupo, tamano, factor, pos, allin_ajeno, headsup, efectivos, rival, bb):
    """Tabla 5.3 de PREFLOT. factor = multiplicador de la 4-bet (2.5) o de la subida ante apertura ajena (3)."""
    if grupo == 'A':
        if allin_ajeno:
            return pagar(validas)
        return intentar_subir(estado, yo, validas, rival * factor) or pagar(validas)
    if grupo == 'B':
        if allin_ajeno:
            return pagar(validas) if headsup and rival <= 20 * bb else accion_segura(validas)
        if tamano == 'pequena':
            return intentar_subir(estado, yo, validas, rival * factor) or pagar(validas)
        if tamano == 'mediana' or (headsup and rival <= 15 * bb):
            return pagar(validas)
    if grupo == 'C':
        if allin_ajeno:
            return pagar(validas) if headsup and rival <= 10 * bb else accion_segura(validas)
        if tamano == 'pequena' or (tamano == 'mediana' and headsup and rival <= 12 * bb and efectivos >= 40):
            return pagar(validas)
    if grupo == 'D' and not allin_ajeno and tamano == 'pequena' and pos in ('CO', 'BTN', 'BB') \
            and headsup and efectivos >= 40:
        return pagar(validas)
    return accion_segura(validas)


def corto_sin_subida(validas, grupo, color):
    """Stack de 20 BB o menos y nadie ha subido: all-in con A, B, C o mano verde."""
    if (grupo in ('A', 'B', 'C') or color == 'G') and 'allin' in validas:
        return {'tipo': 'allin'}
    return accion_segura(validas)


def corto_ante_subida(validas, grupo, allin_ajeno, headsup, rival, bb):
    """Stack de 20 BB o menos ante una subida ajena."""
    if allin_ajeno:
        if grupo in ('A', 'B') or (grupo == 'C' and headsup and rival <= 10 * bb):
            return pagar(validas)
        return accion_segura(validas)
    if grupo in ('A', 'B', 'C') and 'allin' in validas:
        return {'tipo': 'allin'}
    return accion_segura(validas)


def abrir_o_aislar(estado, yo, validas, rng, pos, color, saldo_bb, bb, limpers):
    """Apertura (limpers = 0) o aislamiento de limpers (3 BB + 1 BB por limper)."""
    if color == 'F':
        return accion_segura(validas)
    prob = 1.0 if color == 'G' else prob_apertura(pos, saldo_bb)
    if rng.random() > prob:
        return accion_segura(validas)
    if limpers:
        return intentar_subir(estado, yo, validas, (3 + limpers) * bb) or accion_segura(validas)
    opciones = {'UTG': ((2, .5), (2.5, .5)), 'HJ': ((2, .5), (2.5, .5)),
                'CO': ((2, .4), (2.5, .6)), 'BTN': ((2, .5), (2.5, .5)),
                'SB': ((2.5, .5), (3, .5))}.get(pos)
    if opciones is None:
        return accion_segura(validas)
    multiplicador = opciones[0][0] if rng.random() < opciones[0][1] else opciones[1][0]
    return intentar_subir(estado, yo, validas, multiplicador * bb) or accion_segura(validas)


def preflop(estado, yo, cartas, validas, rng, id_jugador):
    pos = posicion(estado, id_jugador)
    if pos is None:
        return accion_segura(validas)
    hist = [a for a in estado.get('historial_acciones', []) if a.get('etapa') == 'preflop']
    propias = [a for a in hist if a.get('id_jugador') == id_jugador]
    apertura_propia = next((a for a in propias if a.get('accion', {}).get('tipo') == 'raise'), None)
    ajenas = [a for a in hist if a.get('id_jugador') != id_jugador
              and a.get('accion', {}).get('tipo') in ('call', 'bet', 'raise', 'allin')]
    subidas = [a for a in ajenas if a['accion'].get('tipo') in ('bet', 'raise', 'allin')]
    limpers = {a.get('id_jugador') for a in ajenas if a['accion'].get('tipo') == 'call'}
    allin_ajeno = any(a['accion'].get('tipo') == 'allin' for a in ajenas)
    bb = max(1, int(estado.get('ciega_grande') or 100))
    saldo_bb = (int(yo.get('saldo', 0)) + int(yo.get('apuesta_ronda', 0))) / bb
    carta = clase_mano(cartas)
    grupo = grupo_preflop(carta)
    color = rango_color(pos, cartas)
    rival = int(estado.get('apuesta_actual', 0))
    n_activos = sum(bool(j.get('en_mano') and j.get('activo')) for j in estado.get('jugadores', []))
    headsup = n_activos == 2
    efectivos = min(int(yo.get('saldo', 0)) + int(yo.get('apuesta_ronda', 0)),
                    max((int(j.get('saldo', 0)) + int(j.get('apuesta_ronda', 0))
                         for j in estado.get('jugadores', [])
                         if j.get('id') != id_jugador and j.get('activo')), default=0)) / bb

    # Varias subidas ajenas: solo continúan A y B.
    if len(subidas) >= 2 and grupo not in ('A', 'B'):
        return accion_segura(validas)

    # 1) Defensa tras nuestra apertura.
    if apertura_propia and 'call' in validas:
        previa = int(apertura_propia['accion'].get('monto') or 0)
        tamano = tamano_por_relacion(rival / max(1, previa))
        return responder_subida(estado, yo, validas, grupo, tamano, 2.5, pos, allin_ajeno, headsup, efectivos, rival, bb)
    if apertura_propia:
        return accion_segura(validas)

    # 2) Apertura ajena antes de nuestra primera acción.
    if subidas:
        if saldo_bb <= 20:
            return corto_ante_subida(validas, grupo, allin_ajeno, headsup, rival, bb)
        return responder_subida(estado, yo, validas, grupo, tamano_por_bb(rival / bb), 3, pos,
                                allin_ajeno, headsup, efectivos, rival, bb)

    # 3) Ciega grande con check gratis.
    if pos == 'BB' and 'check' in validas:
        return {'tipo': 'check'}

    # 4) Stack corto sin subidas.
    if saldo_bb <= 20:
        return corto_sin_subida(validas, grupo, color)

    # 5) Limpers (aislar) o apertura normal.
    return abrir_o_aislar(estado, yo, validas, rng, pos, color, saldo_bb, bb, len(limpers))

def evaluar_cinco(cartas):
    """Retorna (categoría 0-8, desempates) para exactamente cinco cartas."""
    ranks = [int(c['rango']) for c in cartas]
    freq = Counter(ranks)
    counts = sorted(((v, k) for k, v in freq.items()), reverse=True)
    flush = len({c['palo'] for c in cartas}) == 1
    distintas = set(ranks)
    if 14 in distintas:
        distintas.add(1)
    escalera = max((v for v in range(5, 15) if set(range(v - 4, v + 1)) <= distintas), default=0)
    if flush and escalera:
        return (8, escalera)
    if counts[0][0] == 4:
        return (7, counts[0][1], counts[1][1])
    if counts[0][0] == 3 and counts[1][0] == 2:
        return (6, counts[0][1], counts[1][1])
    if flush:
        return (5, *sorted(ranks, reverse=True))
    if escalera:
        return (4, escalera)
    if counts[0][0] == 3:
        return (3, counts[0][1], *sorted((x for x in ranks if x != counts[0][1]), reverse=True))
    if counts[0][0] == 2 and counts[1][0] == 2:
        parejas = sorted((counts[0][1], counts[1][1]), reverse=True)
        return (2, *parejas, next(x for x in ranks if x not in parejas))
    if counts[0][0] == 2:
        pair = counts[0][1]
        return (1, pair, *sorted((x for x in ranks if x != pair), reverse=True))
    return (0, *sorted(ranks, reverse=True))


def evaluar(cartas):
    """Mejor combinación de 5 de 5-7 cartas."""
    return max(evaluar_cinco(p) for p in combinations(cartas, 5))


def grupo_flop(cartas, mesa):
    if len(cartas) != 2 or len(mesa) < 3:
        return 'E'
    score = evaluar(cartas + mesa[:3])[0]
    if score >= 6:
        return 'A1'
    if score == 3 and len({c['rango'] for c in mesa[:3]}) == 1:
        return 'E'   # el trío está en la mesa y no es nuestro
    if score >= 3:
        return 'A2'
    if score == 2:
        return 'B'
    propios = [c['rango'] for c in cartas]
    bordes = sorted((c['rango'] for c in mesa[:3]))
    if propios[0] == propios[1]:
        if propios[0] > bordes[-1]:
            return 'B'
        return 'D' if propios[0] < bordes[0] else 'C'
    parejas = set(propios) & set(bordes)
    if not parejas:
        return 'E'
    if max(parejas) == bordes[-1]:
        kicker = max((r for r in propios if r != bordes[-1]), default=0)
        return 'B' if kicker >= 10 else 'C'
    return 'D' if max(parejas) == bordes[0] else 'C'


def textura(mesa):
    cartas = mesa[:3]
    if len(cartas) < 3:
        return 'seco'
    ranks = sorted(c['rango'] for c in cartas)
    if len({c['palo'] for c in cartas}) == 1:
        return 'monocolor'
    if len(set(ranks)) < 3:
        return 'emparejado'
    if max(ranks) - min(ranks) <= 4:
        return 'conectado'
    return 'seco'


def flop(estado, yo, cartas, validas, rng):
    mesa = estado.get('comunitarias', [])
    grupo, board = grupo_flop(cartas, mesa), textura(mesa)
    seco = board == 'seco'
    pot = int(estado.get('pozo') or 0)
    pago = max(0, int(estado.get('apuesta_actual', 0)) - int(yo.get('apuesta_ronda', 0)))

    # No hay apuesta pendiente: frecuencias acordadas, tamaños según textura.
    if pago == 0:
        probs_seco = {'A1': .80, 'A2': .80, 'B': .70, 'C': .25, 'D': .10, 'E': .15}
        probs_otro = {'A1': .80, 'A2': .80, 'B': .50, 'C': .10, 'D': 0, 'E': 0}
        prob = (probs_seco if seco else probs_otro)[grupo]
        if rng.random() >= prob:
            return accion_segura(validas)
        fraccion = {'seco': .33, 'conectado': .60, 'emparejado': .50, 'monocolor': .50}[board]
        apuesta_ronda = int(yo.get('apuesta_ronda', 0))
        return intentar_subir(estado, yo, validas, apuesta_ronda + fraccion * pot) or accion_segura(validas)

    # Para primer bet de la calle, pozo antes de apuesta = pozo actual - monto bet.
    # En una cadena de raises es solo una aproximación y se usa fallback prudente.
    hist = [a for a in estado.get('historial_acciones', []) if a.get('etapa') == 'flop']
    apuestas = [a for a in hist if a.get('accion', {}).get('tipo') in ('bet', 'raise', 'allin')]
    if len(apuestas) != 1 or apuestas[0]['accion'].get('tipo') != 'bet':
        return accion_segura(validas)
    apuesta_rival = int(estado.get('apuesta_actual', 0))
    prepozo = max(1, pot - apuesta_rival)
    R = apuesta_rival / prepozo
    if grupo == 'A1':
        if R <= .75:
            return intentar_subir(estado, yo, validas, apuesta_rival + max(int(estado.get('subida_minima', 0)), .50 * pot)) or {'tipo':'call'} if 'call' in validas else accion_segura(validas)
        return {'tipo':'call'} if 'call' in validas else accion_segura(validas)
    if grupo == 'A2':
        if R <= 1.0 and 'call' in validas:
            return {'tipo':'call'}
    elif grupo == 'B':
        if (R <= .33 or (R <= .75 and seco)) and 'call' in validas:
            return {'tipo':'call'}
    elif grupo == 'C':
        if R <= .33 and seco and 'call' in validas:
            return {'tipo':'call'}
    # Proyecto (color/escalera): pagar si la probabilidad de completar supera el precio del pozo.
    proyecto = proyectos(cartas, mesa)
    if proyecto['outs'] and 'call' in validas:
        if proyecto['prob'] >= pago / (pot + pago) + MARGEN_PROYECTO:
            return {'tipo': 'call'}
    return accion_segura(validas)


def decidir(estado, cartas, id_jugador, validas, rng=None):
    """Devuelve dict acción; sin efectos laterales. TURN/RIVER siguen provisionales."""
    rng = rng or random.Random()
    validas = list(validas or [])
    estado = dict(estado)
    for campo in ('historial_acciones', 'comunitarias', 'jugadores'):
        if estado.get(campo) is None:   # la arena manda null cuando no hay datos
            estado[campo] = []
    yo = obtener_yo(estado, id_jugador)
    if yo is None or len(cartas) != 2:
        return accion_segura(validas)
    etapa = estado.get('etapa')
    if etapa == 'preflop':
        return preflop(estado, yo, cartas, validas, rng, id_jugador)
    if etapa == 'flop':
        return flop(estado, yo, cartas, validas, rng)
    # TURN/RIVER: política provisional conservadora hasta aprobar estrategia.
    if etapa in ('turn', 'river'):
        if 'check' in validas:
            return {'tipo': 'check'}
        # Con muy buenas combinaciones, pagar una apuesta pequeña.
        board = estado.get('comunitarias', [])
        score = evaluar(cartas + board)[0] if len(cartas + board) >= 5 else 0
        coste = max(0, int(estado.get('apuesta_actual', 0)) - int(yo.get('apuesta_ronda', 0)))
        if score >= 6 and 'call' in validas and coste <= int(estado.get('pozo', 0)):
            return {'tipo': 'call'}
    return accion_segura(validas)
