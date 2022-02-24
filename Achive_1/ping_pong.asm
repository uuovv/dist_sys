;Подключили библиотеку
.include "m8def.inc"

;Константы для настройки USART
.equ BAUD = 115200
.equ freq = 8000000
.equ UBRR_val = freq/(16*BAUD)-1
;Настройка интревалов Таймеров
.equ TIMER1_INTERVAL = 256/4
.equ TIMER2_INTERVAL = 0
;Регистры для использования
.def sys = r16
.def letter_send = r17
.def T0_R = r18
.def T2_R = r19
.def LOOP_R = r20

.cseg
;Основная программа
.org 0x000
    rjmp MAIN
;Прерывание Timer2
.org 0x004
    rjmp TIM2_OVF
;Прерывание Timer0
.org 0x009
    rjmp TIM0_OVF

;Слова
word1: .db "ping\r\n", 0 ,0
word2: .db "pong\r\n", 0 ,0

;Инициализация Стека
.macro  INITSTACK
    ldi sys, HIGH(RAMEND)
    out SPH, sys
    ldi sys, LOW(RAMEND)
    out SPL, sys
.endmacro

;Настройка Timer0 и Timer2
TIMS_set:
    ;Начальное значение Timer0 (Интервал)
    ldi sys, TIMER1_INTERVAL
    out TCNT0, sys
    ;Начальное значение Timer2 (Интервал)
    ldi sys, TIMER2_INTERVAL
    out TCNT2, sys
    ;Запуск Timer2 с делителем (256)
    ldi sys, 0x4
    out TCCR0, sys
    ;Запуск Timer2 с делителем (256)
    ldi sys, 0x6
    out TCCR2, sys
    ;Разрешить прерывания по переполнению Таймеров
    ldi sys, 0x41
    out TIMSK, sys
    ret

;Настройка USART
USART_init:
    ;Загрузка количества BAUD 
    ldi sys, high(UBRR_val)
    out UBRRH, sys
    ldi sys, low(UBRR_val)
    out UBRRL, sys

    ldi sys, 0x18
    out UCSRB, sys
    ldi sys, 0x86
    out UCSRC, sys
    ret

;Отправка первого сообщения
START_SEND_WORD1:
    ;Установить время срабатывания (Интервал)
    ldi T0_R, TIMER1_INTERVAL
    out TCNT0, T0_R

    ldi ZH, high(2*word1)
    ldi ZL, low(2*word1)
NEW_BYTE_WORD1:
    lpm letter_send, Z+
    cpi letter_send, 0
    breq END_SEND_WORD1 
    rcall TRANSMIT_BYTE 
    rjmp NEW_BYTE_WORD1
END_SEND_WORD1:
    ret

;Отправка второго сообщения
START_SEND_WORD2:
    ;Установить время срабатывания (Интервал)
    ldi T2_R, TIMER2_INTERVAL
    out TCNT2, T2_R

    ldi ZH, high(2*word2)
    ldi ZL, low(2*word2)
NEW_BYTE_WORD2:
    lpm letter_send, Z+
    cpi letter_send, 0
    breq END_SEND_WORD2 
    rcall TRANSMIT_BYTE 
    rjmp NEW_BYTE_WORD2
END_SEND_WORD2:
    ret

;Отправка байта
TRANSMIT_BYTE:
    sbis UCSRA, UDRE
    rjmp TRANSMIT_BYTE 
    out UDR, letter_send
    ret 
    
;Главная программа
MAIN:
    INITSTACK
    rcall USART_init
    rcall TIMS_set
    sei
LOOP:
    rjmp LOOP

;Прерывание Timer0
TIM0_OVF:
    sei
    rcall START_SEND_WORD1
    reti

;Прерывание Timer2
TIM2_OVF:
    sei
    rcall START_SEND_WORD2
    reti
