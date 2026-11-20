# Plan de pruebas y validación

**Meta:** primero robustez y legalidad; después mejorar rendimiento con evidencia estadística.

## 1. Unitarias — contrato TCP/JSON
- [ ] Leer JSON cuando llega fraccionado o varias líneas juntas.
- [ ] No enviar nada ante estado, mano_fin y mensajes informativos.
- [ ] Contestar una sola vez por solicitar_accion.
- [ ] Guardar id_jugador de bienvenida, distinto del token; localizarlo en jugadores[].id.
- [ ] Copiar exactamente id_mano y version=1.0.0.
- [ ] Manejar campos y tipos desconocidos sin finalizar el proceso.
- [ ] Evitar exponer el token en logs.
- [ ] Reconexión y manejo correcto del silencio entre rondas.

## 2. Unitarias — legalidad
- [ ] Todos los tipos de acción pertenecen a acciones_validas.
- [ ] Check cuando es legal; fold como respaldo cuando no hay check ni política validada.
- [ ] Call sin monto; bet/raise con monto **total de ronda** y dentro de límites.
- [ ] All-in corto representado con tipo allin si corresponde.
- [ ] No enviar montos negativos, no numéricos, fuera del stack o por debajo del mínimo.
- [ ] Medir latencia y limitar cómputos según timeout_ms.

## 3. PREFLOP
- [ ] Transcribir y contrastar visualmente las 169 clases de cada tabla.
- [ ] Pruebas verdes, amarillas y grises por posición sin subida previa.
- [ ] Probabilidades amarillas por posición conforme a la **tabla textual** provisional, no leyenda MIX 40 %.
- [ ] Apuestas 2, 2.5 o 3 BB según posición y acciones válidas.
- [ ] Grupos A–E y tamaño R para 3-bets después de nuestra apertura.
- [ ] Fallo seguro ante apertura ajena, limp y situaciones todavía no documentadas.
- [ ] BB con check gratis no debe foldearse por defecto.
- [ ] Stack corto: no utilizar reglas de 100 BB como si fueran universales.

## 4. FLOP
- [ ] Clasificar manos A–E y A1/A2 mediante ejemplos del documento.
- [ ] Diferenciar fuerza actual de proyectos de color, escalera y backdoor.
- [ ] Identificar flops secos, conectados, emparejados y monocolor, incluso solapados.
- [ ] Validar frecuencias BET/CHECK y tamaños sin apuestas previas.
- [ ] Evaluar apuesta rival frente al **pozo anterior a su apuesta**.
- [ ] Probar apuestas pequeñas, medianas, grandes y all-in.
- [ ] Registrar como hipótesis pendiente el fold A2 ante overbet >100 % del pozo previo.

## 5. Integración con la arena
1. Compilar el kit sin alterar motor ni protocolo.
2. Iniciar una mesa de 5–6 bots con stack 10 000, ciegas 50/100, 50 manos, límite 5000 ms.
3. Conectar bot propio y bots del kit (conservador, estadístico, espía, bandido, etc.).
4. Guardar historial y errores, repetir múltiples partidas.
5. Probar pérdida de conexión/reconexión y ventanas de silencio entre rondas.
6. Repetir con condiciones multijugador y fichas persistentes; el torneo básico de ejemplo no equivale necesariamente a la clasificatoria oficial.

## 6. Métricas
| Dimensión | Indicadores |
|---|---|
| Correctitud | Acciones inválidas, excepciones, pérdidas de conexión |
| Tiempo | Latencia de decisión p50/p95/p99; timeouts |
| Ganancia | Fichas netas, BB/100, dispersión |
| Torneo | Supervivencia, frecuencia de clasificación, clasificación final |
| Estilo | VPIP, PFR, agresividad y frecuencia de apuestas por posición |
| Comparación | Rendimiento frente a cada perfil rival y distintas semillas |

## 7. Criterios de entrega
- [ ] Ejecutable mediante comando documentado con IP:puerto y token.
- [ ] No incluye credenciales en el repositorio.
- [ ] Responde antes de 5 segundos y sin jugadas inválidas.
- [ ] Completa manos hasta river autónomamente.
- [ ] Ha pasado pruebas locales multijugador.
- [ ] Incluye README breve con ejecución, requisitos y enfoque.
- [ ] Se ha intentado una conexión al servidor de pruebas cuando esté disponible.

## 8. Registro sugerido de experimentos
    Versión/commit:
    Configuración:
    Rivales:
    Semillas y cantidad de manos:
    Fichas netas / BB100 / supervivencia:
    Latencia p95 / timeouts / acciones inválidas:
    Parámetros modificados:
    Decisión: mantener / revertir
