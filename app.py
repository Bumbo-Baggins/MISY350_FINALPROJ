import streamlit as st
import data_layer
import service_layer
import uuid

# 1. Create the Data Manager object
dm = data_layer.DataManager()

# 2. Use the object's method to load your data
users = dm.load_data(dm.users_file, {})
inventory_raw = dm.load_data(dm.inventory_file, [])

# 3. Initialize your service layer (which we will build next)
# This will turn raw JSON dictionaries into Product objects
inv_service = service_layer.InventoryService(dm)

st.set_page_config("Inventory Manager", layout="wide", initial_sidebar_state="expanded")

# File paths
users_file = "users.json"
inventory_file = "inventory.json"

# Load data using the data layer
users = data_layer.load_json(users_file, {})
inventory = data_layer.load_json(inventory_file, [])

# Ensure test accounts exist for the rubric requirement
if "admin" not in users:
    users["admin"] = {"password": "admin123", "role": "Shop Owner"}
    data_layer.save_json(users_file, users)
if "staff" not in users:
    users["staff"] = {"password": "staff123", "role": "Employee"}
    data_layer.save_json(users_file, users)

# Session State Initialization [cite: 205]
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None

# --- UI LOGIC ---

if not st.session_state["logged_in"]:
    st.title("Small Business Inventory Manager")
    st.info("**Test Accounts:**\n* Owner: `admin` | Pass: `admin123`\n* Employee: `staff` | Pass: `staff123`")
    
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
        # Inside your registration tab logic:
        if st.button("Register", type="primary"):
            if reg_user in users:
                st.error("Username already exists.")
            elif reg_user and reg_pass:
                users[reg_user] = {"password": reg_pass, "role": reg_role}
                
                # Use the class method 'save_data' instead of 'save_json'
                dm.save_data(dm.users_file, users)
                
                st.success("Account created successfully. Please log in.")

else:
    # Sidebar Navigation and Account Management [cite: 95, 206]
    with st.sidebar:
        st.write(f"**User:** {st.session_state['username']}")
        st.write(f"**Role:** {st.session_state['role']}")
        st.divider()
        
        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state.clear()
            st.rerun()

        st.divider()
        if st.button("Delete My Account", type="primary", use_container_width=True):
            if service_layer.delete_account(st.session_state["username"], users, users_file):
                st.session_state.clear()
                st.rerun()

    # --- DASHBOARDS ---
    # Nesting these inside the 'else' ensures they only render when logged in 
    
    if st.session_state["role"] == "Shop Owner":
        st.title("Owner Dashboard")
        st.markdown("### Current Inventory")
        st.dataframe(inventory, use_container_width=True)
        
        st.divider()
        st.markdown("### Manage Products")
        action = st.radio("Select Action", ["Add Product", "Update Product", "Delete Product"], horizontal=True)
        
        if action == "Add Product":
            col1, col2, col3 = st.columns(3)
            with col1: name = st.text_input("Item Name", key="add_name")
            with col2: price = st.number_input("Price", min_value=0.0, key="add_price")
            with col3: stock = st.number_input("Stock", min_value=0, key="add_stock")
            
            if st.button("Add Item", type="primary"):
                if name:
                    new_item = {"id": str(uuid.uuid4())[:8], "name": name, "price": price, "stock": stock}
                    inventory.append(new_item)
                    data_layer.save_json(inventory_file, inventory)
                    st.rerun()

        elif action == "Update Product" and inventory:
            item_names = [i["name"] for i in inventory]
            target = st.selectbox("Select Item", item_names)
            item = next(i for i in inventory if i["name"] == target)
            
            col1, col2 = st.columns(2)
            new_p = col1.number_input("New Price", value=float(item["price"]))
            new_s = col2.number_input("New Stock", value=int(item["stock"]))
            
            if st.button("Update"):
                item["price"], item["stock"] = new_p, new_s
                data_layer.save_json(inventory_file, inventory)
                st.rerun()

    elif st.session_state["role"] == "Employee":
        st.title("Employee Dashboard")
        
        # Stock Alerts [cite: 212]
        low_stock = [i for i in inventory if i["stock"] <= 5]
        if low_stock:
            for i in low_stock:
                st.error(f"Low Stock: {i['name']} ({i['stock']} left)")
        
        st.divider()
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Catalog")
            st.dataframe(inventory, use_container_width=True)
            
        with col2:
            st.subheader("Log Sale")
            if inventory:
                sell_target = st.selectbox("Item", [i["name"] for i in inventory], key="emp_sell")
                qty = st.number_input("Quantity", min_value=1, key="emp_qty")
                if st.button("Record Sale", type="primary"):
                    item = next(i for i in inventory if i["name"] == sell_target)
                    if item["stock"] >= qty:
                        item["stock"] -= qty
                        data_layer.save_json(inventory_file, inventory)
                        st.rerun()