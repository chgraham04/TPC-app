import tkinter as tk
from tkinter import ttk
import sqlite3

# main window
window = tk.Tk()
window.title('TPC App')
window.geometry('800x600')
bg_color = '#a3b18a'
window.configure(bg=bg_color)

# clear window helper
def clear_window():
    for widget in window.winfo_children():
        widget.destroy()

# validate MM-DD-YYYY format
def is_valid_date(date_str):
    parts = date_str.split("-")
    if len(parts) != 3:
        return False
    mm, dd, yyyy = parts
    if not (mm.isdigit() and dd.isdigit() and yyyy.isdigit()):
        return False
    if len(mm) != 2 or len(dd) != 2 or len(yyyy) != 4:
        return False
    mm, dd = int(mm), int(dd)
    return 1 <= mm <= 12 and 1 <= dd <= 31

# button functionality
def place_order():
    clear_window()

    # product type selection
    tk.Label(window, text="Select Product Type", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="Ice Cream", font=('Georgia', 16), command=load_vendor_selection).pack(pady=10)
    tk.Button(window, text="Gelato", font=('Georgia', 16), command=lambda: load_flavor_form("cfFlavors", "cold fusion")).pack(pady=10)

# vendor selection
def load_vendor_selection():
    clear_window()
    tk.Label(window, text="Select Ice Cream Vendor", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16), command=lambda: load_flavor_form("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Warwick", font=('Georgia', 16), command=lambda: load_flavor_form("WarwickFlavors", "warwick")).pack(pady=10)

# flavor form with quantity entries
def load_flavor_form(table_name, vendor_name):
    clear_window()
    tk.Label(window, text=f"{vendor_name.title()} Order", font=('Georgia', 20), bg=bg_color).pack(pady=10)

    frame = tk.Frame(window, bg=bg_color)
    frame.pack()

    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute(f"SELECT flavor_id, name FROM {table_name}")
    flavors = cur.fetchall()
    conn.close()

    entry_widgets = {}
    for fid, name in flavors:
        row = tk.Frame(frame, bg=bg_color)
        row.pack(anchor='w', padx=30, pady=2)
        tk.Label(row, text=name, width=30, anchor='w', font=('Georgia', 12), bg=bg_color).pack(side='left')
        entry = tk.Entry(row, width=5)
        entry.pack(side='left')
        entry_widgets[fid] = entry

    # ask for date and finalize order
    def finalize_order():
        date_str = date_entry.get().strip()
        if not is_valid_date(date_str):
            err_label.config(text="Invalid date format. Use MM-DD-YYYY.")
            return

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO Orders (date, vendor) VALUES (?, ?)", (date_str, vendor_name))
        order_id = cur.lastrowid

        for fid, entry in entry_widgets.items():
            qty_str = entry.get()
            try:
                qty = int(qty_str) if qty_str.strip() else 0
                if qty > 0:
                    cur.execute("INSERT INTO OrderDetails (order_id, flavor_id, quantity) VALUES (?, ?, ?)",
                                (order_id, fid, qty))
            except ValueError:
                pass

        conn.commit()
        conn.close()
        show_main_menu()

    # date entry and submit
    tk.Label(window, text="Enter Order Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack(pady=10)
    date_entry = tk.Entry(window, font=('Georgia', 12))
    date_entry.pack()
    err_label = tk.Label(window, text="", font=('Georgia', 10), fg="red", bg=bg_color)
    err_label.pack()
    tk.Button(window, text="Place Order", font=('Georgia', 14), command=finalize_order).pack(pady=20)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

def review_order():
    return

def add_flavor():
    return

def remove_flavor():
    return

# rebuild main menu
def show_main_menu():
    clear_window()

    # title 
    title_label = tk.Label(master=window,
                           text='TPC Master Application',
                           font=('Georgia', 24),
                           bg=bg_color,
                           fg='black',
                           bd=0,
                           highlightthickness=0)
    title_label.pack(pady=(10, 50))

    # inventory management subtitle
    sub_inventory = tk.Label(master=window,
                             text='Inventory Management',
                             font=('Georgia', 16, 'bold'),
                             bg=bg_color,
                             fg='black',
                             bd=0,
                             highlightthickness=0)
    sub_inventory.pack(pady=0)

    # input field
    main_menu = tk.Frame(master=window,
                         bg=bg_color,
                         bd=0,
                         highlightthickness=0)

    # buttons
    button_place_order = ttk.Button(master=main_menu,
                                    text='Place Order',
                                    command=place_order,
                                    style='TPC_button.TButton')

    button_review_order = ttk.Button(master=main_menu,
                                     text='Review Old Orders',
                                     command=review_order,
                                     style='TPC_button.TButton')

    button_add_flavor = ttk.Button(master=main_menu,
                                   text='Add Flavor',
                                   command=add_flavor,
                                   style='TPC_button.TButton')

    button_remove_flavor = ttk.Button(master=main_menu,
                                      text='Remove Flavor',
                                      command=remove_flavor,
                                      style='TPC_button.TButton')

    # packing buttons
    button_place_order.pack(side=tk.LEFT, padx=10, pady=10)
    button_review_order.pack(side=tk.LEFT, padx=10, pady=10)
    button_add_flavor.pack(side=tk.LEFT, padx=10, pady=10)
    button_remove_flavor.pack(side=tk.LEFT, padx=10, pady=10)
    main_menu.pack(pady=0)

# button style
style = ttk.Style()
style.theme_use('default')
style.configure('TPC_button.TButton',
                font=('Georgia', 14),
                foreground='black',
                background="#ADADAD",
                padx=10)

# load initial menu
show_main_menu()

# run main loop
window.mainloop()
