# Investigación aplicada: estrategias TURN y RIVER para Bot-Poker

**Fecha de revisión:** 21/11/2026  
**Tipo:** investigación y propuesta técnica; **no** son reglas aprobadas por el equipo.  
**Base de comparación:** `Propuesta_Enfoque_Estrategia.pdf`, `PREFLOT.pdf`, `FLOP.pdf`, `docs/protocolo.md` de la organización y fuentes citadas al final.

## 1. Qué existe y qué todavía falta

El equipo definió apertura/defensa parcial PREFLOP y un primer conjunto de reglas FLOP. En FLOP separó fuerza actual (A–E), proyectos, textura de mesa, frecuencias de bet y respuestas condicionadas. **No entregó** una política completa para TURN y RIVER. No debe continuarse aplicando la tabla de FLOP sin evaluar qué cambió en la carta nueva, las apuestas y los rangos.

En el MVP (`feature/bot-v0.1-preflop-flop`) TURN/RIVER usan **respaldo provisional**: `check` cuando se pueda; con apuesta pendiente, `call` solo si la mejor jugada es full house o superior y el precio es ≤ pozo, o `fold`. Es deliberadamente conservador y puede dejar ganancias sobre la mesa. No representa la recomendación final de este documento.

## 2. TURN: cuarta carta comunitaria (queda una por salir)

### 2.1 Qué cambia
- Hay 6 cartas visibles para el bot (2 propias + 4 públicas), 46 cartas desconocidas, y **una** comunitaria pendiente.
- El valor de los proyectos cambia: un proyecto típico de color con 9 outs tiene alrededor de `9/46 = 19,6 %` de completarse en el river (si son outs limpios).
- La nueva carta puede completar color/escalera, emparejar el board, añadir overcards o transformar una mano media en una mano vulnerable.
- El tamaño relativo de la pila (**SPR = stack efectivo / pozo**) condiciona si una apuesta puede comprometer todas las fichas.
- Una apuesta en turn pertenece a una línea iniciada preflop/flop: no basta con leer el estado aislado.

### 2.2 Entradas necesarias

| Elemento | De dónde viene | Uso |
|---|---|---|
| Cartas propias + board | `mano_inicio` + `estado.comunitarias` | Mejor jugada y outs |
| Pozo y apuesta pendiente | `estado.pozo`, `apuesta_actual`, `apuesta_ronda` | Pot odds |
| Stack efectivo | `jugadores[].saldo` y aportes | SPR y riesgo |
| Cantidad de rivales activos | `activo` y `en_mano` | Equidad multiway |
| Línea de acciones | `historial_acciones` de la mano | Rangos condicionales |
| Perfil rival previo | Estadísticas persistidas por alias | Corrección de rangos |
| Acciones permitidas | `acciones_validas` | Evitar jugada inválida |

### 2.3 Algoritmo de referencia recomendado

1. Actualizar textura del board y **re-evaluar** toda mano; no conservar la etiqueta del FLOP por inercia.
2. Calcular `equity` ante **rangos ponderados** de cada rival, no solo manos aleatorias uniformes.
3. Comparar `equity` con `pot odds` y estimar **EV del call**. Para un único rival, si el call cierra la acción: `equity_mínima = coste_call / (pozo_actual + coste_call)`; en multiway con pozos laterales se requiere cálculo por distribución de premios y no vale siempre la fórmula simple.
4. Si se permite `check`, calcular si conviene apostar por valor, semifarolear o proteger el check según rangos, textura y SPR.
5. Enumerar unas pocas apuestas **válidas** (por ejemplo 33 %, 60 %, 100 % del pozo y all-in cuando proceda), estimar EV para cada una y elegir la mejor. Estos porcentajes son opciones de búsqueda, **no** frecuencias óptimas universales.
6. Introducir aleatoriedad únicamente cuando dos acciones tengan EV similares y evitar filtrar la fuerza de la mano por el tamaño de apuesta.
7. Limitar el cómputo a un presupuesto de tiempo inferior al `timeout_ms` del protocolo; si no se termina, usar política segura.

### 2.4 Ejemplo de decisión TURN

