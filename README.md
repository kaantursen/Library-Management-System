# 📚 Library Management System

A professional, GUI-based library management application built with **Python**, **Tkinter**, and **MongoDB Atlas**. 

---

## ✨ Key Features
* **User Dashboard:** Search for books, borrow titles, and track remaining return time.
* **Admin Panel:** Full CRUD operations (Add/Delete) and real-time inventory tracking.
* **Cloud Integration:** Powered by MongoDB Atlas for secure, real-time data storage.

---

## 🛠️ Installation & Setup

### 1. Requirements
* Python 3.10+
* MongoDB Atlas Account

### 2. MongoDB Atlas Configuration (Important)
To make this app work, you need a cloud database:
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new **Cluster** and a database named `library`.
3. Create three collections: `books`, `userinfo`, and `borrows` , `admin`.
4. Go to **Database Access** and create a user with a password.
5. Go to **Network Access** and "Allow Access from Anywhere" (0.0.0.0/0).
6. Click **Connect** -> **Drivers** -> Copy your **Connection String**.
7. Edit `admin` database and add admin accounts.

### 3. Environment Configuration
Create a `.env` file in the root directory and paste your connection string:
```env
MONGO_URI=mongodb+srv://your_username:your_password@cluster.mongodb.net/library
