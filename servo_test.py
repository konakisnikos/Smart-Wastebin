from gpiozero import AngularServo
import time

# Αρχικοποίηση του Servo στο GPIO 18.
# Σύρμα 5V → Pin 2, Σύρμα GND → Pin 6, Σύρμα σήμα → GPIO 18
servo = AngularServo(18, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0024)

print("Ξεκινάει το τεστ του Servo... Πάτα Ctrl+C για διακοπή.")
print("Εντολές:")
print("  'o' - Άνοιγμα καπακιού (90°)")
print("  'c' - Κλείσιμο καπακιού (-90°)")
print("  'm' - Μέση θέση (0°)")
print("  'q' - Έξοδος")

try:
    while True:
        command = input("\nΕισάγετε εντολή (o/c/m/q): ").strip().lower()
        
        if command == 'o':
            print("Άνοιγμα καπακιού...")
            servo.angle = 90
        elif command == 'c':
            print("Κλείσιμο καπακιού...")
            servo.angle = -90
        elif command == 'm':
            print("Μέση θέση...")
            servo.angle = 0
        elif command == 'q':
            print("Έξοδος...")
            break
        else:
            print("Άγνωστη εντολή. Δοκιμάστε ξανά.")

except KeyboardInterrupt:
    print("\nΤο τεστ σταμάτησε.")
    servo.angle = -90
    time.sleep(0.5)
