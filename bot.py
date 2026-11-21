#!/usr/bin/env python3
"""Bot PokerFight v0.1. Cliente TCP/JSON Lines sin dependencias externas."""
import argparse
import json
import logging
import random
import socket
import sys
import time

from estrategia import decidir, accion_segura

VERSION = '1.0.0'
LOG = logging.getLogger('pokerfight')
ERROR_TRANSITORIO = 'demasiadas conexiones esperando el saludo'


class ErrorCredencial(RuntimeError):
    pass


class Cliente:
    def __init__(self, addr, token):
        self.host, puerto = addr.rsplit(':', 1)
        self.puerto = int(puerto)
        self.token = token
        self.socket = None
        self.entrada = None
        self.id_jugador = None

    def conectar(self):
        self.socket = socket.create_connection((self.host, self.puerto), timeout=5.0)
        self.socket.settimeout(None)  # Silencio entre rondas del torneo es normal.
        self.entrada = self.socket.makefile('r', encoding='utf-8', newline='\n')
        self.enviar({'tipo': 'saludo', 'version': VERSION, 'token': self.token})
        mensaje = self.recibir()
        if mensaje is None:
            raise ConnectionError('La arena cerró durante el saludo')
        if mensaje.get('tipo') == 'error':
            if mensaje.get('mensaje') == ERROR_TRANSITORIO:
                raise ConnectionError(ERROR_TRANSITORIO)
            raise ErrorCredencial('La arena rechazó el saludo: ' + str(mensaje.get('mensaje', '?')))
        if mensaje.get('tipo') != 'bienvenida':
            raise ConnectionError('Se esperaba bienvenida, llegó: ' + str(mensaje.get('tipo')))
        self.id_jugador = mensaje['id_jugador']
        LOG.info('Conectado: jugador=%s silla=%s', self.id_jugador, mensaje.get('silla'))

    def enviar(self, objeto):
        self.socket.sendall((json.dumps(objeto, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8'))

    def recibir(self):
        linea = self.entrada.readline()  # El socket puede seguir abierto sin datos entre rondas.
        if not linea:
            return None
        return json.loads(linea)

    def cerrar(self):
        if self.entrada is not None:
            try: self.entrada.close()
            except OSError: pass
        if self.socket is not None:
            try: self.socket.close()
            except OSError: pass
        self.entrada = None
        self.socket = None


def ejecutar(addr, token, reintentos=6):
    cliente = Cliente(addr, token)
    rng = random.Random()
    cartas = []
    mano_abierta = False
    intentos = 0
    while True:
        try:
            cliente.conectar()
            intentos = 0
            while True:
                m = cliente.recibir()
                if m is None:
                    if mano_abierta:
                        raise ConnectionError('Desconexión durante una mano')
                    LOG.info('La arena cerró la conexión; sesión terminada')
                    return 0
                tipo = m.get('tipo')
                if tipo == 'mano_inicio':
                    cartas = m.get('cartas') or []
                    mano_abierta = True
                elif tipo == 'mano_fin':
                    mano_abierta = False
                    cartas = []
                elif tipo == 'solicitar_accion':
                    estado = m.get('estado') or {}
                    validas = m.get('acciones_validas') or []
                    inicio = time.monotonic()
                    try:
                        accion = decidir(estado, cartas, cliente.id_jugador, validas, rng)
                        if accion.get('tipo') not in validas:
                            accion = accion_segura(validas)
                    except Exception:
                        LOG.exception('Fallo en estrategia; aplicando respaldo')
                        accion = accion_segura(validas)
                    cliente.enviar({'tipo': 'accion', 'version': VERSION,
                                   'id_mano': estado.get('id_mano', ''), 'accion': accion})
                    LOG.info('etapa=%s accion=%s ms=%.1f', estado.get('etapa'), accion,
                             (time.monotonic() - inicio) * 1000)
                elif tipo == 'error':
                    LOG.error('Error de arena: %s', m.get('mensaje'))
                    return 2
                # Los mensajes estado y los tipos nuevos son solo informativos.
        except ErrorCredencial as exc:
            LOG.error('%s', exc)
            return 2
        except (OSError, ConnectionError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
            intentos += 1
            if intentos > reintentos:
                LOG.error('Se agotaron los intentos de conexión: %s', exc)
                return 1
            espera = min(2.0, 0.15 * (2 ** (intentos - 1))) * (1 + rng.random() * .5)
            LOG.warning('Conexión interrumpida (%s); reintentando en %.1fs (%s/%s)',
                        type(exc).__name__, espera, intentos, reintentos)
            time.sleep(espera)
        finally:
            cliente.cerrar()


def main(argv=None):
    p = argparse.ArgumentParser(description='Bot PokerFight v0.1 (PREFLOP/FLOP)')
    p.add_argument('-addr', default='localhost:9000', help='servidor host:puerto')
    p.add_argument('-token', required=True, help='token asignado por la organización')
    p.add_argument('--reintentos', type=int, default=6, help='reintentos en desconexiones')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    return ejecutar(args.addr, args.token, args.reintentos)


if __name__ == '__main__':
    sys.exit(main())