Tenemos A♥ Q♥, board 2♥ 7♥ K♣ 9♦. Proyecto de color con 9 outs si no se conocen otros corazones; probabilidad de completarlo en river ≈19,6 %. Si hay 800 fichas en el pozo **después** de la apuesta del rival y cuesta 300 pagar, la equidad mínima directa de call es `300/(800+300) ≈ 27,3 %` si el call cierra la acción. **Solo el proyecto de color no justifica el call** bajo el supuesto simplificado; podría cambiar si A/Q son outs limpios, el rival tiene una distribución de manos concreta, o existen apuestas futuras favorables (implied odds). No convertir esta observación en regla fija.

### 2.5 Errores frecuentes que debemos evitar

- Tratar todos los outs como **limpios**: un color bajo puede perder contra color superior, y completar escalera puede no ganar.
- Utilizar «probabilidad de completar mi proyecto» como equivalente a «equidad de ganar».
- Cobrar doblemente el potencial de un proyecto cuando ya se usa equity Monte Carlo.
- Aplicar `FLOP.A2` y foldear automáticamente una mano muy fuerte solo por un umbral de tamaño.
- Usar un único rival aleatorio cuando hay 3–5 activos.

## 3. RIVER: quinta carta (sin futuras comunitarias)

### 3.1 Diferencia central
En RIVER la mano actual es **definitiva**; no hay proyectos que puedan completarse. Debemos evaluar el valor de showdown frente a cada rival plausible, el patrón de apuestas y el coste de las acciones. El mejor evaluador de siete cartas no reemplaza la estimación del **rango** rival.

### 3.2 Decidir frente a apuesta
- Estimar el rango que **apuesta** del rival (no el rango total que llegó al river).
- Calcular `equity` frente a ese rango. Como ya no faltan cartas, la comparación de manos contra cada combinación del rango puede ser **exacta** y rápida; no hace falta simular runouts.
- Para un call que cierra acción sin pozos laterales: `EV_call = equity * pozo_actual - (1-equity) * coste_call` (los empates se manejan repartiendo el pozo).
- Si `EV_call < 0`, normalmente fold; si `EV_call >= 0`, call puede ser razonable. Para rivales múltiples o acciones futuras, usar EV completo.
- Para un **bluff catcher**, la equidad suele depender de la proporción de faroles dentro de las apuestas del rival.

### 3.3 Si nadie ha apostado: check, valor o farol

**Apuesta por valor:** maximizar la ganancia contra manos peores que **pagarían**, no simplemente apostar porque nuestra categoría es A/B. En apuestas de valor, estimar: porcentaje que foldea, porcentaje que paga peor y porcentaje que paga mejor.

**Farol:** con showdown débil, evaluar si el rival foldeará suficientes manos mejores. Si el pozo actual es `P` y apostamos `B`, la frecuencia mínima de fold en un farol puro heads-up es `B/(P+B)`. Por ejemplo, apuesta de medio pozo necesita >33,3 % de folds; apuesta de pozo necesita >50 %. En multiway, más oponentes pueden pagar; no extender automáticamente la fórmula.

**Bloqueadores:** las cartas propias eliminan combinaciones plausibles de manos rivales. Se deben calcular contra rangos concretos; «tener un as bloquea siempre faroles» no es una regla correcta.

**Check:** manos medias con valor de showdown pueden preferir no aumentar un pozo grande, especialmente contra rivales con rangos más fuertes.

### 3.4 Plan para diferentes tipos de rivales

| Perfil observado (con suficientes muestras) | Ajuste potencial |
|---|---|
| Paga demasiado | Apostar por valor con más frecuencia; reducir faroles |
| Foldea demasiado | Farolear selectivamente si el rango y el board lo permiten |
| Apuesta river con casi puras manos fuertes | Foldear más bluff catchers marginales |
| Apuesta river con demasiados faroles | Pagar con bluff catchers de equidad suficiente |
| Desconocido | Política base sin cambios grandes |

No identificar un perfil con 2–5 manos; usar suavizado bayesiano y límites de ajuste.

## 4. Cómo calcular equity adecuadamente

