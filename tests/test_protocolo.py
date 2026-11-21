"""Prueba end-to-end contra un servidor TCP simulado; no requiere Go."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]


def test_saludo_estado_turno_y_cierre():
    servidor = socket.socket()
    servidor.bind(('127.0.0.1', 0))
    servidor.listen(1)
    puerto = servidor.getsockname()[1]
    resultados = []
    estado = {
        'id_mano': 'prueba-1', 'etapa': 'river', 'pozo': 250,
        'apuesta_actual': 0, 'subida_minima': 100, 'ciega_grande': 100,
        'posicion_boton': 0, 'comunitarias': [
            {'rango':r, 'palo':0} for r in [2, 3, 5, 7, 9]],
        'jugadores':[{'id':'j-001','saldo':1000,'apuesta_ronda':0,'activo':True,
                     'en_mano':True,'en_torneo':True,'posicion_silla':0}],
        'historial_acciones': []}

    def simular():
        with servidor:
            c,_ = servidor.accept()
            with c, c.makefile('rb') as entrada:
                resultados.append(json.loads(entrada.readline()))
                def enviar(obj): c.sendall((json.dumps(obj)+'\n').encode())
                enviar({'tipo':'bienvenida','version':'1.0.0','id_jugador':'j-001','silla':0})
                enviar({'tipo':'mano_inicio','version':'1.0.0','cartas':[{'rango':14,'palo':1},{'rango':13,'palo':2}], 'estado':estado})
                enviar({'tipo':'estado','version':'1.0.0','estado':estado})
                enviar({'tipo':'solicitar_accion','version':'1.0.0','estado':estado,'acciones_validas':['fold','check','bet']})
                resultados.append(json.loads(entrada.readline()))
                enviar({'tipo':'mano_fin','version':'1.0.0','resultado':{'id_mano':'prueba-1'}})

    hilo = threading.Thread(target=simular, daemon=True)
    hilo.start()
    resultado = subprocess.run([sys.executable,str(ROOT/'bot.py'),'-addr',f'127.0.0.1:{puerto}','-token','demo'],
                               capture_output=True,text=True,timeout=6)
    hilo.join(timeout=2)
    assert resultado.returncode == 0, resultado.stderr
    assert len(resultados)==2
    assert resultados[0]=={'tipo':'saludo','version':'1.0.0','token':'demo'}
    assert resultados[1]=={'tipo':'accion','version':'1.0.0','id_mano':'prueba-1','accion':{'tipo':'check'}}
    assert 'demo' not in resultado.stderr  # token nunca se registra
