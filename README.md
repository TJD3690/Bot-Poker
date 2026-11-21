# Bot-Poker — PokerFight v0.1

Primera versión del bot del equipo. Implementa el protocolo TCP/JSON Lines de PokerFight v1.0.0, **las decisiones PREFLOP/FLOP ya descritas por el equipo** y una política conservadora **provisional** para TURN/RIVER. No implementa aún Monte Carlo, aprendizaje de rivales ni optimización de torneo. No se ha validado frente a la arena Go real.

## Requisitos y ejecución

Python 3.10+ (sin dependencias para jugar). Usa un token de pruebas en local y el token privado asignado al equipo en el servidor oficial.

```bash
python3 bot.py -addr localhost:9000 -token bot-prueba
# o bien, con la IP:puerto que comunique la organización:
python3 bot.py -addr HOST:PUERTO -token TU_TOKEN
```

Para las pruebas unitarias: `python3 -m pip install pytest` y `python3 -m pytest -q`.

## Estructura

- `bot.py`: cliente TCP, intercambio JSON por línea, bienvenida, `id_jugador`, envío de acciones y reconexión limitada.
- `estrategia.py`: reglas de PREFLOP y FLOP, evaluador de combinaciones, posición, validación legal y fallback conservador.
- `rangos.json`: seis matrices PREFLOP digitalizadas de PREFLOT.pdf (G verde, Y amarillo, F gris), en orden `AKQJT98765432`.
- `tests/`: pruebas de las reglas y una prueba de protocolo contra un servidor TCP simulado.

## Estado de la estrategia

**PREFLOP:** apertura cuando nadie entró voluntariamente, por posición y matriz; manos amarillas según probabilidades textuales 40/45/50/55/35%; tamaños 2/2.5/3 BB. Defensa simplificada después de una apertura nuestra ante 3-bet. Ante apertura ajena antes de actuar, limp, stack ≤20 BB o reglas no especificadas, emplea fallback; no inventa una estrategia no acordada.

**FLOP:** clasifica fuerza A1/A2/B/C/D/E y textura seca/conectada/emparejada/monocolor. Si no existe apuesta, aplica frecuencias y tamaños acordados. Ante una **primera apuesta sencilla** sigue las condiciones propuestas. Ante cadenas de raises o all-in complejos, fallback. Las reglas A2 ante overbets son del documento y requieren revisión con equity.

**TURN/RIVER:** respaldo provisional, `check` si es legal; si hay apuesta pendiente, `call` solo para full house o superior y pago ≤ pozo; de lo contrario `fold`. Esta no es la estrategia final del equipo.

**LIMITACIONES CRÍTICAS:** Las matrices visuales se digitalizaron por color y necesitan revisión humana; el cómputo de posiciones en mesas reducidas es aproximado; el sistema NO interpreta aún todos los escenarios multijugador, pozos laterales ni las probabilidades de victoria. Nunca subir tokens reales.

## Pruebas realizadas

- 11 pruebas con pytest superadas, incluido un intercambio de saludo, estado, solicitud y acción por socket TCP simulado.
- **Pendiente:** compilar y ejecutar la arena real; el kit descargado usa `go 1.26.10`, no disponible en el entorno de validación offline.

## Fuente de las reglas

Documentos suministrados por el equipo: `Propuesta_Enfoque_Estrategia.pdf`, `PREFLOT.pdf` y `FLOP.pdf`. Contrato técnico: `docs/protocolo.md` del kit oficial [pokerfight-arena-participantes](https://github.com/aicspucp/pokerfight-arena-participantes). Reglas experimentales, no estrategias GTO demostradas.
