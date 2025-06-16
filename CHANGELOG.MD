## v1.4 – 2025-06-10 (estable, sin tests)

### 🆕 Added
- Segundo aerador + lógica complementaria (2 SSR externos)  
- Indicador de arranque correcto (LED/foco)  
- Soporte I2C para sensor de CO₂  
- Comando AWS `reset` y ACK de órdenes server→AWS  
- Comunicación UART bidireccional server⇆client  
- Activación de bomba de recirculación mediante botón  

### 🔄 Changed
- Sensores analógicos migrados a un ADC multiplexer  
- Payload enriquecido (timestamps, logs, device_id)  
- Delay de servidor y reboot programado  

### ✅ Fixed
- Calibración de sensor pH  
- Timestamps consistentes en payload enviado a AWS  

> Generado a partir de commits `081be05…` → `a063aa9…`  

