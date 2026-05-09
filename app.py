import streamlit as st
import json
from pathlib import Path
import uuid

st.set_page_config("Inventory Manager", layout="wide", initial_sidebar_state="expanded")


#checks if the file exists using the Path library.
#If the file is found, it opens the file and loads the JSON data.
#If the file is missing, it returns the provided default_data 
# (i THINK this prevents app crashes when app is running w/o .necessary .json files (users and inventory))
def load_json(filepath, default_data):
    path = Path(filepath)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return default_data

# writes Python data into a JSON file.
def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

users_file = "users.json"
inventory_file = "inventory.json"

users = load_json(users_file, {})
inventory = load_json(inventory_file, [])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None

if not st.session_state["logged_in"]:
    st.title("Small Business Inventory Manager")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        login_user = st.text_input("Username", key="log_user")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Log In", type="primary"):
            if login_user in users and users[login_user]["password"] == login_pass:
                st.session_state["logged_in"] = True
                st.session_state["username"] = login_user
                st.session_state["role"] = users[login_user]["role"]
                st.rerun()
            else:
                st.error("Invalid credentials.")
    
    with tab2:
        st.subheader("Register")
        reg_user = st.text_input("New Username", key="reg_user")
        reg_pass = st.text_input("New Password", type="password", key="reg_pass")
        reg_role = st.selectbox("Role", ["Employee", "Shop Owner"])
        if st.button("Register", type="primary"):
            if reg_user in users:
                st.error("Username already exists.")
            elif reg_user and reg_pass:
                users[reg_user] = {"password": reg_pass, "role": reg_role}
                save_json(users_file, users)
                st.success("Account created successfully. Please log in.")
            else:
                st.error("Please fill all required fields.")

# creates a user profile and logout interface in the sidebar. It executes only when a user is logged in.
else:
    with st.sidebar:
        st.write(f"**User:** {st.session_state['username']}")
        st.write(f"**Role:** {st.session_state['role']}")
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = ""
            st.rerun()

#dashboard for shop owners
if st.session_state["role"] == "Shop Owner":
        st.title("Owner Dashboard")
        st.markdown("### Current Inventory")
        if len(inventory) > 0:
            st.dataframe(inventory, use_container_width=True)
        else:
            st.warning("No items found in inventory.")
        
        st.divider()
        st.markdown("### Manage Products")
        action = st.radio("Select Action", ["Add Product", "Update Product", "Delete Product"], horizontal=True)
        
        # allows shop owners to add new products
        # each item is given. a unique ID using the uuid library, and the new item is appended to inventory list.
        # we are assuming the shop owner will add items from scratch, so no initial inventory
        if action == "Add Product":
            col1, col2, col3 = st.columns(3)
            with col1: new_name = st.text_input("Item Name")
            with col2: new_price = st.number_input("Unit Price", min_value=0.0, format="%.2f")
            with col3: new_stock = st.number_input("Initial Stock", min_value=0, step=1)
            
            if st.button("Add Item", type="primary"):
                new_item = {
                    "id": str(uuid.uuid4())[:8],
                    "name": new_name,
                    "price": new_price,
                    "stock": new_stock
                }
                inventory.append(new_item)
                save_json(inventory_file, inventory)
                st.success("Item added successfully.")
                st.rerun()

#shopowners update products here
        elif action == "Update Product":
            if inventory:
                item_names = [item["name"] for item in inventory]
                selected_name = st.selectbox("Select Item", item_names)
                selected_item = next(item for item in inventory if item["name"] == selected_name)
                
                col1, col2 = st.columns(2)
                with col1: upd_price = st.number_input("New Price", value=float(selected_item["price"]), format="%.2f")
                with col2: upd_stock = st.number_input("New Stock", value=int(selected_item["stock"]), step=1)
                
                if st.button("Update Item", type="primary"):
                    selected_item["price"] = upd_price
                    selected_item["stock"] = upd_stock
                    save_json(inventory_file, inventory)
                    st.success("Item updated successfully.")
                    st.rerun()
            else:
                st.info("No items available to update.")
                
        elif action == "Delete Product":
            if inventory:
                item_names = [item["name"] for item in inventory]
                del_name = st.selectbox("Select Item to Delete", item_names)
                
                if st.button("Delete Item", type="primary"):
                    inventory[:] = [item for item in inventory if item["name"] != del_name]
                    save_json(inventory_file, inventory)
                    st.success("Item deleted successfully.")
                    st.rerun()
            else:
                st.info("No items available to delete.")

# here, employees can view inventory. 
# They also receive low stock alerts when inventory levels are low (equal to or less than 5).
elif st.session_state["role"] == "Employee":
            st.title("Employee Dashboard")
            
            st.markdown("### Stock Alerts")
            alerts = [item for item in inventory if item["stock"] <= 5]
            if alerts:
                for item in alerts:
                    st.error(f"Low Stock Alert: {item['name']} (Quantity: {item['stock']})")
            else:
                st.success("All stock levels are optimal.")
            
            st.divider()
            col1, col2 = st.columns([3, 2])

            # employees can view product catalog
            with col1:
                st.markdown("### Product Catalog")
                if len(inventory) > 0:
                    st.dataframe(inventory, use_container_width=True)
                else:
                    st.warning("Catalog is empty.")

            # here the employee can log daily sales. 
            # can update inventory levels based on sales, and also record the sale in the orders.json file.
            with col2:
                st.markdown("### Log Daily Sale")
                if inventory:
                    item_names = [item["name"] for item in inventory]
                    sold_name = st.selectbox("Item Sold", item_names)
                    sold_qty = st.number_input("Quantity Sold", min_value=1, step=1)
                    
                    if st.button("Record Sale", type="primary", use_container_width=True):
                        selected_item = next(item for item in inventory if item["name"] == sold_name)
                        if selected_item["stock"] >= sold_qty:
                            selected_item["stock"] -= sold_qty
                            save_json(inventory_file, inventory)
                            st.success(f"Sale recorded. {sold_qty} units deducted.")
                            st.rerun()
                        else:
                            st.error("Insufficient stock to log sale.")
                else:
                    st.info("No items available to sell.")

# this is a test to see if my git is working