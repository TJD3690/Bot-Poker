# Cómo funcionan los bots competitivos de póker y qué conviene implementar en PokerFight

**Estado:** investigación técnica al 21/11/2026. No es implementación completada. **Alcance:** seis jugadores No-Limit Hold'em, conexión TCP, 5 segundos por decisión.

## 1. Familias de bots: mecanismos y trade-offs

| Enfoque | Qué calcula realmente | Ventajas | Riesgos para la hackathon |
|---|---|---|---|
| Reglas y tablas | Umbrales por posición, mano, apuestas | Muy rápido; explicable; reproducible | Predecible, no generaliza |
| Monte Carlo / equity | Frecuencia de victoria/empate frente a manos y runouts muestreados | Adaptable a calle y #rivales | Sesgo si muestra rangos poco realistas |
| Modelado de rivales | Priors + estadísticas de VPIP, PFR, fold, agresión; actualiza rangos | Puede explotar hábitos | Pocas muestras, etiquetas falsas |
| Bandido multibrazo / UCB1 | Compara estilos según recompensa observada | Selección adaptativa sencilla | Mucho ruido en premios de póker |
| Algoritmos genéticos | Ajusta parámetros de una política con muchos torneos | No exige gradientes | Sobreajuste a bots conocidos |
| CFR / MCCFR / Deep CFR | Minimiza regret en juego de información imperfecta, normalmente con abstracciones | Estrategias mezcladas más equilibradas | Entrenamiento caro y adaptación compleja |
| Blueprint + re-solving | Política offline base, afinada con búsqueda desde estado actual | Alto potencial competitivo | Gran complejidad y tiempo de ejecución |

El kit de PokerFight trae `novato`, `estadistico`, `espia`, `bandido`, `darwin`, además de `aleatorio`, `conservador` y `base`. Son referencias útiles para comparar **algoritmos**, pero no sustituyen la validación con mesas 5–6 jugadores.

## 2. Qué hacen los sistemas de investigación

### Pluribus (Brown y Sandholm, 2019)
Desarrollado para **seis jugadores**. Calcula una política **blueprint** por autojuego y aplica búsqueda de mayor resolución durante las partidas. Al explorar continuaciones, considera varios estilos posibles de sus rivales en lugar de suponer una única política fija. Meta indica que Pluribus **no** explotaba en línea las tendencias individuales observadas de sus oponentes; no confundir su metodología con el enfoque explotativo que proponemos para nuestro equipo.

**Aplicación práctica:** política base sólida + búsquedas/ajustes puntuales, pero no intentar reproducir entrenamiento a gran escala durante las 5 s por jugada.

### DeepStack (Moravčík y colaboradores, 2017)
Diseñado para **heads-up** (dos jugadores). Utiliza re-solving continuo con evaluación de posiciones futuras. Su arquitectura muestra el valor de combinar abstracción, evaluación de estado y búsqueda, pero los resultados **no se transfieren directamente** a mesas de seis.

### SHARINGAN-2 (descripción pública actualizada 05/11/2026)
Proyecto de IA abierto para **seis jugadores**, con blueprint MCCFR y búsqueda opcional en TURN/RIVER, código Rust y pesos públicos. La documentación del proyecto afirma que el entrenamiento fue enorme; verificar licencia y requisitos de integración antes de reutilizarlo. Su descripción constituye evidencia de una arquitectura contemporánea, **no prueba que sea el mejor bot para PokerFight ni que su infraestructura pueda usarse dentro de 5 segundos**.

## 3. Propuesta concreta de arquitectura incremental

### V0.1 — base implementada
- TCP/JSON Lines 1.0.0, acciones legales, estrategia PREFLOP/FLOP parcial.
- Evaluador exacto de combinaciones, fallback provisional TURN/RIVER.
- Tests unitarios y prueba TCP simulada.

### V0.2 — implementar antes de sofisticar IA
- Resolver PREFLOP faltante (defensa frente apertura ajena, BB y stack ≤20 BB).
- Terminar política base TURN/RIVER y casos multiway.
- Reproducir rangos en datos verificables y parámetros en configuración.
- Añadir batería de estados adversarios, replayer y métricas por mano.

### V0.3 — matemática bien implementada
- Monte Carlo para flop/turn, con mazo sin cartas conocidas.
- Equidad exacta en river contra **rangos ponderados**.
- Pot odds, SPR y un pequeño menú de acciones legalmente realizables.
- Benchmarks con presupuesto configurable (`timeout_ms` menos margen), caché y semilla de RNG para repetir experimentos.

