import os
import re
from datetime import datetime, timedelta

import flet as ft
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client["library"]
books_col = db["books"]
userinfo_col = db["userinfo"]
admin_col = db["admin"]
borrows_col = db["borrows"]


#You can easily change colors
PRIMARY = "#576238"
PRIMARY_DARK = "#F0EADC"
SURFACE = "#1E1E2E"
SURFACE_LIGHT = "#2A2A3C"
CARD_BG = "#313145"
TEXT_PRIMARY = "white"
TEXT_SECONDARY = "#B0B0C0"
SUCCESS = "#4CAF50"
ERROR = "#EF5350"
WARNING = "#FFA726"

#Animation durations
FADE_DURATION = 400
SCALE_DURATION = 350
SLIDE_DURATION = 300


async def main(page: ft.Page):
    page.title = "Library Management System"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = SURFACE
    page.window.width = 480
    page.window.height = 700
    await page.window.center()
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    current_user = {"username": "", "is_admin": False}

    def show_snack(msg, color=SUCCESS):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor=color,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def styled_button(text, on_click, bgcolor=PRIMARY, icon=None, width=260):
        return ft.Button(
            content=ft.Row(
                [
                    ft.Icon(icon, color=TEXT_PRIMARY, size=20) if icon else ft.Container(),
                    ft.Text(text, color=TEXT_PRIMARY, size=14),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            on_click=on_click,
            width=width,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=bgcolor,
                color=TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

    def styled_field(label, password=False, hint=""):
        return ft.TextField(
            label=label,
            hint_text=hint,
            password=password,
            can_reveal_password=password,
            border_radius=12,
            border_color=PRIMARY,
            focused_border_color=PRIMARY_DARK,
            text_size=14,
            width=300,
        )

    def page_title(text, subtitle=None):
        controls = [
            ft.Text(text, size=26, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ]
        if subtitle:
            controls.append(
                ft.Text(subtitle, size=14, color=TEXT_SECONDARY),
            )
        return ft.Column(controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def card_container(*children, width=380):
        return ft.Container(
            content=ft.Column(
                list(children),
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
            bgcolor=CARD_BG,
            border_radius=20,
            padding=30,
            width=width,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color="#4D000000",
            ),
            animate_scale=ft.Animation(SCALE_DURATION, ft.AnimationCurve.EASE_OUT),
            scale=1,
        )

    def animated_view(*children):
        container = ft.Container(
            content=ft.Column(
                list(children),
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            opacity=0,
            offset=ft.Offset(0, 0.03),
            animate_opacity=ft.Animation(FADE_DURATION, ft.AnimationCurve.EASE_IN_OUT),
            animate_offset=ft.Animation(SLIDE_DURATION, ft.AnimationCurve.EASE_OUT),
        )
        return container

    def show_view(view_container):
        page.controls.clear()
        page.controls.append(view_container)
        page.update()
        view_container.opacity = 1
        view_container.offset = ft.Offset(0, 0)
        page.update()

    async def do_exit(_):
        await page.window.close()

    def go_initial_setup(e=None):
        pending_admins = []
        admins_list_column = ft.Column(spacing=8)

        username_field = styled_field("Admin Username", hint="Enter admin username")
        password_field = styled_field("Admin Password", password=True, hint="Min 8 chars, letters & numbers")

        no_admin_text = ft.Text(
            "No admins added yet.",
            size=13,
            color=TEXT_SECONDARY,
            italic=True,
        )
        admins_list_column.controls.append(no_admin_text)

        def refresh_admin_list():
            admins_list_column.controls.clear()
            if not pending_admins:
                admins_list_column.controls.append(
                    ft.Text("No admins added yet.", size=13, color=TEXT_SECONDARY, italic=True)
                )
            else:
                for i, admin in enumerate(pending_admins):
                    admins_list_column.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=PRIMARY, size=18),
                                    ft.Text(
                                        admin["username"],
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_PRIMARY,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.REMOVE_CIRCLE,
                                        icon_color=ERROR,
                                        icon_size=20,
                                        tooltip="Remove",
                                        on_click=lambda _, idx=i: remove_admin(idx),
                                    ),
                                ],
                            ),
                            bgcolor=SURFACE_LIGHT,
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            width=300,
                        )
                    )
            page.update()

        def remove_admin(index):
            if 0 <= index < len(pending_admins):
                removed = pending_admins.pop(index)
                show_snack(f"'{removed['username']}' removed from list.", WARNING)
                refresh_admin_list()

        def add_admin(_):
            username = username_field.value.strip() if username_field.value else ""
            password = password_field.value or ""

            if not username:
                show_snack("Please enter a username.", WARNING)
                return
            if len(password) < 8 or not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
                show_snack("Password must be 8+ chars with letters and numbers!", WARNING)
                return
            if any(a["username"] == username for a in pending_admins):
                show_snack("This username is already in the list!", ERROR)
                return

            pending_admins.append({"username": username, "password": password})
            username_field.value = ""
            password_field.value = ""
            show_snack(f"Admin '{username}' added to list.")
            refresh_admin_list()

        def finalize_setup(_):
            if not pending_admins:
                show_snack("Add at least one admin before proceeding!", WARNING)
                return

            try:
                admin_col.insert_many(pending_admins)
                show_snack(f"{len(pending_admins)} admin(s) created. Setup complete!")
                go_main_menu()
            except Exception as ex:
                show_snack(f"Database error: {ex}", ERROR)

        view = animated_view(
            ft.Container(height=20),
            ft.Icon(ft.Icons.SECURITY_ROUNDED, size=64, color=WARNING),
            page_title("Initial Setup", "Create admin account(s) — this can only be done once"),
            ft.Container(height=6),
            card_container(
                username_field,
                password_field,
                styled_button("Add Admin to List", add_admin, icon=ft.Icons.PERSON_ADD, bgcolor=PRIMARY),
                ft.Divider(color=SURFACE_LIGHT, thickness=1),
                ft.Text("Admins to create:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                admins_list_column,
                ft.Divider(color=SURFACE_LIGHT, thickness=1),
                styled_button(
                    "Complete Setup",
                    finalize_setup,
                    icon=ft.Icons.CHECK_CIRCLE,
                    bgcolor=SUCCESS,
                ),
            ),
        )
        show_view(view)

    def go_main_menu(e=None):
        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.LOCAL_LIBRARY_ROUNDED, size=72, color=PRIMARY),
            page_title("Library Manager", "Modern Library Management System"),
            ft.Container(height=20),
            card_container(
                styled_button("Create Account", go_register, icon=ft.Icons.PERSON_ADD),
                styled_button("Login", go_login, icon=ft.Icons.LOGIN),
                styled_button("Exit", do_exit, bgcolor=ERROR, icon=ft.Icons.EXIT_TO_APP),
            ),
        )
        show_view(view)

    def go_register(e=None):
        username_field = styled_field("Username", hint="Choose a username")
        password_field = styled_field("Password", password=True, hint="Min 8 chars, letters & numbers")

        def do_register(_):
            username = username_field.value.strip() if username_field.value else ""
            password = password_field.value or ""

            if not username:
                show_snack("Please enter a username.", WARNING)
                return
            if userinfo_col.find_one({"username": username}):
                show_snack("Username already exists!", ERROR)
                return
            if admin_col.find_one({"username": username}):
                show_snack("This username is reserved!", ERROR)
                return
            if len(password) < 8 or not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
                show_snack("Password must be 8+ chars with letters and numbers!", WARNING)
                return

            try:
                userinfo_col.insert_one({"username": username, "password": password})
                show_snack("Account created successfully!")
                go_main_menu()
            except Exception as ex:
                show_snack(f"Database error: {ex}", ERROR)

        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, size=56, color=PRIMARY),
            page_title("Create Account"),
            ft.Container(height=10),
            card_container(
                username_field,
                password_field,
                styled_button("Register", do_register, icon=ft.Icons.CHECK_CIRCLE),
                styled_button("Back", go_main_menu, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ),
        )
        show_view(view)

    def go_login(e=None):
        username_field = styled_field("Username")
        password_field = styled_field("Password", password=True)

        def do_login(_):
            username = username_field.value.strip() if username_field.value else ""
            password = password_field.value or ""

            if not username:
                show_snack("Please enter a username.", WARNING)
                return

            admin_data = admin_col.find_one({"username": username})
            user_data = userinfo_col.find_one({"username": username})

            if not admin_data and not user_data:
                show_snack("User not found!", ERROR)
                return

            if admin_data and admin_data["password"] == password:
                current_user["username"] = username
                current_user["is_admin"] = True
                show_snack(f"Welcome, admin {username}!")
                go_admin_panel()
            elif user_data and user_data["password"] == password:
                current_user["username"] = username
                current_user["is_admin"] = False
                show_snack(f"Welcome, {username}!")
                go_library_panel()
            else:
                show_snack("Incorrect password!", ERROR)

        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.LOCK_OPEN_ROUNDED, size=56, color=PRIMARY),
            page_title("Login"),
            ft.Container(height=10),
            card_container(
                username_field,
                password_field,
                styled_button("Login", do_login, icon=ft.Icons.LOGIN),
                styled_button("Back", go_main_menu, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ),
        )
        show_view(view)

    def go_admin_panel(e=None):
        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED, size=56, color=PRIMARY),
            page_title("Admin Panel", f"Logged in as {current_user['username']}"),
            ft.Container(height=10),
            card_container(
                styled_button("Add Book", go_add_book, icon=ft.Icons.ADD_CIRCLE),
                styled_button("Delete Book", go_delete_book, icon=ft.Icons.DELETE, bgcolor=ERROR),
                styled_button("Overdue Returns", go_overdue_list, icon=ft.Icons.WARNING_AMBER_ROUNDED, bgcolor=WARNING),
                styled_button("Logout", go_main_menu, bgcolor=SURFACE_LIGHT, icon=ft.Icons.LOGOUT),
            ),
        )
        show_view(view)

    def go_add_book(e=None):
        name_field = styled_field("Book Name")
        author_field = styled_field("Author")
        copies_field = styled_field("Number of Copies", hint="e.g. 5")

        def do_add(_):
            name = name_field.value.strip() if name_field.value else ""
            author = author_field.value.strip() if author_field.value else ""
            copies = copies_field.value.strip() if copies_field.value else ""

            if not name or not author or not copies:
                show_snack("All fields are required.", WARNING)
                return
            try:
                num = int(copies)
            except ValueError:
                show_snack("Copies must be a number.", WARNING)
                return

            books_col.insert_one({"name": name, "author": author, "number": num})
            show_snack("Book added successfully!")
            go_admin_panel()

        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.BOOK_ROUNDED, size=56, color=PRIMARY),
            page_title("Add a Book"),
            ft.Container(height=10),
            card_container(
                name_field,
                author_field,
                copies_field,
                styled_button("Add Book", do_add, icon=ft.Icons.CHECK),
                styled_button("Back", go_admin_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ),
        )
        show_view(view)

    def go_delete_book(e=None):
        name_field = styled_field("Book Name to Delete")

        def do_delete(_):
            name = name_field.value.strip() if name_field.value else ""
            if not name:
                show_snack("Please enter a book name.", WARNING)
                return
            result = books_col.delete_one({"name": name})
            if result.deleted_count > 0:
                show_snack("Book deleted!")
                go_admin_panel()
            else:
                show_snack("Book not found!", ERROR)

        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, size=56, color=ERROR),
            page_title("Delete a Book"),
            ft.Container(height=10),
            card_container(
                name_field,
                styled_button("Delete", do_delete, bgcolor=ERROR, icon=ft.Icons.DELETE),
                styled_button("Back", go_admin_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ),
        )
        show_view(view)

    def go_overdue_list(e=None):
        cutoff_date = datetime.now() - timedelta(days=14)
        overdue_borrows = list(borrows_col.find({"date": {"$lt": cutoff_date}}))

        items_list = ft.Column(spacing=10)

        if overdue_borrows:
            for item in overdue_borrows:
                borrow_date = item.get("date", datetime.now())
                overdue_days = (datetime.now() - (borrow_date + timedelta(days=14))).days
                username = item.get("username", "Unknown")
                book_name = item.get("name", "Unknown")
                book_author = item.get("author", "Unknown")

                items_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.PERSON, color=ERROR, size=18),
                                        ft.Text(
                                            username,
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_PRIMARY,
                                        ),
                                    ],
                                    spacing=6,
                                ),
                                ft.Text(
                                    f"📖 {book_name} — {book_author}",
                                    size=13,
                                    color=TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    f"Borrowed: {borrow_date.strftime('%Y-%m-%d')}",
                                    size=12,
                                    color=TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    f"⚠ {overdue_days} days overdue",
                                    size=13,
                                    color=ERROR,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ],
                            spacing=4,
                        ),
                        bgcolor=SURFACE_LIGHT,
                        border_radius=12,
                        padding=16,
                        width=340,
                        animate_opacity=ft.Animation(FADE_DURATION, ft.AnimationCurve.EASE_IN),
                    )
                )
        else:
            items_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=SUCCESS, size=24),
                            ft.Text(
                                "No overdue books! All returns are on time.",
                                color=SUCCESS,
                                size=14,
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=16,
                )
            )

        view = animated_view(
            ft.Container(height=30),
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=56, color=WARNING),
            page_title("Overdue Returns", f"{len(overdue_borrows)} overdue book(s)"),
            ft.Container(height=10),
            card_container(items_list, width=380),
            ft.Container(height=10),
            styled_button("Back", go_admin_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ft.Container(height=20),
        )
        show_view(view)

    def go_library_panel(e=None):
        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, size=56, color=PRIMARY),
            page_title("Library", f"Welcome, {current_user['username']}!"),
            ft.Container(height=10),
            card_container(
                styled_button("Borrow a Book", go_borrow, icon=ft.Icons.BOOKMARK_ADD),
                styled_button("Search for a Book", go_search, icon=ft.Icons.SEARCH),
                styled_button("My Borrowed Books", go_my_books, icon=ft.Icons.LIST_ALT),
                styled_button("Logout", go_main_menu, bgcolor=SURFACE_LIGHT, icon=ft.Icons.LOGOUT),
            ),
        )
        show_view(view)

    def go_search(e=None):
        query_field = styled_field("Book Name", hint="Enter book name to search")
        results_column = ft.Column(spacing=10)

        def do_search(_):
            query = query_field.value.strip() if query_field.value else ""
            if not query:
                show_snack("Please enter a book name.", WARNING)
                return

            found = list(books_col.find({"name": query}))
            results_column.controls.clear()

            if found:
                for book in found:
                    stock = book.get("number", 0)
                    stock_color = SUCCESS if stock > 0 else ERROR
                    results_column.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(book.get("name", ""), size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                    ft.Text(f"Author: {book.get('author', '')}", size=13, color=TEXT_SECONDARY),
                                    ft.Text(f"In Stock: {stock}", size=13, color=stock_color, weight=ft.FontWeight.W_600),
                                ],
                                spacing=4,
                            ),
                            bgcolor=SURFACE_LIGHT,
                            border_radius=12,
                            padding=16,
                            width=300,
                            animate_opacity=ft.Animation(FADE_DURATION, ft.AnimationCurve.EASE_IN),
                        )
                    )
            else:
                results_column.controls.append(
                    ft.Text("No books found.", color=TEXT_SECONDARY, size=14),
                )
            page.update()

        view = animated_view(
            ft.Container(height=30),
            ft.Icon(ft.Icons.SEARCH_ROUNDED, size=56, color=PRIMARY),
            page_title("Search Books"),
            ft.Container(height=10),
            card_container(
                query_field,
                styled_button("Search", do_search, icon=ft.Icons.SEARCH),
            ),
            results_column,
            ft.Container(height=10),
            styled_button("Back", go_library_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ft.Container(height=20),
        )
        show_view(view)

    def go_borrow(e=None):
        name_field = styled_field("Book Name")
        author_field = styled_field("Author Name")

        def do_borrow(_):
            book_name = name_field.value.strip() if name_field.value else ""
            book_author = author_field.value.strip() if author_field.value else ""

            if not book_name or not book_author:
                show_snack("Both fields are required.", WARNING)
                return

            try:
                book = books_col.find_one({"name": book_name, "author": book_author})
                if book:
                    if book.get("number", 0) > 0:
                        books_col.update_one({"_id": book["_id"]}, {"$inc": {"number": -1}})
                        borrows_col.insert_one({
                            "username": current_user["username"],
                            "name": book_name,
                            "author": book_author,
                            "date": datetime.now(),
                        })
                        show_snack(f"Borrowed '{book_name}' — return within 14 days.")
                        go_library_panel()
                    else:
                        show_snack("Sorry, this book is out of stock.", WARNING)
                else:
                    show_snack("Book/author combination not found.", ERROR)
            except Exception as ex:
                show_snack(f"Database error: {ex}", ERROR)

        view = animated_view(
            ft.Container(height=40),
            ft.Icon(ft.Icons.BOOKMARK_ADD_ROUNDED, size=56, color=PRIMARY),
            page_title("Borrow a Book"),
            ft.Container(height=10),
            card_container(
                name_field,
                author_field,
                styled_button("Borrow", do_borrow, icon=ft.Icons.CHECK),
                styled_button("Back", go_library_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ),
        )
        show_view(view)

    def go_my_books(e=None):
        user_books = list(borrows_col.find({"username": current_user["username"]}))
        books_list = ft.Column(spacing=10)

        if user_books:
            for item in user_books:
                borrow_date = item.get("date", datetime.now())
                remaining = (borrow_date + timedelta(days=14)) - datetime.now()
                if remaining.days > 0:
                    time_text = f"{remaining.days} days left"
                    time_color = SUCCESS
                else:
                    time_text = "EXPIRED"
                    time_color = ERROR

                b_name = item.get("name", "")
                b_author = item.get("author", "")

                def make_return(name=b_name, author=b_author):
                    def do_return(_):
                        borrows_col.delete_one({
                            "username": current_user["username"],
                            "name": name,
                            "author": author,
                        })
                        books_col.update_one(
                            {"name": name, "author": author},
                            {"$inc": {"number": 1}},
                        )
                        show_snack(f"'{name}' returned successfully!")
                        go_my_books()
                    return do_return

                books_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(b_name, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                        ft.Text(f"by {b_author}", size=12, color=TEXT_SECONDARY),
                                        ft.Text(time_text, size=12, color=time_color, weight=ft.FontWeight.W_600),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.KEYBOARD_RETURN_ROUNDED,
                                    icon_color=SUCCESS,
                                    tooltip="Return Book",
                                    on_click=make_return(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        bgcolor=SURFACE_LIGHT,
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        width=340,
                        animate_opacity=ft.Animation(FADE_DURATION, ft.AnimationCurve.EASE_IN),
                    )
                )
        else:
            books_list.controls.append(
                ft.Text("You have no borrowed books.", color=TEXT_SECONDARY, size=14),
            )

        view = animated_view(
            ft.Container(height=30),
            ft.Icon(ft.Icons.LIST_ALT_ROUNDED, size=56, color=PRIMARY),
            page_title("My Borrowed Books"),
            ft.Container(height=10),
            card_container(books_list, width=380),
            ft.Container(height=10),
            styled_button("Back", go_library_panel, bgcolor=SURFACE_LIGHT, icon=ft.Icons.ARROW_BACK),
            ft.Container(height=20),
        )
        show_view(view)

    if admin_col.count_documents({}) == 0:
        go_initial_setup()
    else:
        go_main_menu()


ft.run(main)
