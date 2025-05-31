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
    tk.Label(window, text="Select Product Type", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="Ice Cream", font=('Georgia', 16), command=load_vendor_selection).pack(pady=10)
    tk.Button(window, text="Gelato", font=('Georgia', 16),
              command=lambda: load_flavor_form("cfFlavors", "cold fusion")).pack(pady=10)

# vendor selection
def load_vendor_selection():
    clear_window()
    tk.Label(window, text="Select Ice Cream Vendor", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16),
              command=lambda: load_flavor_form("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Warwick", font=('Georgia', 16),
              command=lambda: load_flavor_form("WarwickFlavors", "warwick")).pack(pady=10)

# flavor form with scroll and centered layout
def load_flavor_form(table_name, vendor_name):
    clear_window()

    # scrollable window container
    container = tk.Frame(window)
    canvas = tk.Canvas(container, bg=bg_color)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=bg_color)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # header
    header = tk.Label(scrollable_frame, text=f"{vendor_name.title()} Order", font=('Georgia', 20), bg=bg_color)
    header.pack(pady=10, padx=(280,0), anchor='center')

    # load flavor fields
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute(f"SELECT flavor_id, name FROM {table_name} ORDER BY name ASC")
    flavors = cur.fetchall()
    conn.close()

    entry_widgets = {}
    for fid, name in flavors:
        row_outer = tk.Frame(scrollable_frame, bg=bg_color)
        row_outer.pack(anchor='center', pady=2)

        row = tk.Frame(row_outer, bg=bg_color)
        row.pack()

        tk.Label(row, text=name, width=30, anchor='e', font=('Georgia', 12), bg=bg_color).pack(side='left')
        entry = tk.Entry(row, width=5, justify='center')
        entry.pack(side='left')
        entry_widgets[fid] = entry

    # date + buttons
    date_label = tk.Label(scrollable_frame, text="Enter Order Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color)
    date_label.pack(pady=(20, 5), padx=(290,0), anchor='center')

    date_entry = tk.Entry(scrollable_frame, font=('Georgia', 12), justify='center')
    date_entry.pack(anchor='center', padx=(280,0))

    err_label = tk.Label(scrollable_frame, text="", font=('Georgia', 10), fg="red", bg=bg_color)
    err_label.pack(anchor='center', padx=(280,0))

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

    tk.Button(scrollable_frame, text="Place Order", font=('Georgia', 14), command=finalize_order).pack(pady=20, padx=(280,0), anchor='center')
    tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5, padx=(280,0), anchor='center')

# review orders button functionality
def review_order():
    clear_window()

    def load_flavor_dict():
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("SELECT flavor_id, name FROM WarwickFlavors")
        warwick = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM CrescentFlavors")
        crescent = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM cfFlavors")
        cold_fusion = dict(cur.fetchall())
        conn.close()
        return {**warwick, **crescent, **cold_fusion}

    def display_orders(filter_date=None):
        clear_window()
        container = tk.Frame(window)
        canvas = tk.Canvas(container, bg=bg_color)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_color)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()

        if filter_date:
            cur.execute("""
                SELECT Orders.date, Orders.vendor, OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                WHERE Orders.date = ? ORDER BY Orders.order_id
            """, (filter_date,))
        else:
            cur.execute("""
                SELECT Orders.date, Orders.vendor, OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                ORDER BY Orders.order_id
            """)
        rows = cur.fetchall()
        conn.close()

        flavor_dict = load_flavor_dict()
        last_date_vendor = None

        for date, vendor, fid, qty in rows:
            if (date, vendor) != last_date_vendor:
                tk.Label(scrollable_frame, text=f"Date: {date} | Vendor: {vendor.title()}", font=('Georgia', 14, 'bold'), bg=bg_color).pack(pady=(10, 0))
                last_date_vendor = (date, vendor)

            fname = flavor_dict.get(fid, "Unknown Flavor")
            tk.Label(scrollable_frame, text=f"{fname} - {qty}", font=('Georgia', 12), bg=bg_color).pack()

        tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=10)

    def delete_orders():
        clear_window()
        tk.Label(window, text="Delete Orders", font=('Georgia', 20), bg=bg_color).pack(pady=10)

        date_entry = tk.Entry(window, font=('Georgia', 12), justify='center')
        date_entry.pack(pady=5)
        vendor_box = ttk.Combobox(window, values=["Crescent Ridge", "Warwick", "Cold Fusion"], font=('Georgia', 12), state="readonly")
        vendor_box.pack(pady=5)

        err_label = tk.Label(window, text="", font=('Georgia', 10), fg="red", bg=bg_color)
        err_label.pack()

        def confirm_delete():
            date = date_entry.get().strip()
            vendor = vendor_box.get().strip().lower()
            if not is_valid_date(date):
                err_label.config(text="Invalid date format.")
                return
            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            cur.execute("SELECT order_id FROM Orders WHERE date = ? AND vendor = ?", (date, vendor))
            order_ids = [row[0] for row in cur.fetchall()]
            for oid in order_ids:
                cur.execute("DELETE FROM OrderDetails WHERE order_id = ?", (oid,))
                cur.execute("DELETE FROM Orders WHERE order_id = ?", (oid,))
            conn.commit()
            conn.close()
            show_main_menu()

        tk.Button(window, text="Delete", font=('Georgia', 12), command=confirm_delete).pack(pady=5)
        tk.Button(window, text="Back", font=('Georgia', 12), command=review_order).pack(pady=5)

    clear_window()
    tk.Label(window, text="Review Orders", font=('Georgia', 20), bg=bg_color).pack(pady=10)
    tk.Button(window, text="View All Orders", font=('Georgia', 14), command=lambda: display_orders()).pack(pady=5)
    tk.Button(window, text="Find by Date", font=('Georgia', 14), command=lambda: search_by_date()).pack(pady=5)
    tk.Button(window, text="Delete an Order", font=('Georgia', 14), command=delete_orders).pack(pady=5)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=10)

    def search_by_date():
        clear_window()
        tk.Label(window, text="Enter Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack(pady=10)
        date_entry = tk.Entry(window, font=('Georgia', 12), justify='center')
        date_entry.pack(pady=5)
        err_label = tk.Label(window, text="", font=('Georgia', 10), fg="red", bg=bg_color)
        err_label.pack()

        def search():
            date = date_entry.get().strip()
            if not is_valid_date(date):
                err_label.config(text="Invalid date format.")
                return
            display_orders(filter_date=date)

        tk.Button(window, text="Search", font=('Georgia', 12), command=search).pack(pady=5)
        tk.Button(window, text="Back", font=('Georgia', 12), command=review_order).pack(pady=5)

def add_flavor():
    pass

def remove_flavor():
    pass

# rebuild main menu
def show_main_menu():
    clear_window()

    title_label = tk.Label(master=window,
                           text='TPC Master Application',
                           font=('Georgia', 24),
                           bg=bg_color,
                           fg='black',
                           bd=0,
                           highlightthickness=0)
    title_label.pack(pady=(10, 50), anchor='center')

    sub_inventory = tk.Label(master=window,
                             text='Inventory Management',
                             font=('Georgia', 16, 'bold'),
                             bg=bg_color,
                             fg='black',
                             bd=0,
                             highlightthickness=0)
    sub_inventory.pack(pady=0, anchor='center')

    main_menu = tk.Frame(master=window,
                         bg=bg_color,
                         bd=0,
                         highlightthickness=0)

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

show_main_menu()
window.mainloop()