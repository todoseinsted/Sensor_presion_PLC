# Sensor de presión en Raspberry PLC 19R

Lectura segura de un transmisor de presión Yokogawa DPharp EJA530E mediante un
conversor Weidmüller ACT20M-AI-AO-S y la entrada analógica `I0.5` de un
Industrial Shields Raspberry PLC 19R V6.

El programa es de solo lectura. No acciona relés ni salidas del PLC.

## Equipos verificados

- Transmisor Yokogawa DPharp EJA530E, Style S2.
- Salida del transmisor: 4-20 mA DC con HART.
- Alimentación del transmisor: 10,5-30/32 VDC.
- Conversor Weidmüller ACT20M-AI-AO-S.
- PLC Industrial Shields Raspberry PLC 19R V6.
- Entrada utilizada: `I0.5`, ADC de 12 bits y rango 0-10 V.

El borne `A` del EJA530E es el terminal de comprobación para amperímetro. No es
una salida analógica independiente. La alimentación y la señal 4-20 mA
circulan por los terminales `SUP+` y `SUP-`.

## Conexionado con una fuente común de 24 V

El ACT20M se utiliza como entrada pasiva. El retorno `SUP-` del transmisor debe
atravesar la entrada del conversor; no debe conectarse directamente a 0 V.

```text
                    +-- ACT20M borne 7 (alimentación +)
+24 V --------------+
                    +-- Yokogawa SUP+

Yokogawa SUP- ---------- ACT20M borne 4 (+ entrada mA)
ACT20M borne 3 ---------- 0 V
ACT20M borne 8 ---------- 0 V

Yokogawa borne A -------- sin conectar

ACT20M borne 5 (+V) ----- PLC I0.5
ACT20M borne 6 (-V) ----- GND analógico del PLC
```

No combinar este conexionado con el modo de alimentación de lazo del ACT20M.

## Configuración DIP del ACT20M

Entrada pasiva 4-20 mA:

| DIP | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| Estado | OFF | OFF | ON | OFF |

Salida 0-10 V:

| DIP | 5 | 6 | 7 |
| --- | --- | --- | --- |
| Estado | ON | OFF | OFF |

Después de cambiar los DIP se debe reiniciar eléctricamente el conversor.

## Instalación

Copiar `prueba_weidmuller.py` al PLC. La ruta utilizada durante el ensayo fue:

```text
/home/RaspPLC1/Ensayos/prueba_weidmuller.py
```

El lector nativo esperado por defecto es:

```text
~/test/RPIPLC_V6/RPIPLC_19R/get-analog-input
```

Se puede indicar otra ubicación mediante `--driver`.

## Uso

Lectura continua en porcentaje:

```bash
python3 prueba_weidmuller.py --channel I0.5
```

Veinte muestras cada 250 ms:

```bash
python3 prueba_weidmuller.py \
  --channel I0.5 \
  --samples 20 \
  --interval 0.25
```

Si se confirma que el rango configurado del transmisor es 0-5 kgf/cm²:

```bash
python3 prueba_weidmuller.py \
  --channel I0.5 \
  --min 0 \
  --max 5 \
  --unit kgf/cm2
```

Salida JSON para integración con otro programa:

```bash
python3 prueba_weidmuller.py \
  --channel I0.5 \
  --min 0 \
  --max 5 \
  --unit kgf/cm2 \
  --json
```

## Conversión

El PLC entrega un valor ADC entre 0 y 4095:

```text
voltaje = raw * 10 / 4095
porcentaje = voltaje / 10 * 100
corriente equivalente = 4 + porcentaje/100 * 16
valor = mínimo + porcentaje/100 * (máximo - mínimo)
```

Debido a que el ACT20M convierte 4-20 mA en 0-10 V, tanto un cero de escala
válido como un lazo abierto pueden producir una lectura cercana a 0 V. El
programa lo informa como `CERO_ESCALA_O_LAZO_ABIERTO`.

## Resultado del ensayo real

Con aproximadamente 2-2,2 kgf/cm² indicados por el transmisor se obtuvieron 20
lecturas estables:

| Magnitud | Resultado |
| --- | --- |
| ADC | 1754-1764 |
| Tensión en I0.5 | 4,28-4,31 V |
| Corriente equivalente | 10,85-10,89 mA |
| Porcentaje de escala | aproximadamente 43 % |

Para un rango 0-5 kgf/cm², el valor calculado es aproximadamente 2,15 kgf/cm².
Se debe confirmar LRV y URV en el transmisor antes de usar el valor en proceso.

## Pruebas

```bash
python3 -m unittest -v
```

## Diagnóstico rápido

- Salida del ACT20M en 0 V: comprobar que `SUP-` regrese por los bornes 4 y 3.
- Cero de escala o lazo abierto: medir la corriente en serie; debe ser al menos
  aproximadamente 4 mA.
- El borne `A` del Yokogawa solo admite un instrumento de comprobación de baja
  resistencia. No instalar allí una resistencia de 520 ohmios.
- Verificar aproximadamente 24 V entre los bornes 7 y 8 del ACT20M.
- No aplicar más de 10 V a la entrada analógica del PLC.

## Documentación del fabricante

- [Manual de hardware Yokogawa EJA510E/EJA530E](https://web-material3.yokogawa.com/IM01C25F01-01EN_013.pdf)
- [Hoja de datos Yokogawa EJA530E](https://web-material3.yokogawa.com/GS01C31F01-01EN.pdf)
- [Guía Yokogawa de configuración local LRV/URV](https://web-material3.yokogawa.com/2/20224/files/FGP-300%20_02_.pdf)

## Seguridad

Realizar el ensayo en banco, fuera de proceso y de atmósferas peligrosas. Cortar
la alimentación antes de modificar conexiones o DIP. No abrir el transmisor en
una atmósfera explosiva y no superar el rango de presión indicado en su placa.
