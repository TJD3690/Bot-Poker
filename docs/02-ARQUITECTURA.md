# Arquitectura técnica propuesta

**Estado del repositorio verificado el 19/11/2026:** main contiene README.md y .gitignore; todavía no se encontró implementación del bot. Los módulos siguientes son **propuesta**, no archivos existentes.

## Flujo lógico
    Servidor PokerFight (TCP / JSON Lines UTF-8)
      ↓
    Cliente: conexión, saludo, bienvenida, reconexión
      ↓
    Normalizador: id_jugador, cartas, posición, apuesta, pozo, stack, historial
      ↓
    Estrategia: PREFLOP / FLOP / TURN / RIVER
      ↓
    Validador: acciones_validas, montos, stack, plazo
      ↓
    Respuesta tipo=accion con id_mano y version=1.0.0

## 1. Protocolo oficial v1.0.0
Referencia normativa: archivo docs/protocolo.md del kit oficial pokerfight-arena-participantes.

- Transporte: TCP; JSON **una línea por mensaje**, terminado en salto de línea; UTF-8.
- El socket es un flujo de bytes: acumular entradas y separar por salto de línea; nunca asumir un JSON completo por llamada a recv.
- Saludo: objeto con tipo=saludo, version=1.0.0 y token privado.
- Bienvenida: persistir id_jugador y silla. **id_jugador no equivale al token**.
- mano_inicio: dos cartas propias (rango 2–14, palo 0–3) y estado público.
- solicitar_accion: incluye acciones_validas, timeout_ms y estado. **Solo este tipo espera respuesta**.
- estado / mano_fin: informativos; mano_fin puede incluir cartas rivales reveladas al showdown.
- Ignorar tipos/campos desconocidos de manera compatible.
- En un torneo, la conexión puede permanecer **silenciosa entre rondas**; no confundirlo con caída de red.

Ejemplo de acción sin monto:

    {"tipo":"accion","version":"1.0.0","id_mano":"mesa-1-mano-7","accion":{"tipo":"check"}}

El valor de id_mano se copia exactamente de estado.id_mano.

## 2. Datos relevantes del estado público
- id_mano, etapa (preflop/flop/turn/river/showdown), comunitarias.
- pozo, apuesta_actual, subida_minima, ciega_chica, ciega_grande.
- posicion_boton, jugadores[], historial_acciones[].
- Para identificar nuestro jugador: buscar id igual al id_jugador recibido en bienvenida.
- Cada jugador tiene saldo, apuesta_ronda, activo, en_mano, en_torneo, allin y posicion_silla.
- Historial de la mano **no equivale a memoria de torneo**: si se quiere estudiar rivales, almacenar agregados por alias entre manos.

## 3. Validador de acciones
- Solo enviar tipos presentes en acciones_validas.
- fold/check/call/allin: sin campo monto.
- bet/raise: **monto total** de apuesta de la ronda, no cantidad adicional.
- Regla de monto: monto >= apuesta_actual + subida_minima y monto <= saldo + apuesta_ronda.
- Cuando solo alcanza para all-in corto, enviar tipo allin si está permitido; no forzar raise inválido.
- Fallback: preferir check cuando sea legal; en caso contrario fold, o política explícita adicional validada.
- Respetar timeout_ms del mensaje, con margen de seguridad bajo los 5 s oficiales.

## 4. Módulos propuestos
| Módulo | Responsabilidad |
|---|---|
| bot.py | CLI -addr/-token y proceso principal |
| protocolo.py | Socket, JSON Lines, handshake y reconexión |
| contexto.py | Estado normalizado y contexto de apuestas |
| legales.py | Validador y fallback de acciones |
| preflop.py | Rangos, posición, apertura/defensa |
| flop.py | Clasificación y decisiones del flop |
| turn.py / river.py | Fallback provisional, luego políticas específicas |
| evaluacion/ | Ranking de manos, outs y equity |
| rivales/ | Métricas por alias y adaptación con incertidumbre |
| tests/ | Contrato, reglas y simulaciones |

Se recomienda que la función de decisión reciba un objeto de estado y devuelva una acción **sin abrir conexiones**, para permitir pruebas unitarias sin la arena.

## 5. Operación
- El kit de la organización solo se usa para compilar arena y bots rivales en pruebas locales; no modificar su protocolo para mejorar nuestro bot.
- Conexión local: localhost:9000 y token libre de pruebas.
- Servidor de organización: dirección publicada + token secreto del equipo.
- La IP del servidor de pruebas puede cambiar; no fijarla en el código.
- No publicar tokens en README, logs, commits ni capturas compartidas.
- Si el socket se cierra al concluir el campeonato puede ser normal. Si se cae durante el torneo, reconectar usando el mismo token; no crear conexiones duplicadas.
