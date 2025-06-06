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

def update_orders_table():
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE Orders ADD COLUMN total REAL")
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS PayrollSummary (
        pay_period TEXT PRIMARY KEY,
        total_payout REAL
    );
""")

    conn.commit()
    conn.close()

def clear_window():
    for widget in window.winfo_children():
        widget.destroy()

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

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tk.Label(scrollable_frame, text=f"{vendor_name.title()} Order", font=('Georgia', 20), bg=bg_color).pack(pady=10)

    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute(f"SELECT flavor_id, name FROM {table_name} ORDER BY name ASC")
    flavors = cur.fetchall()
    conn.close()

    entry_widgets = {}
    for fid, name in flavors:
        row = tk.Frame(scrollable_frame, bg=bg_color)
        row.pack(anchor='center', pady=2)
        tk.Label(row, text=name, width=30, anchor='e', font=('Georgia', 12), bg=bg_color).pack(side='left')
        entry = tk.Entry(row, width=5, justify='center')
        entry.pack(side='left')
        entry_widgets[fid] = entry

    tk.Label(scrollable_frame, text="Enter Order Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack(pady=(20, 5))
    date_entry = tk.Entry(scrollable_frame, font=('Georgia', 12), justify='center')
    date_entry.pack()

    err_label = tk.Label(scrollable_frame, text="", font=('Georgia', 10), fg="red", bg=bg_color)
    err_label.pack()

    def finalize_order():
        date_str = date_entry.get().strip()
        if not is_valid_date(date_str):
            err_label.config(text="Invalid date format. Use MM-DD-YYYY.")
            return

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO Orders (date, vendor) VALUES (?, ?)", (date_str, vendor_name))
        order_id = cur.lastrowid

        total_price = 0.0

        for fid, entry in entry_widgets.items():
            qty_str = entry.get()
            try:
                qty = int(qty_str) if qty_str.strip() else 0
                if qty > 0:
                    cur.execute(f"SELECT unit_price FROM {table_name} WHERE flavor_id = ?", (fid,))
                    result = cur.fetchone()
                    unit_price = result[0] if result else 0
                    total_price += unit_price * qty
                    cur.execute("INSERT INTO OrderDetails (order_id, flavor_id, quantity) VALUES (?, ?, ?)",
                                (order_id, fid, qty))
            except ValueError:
                pass

        cur.execute("UPDATE Orders SET total = ? WHERE order_id = ?", (total_price, order_id))
        conn.commit()
        conn.close()
        show_main_menu()

    tk.Button(scrollable_frame, text="Place Order", font=('Georgia', 14), command=finalize_order).pack(pady=20)
    tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

def review_order():
    def show_orders_page(rows):
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

        tk.Label(scrollable_frame, text="Reviewing Orders", font=('Georgia', 20), bg=bg_color).pack(pady=20, anchor='w', padx=50)

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()

        # Pre-load flavor name dictionaries
        cur.execute("SELECT flavor_id, name FROM WarwickFlavors")
        warwick = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM CrescentFlavors")
        crescent = dict(cur.fetchall())
        cur.execute("SELECT flavor_id, name FROM cfFlavors")
        cf = dict(cur.fetchall())

        # Pre-load order totals
        orders_total_lookup = {}
        cur.execute("SELECT order_id, total FROM Orders")
        for oid, total in cur.fetchall():
            orders_total_lookup[oid] = total if total is not None else 0.00

        conn.close()

        last_order = None
        for order_id, date, vendor, fid, qty in rows:
            if order_id != last_order:
                if last_order is not None:
                    tk.Label(scrollable_frame, text="", bg=bg_color).pack()
                total_str = f"${orders_total_lookup.get(order_id, 0.00):.2f}"
                header_text = f"Date: {date}  |  Vendor: {vendor.title()}  |  Total: {total_str}"
                tk.Label(scrollable_frame, text=header_text, font=('Georgia', 14, 'bold'), bg=bg_color).pack(pady=(10, 2), anchor='w', padx=50)
                last_order = order_id

            name = warwick.get(fid) or crescent.get(fid) or cf.get(fid) or "Unknown"
            line_text = f"{name}  –  {qty}"
            tk.Label(scrollable_frame, text=line_text, font=('Georgia', 12), bg=bg_color).pack(anchor='w', padx=50)

        tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)


    def fetch_orders(date=None):
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        if date:
            cur.execute("""
                SELECT Orders.order_id, Orders.date, Orders.vendor,
                       OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders
                JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                WHERE Orders.date = ?
                ORDER BY Orders.order_id
            """, (date,))
        else:
            cur.execute("""
                SELECT Orders.order_id, Orders.date, Orders.vendor,
                       OrderDetails.flavor_id, OrderDetails.quantity
                FROM Orders
                JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
                ORDER BY Orders.order_id
            """)
        rows = cur.fetchall()
        conn.close()
        show_orders_page(rows)

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
            for (oid,) in matches:
                cur.execute("DELETE FROM OrderDetails WHERE order_id = ?", (oid,))
                cur.execute("DELETE FROM Orders WHERE order_id = ?", (oid,))
            conn.commit()
            conn.close()
            show_main_menu()

        tk.Button(window, text="Delete", font=('Georgia', 14), command=perform_delete).pack(pady=10)
        tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

    # Main review orders menu
    clear_window()
    tk.Label(window, text="Review Orders Menu", font=('Georgia', 20), bg=bg_color).pack(pady=20)
    tk.Button(window, text="View All Orders", font=('Georgia', 14), command=lambda: fetch_orders()).pack(pady=10)
    tk.Button(window, text="Find by Date", font=('Georgia', 14), command=fetch_orders_by_date).pack(pady=10)
    tk.Button(window, text="Delete Orders", font=('Georgia', 14), command=delete_orders).pack(pady=10)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=20)

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

def browse_all_flavors():
    clear_window()
    tk.Label(window, text="All Flavors by Vendor", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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

    for vendor_table, vendor_label in [("WarwickFlavors", "Warwick"),
                                       ("CrescentFlavors", "Crescent Ridge"),
                                       ("cfFlavors", "Cold Fusion")]:
        tk.Label(scrollable_frame, text=vendor_label, font=('Georgia', 16, 'bold'), bg=bg_color).pack(pady=(15, 5), anchor='w', padx=40)
        cur.execute(f"SELECT name, unit_price FROM {vendor_table} ORDER BY name ASC")
        rows = cur.fetchall()
        for name, price in rows:
            price_str = f"${price:.2f}" if price is not None else "$0.00"
            entry = f"{name}  -  {price_str}"
            tk.Label(scrollable_frame, text=entry, font=('Georgia', 12), bg=bg_color).pack(anchor='w', padx=60)

    conn.close()
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).place(x=10, y=10)

def edit_existing_flavor():
    clear_window()
    tk.Label(window, text="Select Vendor to Edit Flavors From", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    def choose_vendor(vendor_table, vendor_label):
        clear_window()
        tk.Label(window, text=f"Editing Flavors for {vendor_label.title()}", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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
        cur.execute(f"SELECT flavor_id, name, unit_price FROM {vendor_table} ORDER BY name ASC")
        flavors = cur.fetchall()
        conn.close()

        edits = {}

        for fid, name, price in flavors:
            row = tk.Frame(scrollable_frame, bg=bg_color)
            row.pack(anchor='w', padx=20, pady=5)

            tk.Label(row, text="Name:", font=('Georgia', 12), bg=bg_color).pack(side='left')
            name_entry = tk.Entry(row, font=('Georgia', 12), width=25)
            name_entry.insert(0, name)
            name_entry.pack(side='left', padx=5)

            tk.Label(row, text="Price:", font=('Georgia', 12), bg=bg_color).pack(side='left')
            price_entry = tk.Entry(row, font=('Georgia', 12), width=8)
            price_entry.insert(0, f"{price:.2f}" if price is not None else "0.00")
            price_entry.pack(side='left')

            edits[fid] = (name_entry, price_entry)

        def save_edits():
            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            for fid, (name_entry, price_entry) in edits.items():
                new_name = name_entry.get().strip()
                try:
                    new_price = float(price_entry.get().strip())
                    if new_price < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid Price", f"Invalid price entered for flavor ID: {fid}")
                    conn.close()
                    return
                cur.execute(f"UPDATE {vendor_table} SET name = ?, unit_price = ? WHERE flavor_id = ?",
                            (new_name, new_price, fid))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Flavors updated successfully!")
            show_main_menu()

        tk.Button(scrollable_frame, text="Save Changes", font=('Georgia', 14), command=save_edits).pack(pady=20)
        tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

    # Vendor selection buttons
    tk.Button(window, text="Warwick", font=('Georgia', 16), command=lambda: choose_vendor("WarwickFlavors", "warwick")).pack(pady=10)
    tk.Button(window, text="Crescent Ridge", font=('Georgia', 16), command=lambda: choose_vendor("CrescentFlavors", "crescent ridge")).pack(pady=10)
    tk.Button(window, text="Cold Fusion", font=('Georgia', 16), command=lambda: choose_vendor("cfFlavors", "cold fusion")).pack(pady=10)
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

def pay_employees():
    clear_window()
    tk.Label(window, text="Enter Pay Period Dates", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    tk.Label(window, text="Start Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack()
    start_entry = tk.Entry(window, font=('Georgia', 12), justify='center')
    start_entry.pack()

    tk.Label(window, text="End Date (MM-DD-YYYY):", font=('Georgia', 14), bg=bg_color).pack(pady=5)
    end_entry = tk.Entry(window, font=('Georgia', 12), justify='center')
    end_entry.pack()

    def proceed():
        start = start_entry.get().strip()
        end = end_entry.get().strip()
        if not (is_valid_date(start) and is_valid_date(end)):
            messagebox.showerror("Invalid Date", "Use MM-DD-YYYY for both dates.")
            return
        pay_period = f"{start} to {end}"
        launch_payroll_form(pay_period)

    tk.Button(window, text="Continue", font=('Georgia', 14), command=proceed).pack(pady=15)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack()

def launch_payroll_form(pay_period):
    clear_window()
    tk.Label(window, text=f"Pay Employees ({pay_period})", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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
    cur.execute("SELECT employee_id, f_name, l_name, wage FROM Employee ORDER BY employee_id")
    employees = cur.fetchall()
    conn.close()

    entries = {}
    for eid, f, l, w in employees:
        row = tk.Frame(scrollable_frame, bg=bg_color)
        row.pack(anchor='w', pady=4, padx=30)
        tk.Label(row, text=f"{f} {l} (${w:.2f}/hr)", font=('Georgia', 12), bg=bg_color).pack(side='left', padx=5)

        hw_entry = tk.Entry(row, font=('Georgia', 12), width=8)
        hw_entry.pack(side='left', padx=5)
        tk.Label(row, text="hrs", bg=bg_color).pack(side='left')

        ot_entry = tk.Entry(row, font=('Georgia', 12), width=8)
        ot_entry.pack(side='left', padx=5)
        tk.Label(row, text="OT", bg=bg_color).pack(side='left')

        sick_entry = tk.Entry(row, font=('Georgia', 12), width=8)
        sick_entry.pack(side='left', padx=5)
        tk.Label(row, text="sick", bg=bg_color).pack(side='left')

        entries[eid] = (hw_entry, ot_entry, sick_entry, w)

    def submit_payroll():
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        total_payout = 0.0

        for eid, (hw_entry, ot_entry, sick_entry, wage) in entries.items():
            try:
                hw = float(hw_entry.get().strip()) if hw_entry.get().strip() else 0.0
                ot = float(ot_entry.get().strip()) if ot_entry.get().strip() else 0.0
                sick = float(sick_entry.get().strip()) if sick_entry.get().strip() else 0.0
                if hw < 0 or ot < 0 or sick < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", f"Invalid entry for employee ID {eid}")
                conn.close()
                return

            # Store record
            cur.execute("""
                INSERT INTO PayPeriods (employee_id, pay_period, hours_worked, overtime_hours, sick_hours)
                VALUES (?, ?, ?, ?, ?)
            """, (eid, pay_period, hw, ot, sick))

            total_payout += wage * (hw + 1.5 * ot)

        cur.execute("INSERT OR REPLACE INTO PayrollSummary (pay_period, total_payout) VALUES (?, ?)",
                    (pay_period, total_payout))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Payroll submitted.\nTotal Payout: ${total_payout:.2f}")
        show_main_menu()

    tk.Button(scrollable_frame, text="Submit Payroll", font=('Georgia', 14), command=submit_payroll).pack(pady=20)
    tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

def browse_pay_periods():
    clear_window()
    tk.Label(window, text="Payroll Summary", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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
    cur.execute("SELECT pay_period, total_payout FROM PayrollSummary ORDER BY pay_period DESC")
    summaries = cur.fetchall()
    conn.close()

    for period, total in summaries:
        label = f"{period}  –  Total Payout: ${total:.2f}"
        tk.Label(scrollable_frame, text=label, font=('Georgia', 12), bg=bg_color).pack(anchor='w', padx=40, pady=3)

    def open_delete_window():
        clear_window()
        tk.Label(window, text="Delete a Pay Period", font=('Georgia', 20), bg=bg_color).pack(pady=20)

        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT pay_period FROM PayrollSummary ORDER BY pay_period DESC")
        periods = [row[0] for row in cur.fetchall()]
        conn.close()

        if not periods:
            tk.Label(window, text="No pay periods found.", font=('Georgia', 14), bg=bg_color).pack(pady=10)
            tk.Button(window, text="Back to Summary", font=('Georgia', 12), command=browse_pay_periods).pack()
            return

        tk.Label(window, text="Select Pay Period to Delete:", font=('Georgia', 14), bg=bg_color).pack(pady=10)

        selected_period = tk.StringVar(value=periods[0])
        dropdown = ttk.Combobox(window, textvariable=selected_period, values=periods, font=('Georgia', 12), state="readonly", width=35)
        dropdown.pack(pady=5)

        def confirm_delete():
            period = selected_period.get()
            if not period:
                messagebox.showerror("Selection Error", "Please select a pay period.")
                return
            conn = sqlite3.connect("icecream_orders.db")
            cur = conn.cursor()
            cur.execute("DELETE FROM PayPeriods WHERE pay_period = ?", (period,))
            cur.execute("DELETE FROM PayrollSummary WHERE pay_period = ?", (period,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Deleted pay period: {period}")
            browse_pay_periods()

        tk.Button(window, text="Delete", font=('Georgia', 14), command=confirm_delete).pack(pady=10)
        tk.Button(window, text="Back to Summary", font=('Georgia', 12), command=browse_pay_periods).pack(pady=5)

    tk.Button(window, text="Delete Pay Period", font=('Georgia', 14), command=open_delete_window).pack(pady=20)
    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).place(x=10, y=10)

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
    headers = ["ID", "First", "Last", "Wage"]
    for col, header in enumerate(headers):
        tk.Label(scrollable_frame, text=header, font=('Georgia', 12, 'bold'),
                 bg=bg_color, padx=20).grid(row=0, column=col, sticky='w', pady=(0, 10))

    # Fetch and display employee rows
    conn = sqlite3.connect("icecream_orders.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM Employee ORDER BY employee_id")
    rows = cur.fetchall()
    conn.close()

    for i, (eid, f, l, w) in enumerate(rows, start=1):
        tk.Label(scrollable_frame, text=str(eid), font=('Georgia', 12), bg=bg_color, padx=20).grid(row=i, column=0, sticky='w')
        tk.Label(scrollable_frame, text=f, font=('Georgia', 12), bg=bg_color, padx=20).grid(row=i, column=1, sticky='w')
        tk.Label(scrollable_frame, text=l, font=('Georgia', 12), bg=bg_color, padx=20).grid(row=i, column=2, sticky='w')
        tk.Label(scrollable_frame, text=f"${w:.2f}", font=('Georgia', 12), bg=bg_color, padx=20).grid(row=i, column=3, sticky='w')

    tk.Button(window, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).place(x=10, y=10)

def edit_employees():
    clear_window()
    tk.Label(window, text="Edit Employee Information", font=('Georgia', 20), bg=bg_color).pack(pady=20)

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
    cur.execute("SELECT employee_id, f_name, l_name, wage FROM Employee ORDER BY employee_id")
    employees = cur.fetchall()
    conn.close()

    edits = {}

    for eid, f, l, w in employees:
        row = tk.Frame(scrollable_frame, bg=bg_color)
        row.pack(anchor='w', pady=4, padx=30)

        tk.Label(row, text=f"ID {eid}", font=('Georgia', 12), bg=bg_color).pack(side='left', padx=5)

        fname_entry = tk.Entry(row, font=('Georgia', 12), width=15)
        fname_entry.insert(0, f)
        fname_entry.pack(side='left', padx=5)

        lname_entry = tk.Entry(row, font=('Georgia', 12), width=15)
        lname_entry.insert(0, l)
        lname_entry.pack(side='left', padx=5)

        wage_entry = tk.Entry(row, font=('Georgia', 12), width=10)
        wage_entry.insert(0, f"{w:.2f}")
        wage_entry.pack(side='left', padx=5)

        edits[eid] = (fname_entry, lname_entry, wage_entry)

    def save_edits():
        conn = sqlite3.connect("icecream_orders.db")
        cur = conn.cursor()
        for eid, (fname_entry, lname_entry, wage_entry) in edits.items():
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            try:
                wage = float(wage_entry.get().strip())
                if wage < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Wage", f"Invalid wage entered for employee ID {eid}")
                conn.close()
                return

            if not fname or not lname:
                messagebox.showerror("Missing Fields", f"First and Last name required for ID {eid}")
                conn.close()
                return

            cur.execute("""
                UPDATE Employee SET f_name = ?, l_name = ?, wage = ? WHERE employee_id = ?
            """, (fname, lname, wage, eid))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Employee information updated successfully!")
        show_main_menu()

    tk.Button(scrollable_frame, text="Save Changes", font=('Georgia', 14), command=save_edits).pack(pady=20)
    tk.Button(scrollable_frame, text="Back to Menu", font=('Georgia', 12), command=show_main_menu).pack(pady=5)

def manage_flavors_menu():
    clear_window()
    tk.Label(window, text="Manage Flavors", font=('Georgia', 20), bg=bg_color).pack(pady=20)

    tk.Button(window, text="Add Flavor", font=('Georgia', 14), command=add_flavor).pack(pady=10)
    tk.Button(window, text="Remove Flavor", font=('Georgia', 14), command=remove_flavor).pack(pady=10)
    tk.Button(window, text="Browse All Flavors", font=('Georgia', 14),
          command=browse_all_flavors).pack(pady=10)
    tk.Button(window, text="Edit Existing Flavor", font=('Georgia', 14), command=edit_existing_flavor).pack(pady=10)
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

    # Payroll section
    tk.Label(window, text='Manage Payroll', font=('Georgia', 16, 'bold'), bg=bg_color).pack(pady=(40, 10))
    payroll_menu = tk.Frame(window, bg=bg_color)
    payroll_menu.pack(pady=10)
    ttk.Button(payroll_menu, text='Pay Employees', command=pay_employees, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(payroll_menu, text='Browse Pay Periods', command=browse_pay_periods, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(payroll_menu, text='Add Employee', command=add_employee, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(payroll_menu, text='View Employee List', command=view_employees_scrollable, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)
    ttk.Button(payroll_menu, text='Edit Employee Info', command=edit_employees, style='TPC_button.TButton').pack(side=tk.LEFT, padx=10)

# Style setup
style = ttk.Style()
style.theme_use('default')
style.configure('TPC_button.TButton', font=('Georgia', 14), foreground='black', background="#ADADAD", padx=10)

show_main_menu()
init_payroll_tables()
update_flavor_tables()
update_orders_table()
window.mainloop()