### 4.1 Monte Carlo con cartas ocultas
Para turn: construir mazo de 52 cartas **eliminando las conocidas**, muestrear manos rivales sin reemplazo según rangos condicionales y una carta river restante; evaluar mejores 5 de 7. Estimar la proporción del pozo ganada, **dividiendo empates**. Repetir hasta la precisión o presupuesto temporal deseado.

### 4.2 Rangos ponderados
Representar un rango rival como `peso[combinación]` sobre sus parejas de cartas posibles. Tras observar una acción `a`: `peso_nuevo(h) ∝ peso_anterior(h) × P(a | h, contexto)`, renormalizando después y eliminando combinaciones bloqueadas. Sin modelo confiable de `P(a | h)`, utilizar un prior prudente y documentar la incertidumbre. Evitar mirar cartas privadas ajenas: solo se pueden usar las mostradas en `mano_fin.mostradas`.

### 4.3 Exacto vs aproximado
- River heads-up: enumerar todas las combinaciones legales de las 2 cartas ocultas del rival, ponderadas por el rango. **Equidad exacta condicionada al rango**.
- Turn: una carta futura y combinaciones rivales; se puede enumerar si el tiempo lo permite, o muestrear.
- 5–6 jugadores: el espacio conjunto crece; usar muestreo estratificado/ponderado y un número fijo de muestras con límite de tiempo.
- Evitar dependencia de LLM/API en turno por latencia, incertidumbre y límite estricto de 5 s.

## 5. Integración con el bot actual

```text
estrategia.py / motor de decisión
 ├── preflop: rangos de apertura + defensa acordada
 ├── flop: categorías + texturas + decisiones actuales
 ├── turn: [NUEVO] equity ponderada, SPR, EV, valor/semifarol
 └── river: [NUEVO] equity final, valor/check/farol/bluff-catch
         ↕
  evaluador exacto (7 cartas)
  generador de rangos de rivales
  estadísticas por alias + línea de apuestas
  validador de acciones (compartido)
```

Se recomienda primero **separar el evaluador** de la estrategia para probarlo; después implementar motor de equity; finalmente conectar políticas TURN y RIVER. Mantener fallback seguro para los escenarios no evaluados.

## 6. Especificaciones que el equipo todavía debe aprobar

1. Qué rangos iniciales asignar tras cada posición y secuencia preflop.
2. Qué cambios de rango corresponden a check/call/bet/raise de cada calle.
3. Política de stack corto y manos multiway; resolver pozos laterales.
4. Menú de apuestas y mezcla de faroles por tamaño de apuesta.
5. Tamaño mínimo de muestra antes de explotar perfiles rivales.
6. Meta del torneo: priorizar fichas netas, supervivencia y clasificación; **no adoptar ICM convencional sin un modelo de pagos adecuado**.
7. Cómo evaluar EV cuando se pierde la opción de ver la siguiente carta gratis.
8. Presupuesto de cómputo: p95/p99 de latencia con 5–6 jugadores y 5 s máximos.

## 7. Fuentes externas revisadas

- PokerStars Learn, [Pot Odds Explained](https://www.pokerstars.com/poker/learn/lesson/pot-odds/) — comparación equity/pot odds y advertencia sobre apuestas futuras.
- PokerStars Learn, [5 questions to ask before betting the river](https://www.pokerstars.com/poker/learn/strategies/5-questions-to-ask-before-betting-the-river/) (2024) — decisiones de valor, showdown, farol y tamaños en river.
- PokerStars Learn, [Value Betting](https://www.pokerstars.com/poker/learn/lesson/value-betting/) — apuestas por valor postflop.
- Brown & Sandholm, [Superhuman AI for multiplayer poker](https://pubmed.ncbi.nlm.nih.gov/31296650/) (*Science*, 2019) — marco de autojuego y búsqueda para póker multijugador.
- Meta AI, [Pluribus explanation](https://ai.meta.com/blog/pluribus-first-ai-to-beat-pros-in-6-player-poker/) — estrategia blueprint y búsqueda posterior.

Las fuentes apoyan principios y arquitecturas, **no demuestran que los umbrales concretos sugeridos sean óptimos para PokerFight**.