### V0.4 — adaptación
- Estadísticas por alias del torneo; almacenar únicamente datos visibles o de showdown.
- Suavizado bayesiano (`Beta`-`Binomial` para probabilidades de fold, ejemplo) y tamaño mínimo de muestra.
- Multiplicadores de riesgo acotados: si pocos datos, volver a política base.
- Clasificación de rivales y pruebas A/B por perfil.

### V0.5 — calibración y teoría de juegos (opcional)
- Entrenar offline tamaños de apuesta, rangos y mezcla de acciones contra ligas diversas de bots.
- Estudiar MCCFR/solvers de forma aislada; no mezclar políticas de otras arenas sin adaptar cartas, rondas, side pots y escala de apuestas.
- Mantener una versión estable anterior y pruebas de regresión para evitar empeorar.

## 4. Diseño de experimento recomendado

**Control de calidad primero:** objetivo de 0 acciones inválidas y 0 timeouts en 5–6 jugadores; medir tiempo p50/p95/p99 de decisión. La arena, no el bot, debe ser fuente normativa de acciones permitidas y límites de apuesta.

**Comparación de estrategia después:** ejecutar miles de manos con semillas, posiciones y rivales cambiantes; reportar fichas/100 manos, BB/100, volatilidad, frecuencias de eliminación, clasificación y rendimiento frente a `estadistico`, `espia`, `bandido` y `darwin`. Usar varias composiciones de mesa y escenarios de stack, no solo el torneo de ejemplos (que puede ser heads-up).

**Validación fuera de muestra:** entrenar o ajustar sobre un conjunto de rivales/semillas y reservar otros para evaluar. Los cambios con mejoras pequeñas y varianza alta deben permanecer experimentales.

**Torneo específico:** en clasificatoria las fichas se conservan y 0 elimina. Optimizar solo chipEV puede ignorar el riesgo de eliminación; optimizar solo supervivencia impide clasificar con fichas suficientes. El puntaje/objetivo completo debe venir de las bases, no suponer estructura de premios de un torneo tradicional.

## 5. Seguridad y operación
- No subir tokens reales; usar flags o variables de entorno que nunca se imprimen en los logs.
- Nunca consultar APIs externas en el camino crítico sin medir latencia y tener fallback.
- Prohibido ver cartas rivales distintas de `mano_fin.mostradas`; no explotar fallos del servidor.
- Una conexión por token; reencontrar el `id_jugador` en cada bienvenida.
- Mantener el socket abierto durante silencios entre rondas.

## 6. Referencias y lecturas prácticas

1. [PokerFight, protocolo oficial](https://github.com/aicspucp/pokerfight-arena-participantes/blob/main/docs/protocolo.md) — contrato de transporte y mensajes.
2. [PokerFight, guía del bot](https://github.com/aicspucp/pokerfight-arena-participantes/blob/main/docs/guia-del-bot.md) — pruebas y reconexión.
3. [Pluribus, investigación original (2019)](https://pubmed.ncbi.nlm.nih.gov/31296650/) — póker de seis jugadores, blueprint y búsqueda.
4. [Meta AI, detalles de Pluribus](https://ai.meta.com/blog/pluribus-first-ai-to-beat-pros-in-6-player-poker/) — explicación conceptual y limitaciones.
5. [DeepStack (2017)](https://arxiv.org/abs/1701.01724) — re-solving con evaluaciones aprendidas en heads-up.
6. [SHARINGAN-2, actualizado noviembre 2026](https://sharingan.poker/learn/sharingan-2/) — blueprint abierto de seis jugadores y opción de búsqueda turn/river.
7. [PokerStars Learn, pot odds](https://www.pokerstars.com/poker/learn/lesson/pot-odds/) — equity, coste de call e implied odds.
8. [PokerStars Learn, decisiones river](https://www.pokerstars.com/poker/learn/strategies/5-questions-to-ask-before-betting-the-river/) — showdown, valor, bluff, tamaño y check-raise.

**Conclusión:** para esta hackathon, priorizar una implementación **legal y rápida de equity/rangos y EV** antes de entrenar CFR, integrar LLMs o perseguir una solución GTO exacta multijugador. Estas prioridades son una evaluación de ingeniería, no la garantía de una estrategia ganadora.
