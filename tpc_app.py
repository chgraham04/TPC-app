import tkinter as tk
from tkinter import ttk

# main window
window = tk.Tk()
window.title('TPC App')
window.geometry('800x600')
#window.geometry('1200x975')

# window background color
bg_color = '#a3b18a'
window.configure(bg=bg_color)


# title 
title_label = tk.Label(master = window,
                        text = 'TPC Master Application',
                        font = ('Georgia', 24),
                        bg = bg_color,
                        fg = 'black',
                        bd = 0,
                        highlightthickness = 0)
title_label.pack(pady = (10, 50))

# inventory management subtitle
sub_inventory = tk.Label(master = window,
                            text = 'Inventory Management',
                            font = ('Georgia', 16, 'bold'),
                            bg = bg_color,
                            fg = 'black',
                            bd = 0,
                            highlightthickness = 0)
sub_inventory.pack(pady = 0)

# button functionality
def place_order():
    return

def review_order():
    return

def add_flavor():
    return

def remove_flavor():
    return

# input field
main_menu = tk.Frame(master = window,
                      bg = bg_color,
                      bd = 0,
                      highlightthickness = 0)

# button style
style = ttk.Style()
style.theme_use('default')
style.configure('TPC_button.TButton', 
                font = ('Georgia', 14),
                foreground = 'black',
                background = "#ADADAD",
                padx = 10)

# buttons
button_place_order = ttk.Button(master = main_menu, 
                               text = 'Place Order', 
                               command = place_order,
                               style = 'TPC_button.TButton')

button_review_order = ttk.Button(master = main_menu, 
                                text = 'Review Old Orders', 
                                command = review_order,
                                style = 'TPC_button.TButton')

button_add_flavor = ttk.Button(master = main_menu, 
                              text = 'Add Flavor', 
                              command = add_flavor,
                              style = 'TPC_button.TButton')

button_remove_flavor = ttk.Button(master = main_menu, 
                                 text = 'Remove Flavor', 
                                 command = remove_flavor,
                                 style = 'TPC_button.TButton')

# packing buttons
button_place_order.pack(side = tk.LEFT, padx = 10, pady = 10)
button_review_order.pack(side = tk.LEFT, padx = 10, pady = 10)
button_add_flavor.pack(side = tk.LEFT, padx = 10, pady = 10)
button_remove_flavor.pack(side = tk.LEFT, padx = 10, pady = 10)
main_menu.pack(pady = 0)



# run main loop
window.mainloop()


