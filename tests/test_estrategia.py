"""Regresión del contrato legal y de las reglas documentadas (pytest)."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from estrategia import clase_mano, rango_color, evaluar, grupo_flop, textura, decidir, posicion


def c(r, p): return {'rango': r, 'palo': p}


def estado(etapa='preflop', p=3, historia=None, pozo=150, apuesta=100, saldo=10000, board=None):
    jugadores=[]
    for n in range(6):
        jugadores.append({'id': f'p{n}', 'posicion_silla':n, 'en_mano':True,
                          'activo':True, 'en_torneo':True, 'saldo':saldo,
                          'apuesta_ronda':100 if n == 2 and etapa=='preflop' else 0})
    return {'id_mano':'m1','etapa':etapa,'comunitarias':board or [],'pozo':pozo,
            'apuesta_actual':apuesta,'subida_minima':100,'ciega_chica':50,
            'ciega_grande':100,'posicion_boton':0,'jugadores':jugadores,
            'historial_acciones':historia or []}


def test_169_clases_y_orientacion():
    assert clase_mano([c(14,3),c(13,3)]) == 'AKs'
    assert clase_mano([c(13,1),c(14,3)]) == 'AKo'
    assert rango_color('UTG',[c(14,0),c(14,3)]) == 'G'
    assert rango_color('UTG',[c(7,0),c(2,2)]) == 'F'
    assert rango_color('UTG',[c(14,0),c(9,0)]) == 'Y'


def test_posiciones_seis():
    e=estado()
    assert [posicion(e,f'p{i}') for i in range(6)] == ['BTN','SB','BB','UTG','HJ','CO']


def test_apertura_premium_monto_total():
    e=estado()
    a=decidir(e,[c(14,1),c(14,3)],'p3',['fold','call','raise','allin'],random.Random(3))
    assert a['tipo']=='raise' and a['monto'] in (200,250)


def test_preflop_abierto_por_otro_no_usar_tabla_apertura():
    e=estado(historia=[{'id_jugador':'p4','etapa':'preflop','accion':{'tipo':'raise','monto':300}}],apuesta=300)
    a=decidir(e,[c(14,1),c(14,3)],'p3',['fold','call','raise','allin'],random.Random(3))
    assert a == {'tipo':'fold'}


def test_check_bb_gratis():
    e=estado()
    assert decidir(e,[c(7,1),c(2,3)],'p2',['fold','check','raise'],random.Random(3)) == {'tipo':'check'}


def test_ranking_y_ases_bajos():
    assert evaluar([c(14,1),c(2,3),c(3,0),c(4,1),c(5,3)])[:2] == (4,5)
    assert evaluar([c(14,0),c(14,1),c(14,2),c(14,3),c(5,1)])[0] == 7
    assert evaluar([c(2,0),c(3,0),c(4,0),c(5,0),c(14,0)])[0] == 8


def test_flop_grupos_y_textura():
    assert grupo_flop([c(8,0),c(8,1)],[c(8,2),c(13,3),c(2,1)]) == 'A2'
    assert grupo_flop([c(14,0),c(13,1)],[c(14,2),c(7,3),c(2,1)]) == 'B'
    assert textura([c(11,2),c(10,2),c(9,0)]) == 'conectado'
    assert textura([c(11,2),c(10,2),c(9,2)]) == 'monocolor'


def test_flop_apuesta_valida():
    e=estado('flop',pozo=600,apuesta=0,board=[c(8,2),c(13,3),c(2,1)])
    a=decidir(e,[c(8,0),c(8,1)],'p3',['fold','check','bet','allin'],random.Random(1))
    assert a['tipo'] in ('check','bet')
    if a['tipo']=='bet': assert a['monto']>=100


def test_fallback_turn_y_river():
    for stage in ('turn','river'):
        e=estado(stage,pozo=800,apuesta=0,board=[c(8,2),c(13,3),c(2,1),c(6,2),c(4,3)][:4 if stage=='turn' else 5])
        assert decidir(e,[c(14,0),c(9,1)],'p3',['fold','check','bet']) == {'tipo':'check'}


def test_all_actions_legal_in_randomized_states():
    validas=['fold','call','raise','allin']
    e=estado(apuesta=300,history=None) if False else estado(apuesta=300)
    for i in range(100):
        a=decidir(e,[c(14,0),c(14,1)],'p3',validas,random.Random(i))
        assert a['tipo'] in validas
        if a['tipo'] in ('bet','raise'):
            assert e['apuesta_actual']+e['subida_minima']<=a['monto']<=e['jugadores'][3]['saldo']
