# Estrategia del equipo — PREFLOP y FLOP

**Fuente:** Propuesta_Enfoque_Estrategia.pdf, PREFLOT.pdf y FLOP.pdf proporcionados por el equipo.  
**Estado:** propuesta parcial, **no** código implementado ni estrategia optimizada.

## 1. Enfoque general (seis capas)
1. Robustez: contestar siempre con una acción permitida dentro de 5 s y reconectar cuando corresponda.
2. Matemática: equity mediante Monte Carlo y pot odds; preflop parte de tablas.
3. Imprevisibilidad: frecuencias mixtas y algunos tamaños alternativos.
4. Rivales: mantener estadísticas por alias estable; no sobrerreaccionar a pocas manos.
5. Ajuste: calibrar parámetros comparando numerosas simulaciones.
6. Torneo: preservar fichas en clasificatoria y adaptar riesgos en la final.

**Importante:** estas capas describen objetivos de desarrollo. Monte Carlo, memoria de rivales y adaptación por fases aún no aparecen especificados con detalle operacional.

## 2. PREFLOP

### 2.1 Apertura si nadie ha subido antes
Se propone una tabla de **169 clases** por posición: UTG, HJ, CO, BTN y SB. En BB se usa una rama especial de defensa. Las celdas tienen tres colores:

| Color | Decisión |
|---|---|
| Verde | Raise al abrir (siempre que sea legal) |
| Amarillo | Raise con probabilidad dependiente de posición; en otro caso fold |
| Gris | Fold si hay que pagar; si check es válido, no debe foldearse gratuitamente |

Las matrices están en imágenes del PDF. **Falta transcribir y verificar las 169 celdas por posición**; no inferir valores inexistentes.

Probabilidad textual para una mano amarilla, sin ajuste de rivales ni stack:

| Posición | Abrir |
|---|---:|
| UTG | 40 % |
| HJ | 45 % |
| CO | 50 % |
| BTN | 55 % |
| SB | 35 % |
| BB | No aplica |

Fórmula general propuesta: P = limitar(P0(posición) + ajuste_rival + ajuste_fichas, 20 %, 70 %). En el documento: sin información rival, ajuste_rival = 0; entre 21 y 40 BB, restar 10 puntos; con 20 BB o menos, política especial **pendiente**.

**Inconsistencia que requiere revisión:** las leyendas de los gráficos dicen «MIX 40 %», mientras el texto da probabilidades distintas por posición. El documento recomienda tomar provisionalmente la tabla textual como fuente operativa.

### 2.2 Tamaños de apertura
Todos los montos son **total de la apuesta de la ronda**, no incremento:

| Posición | Primera opción | Segunda opción |
|---|---|---|
| UTG, HJ, BTN | 2 BB (50 %) | 2.5 BB (50 %) |
| CO | 2 BB (40 %) | 2.5 BB (60 %) |
| SB | 2.5 BB (50 %) | 3 BB (50 %) |
| BB | Rama de defensa | Rama de defensa |

Con ciegas oficiales de 50/100, BB=100 fichas. Los montos se ajustan si la situación legal o saldo cambia.

### 2.3 Tras abrir: defensa ante 3-bet
El PDF define R = apuesta total del rival / nuestra apertura total:
- Pequeña R ≤ 2.5; mediana 2.5 < R ≤ 4; grande R > 4.
- All-in requiere evaluación aparte.

| Grupo | Manos representativas | Política propuesta |
|---|---|---|
| A | AA, KK | Generalmente 4-bet; call frente all-in |
| B | QQ, AKs, AKo | 4-bet pequeña; call mediana; condiciones para grande/all-in |
| C | JJ, TT, AQs, AJs, KQs | Call pequeña; mediana condicional; fold grande |
| D | 99–66, ATs, KJs, QJs, JTs, T9s, 98s, AJo, KQo | Call selectivo pequeño desde CO/BTN/BB y con stack suficiente |
| E | Otras manos inicialmente admitidas | Generalmente fold ante resubida |

La 4-bet sugerida es 2.5 × apuesta total rival, sujeta a mínimo legal y fichas disponibles. Para B/C/D hay límites adicionales de BB, número de rivales y stack descritos en las pp. 11–14 del PDF; **implementarlos íntegramente antes de activar la rama**.

**No cubierto:** respuesta ante apertura ajena antes de nuestra primera acción, limpers, defensa BB completa, muchas situaciones all-in y stack corto.

## 3. FLOP

### 3.1 Fuerza actual
| Grupo | Descripción |
|---|---|
| A | Trío, escalera, color, full house, póker o escalera de color |
| B | Doble pareja, overpair, top pair con buen kicker |
| C | Top pair con kicker débil o middle pair |
| D | Bottom pair o underpair |
| E | Carta alta, sin mano superior |

Para enfrentar apuestas, A se subdivide en A1 (full house, póker, escalera de color) y A2 (trío, escalera, color). **La categoría no reemplaza la equidad contra el rango rival**.

### 3.2 Proyectos y textura
- Proyecto de color: 9 outs convencionales.
- Escalera abierta: 8 outs convencionales.
- Escalera interna (gutshot): 4 outs convencionales.
- Backdoor: requiere dos cartas favorables; depende de la configuración.

Identificar flop seco, conectado, emparejado y monocolor. Un flop puede pertenecer a más de una categoría; falta establecer prioridad de reglas. Los outs convencionales no siempre son outs ganadores.

### 3.3 Si nadie ha apostado
Frecuencia de BET propuesta (si no apuesta, CHECK):

| Grupo | Flop seco | Conectado / emparejado / monocolor |
|---|---:|---:|
| A | 80 % | 80 % |
| B | 70 % | 50 % |
| C | 25 % | 10 % |
| D | 10 % | 0 % |
| E | 15 % | 0 % |

Tamaño orientativo de BET: seco 33 % del pozo; conectado 60 %; emparejado 50 %; monocolor 50 %. Debe normalizarse el tamaño al monto **total de ronda** y comprobar acciones válidas.

### 3.4 Respuesta a apuesta rival
R = monto apostado por rival / pozo **previo** a su apuesta:
- Pequeña R ≤ 0.33
- Mediana 0.33 < R ≤ 0.75
- Grande R > 0.75
- All-in aparte

En la propuesta: A1 suele raise frente a apuesta pequeña/mediana y call frente a grande; A2 suele call y ante apuesta grande solo paga si no supera el pozo previo; B paga pequeña y mediana solo en flop seco; C paga pequeña solo en flop seco; D/E fold según tabla.

**Pendiente crítico de validación:** foldear automáticamente un trío, escalera o color frente a apuesta >100 % del pozo puede ser incorrecto; contrastar con equity, stack efectivo, rivales y pot odds. No asumir estos umbrales como matemáticamente óptimos.

## 4. No definido en los PDFs
TURN, RIVER, defensa completa de aperturas ajenas, estrategia push/fold ≤20 BB, modelado efectivo de rivales y parámetros del optimizador. Estas ramas se documentan como decisiones abiertas, no como estrategias aprobadas.

## 5. Jerarquía de implementación
1. Acciones y datos legales según el **protocolo oficial**.
2. Política del equipo en las situaciones realmente definidas.
3. Fallback seguro en situaciones no definidas.
4. Mejoras posteriores sujetas a pruebas cuantitativas.
