from tkinter import Tk, Label
import time

base = "Deneyap Elektronik Geliştirme Kart'ları kütüphaneleri indiriliyor. Lütfen bekleyiniz."
lbl = ""
window = ""

def startGUI() -> None:
    """
    Starts tkinter gui to indicate core and library download
    """

    global lbl
    global window

    window = Tk()
    try:
        # .ico Linux'ta cogunlukla desteklenmez; varsa dene, yoksa sessiz gec
        window.iconbitmap('icon.ico')
    except Exception:
        pass
    window.title("Deneyap Kart Web")
    window.geometry("700x80")
    lbl = Label(window, text=base, font=("Arial", 15))

    lbl.pack(pady = 20, padx=10, anchor="w")
    window.after(1, animateText)
    window.mainloop()

def animateText() -> None:
    """
    to make sure user understants it is not hanging, dots keeps moving.
    """
    i = 0
    while True:
        i+=1
        text = base + "." *(i%4)
        lbl.config(text = text)
        window.update()
        time.sleep(0.5)

if __name__ == '__main__':
    startGUI()
