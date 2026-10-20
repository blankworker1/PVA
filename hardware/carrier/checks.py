# Design checks for the PVA carrier board v1 (figures from hardware/CARRIER.md)
R1, R2 = 100e3, 5.6e3
k = R2/(R1+R2)
print("Divider ratio %.4f (x%.2f)" % (k, 1/k))
for v in (7, 8, 12, 37.5, 44.5, 48, 60):
    print("  panel %5.1f V -> GPIO34 %.3f V" % (v, v*k))
print("  ESP32 ADC, 12 dB attenuation: recommended range 0.15-2.45 V -> top of reliable range = %.1f V panel" % (2.45/k))
SH, G = 0.005, 100
print("Current sense %.2f V/A" % (SH*G))
for i in (0.6, 1.8, 3.0, 4.95, 5.4, 6.0):
    print("  Isc %4.2f A -> GPIO35 %.3f V   shunt dissipation during pulse %.3f W" % (i, i*SH*G, i*i*SH))
print("  reliable to %.2f A (2.45 V); INA180 output clips near 3.28 V (=%.2f A)" % (2.45/(SH*G), 3.28/(SH*G)))
print("  shunt drop at 6 A: %.0f mV (INA180 differential input full scale with gain 100 at 3.3 V supply ~ 33 mV)" % (6*SH*1000))
C = 10/2  # two 10 F in series
for p in (0.4, 0.5, 0.6):
    E = 0.5*C*(5.0**2-4.0**2)
    print("Supercap 5 F, 5.0->4.0 V: %.1f J -> %.0f s at %.1f W" % (E, E/p, p))
print("Supercap per cell at 5.0 V: %.2f V (rated 2.7 V); balancing leakage %.2f mA" % (2.5, 5.0/20e3*1000))
print("RC filter R6 C7: tau = %.0f us" % (1e3*10e-9*1e6))
print("LED1 current: %.2f mA" % ((5.0-2.0)/10e3*1000))
print("Pulse duty: 1 ms every 10 s -> mean shunt loss %.1f uW at 6 A" % (6*6*SH*0.001/10*1e6))
for i in (2, 5, 9):
    print("AUX %d A: D5 (~0.7 V) %.1f W, D0 (~0.5 V) %.1f W -> heatsinking needed above ~2 A" % (i, i*0.7, i*0.5))
