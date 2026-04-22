import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pyodbc

# THEME
PRIMARY = "#0f766e"
HOVER = "#115e59"
BG = "#e6fffa"
CARD = "#ffffff"
BORDER = "#0f766e"

ctk.set_appearance_mode("light")

# DB
def connect_db():
    try:
        return pyodbc.connect(
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=C:\Users\pc\Desktop\New Folder\billing.system.accdb'
        )
    except Exception as e:
        messagebox.showerror("Error", f"Database connection failed\n{e}")
        return None


def get_all_products():
    conn = connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT product_name FROM PRODUCTS")
            return [i[0] for i in cur.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products\n{e}")
        finally:
            conn.close()
    return []


def get_price(name):
    conn = connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT product_price FROM PRODUCTS WHERE product_name=?", (name,))
            r = cur.fetchone()
            return float(r[0]) if r else 0
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch price\n{e}")
        finally:
            conn.close()
    return 0


def refresh_products():
    global all_products
    all_products = get_all_products()


all_products = get_all_products()
active_entry = None

# AUTOCOMPLETE
def update_suggestions(event=None):
    global active_entry
    widget = event.widget
    active_entry = widget

    typed = widget.get().strip().lower()
    listbox.delete(0, tk.END)

    if not typed:
        listbox.place_forget()
        return

    matches = [p for p in all_products if p.lower().startswith(typed)]

    if not matches:
        listbox.place_forget()
        return

    for m in matches:
        listbox.insert(tk.END, m)

    root.update_idletasks()

    x = widget.winfo_rootx() - root.winfo_rootx()
    y = widget.winfo_rooty() - root.winfo_rooty() + widget.winfo_height()

    listbox.place(
        x=x,
        y=y,
        width=widget.winfo_width(),
        height=min(len(matches), 6) * 28
    )
    listbox.lift()


def select_item(event=None):
    global active_entry
    if listbox.curselection():
        value = listbox.get(listbox.curselection())

        if isinstance(active_entry, tk.Entry):
            active_entry.delete(0, "end")
            active_entry.insert(0, value)

        listbox.place_forget()


# PURCHASE
def add_purchase():
    try:
        if not e_pid.get() or not e_cid.get() or not entry_product.get() or not e_qty.get():
            messagebox.showerror("Error", "Fill all fields")
            return

        pid = int(e_pid.get())
        cid = int(e_cid.get())
        cname = e_cname.get().strip()
        pname = entry_product.get().strip()
        qty = int(e_qty.get())

        price = get_price(pname)

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO PURCHASES 
            (purchase_id, customer_id, product_name, quantity, product_price, customer_name)
            VALUES (?,?,?,?,?,?)
        """, (pid, cid, pname, qty, price, cname))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Successfully added")

        e_pid.delete(0, "end")
        entry_product.delete(0, "end")
        e_qty.delete(0, "end")

    except Exception as e:
        messagebox.showerror("Error", f"Invalid purchase data\n{e}")


# PRODUCT
def add_product():
    try:
        if not e_new_name.get() or not e_new_price.get():
            messagebox.showerror("Error", "Fill all fields")
            return

        name = e_new_name.get().strip()
        price = float(e_new_price.get())

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO PRODUCTS (product_name, product_price) VALUES (?, ?)",
            (name, price)
        )

        conn.commit()
        conn.close()

        refresh_products()
        messagebox.showinfo("Success", "Successfully added")

        e_new_name.delete(0, "end")
        e_new_price.delete(0, "end")

    except Exception as e:
        messagebox.showerror("Error", f"Add failed\n{e}")


def update_price():
    try:
        if not entry_update.get() or not e_update_price.get():
            messagebox.showerror("Error", "Fill all fields")
            return

        name = entry_update.get().strip()
        price = float(e_update_price.get())

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE PRODUCTS SET product_price=? WHERE product_name=?", (price, name))
        conn.commit()
        conn.close()

        refresh_products()
        messagebox.showinfo("Success", "Successfully updated")

        entry_update.delete(0, "end")
        e_update_price.delete(0, "end")

    except Exception as e:
        messagebox.showerror("Error", f"Update failed\n{e}")


def delete_product():
    try:
        if not entry_delete.get():
            messagebox.showerror("Error", "Fill all fields")
            return

        name = entry_delete.get().strip()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM PRODUCTS WHERE product_name=?", (name,))
        conn.commit()
        conn.close()

        refresh_products()
        messagebox.showinfo("Success", "Successfully deleted")

        entry_delete.delete(0, "end")

    except Exception as e:
        messagebox.showerror("Error", f"Delete failed\n{e}")


# RECEIPT
def generate_receipt():
    cid = e_rcid.get()

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT product_name, quantity, product_price, customer_name
        FROM PURCHASES WHERE customer_id=?
    """, (cid,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        messagebox.showinfo("Info", "No records found")
        return

    total = 0
    receipt = f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
    receipt += f"Customer ID: {cid}\n"
    receipt += f"Customer Name: {rows[0][3]}\n\n"

    receipt += "-" * 50 + "\n"
    receipt += "{:<20}{:<10}{:>10}\n".format("Product", "Qty", "Total")
    receipt += "-" * 50 + "\n"

    for p, q, pr, _ in rows:
        line = int(q) * float(pr)
        total += line
        receipt += "{:<20}{:<10}{:>10.2f}\n".format(p, q, line)

    discount = 0.05 if total >= 2000 else 0
    final = total - total * discount

    receipt += "-" * 50 + "\n"
    receipt += f"Total: {total:.2f}\n"
    receipt += f"Discount: {total*discount:.2f}\n"
    receipt += f"Final Total: {final:.2f}\n"

    txt.delete("1.0", "end")
    txt.insert("end", receipt)


# CLEAR
def clear_all():
    for e in [e_pid, e_cid, e_cname, e_qty,
              e_new_name, e_new_price,
              entry_update, e_update_price,
              entry_delete, e_rcid]:
        e.delete(0, "end")

    entry_product.delete(0, "end")
    listbox.place_forget()
    txt.delete("1.0", "end")


# UI
root = ctk.CTk()
root.geometry("1300x750")
root.title("Billing System")
root.configure(fg_color=BG)

left = ctk.CTkFrame(root, fg_color=CARD, border_width=2, border_color=BORDER)
center = ctk.CTkFrame(root, fg_color=CARD, border_width=2, border_color=BORDER)
right = ctk.CTkFrame(root, fg_color=CARD, border_width=2, border_color=BORDER)

left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
center.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
right.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)


def entry(p): return ctk.CTkEntry(p, width=240)
def label(p, t): return ctk.CTkLabel(p, text=t, font=("Arial", 13, "bold"))

# LEFT
label(left, "PURCHASE DETAILS").pack(pady=10)

label(left, "Purchase ID").pack()
e_pid = entry(left); e_pid.pack()

label(left, "Customer ID").pack()
e_cid = entry(left); e_cid.pack()

label(left, "Customer Name").pack()
e_cname = entry(left); e_cname.pack()

label(left, "Product Name").pack()
entry_product = entry(left)
entry_product.pack()
entry_product.bind("<KeyRelease>", update_suggestions)

listbox = tk.Listbox(root, font=("Arial", 14))
listbox.bind("<<ListboxSelect>>", select_item)

label(left, "Quantity").pack()
e_qty = entry(left); e_qty.pack()

ctk.CTkButton(left, text="ADD PURCHASE", fg_color=PRIMARY, hover_color=HOVER,
              command=add_purchase).pack(pady=5)

# CENTER
label(center, "PRODUCT MANAGEMENT").pack(pady=10)

label(center, "Product Name").pack()
e_new_name = entry(center); e_new_name.pack()

label(center, "Product Price").pack()
e_new_price = entry(center); e_new_price.pack()

ctk.CTkButton(center, text="ADD PRODUCT", fg_color=PRIMARY, hover_color=HOVER,
              command=add_product).pack(pady=5)

label(center, "Product Name").pack()
entry_update = entry(center); entry_update.pack()
entry_update.bind("<KeyRelease>", update_suggestions)

label(center, "New Price").pack()
e_update_price = entry(center); e_update_price.pack()

ctk.CTkButton(center, text="UPDATE PRICE", fg_color=PRIMARY, hover_color=HOVER,
              command=update_price).pack(pady=5)

label(center, "Delete Product").pack()
entry_delete = entry(center); entry_delete.pack()
entry_delete.bind("<KeyRelease>", update_suggestions)

ctk.CTkButton(center, text="DELETE PRODUCT", fg_color=PRIMARY, hover_color=HOVER,
              command=delete_product).pack(pady=5)

ctk.CTkButton(center, text="CLEAR ALL", fg_color=PRIMARY, hover_color=HOVER,
              command=clear_all).pack(pady=10)

# RIGHT
label(right, "RECEIPT").pack(pady=10)

label(right, "Customer ID").pack()
e_rcid = entry(right); e_rcid.pack()

ctk.CTkButton(right, text="GENERATE RECEIPT", fg_color=PRIMARY, hover_color=HOVER,
              command=generate_receipt).pack(pady=5)

txt = ctk.CTkTextbox(right, width=420, height=500, font=("Courier", 12))
txt.pack(pady=10)

root.mainloop()