import tkinter as tk
from tkinter import ttk, messagebox
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

def load_vendor_selection():
    clear_window()
    tk.Label(window, text="Select Ice Cream Vendor", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16),
              command=lambda: load_flavor_form("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Warwick", font=('Georgia', 16),
              command=lambda: load_flavor_form("WarwickFlavors", "warwick")).pack(pady=10)

def load_flavor_form(table_name, vendor_name):
    clear_window()

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

    header = tk.Label(scrollable_frame, text=f"{vendor_name.title()} Order", font=('Georgia', 20), bg=bg_color)
    header.pack(pady=10, padx=(290,0), anchor='center')

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

    date_label = tk.Label(scrollable_frame, text="Enter Order Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color)
    date_label.pack(pady=(20, 5), padx=(290,0), anchor='center')

    date_entry = tk.Entry(scrollable_frame, font=('Georgia', 12), justify='center')
    date_entry.pack(anchor='center', padx=(290,0))

    err_label = tk.Label(scrollable_frame, text="", font=('Georgia', 10), fg="red", bg=bg_color)
    err_label.pack(anchor='center', padx=(290,0))

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

    tk.Button(scrollable_frame, text="Place Order", font=('Georgia', 14), command=finalize_order).pack(pady=20, padx=(290,0), anchor='center')
    tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5, padx=(290,0), anchor='center')

def review_order():
    clear_window()

    def show_orders(rows):
        canvas_frame = tk.Frame(window)
        canvas = tk.Canvas(canvas_frame, bg=bg_color)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=bg_color)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas_frame.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(scrollable, text="Reviewing Orders", font=('Georgia', 20), bg=bg_color).pack(pady=20)

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("SELECT flavor_id, name FROM WarwickFlavors")
        warwick = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM CrescentFlavors")
        crescent = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM cfFlavors")
        cf = dict(cur.fetchall())

        last_order = None
        for order_id, date, vendor, fid, qty in rows:
            if order_id != last_order:
                if last_order is not None:
                    tk.Label(scrollable, text="", bg=bg_color).pack()
                tk.Label(scrollable, text=f"Date: {date} | Vendor: {vendor}", font=('Georgia', 14, 'bold'), bg=bg_color).pack()
                last_order = order_id

            name = warwick.get(fid) or crescent.get(fid) or cf.get(fid) or "Unknown"
            tk.Label(scrollable, text=f"{name} - {qty}", font=('Georgia', 12), bg=bg_color).pack()

        tk.Button(scrollable, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=10)
        conn.close()

    def fetch_orders(date=None):
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        if date:
            cur.execute("""
                SELECT Orders.order_id, Orders.date, Orders.vendor, OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                WHERE Orders.date = ? ORDER BY Orders.order_id
            """, (date,))
        else:
            cur.execute("""
                SELECT Orders.order_id, Orders.date, Orders.vendor, OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                ORDER BY Orders.order_id
            """)
        rows = cur.fetchall()
        conn.close()
        show_orders(rows)

    def delete_orders():
        clear_window()
        tk.Label(window, text="Delete Orders", font=('Georgia', 20), bg=bg_color).pack(pady=10)

        tk.Label(window, text="Enter Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack()
        date_entry = tk.Entry(window, font=('Georgia', 12), justify='center')
        date_entry.pack()

        tk.Label(window, text="Select Vendor:", font=('Georgia', 14), bg=bg_color).pack(pady=10)

        vendor_var = tk.StringVar(value="crescent ridge")
        for vendor in ["crescent ridge", "warwick", "cold fusion"]:
            ttk.Radiobutton(window, text=vendor.title(), variable=vendor_var, value=vendor).pack(anchor='center')

        def perform_delete():
            date = date_entry.get().strip()
            vendor = vendor_var.get()
            if not is_valid_date(date):
                messagebox.showerror("Invalid Date", "Please enter date as MM-DD-YYYY")
                return
            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            cur.execute("SELECT order_id FROM Orders WHERE date = ? AND vendor = ?", (date, vendor))
            matches = cur.fetchall()
            for oid, in matches:
                cur.execute("DELETE FROM OrderDetails WHERE order_id = ?", (oid,))
                cur.execute("DELETE FROM Orders WHERE order_id = ?", (oid,))
            conn.commit()
            conn.close()
            show_main_menu()

        tk.Button(window, text="Delete", font=('Georgia', 14), command=perform_delete).pack(pady=10)
        tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

    clear_window()
    tk.Label(window, text="Review Orders Menu", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    tk.Button(window, text="View All Orders", font=('Georgia', 14), command=lambda: fetch_orders()).pack(pady=10)
    tk.Button(window, text="Find by Date", font=('Georgia', 14), command=lambda: fetch_orders_by_date()).pack(pady=10)
    tk.Button(window, text="Delete Orders", font=('Georgia', 14), command=delete_orders).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

    def fetch_orders_by_date():
        clear_window()
        tk.Label(window, text="Enter Date to Search (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack(pady=10)
        entry = tk.Entry(window, font=('Georgia', 12), justify='center')
        entry.pack()

        def run_search():
            date = entry.get().strip()
            if is_valid_date(date):
                fetch_orders(date)
            else:
                messagebox.showerror("Invalid Date", "Please enter date as MM-DD-YYYY")

        tk.Button(window, text="Search", font=('Georgia', 14), command=run_search).pack(pady=10)
        tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

def add_flavor():
    clear_window()
    tk.Label(window, text="Select Vendor to Add Flavor To", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    def vendor_choice(vendor_table, vendor_label):
        clear_window()
        tk.Label(window, text=f"Adding to {vendor_label.title()}", font=('Georgia', 20), bg=bg_color).pack(pady=20)
        tk.Label(window, text="Enter Flavor Name:", font=('Georgia', 14), bg=bg_color).pack(pady=10)

        entry = tk.Entry(window, font=('Georgia', 12), justify='center')
        entry.pack()

        def confirm_add():
            name = entry.get().strip()
            if not name:
                messagebox.showerror("Input Error", "Flavor name cannot be blank")
                return
            flavor_id = name.lower().replace(" ", "_")
            flavor_type = "gelato" if vendor_table == "cfFlavors" else "ice cream"

            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {vendor_table} WHERE flavor_id = ?", (flavor_id,))
            if cur.fetchone():
                messagebox.showerror("Duplicate", "Flavor already exists")
                conn.close()
                return

            cur.execute(f"INSERT INTO {vendor_table} (flavor_id, name, type) VALUES (?, ?, ?)",
                        (flavor_id, name, flavor_type))
            conn.commit()
            conn.close()
            show_main_menu()

        tk.Button(window, text="Add Flavor", font=('Georgia', 14), command=confirm_add).pack(pady=10)
        tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

    tk.Button(window, text="Warwick", font=('Georgia', 16), command=lambda: vendor_choice("WarwickFlavors", "warwick")).pack(pady=10)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16), command=lambda: vendor_choice("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Cold Fusion", font=('Georgia', 16), command=lambda: vendor_choice("cfFlavors", "cold fusion")).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

def remove_flavor():
    return

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

style = ttk.Style()
style.theme_use('default')
style.configure('TPC_button.TButton',
                font=('Georgia', 14),
                foreground='black',
                background="#ADADAD",
                padx=10)

show_main_menu()
window.mainloop()