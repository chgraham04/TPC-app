import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# main window
window = tk.Tk()
window.title('TPC App')
window.geometry('1100x925')
bg_color = '#a3b18a'
window.configure(bg=bg_color)

def update_flavor_tables():
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    for table in ["WarwickFlavors", "CrescentFlavors", "cfFlavors"]:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN unit_price REAL")
        except:
            pass  
    conn.commit()
    conn.close()

def init_payroll_tables():
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Employee (
        employee_id INTEGER PRIMARY KEY,
        f_name TEXT NOT NULL,
        l_name TEXT NOT NULL,
        wage REAL NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS PayPeriods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        pay_period TEXT,
        hours_worked REAL,
        overtime_hours REAL,
        sick_hours REAL,
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
    )""")
    conn.commit()
    conn.close()

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
        name_entry = tk.Entry(window, font=('Georgia', 12))
        name_entry.pack()

        # 🔧 NEW: Ask for unit price
        tk.Label(window, text="Enter Unit Price (e.g., 4.50):", font=('Georgia', 14), bg=bg_color).pack(pady=10)
        price_entry = tk.Entry(window, font=('Georgia', 12))
        price_entry.pack()

        def confirm_add():
            name = name_entry.get().strip()
            price_str = price_entry.get().strip()

            if not name:
                messagebox.showerror("Input Error", "Flavor name cannot be blank")
                return
            try:
                price = float(price_str)
                if price < 0 or round(price, 2) != price:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Enter a valid price (e.g., 3.99)")
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

            # 🔧 Insert with price
            cur.execute(f"INSERT INTO {vendor_table} (flavor_id, name, type, unit_price) VALUES (?, ?, ?, ?)",
                        (flavor_id, name, flavor_type, price))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Flavor added successfully!")
            show_main_menu()

        tk.Button(window, text="Add Flavor", font=('Georgia', 14), command=confirm_add).pack(pady=10)
        tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

    # Vendor selection buttons
    tk.Button(window, text="Warwick", font=('Georgia', 16), command=lambda: vendor_choice("WarwickFlavors", "warwick")).pack(pady=10)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16), command=lambda: vendor_choice("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Cold Fusion", font=('Georgia', 16), command=lambda: vendor_choice("cfFlavors", "cold fusion")).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

def remove_flavor():
    clear_window()
    tk.Label(window, text="Select Vendor to Remove Flavors From", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    def vendor_choice(vendor_table, vendor_label):
        clear_window()
        tk.Label(window, text=f"Remove Flavors from {vendor_label.title()}", font=('Georgia', 20), bg=bg_color).pack(pady=10)

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

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute(f"SELECT flavor_id, name FROM {vendor_table} ORDER BY name ASC")
        flavors = cur.fetchall()
        conn.close()

        vars_dict = {}
        for fid, name in flavors:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(scrollable, text=name, variable=var, bg=bg_color, font=('Georgia', 12))
            cb.pack(anchor='w', padx=20)
            vars_dict[fid] = var

        def confirm_delete():
            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            deleted = 0
            for fid, var in vars_dict.items():
                if var.get():
                    cur.execute(f"DELETE FROM {vendor_table} WHERE flavor_id = ?", (fid,))
                    deleted += 1
            conn.commit()
            conn.close()
            show_main_menu()

        tk.Button(scrollable, text="Delete Selected", font=('Georgia', 14), command=confirm_delete).pack(pady=20)
        tk.Button(scrollable, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

    tk.Button(window, text="Warwick", font=('Georgia', 16), command=lambda: vendor_choice("WarwickFlavors", "warwick")).pack(pady=10)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16), command=lambda: vendor_choice("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Cold Fusion", font=('Georgia', 16), command=lambda: vendor_choice("cfFlavors", "cold fusion")).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

def manage_payroll():
    clear_window()
    tk.Label(window, text="Payroll Management", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    def view_employees():
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM Employee ORDER BY employee_id")
        rows = cur.fetchall()
        conn.close()

        text = tk.Text(window, height=20, width=80, font=('Georgia', 12))
        text.pack()
        text.insert("end", f"{'ID':<5}{'First':<15}{'Last':<15}{'Wage':<10}\n")
        text.insert("end", "-" * 60 + "\n")
        for row in rows:
            eid, f, l, w = row
            text.insert("end", f"{eid:<5}{f:<15}{l:<15}${w:<10.2f}\n")

    tk.Button(window, text="View Employees", font=('Georgia', 14), command=view_employees).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=10)

def add_employee():
    clear_window()
    tk.Label(window, text="Add New Employee", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    tk.Label(window, text="First Name:", font=('Georgia', 14), bg=bg_color).pack()
    fname_entry = tk.Entry(window, font=('Georgia', 12))
    fname_entry.pack()

    tk.Label(window, text="Last Name:", font=('Georgia', 14), bg=bg_color).pack()
    lname_entry = tk.Entry(window, font=('Georgia', 12))
    lname_entry.pack()

    tk.Label(window, text="Wage (per hour):", font=('Georgia', 14), bg=bg_color).pack()
    wage_entry = tk.Entry(window, font=('Georgia', 12))
    wage_entry.pack()

    def save_employee():
        fname = fname_entry.get().strip()
        lname = lname_entry.get().strip()
        try:
            wage = float(wage_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Wage must be a number.")
            return

        if not fname or not lname:
            messagebox.showerror("Missing Fields", "First and Last name are required.")
            return

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO Employee (f_name, l_name, wage) VALUES (?, ?, ?)",
                    (fname, lname, wage))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Employee added successfully!")
        show_main_menu()

    tk.Button(window, text="Save Employee", font=('Georgia', 14), command=save_employee).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

def view_employees_scrollable():
    clear_window()
    tk.Label(window, text="Employee List", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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

    # Header row
    header = tk.Label(scrollable_frame, text=f"{'ID':<5}{'First':<15}{'Last':<15}{'Wage':<10}",
                      font=('Georgia', 12, 'bold'), bg=bg_color)
    header.pack(anchor='w', padx=40)

    # Fetch and display employees
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM Employee ORDER BY employee_id")
    rows = cur.fetchall()
    conn.close()

    for row in rows:
        eid, f, l, w = row
        text = f"{eid:<5}{f:<15}{l:<15}${w:<10.2f}"
        tk.Label(scrollable_frame, text=text, font=('Georgia', 12), bg=bg_color).pack(anchor='w', padx=40)

    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).place(x=10, y=10)

def manage_flavors_menu():
    clear_window()
    tk.Label(window, text="Manage Flavors", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    tk.Button(window, text="Add Flavor", font=('Georgia', 14), command=add_flavor).pack(pady=10)
    tk.Button(window, text="Remove Flavor", font=('Georgia', 14), command=remove_flavor).pack(pady=10)
    tk.Button(window, text="Browse All Flavors", font=('Georgia', 14),
              command=lambda: messagebox.showinfo("Coming Soon", "Browse All Flavors will be implemented next.")).pack(pady=10)
    tk.Button(window, text="Edit Existing Flavor", font=('Georgia', 14),
              command=lambda: messagebox.showinfo("Coming Soon", "Edit Flavor will be implemented next.")).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

def show_main_menu():
    clear_window()
    tk.Label(window, text='TPC Master Application', font=('Georgia', 24), bg=bg_color).pack(pady=(10, 50))

    # Inventory section
    tk.Label(window, text='Inventory Management', font=('Georgia', 16, 'bold'), bg=bg_color).pack()
    inventory_menu = tk.Frame(window, bg=bg_color)
    inventory_menu.pack(pady=10)

    ttk.Button(inventory_menu, text='Place Order', command=place_order, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(inventory_menu, text='Review Old Orders', command=review_order, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(inventory_menu, text='Manage Flavors', command=manage_flavors_menu, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)

    # Payroll section (unchanged)
    tk.Label(window, text='Manage Payroll', font=('Georgia', 16, 'bold'), bg=bg_color).pack(pady=(40, 10))
    payroll_menu = tk.Frame(window, bg=bg_color)
    payroll_menu.pack(pady=10)

    ttk.Button(payroll_menu, text='View Employee List', command=view_employees_scrollable, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(payroll_menu, text='Add Employee', command=add_employee, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)

# Style setup
style = ttk.Style()
style.theme_use('default')
style.configure('TPC_button.TButton', font=('Georgia', 14), foreground='black', background="#ADADAD", padx=10)

show_main_menu()
init_payroll_tables()
update_flavor_tables()
window.mainloop()