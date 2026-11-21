"""Pruebas de los huecos de PREFLOP: apertura ajena, limp, BB, stack corto y varias subidas."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from estrategia import decidir, grupo_preflop, prob_apertura, tamano_por_bb

VALIDAS = ['fold', 'call', 'raise', 'allin']


def c(r, p): return {'rango': r, 'palo': p}


def estado(historia=None, apuesta=100, saldo=10000, activos=range(6)):
    jugadores = []
    for n in range(6):
        jugadores.append({'id': f'p{n}', 'posicion_silla': n, 'en_mano': n in activos,
                          'activo': n in activos, 'en_torneo': True, 'saldo': saldo,
                          'apuesta_ronda': 100 if n == 2 else 0})
    return {'id_mano': 'm1', 'etapa': 'preflop', 'comunitarias': [], 'pozo': 150,
            'apuesta_actual': apuesta, 'subida_minima': 100, 'ciega_chica': 50, 'ciega_grande': 100,
            'posicion_boton': 0, 'jugadores': jugadores, 'historial_acciones': historia or []}


def acc(pid, tipo, monto=None):
    a = {'tipo': tipo}
    if monto is not None: a['monto'] = monto
    return {'id_jugador': pid, 'etapa': 'preflop', 'accion': a}


def test_grupos():
    assert [grupo_preflop(x) for x in ('AA', 'AKo', 'TT', 'JTs', '55')] == ['A', 'B', 'C', 'D', 'E']


def test_probabilidad_limitada():
    assert prob_apertura('SB', 100) == .35
    assert abs(prob_apertura('SB', 30) - .25) < 1e-9
    assert .20 <= prob_apertura('SB', 30) <= .70


def test_tamano_por_bb():
    assert [tamano_por_bb(x) for x in (2, 3, 4, 5, 6)] == ['pequena', 'pequena', 'mediana', 'mediana', 'grande']


def test_apertura_ajena_A_sube_3x():
    e = estado([acc('p4', 'raise', 300)], apuesta=300)
    a = decidir(e, [c(14, 1), c(14, 3)], 'p3', VALIDAS, random.Random(1))
    assert a == {'tipo': 'raise', 'monto': 900}


def test_apertura_ajena_E_foldea():
    e = estado([acc('p4', 'raise', 300)], apuesta=300)
    assert decidir(e, [c(5, 1), c(5, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_apertura_ajena_B_grande_call_solo_un_rival_y_hasta_15bb():
    qq = [c(12, 1), c(12, 3)]
    e = estado([acc('p4', 'raise', 1000)], apuesta=1000, activos={3, 4})
    assert decidir(e, qq, 'p3', VALIDAS, random.Random(1)) == {'tipo': 'call'}
    e = estado([acc('p4', 'raise', 1600)], apuesta=1600, activos={3, 4})
    assert decidir(e, qq, 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}
    e = estado([acc('p4', 'raise', 1000)], apuesta=1000)   # 6 jugadores activos
    assert decidir(e, qq, 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_varias_subidas_solo_A_y_B():
    e = estado([acc('p4', 'raise', 300), acc('p5', 'raise', 900)], apuesta=900)
    assert decidir(e, [c(11, 1), c(11, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}   # JJ
    assert decidir(e, [c(14, 1), c(14, 3)], 'p3', VALIDAS, random.Random(1))['tipo'] in ('raise', 'call', 'allin')


def test_limp_mano_verde_sube_3bb_mas_1bb_por_limper():
    e = estado([acc('p4', 'call', 100), acc('p5', 'call', 100)])
    a = decidir(e, [c(14, 1), c(14, 3)], 'p3', ['fold', 'call', 'raise', 'allin'], random.Random(1))
    assert a == {'tipo': 'raise', 'monto': 500}


def test_limp_mano_gris_no_sube():
    e = estado([acc('p4', 'call', 100)])
    assert decidir(e, [c(7, 1), c(2, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_bb_con_limp_hace_check():
    e = estado([acc('p4', 'call', 100)])
    assert decidir(e, [c(14, 1), c(14, 3)], 'p2', ['fold', 'check', 'raise'], random.Random(1)) == {'tipo': 'check'}


def test_stack_corto_empuja_A_B_C_y_verdes():
    e = estado(saldo=1500)
    assert decidir(e, [c(14, 1), c(14, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'allin'}
    assert decidir(e, [c(7, 1), c(2, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_stack_corto_ante_allin_rival():
    e = estado([acc('p4', 'allin', 1500)], apuesta=1500, saldo=1500)
    assert decidir(e, [c(13, 1), c(13, 3)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'call'}
    assert decidir(e, [c(10, 1), c(9, 1)], 'p3', VALIDAS, random.Random(1)) == {'tipo': 'fold'}


def test_nunca_accion_ilegal():
    rng = random.Random(7)
    manos = [[c(rng.randint(2, 14), rng.randint(0, 3)), c(rng.randint(2, 14), rng.randint(0, 3))] for _ in range(300)]
    manos = [m for m in manos if (m[0]['rango'], m[0]['palo']) != (m[1]['rango'], m[1]['palo'])]
    for saldo in (900, 1500, 3000, 10000):
        for hist, ap in (([], 100), ([acc('p4', 'call', 100)], 100), ([acc('p4', 'raise', 300)], 300),
                         ([acc('p4', 'allin', saldo)], saldo)):
            e = estado(hist, apuesta=ap, saldo=saldo)
            for k, m in enumerate(manos):
                for pid in ('p0', 'p1', 'p3', 'p4', 'p5'):
                    a = decidir(e, m, pid, VALIDAS, random.Random(k))
                    assert a['tipo'] in VALIDAS
                    if a['tipo'] in ('bet', 'raise'):
                        yo = next(j for j in e['jugadores'] if j['id'] == pid)
                        assert ap + 100 <= a['monto'] <= yo['saldo'] + yo['apuesta_ronda']