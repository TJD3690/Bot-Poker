# Roadmap y decisiones pendientes

**Objetivo:** obtener una primera versión ejecutable, legal y estable mientras se definen estrategias más sofisticadas. Estado revisado: el repositorio privado solo tiene README.md y .gitignore en main (19/11/2026); este roadmap no representa tareas ya realizadas.

## Plan incremental
| Prioridad | Entregable | Criterio de aceptación |
|---|---|---|
| P0 | Conexión TCP, saludo, JSON Lines | Handshake válido, recepción de bienvenida y estados |
| P0 | Identificación, acciones legales y fallback | Sin errores ni apuestas ilegales |
| P0 | Política provisional en todas las etapas | Completa manos hasta river sin intervención |
| P1 | PREFLOP apertura | 169 clases verificadas por posición y frecuencias correctas |
| P1 | PREFLOP 3-bet | Grupos A–E, montos legales, condiciones de BB/stack |
| P1 | FLOP clasificación y proyectos | Detecta manos, outs y textura con pruebas |
| P1 | FLOP decisiones | Frecuencias/tamaños y respuestas a apuesta según ramas documentadas |
| P2 | TURN / RIVER | Política validada que reemplace el fallback |
| P2 | Monte Carlo / pot odds | Comparación contra resultados conocidos |
| P2 | Rivales | Estadísticas por alias y ajustes con tamaño mínimo de muestra |
| P2 | Ajuste por torneo | Validación multijugador, fichas persistentes y calibración |

## Decisiones abiertas del equipo
1. PREFLOP ante apertura ajena **antes de nuestra primera acción**; limpers, 3-bet y multiway.
2. Defensa de ciega grande y pequeña: limp, check disponible, aperturas, all-ins.
3. Política para stack corto (20 BB o menos) y cambios según stack efectivo.
4. Digitalizar las matrices visuales de 169 clases sin errores de transcripción.
5. Diferencia entre leyenda visual MIX 40 % y frecuencia textual dependiente de posición.
6. Prioridad entre texturas superpuestas (p. ej., flop conectado y monocolor).
7. Cómo incorporar proyectos, outs y pot odds a las frecuencias de FLOP.
8. Revisar el fold automático de manos A2 ante apuesta >100 % del pozo previo.
9. Política concreta de TURN y RIVER, incluyendo apuestas futuras y showdown.
10. All-in, varios rivales activos y pozos laterales.
11. Observaciones mínimas y persistencia de estadísticas de rivales.
12. Información realmente disponible sobre fase y clasificación; no suponer datos no expuestos por la arena.

## Forma recomendada de decidir
- Crear un issue para cada decisión abierta, con ejemplo de estado y acciones posibles.
- Estrategia propone reglas; desarrollo valida disponibilidad de campos y legalidad.
- Añadir pruebas antes de activar cambios en la estrategia.
- Comparar versiones con semillas y rivales similares; guardar resultados.
- Cuando falte definición, implementar fallback explícitamente marcado como provisional.

## Próximas tareas
1. Cliente de referencia Python a partir del kit, sin modificar el kit.
2. Validación completa de acciones y montos.
3. Prueba de integración de una mesa 5–6 jugadores.
4. Digitalización de tablas y política PREFLOP especificada.
5. Clasificador FLOP, proyectos y reglas existentes.
6. Política provisional TURN/RIVER hasta acordar nuevas reglas.
7. Ensayos sistemáticos y calibración.

**Nota:** la entrega de la competencia requiere código propio y descripción breve/README; esta documentación interna puede ser más amplia y es distinta del resumen de entrega.
