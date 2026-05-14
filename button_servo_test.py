from gpiozero import Button, AngularServo
import time

# Αρχικοποίηση του Servo στο GPIO 18
servo = AngularServo(18, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0024)

# Αρχικοποίηση του κουμπιού στο GPIO 22
button = Button(22)

# Κατάσταση - true = ανοιχτό, false = κλειστό
is_open = False
last_press_time = 0
cooldown = 5  # 5 δευτερόλεπτα

def toggle_servo():
    global is_open, last_press_time
    current_time = time.time()
    
    # Ελέγχουμε αν έχουν περάσει τα 5 δευτερόλεπτα
    if current_time - last_press_time < cooldown:
        print(f"Περιμένετε {cooldown - (current_time - last_press_time):.1f} δευτερόλεπτα...")
        return
    
    last_press_time = current_time
    
    if is_open:
        print("Κλείσιμο καπακιού...")
        servo.angle = -90
        is_open = False
    else:
        print("Άνοιγμα καπακιού...")
        servo.angle = 90
        is_open = True
    time.sleep(0.5)

# Ορισμός ενέργειας για το κουμπί
button.when_pressed = toggle_servo

print("Δοκιμή Κουμπιού + Servo - Πάτα το κουμπί για να ανοίξεις/κλείσεις το καπάκι")
print("Αρχική κατάσταση: Κλειστό")
print("Cooldown: 5 δευτερόλεπτα")
print("Πάτα Ctrl+C για διακοπή")

try:
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nΗ δοκιμή σταμάτησε.")
    servo.angle = -90
    time.sleep(0.5)
