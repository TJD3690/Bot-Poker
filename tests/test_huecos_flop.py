"""Pruebas del flop: análisis de mesa, proyectos y decisión ante apuesta con proyecto."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from estrategia import decidir, grupo_flop
from mesa import analizar_mesa, proyectos, prob_completar

VALIDAS = ['fold', 'call', 'raise', 'allin']
S, H, D, C = 0, 1, 2, 3   # picas, corazones, diamantes, tréboles


def c(r, p): return {'rango': r, 'palo': p}


def test_trio_en_mesa_sin_ser_nuestro_es_E():
    assert grupo_flop([c(2, S), c(3, H)], [c(13, S), c(13, H), c(13, D)]) == 'E'
    assert grupo_flop([c(13, C), c(3, H)], [c(13, S), c(13, H), c(13, D)]) == 'A1'   # póker propio


def test_analizar_mesa():
    m = analizar_mesa([c(13, S), c(12, S), c(11, S)])
    assert m == {'palos_iguales': 3, 'conectividad': 'muy', 'emparejada': 'ninguna',
                 'carta_alta': 13, 'amenazas': 'ambas'}
    m = analizar_mesa([c(13, S), c(13, H), c(2, D)])
    assert m['emparejada'] == 'pareja' and m['amenazas'] == 'ninguna' and m['conectividad'] == 'poco'
    assert analizar_mesa([c(9, S), c(9, H), c(9, D)])['emparejada'] == 'trio'
    assert analizar_mesa([c(14, S), c(2, H), c(4, D)])['conectividad'] == 'muy'   # rueda A-2-4


def test_probabilidades_de_la_tabla():
    assert abs(prob_completar(9) - .350) < .001
    assert abs(prob_completar(8) - .315) < .001
    assert abs(prob_completar(4) - .165) < .001


def test_proyecto_de_color():
    p = proyectos([c(14, S), c(13, S)], [c(12, S), c(7, S), c(2, D)])
    assert p['color'] and p['outs'] >= 9
    p = proyectos([c(14, S), c(13, S)], [c(12, S), c(7, D), c(2, H)])
    assert p['backdoor'] and not p['color']


def test_escalera_abierta_e_interna():
    p = proyectos([c(10, S), c(9, D)], [c(11, C), c(8, H), c(2, D)])
    assert p['escalera'] == 'abierta' and p['outs'] == 8
    p = proyectos([c(11, S), c(9, D)], [c(12, C), c(8, H), c(2, D)])
    assert p['escalera'] == 'interna' and p['outs'] == 4


def test_mano_hecha_no_es_proyecto():
    p = proyectos([c(10, S), c(9, D)], [c(11, C), c(8, H), c(7, D)])   # escalera hecha
    assert p['outs'] == 0 and p['escalera'] is None


def estado_flop(pozo, apuesta, mesa):
    jugadores = [{'id': f'p{n}', 'posicion_silla': n, 'en_mano': True, 'activo': True, 'en_torneo': True,
                  'saldo': 10000, 'apuesta_ronda': 0} for n in range(2)]
    return {'id_mano': 'm1', 'etapa': 'flop', 'comunitarias': mesa, 'pozo': pozo,
            'apuesta_actual': apuesta, 'subida_minima': 100, 'ciega_chica': 50, 'ciega_grande': 100,
            'posicion_boton': 0, 'jugadores': jugadores,
            'historial_acciones': [{'id_jugador': 'p1', 'etapa': 'flop', 'accion': {'tipo': 'bet', 'monto': apuesta}}]}


def test_proyecto_de_color_paga_apuesta_pequena_y_foldea_apuesta_grande():
    mano = [c(14, S), c(13, S)]
    mesa = [c(12, S), c(7, S), c(2, D)]
    # apuesta 200 sobre pozo previo 400: precio 25 % + 5 de margen < 35 %
    e = estado_flop(600, 200, mesa)
    assert decidir(e, mano, 'p0', VALIDAS, random.Random(1)) == {'tipo': 'call'}
    # apuesta de pozo completo (400 sobre 400): precio 33 % + 5 > 35 %
    e = estado_flop(800, 400, mesa)
    assert decidir(e, mano, 'p0', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_sin_proyecto_sigue_foldeando():
    mano = [c(14, S), c(9, H)]
    mesa = [c(12, D), c(7, S), c(2, D)]
    assert decidir(estado_flop(600, 200, mesa), mano, 'p0', VALIDAS, random.Random(1)) == {'tipo': 'fold'}
