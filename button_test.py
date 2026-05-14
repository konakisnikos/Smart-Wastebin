from gpiozero import Button

# Αρχικοποίηση του κουμπιού στο GPIO 22
button = Button(22)

print("Κουμπί δοκιμή - Πάτα το κουμπί (Πάτα Ctrl+C για διακοπή)")

try:
    while True:
        button.wait_for_press()
        print("Κουμπί πατήθηκε!")
        button.wait_for_release()
        print("Κουμπί απελευθερώθηκε!")

except KeyboardInterrupt:
    print("\nΗ δοκιμή σταμάτησε.")
