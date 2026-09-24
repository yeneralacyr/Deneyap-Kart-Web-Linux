from tkinter import Tk
from tkinter.messagebox import showerror




def showError(message:str) -> None:
    """
    tkinter gui to show error window

    :param message: error message
    :type message str
    """
    root = Tk()
    root.withdraw()
    showerror(title = "Hata", message = message)
    root.destroy()