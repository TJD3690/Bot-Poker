# PokerFight — Documentación inicial del bot

**Versión:** 0.1 (19/11/2026)  
**Estado:** diseño estratégico parcial; implementación y pruebas pendientes.

## Objetivo
Construir un bot autónomo para Texas Hold'em No-Limit que se conecte por TCP a la arena PokerFight, tome decisiones válidas antes del plazo y compita contra otros bots.

El repositorio privado fue inspeccionado el 19/11/2026: su rama principal contiene únicamente README.md y .gitignore. Todavía no se ha observado código propio del bot. Este documento **no afirma que exista una implementación**.

## Material del equipo
- **Propuesta_Enfoque_Estrategia.pdf:** seis capas: robustez, equity/pot odds, imprevisibilidad, lectura de rivales, calibración y adaptación al torneo.
- **PREFLOT.pdf:** matrices visuales de 169 clases de manos por posición; apertura verde/amarillo/gris, tamaños y defensa parcial ante 3-bet.
- **FLOP.pdf:** fuerza de manos A–E, proyectos, textura de mesa, frecuencias de apuesta y respuesta simplificada a apuestas.
- **Kit de la organización:** protocolo TCP/JSON Lines v1.0.0, bots de referencia y arena local.

Las reglas y porcentajes de los PDFs son **propuestas sin validación experimental**. El protocolo oficial prevalece sobre cualquier estrategia.

## ¿Podemos comenzar?
**Sí.** Conviene construir el cliente TCP, normalizador de estado y validador de jugadas mientras se completan las decisiones de PREFLOP, FLOP, TURN y RIVER. Para casos sin política definida se usa un respaldo conservador y legal. Eso mantiene el bot operativo, pero **no garantiza competitividad**.

## Arquitectura sugerida (no es el árbol actual del repositorio)
    bot.py                         Cliente TCP y ciclo de mensajes
    pokerfight/protocolo.py        Saludo, recepción JSON Lines, reconexión
    pokerfight/contexto.py         Estado normalizado y posición
    pokerfight/legales.py          Acciones válidas, montos, fallback
    pokerfight/estrategia/         preflop.py, flop.py, turn.py, river.py
    pokerfight/evaluacion/         Manos, proyectos y equity
    pokerfight/rivales/            Estadísticas por alias
    config/                        Rangos y parámetros versionados
    tests/                         Pruebas unitarias y de integración
    docs/                          Documentación del proyecto

## Prioridades
1. Conexión estable y respuesta legal en menos de 5 s.
2. Apertura PREFLOP según tablas digitalizadas, sin extrapolar a subidas ajenas.
3. Reglas de defensa PREFLOP y FLOP en situaciones especificadas.
4. Respaldo para TURN/RIVER y stack corto mientras se diseñan.
5. Simulaciones, medidas de rendimiento, equity y aprendizaje de rivales.

## Documentos
- [Estrategia y límites](01-ESTRATEGIA-ACTUAL.md)
- [Arquitectura y protocolo](02-ARQUITECTURA.md)
- [Roadmap y decisiones pendientes](03-ROADMAP-Y-DECISIONES.md)
- [Plan de pruebas](04-PRUEBAS.md)

## Colaboración
Mantener estrategias, comunicación y pruebas en módulos independientes. Cada ajuste debe quedar identificado con commit, motivo y resultados. No subir tokens reales a GitHub, ni siquiera en un repositorio privado.
