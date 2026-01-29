import os
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

MONGO_URI = os.getenv("MONGO_URI")

# Database Connection
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client["library"]
books = db["books"]
userinfo = db["userinfo"]
admin = db["admin"]

root = tk.Tk()
current_user = ""


# Window Centering Function
def center_window(window, width=500, height=400):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_acc():
    username = simpledialog.askstring("Register", "Enter your username:")
    if not username: return

    if userinfo.find_one({"username": username}):
        messagebox.showerror("Error", "Username already exists!")
        return

    pass_window = tk.Toplevel(root)
    pass_window.title("Set Password")
    center_window(pass_window, 300, 200)

    tk.Label(pass_window, text="Enter Password:").pack(pady=5)
    pass_entry = tk.Entry(pass_window, show="*")
    pass_entry.pack(pady=5)

    def save_db():
        password = pass_entry.get()
        if len(password) < 8 or not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
            messagebox.showwarning("Weak Password", "Must be 8+ chars with letters and numbers!")
            return

        try:
            userinfo.insert_one({"username": username, "password": password})
            messagebox.showinfo("Success", "Account created successfully!")
            pass_window.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(pass_window, text="Save", command=save_db).pack(pady=10)


def login():
    global current_user
    username = simpledialog.askstring("Login", "Enter Username:")
    if not username: return

    admin_data = admin.find_one({"username": username})
    user_data = userinfo.find_one({"username": username})

    if not admin_data and not user_data:
        messagebox.showerror("Error", "User not found!")
        return

    login_win = tk.Toplevel(root)
    login_win.title("Password Entry")
    center_window(login_win, 300, 150)

    tk.Label(login_win, text=f"Password for {username}:").pack(pady=5)
    pass_entry = tk.Entry(login_win, show="*")
    pass_entry.pack(pady=5)

    def check_pass():
        global current_user
        password_attempt = pass_entry.get()
        if admin_data and admin_data["password"] == password_attempt:
            current_user = username
            login_win.destroy()
            admin_panel(username)
        elif user_data and user_data["password"] == password_attempt:
            current_user = username
            login_win.destroy()
            library_panel(username)
        else:
            messagebox.showerror("Error", "Incorrect password!")

    tk.Button(login_win, text="Login", command=check_pass).pack(pady=10)


def admin_panel(username):
    admin_win = tk.Toplevel(root)
    admin_win.title(f"Admin Panel - {username}")
    center_window(admin_win, 500, 400)

    tk.Label(admin_win, text="Administrator Access", font=("Arial", 14, "bold")).pack(pady=15)
    tk.Button(admin_win, text="Add Book", command=add_book, width=25).pack(pady=5)
    tk.Button(admin_win, text="Delete Book", command=delete_book, width=25).pack(pady=5)
    tk.Button(admin_win, text="Logout", command=admin_win.destroy, fg="red").pack(pady=20)


def library_panel(username):
    lib_win = tk.Toplevel(root)
    lib_win.title(f"Library - {username}")
    center_window(lib_win, 500, 450)

    tk.Label(lib_win, text=f"Welcome, {username}!", font=("Arial", 14, "bold")).pack(pady=15)
    tk.Button(lib_win, text="Borrow a Book", command=borrow, width=25).pack(pady=5)
    tk.Button(lib_win, text="Search for a Book", command=search, width=25).pack(pady=5)
    tk.Button(lib_win, text="My Borrowed Books", command=list_all, width=25).pack(pady=5)
    tk.Button(lib_win, text="Logout", command=lib_win.destroy, fg="red").pack(pady=20)


def add_book():
    name = simpledialog.askstring("Add Book", "Book Name:")
    if not name: return
    author = simpledialog.askstring("Add Book", "Author:")
    if not author: return
    num = simpledialog.askinteger("Add Book", "Number of copies:")
    if not num: return

    books.insert_one({"name": name, "author": author, "number": num})
    messagebox.showinfo("Success", "Book added successfully!")


def delete_book():
    name = simpledialog.askstring("Delete", "Enter book name to delete:")
    if not name: return

    result = books.delete_one({"name": name})
    if result.deleted_count > 0:
        messagebox.showinfo("Success", "Book deleted!")
    else:
        messagebox.showerror("Error", "Book not found!")


