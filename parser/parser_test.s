 ldi Xh, 0x00
 push r0
 ldi r26,0x00
 ldi r27,0x01
 ldi r16,0x05
 ldi r30, 0xab
 pop r1
 eor r24, r30
 mov r16, r24
 st X+,r16
 mov r16, r22
 ldi r16,0x07
 st X+,r16
 mov r16, r20
 ldi r16,0x03
 st X+,r16


