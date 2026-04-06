from machine import Pin, ADC, PWM
import time

#CONFIGURACIÓN

# Entradas analógicas
pot_base = ADC(Pin(34))
pot_brazo = ADC(Pin(35))

pot_base.width(ADC.WIDTH_12BIT)
pot_brazo.width(ADC.WIDTH_10BIT)

# Servos
servo_base = PWM(Pin(18), freq=50)
servo_brazo = PWM(Pin(19), freq=50)

# Indicadores
led_ok = Pin(2, Pin.OUT)
led_alerta = Pin(4, Pin.OUT)
buzzer = Pin(5, Pin.OUT)

# Botones
btn_home = Pin(12, Pin.IN, Pin.PULL_UP)
btn_seq = Pin(14, Pin.IN, Pin.PULL_UP)

# ESTADOS 

MANUAL = 0
HOME = 1
SECUENCIA = 2

estado_actual = MANUAL

# Flags interrupción
flag_home = False
flag_seq = False

# Antirrebote
ultimo_evento = 0
debounce = 200

# FUNCIONES 

def escalar_adc(valor, max_adc):
    return (valor / max_adc) * 180

def angulo_a_pwm(angulo):
    return int(26 + (angulo / 180) * 102)

def set_servo(servo, angulo):
    servo.duty(angulo_a_pwm(angulo))

def control_manual():
    led_ok.value(1)
    led_alerta.value(0)
    buzzer.value(0)

    a1 = escalar_adc(pot_base.read(), 4095)
    a2 = escalar_adc(pot_brazo.read(), 1023)

    set_servo(servo_base, a1)
    set_servo(servo_brazo, a2)

def mover_suave(servo, inicio, fin, paso=2):
    if inicio < fin:
        r = range(int(inicio), int(fin), paso)
    else:
        r = range(int(inicio), int(fin), -paso)

    for i in r:
        set_servo(servo, i)
        time.sleep(0.02)

def rutina_home():
    global estado_actual

    led_ok.value(0)
    led_alerta.value(1)
    buzzer.value(1)

    mover_suave(servo_base, 90, 0)
    mover_suave(servo_brazo, 90, 0)

    buzzer.value(0)
    estado_actual = MANUAL

def rutina_secuencia():
    global estado_actual

    led_ok.value(0)
    led_alerta.value(1)
    buzzer.value(1)

    movimientos = [
        (0, 0),
        (120, 40),
        (60, 120),
        (90, 90)
    ]

    for pos in movimientos:
        set_servo(servo_base, pos[0])
        set_servo(servo_brazo, pos[1])
        time.sleep(0.8)

    buzzer.value(0)
    estado_actual = MANUAL

#  INTERRUPCIONES 

def gestionar_evento(tipo):
    global ultimo_evento, flag_home, flag_seq

    ahora = time.ticks_ms()

    if time.ticks_diff(ahora, ultimo_evento) > debounce:
        ultimo_evento = ahora

        if tipo == "home":
            flag_home = True
        elif tipo == "seq":
            flag_seq = True

def irq_home(pin):
    gestionar_evento("home")

def irq_seq(pin):
    gestionar_evento("seq")

btn_home.irq(trigger=Pin.IRQ_FALLING, handler=irq_home)
btn_seq.irq(trigger=Pin.IRQ_FALLING, handler=irq_seq)

#  LOOP PRINCIPAL 

while True:

    if flag_home:
        flag_home = False
        estado_actual = HOME

    if flag_seq:
        flag_seq = False
        estado_actual = SECUENCIA

    if estado_actual == MANUAL:
        control_manual()

    elif estado_actual == HOME:
        rutina_home()

    elif estado_actual == SECUENCIA:
        rutina_secuencia()

    time.sleep(0.05)