def search():
    query = simpledialog.askstring("Search", "Enter book name:")
    if not query: return

    # find_one yerine find kullanarak tüm eşleşmeleri alıyoruz
    all_books = list(books.find({"name": query}))

    if all_books:
        offset = 0
        for book in all_books:
            search_win = tk.Toplevel(root)
            search_win.title(f"Found: {book['name']}")
            w, h = 300, 200
            x = (search_win.winfo_screenwidth() // 2) - (w // 2) + offset
            y = (search_win.winfo_screenheight() // 2) - (h // 2) + offset
            search_win.geometry(f"{w}x{h}+{x}+{y}")

            tk.Label(search_win, text="[ Book Details ]", font=("Arial", 10, "bold")).pack(pady=10)
            tk.Label(search_win, text=f"Name: {book.get('name')}").pack()
            tk.Label(search_win, text=f"Author: {book.get('author')}").pack()
            tk.Label(search_win, text=f"In Stock: {book.get('number')}", fg="green").pack(pady=5)
            tk.Button(search_win, text="Close", command=search_win.destroy).pack(pady=10)

            offset += 30
    else:
        messagebox.showinfo("Not Found", "No books found with that name.")


def borrow():
    book_name = simpledialog.askstring("Borrow", "Book Name:")
    if not book_name: return
    book_author = simpledialog.askstring("Borrow", "Author Name:")
    if not book_author: return

    try:
        book = db["books"].find_one({"name": book_name, "author": book_author})

        if book:
            if book.get("number", 0) > 0:
                db["books"].update_one(
                    {"_id": book["_id"]},
                    {"$inc": {"number": -1}}
                )
                db["borrows"].insert_one({
                    "username": current_user,
                    "name": book_name,
                    "author": book_author,
                    "date": datetime.now()
                })
                messagebox.showinfo("Success",
                                    f"You borrowed '{book_name}' by {book_author}.\nPlease return it within 14 days.")
            else:
                messagebox.showwarning("Out of Stock", "Sorry, this book is currently out of stock.")
        else:
            messagebox.showerror("Not Found", "We couldn't find this book/author combination.")

    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")


def list_all():
    list_win = tk.Toplevel(root)
    list_win.title("My Books")
    center_window(list_win, 550, 450)
    list_win.grab_set()
    user_books = list(db["borrows"].find({"username": current_user}))

    tree = ttk.Treeview(list_win, columns=("Name", "Author", "Time"), show="headings")
    tree.heading("Name", text="Title")
    tree.heading("Author", text="Author")
    tree.heading("Time", text="Remaining Time")

    for item in user_books:
        borrow_date = item.get("date", datetime.now())
        remaining = (borrow_date + timedelta(days=14)) - datetime.now()

        if remaining.days > 0:
            time_text = f"{remaining.days} days left"
        else:
            time_text = "EXPIRED"

        tree.insert("", tk.END, values=(item.get("name"), item.get("author"), time_text))

    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    def return_book():
        selected = tree.selection()
        if not selected: return
        item_values = tree.item(selected)["values"]
        b_name = item_values[0]
        b_author = item_values[1]
        db["borrows"].delete_one({"username": current_user, "name": b_name, "author": b_author})
        books.update_one({"name": b_name, "author": b_author}, {"$inc": {"number": 1}})

        messagebox.showinfo("Returned", f"'{b_name}' returned successfully!")
        list_win.destroy()
        list_all()
    tk.Button(list_win, text="RETURN SELECTED BOOK", bg="green", fg="white", command=return_book).pack(pady=10)

root.title("Library Management System")
center_window(root, 400, 300)

tk.Label(root, text="MAIN MENU", font=("Arial", 16, "bold")).pack(pady=20)
tk.Button(root, text="Create Account", command=create_acc, width=20).pack(pady=5)
tk.Button(root, text="Login", command=login, width=20).pack(pady=5)
tk.Button(root, text="Exit", command=root.destroy, width=20).pack(pady=5)

root.mainloop()