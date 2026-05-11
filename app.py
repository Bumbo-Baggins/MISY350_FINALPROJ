import streamlit as st
import data_layer
import service_layer
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
ai_assistant = service_layer.AIChatAssistant(api_key)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

dm = data_layer.DataManager()
inv_service = service_layer.InventoryService(dm)

users = dm.load_data(dm.users_file, {})

if "admin" not in users:
    users["admin"] = {"password": hash_password("admin123"), "role": "Shop Owner"}
    dm.save_data(dm.users_file, users)
if "staff" not in users:
    users["staff"] = {"password": hash_password("staff123"), "role": "Employee"}
    dm.save_data(dm.users_file, users)

st.set_page_config("Inventory Manager", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Small Business Inventory Manager")
    
    with st.expander("View Test Accounts", expanded=True):
        st.info("* Owner: `admin` | Pass: `admin123`\n* Employee: `staff` | Pass: `staff123`")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")
            if submitted:
                if u in users and users[u]["password"] == hash_password(p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.session_state["role"] = users[u]["role"]
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            ru = st.text_input("New Username")
            rp = st.text_input("New Password", type="password")
            rr = st.selectbox("Role", ["Employee", "Shop Owner"])
            reg_submit = st.form_submit_button("Register")
            if reg_submit:
                if ru.strip() and rp.strip():
                    if ru in users:
                        st.error("Username already exists.")
                    else:
                        users[ru] = {"password": hash_password(rp), "role": rr}
                        dm.save_data(dm.users_file, users)
                        st.success("Account created! You can now log in.")
                else:
                    st.error("Username and password cannot be empty.")

else:
    with st.sidebar:
        st.write(f"**User:** {st.session_state['username']}")
        st.write(f"**Role:** {st.session_state['role']}")
        st.divider()
        
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Dashboard"

        nav_options = ["Dashboard", "Account Settings"]
        if st.session_state["role"] == "Shop Owner":
            nav_options.insert(1, "Archive Management")
            
        st.subheader("Navigation")
        for option in nav_options:
            btn_type = "primary" if st.session_state["current_page"] == option else "secondary"
            if st.button(option, use_container_width=True, type=btn_type):
                st.session_state["current_page"] = option
                st.rerun()
                
        current_page = st.session_state["current_page"]
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    inventory_list = inv_service.get_all_inventory_dicts()
    active_items = [i for i in inventory_list if not i.get("archived", False)]
    archived_items = [i for i in inventory_list if i.get("archived", False)]

    if current_page == "Dashboard":
        if st.session_state["role"] == "Shop Owner":
            st.title("Owner Dashboard")
            st.dataframe(active_items, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Add Product")
                with st.form("add_form"):
                    n = st.text_input("Name")
                    p = st.number_input("Price", min_value=0.0)
                    s = st.number_input("Stock", min_value=0)
                    if st.form_submit_button("Add Item"):
                        if n.strip():
                            inv_service.add_product(n, p, s)
                            st.rerun()
                        else:
                            st.error("Product name required.")

            with col2:
                st.subheader("Update Product")
                if active_items:
                    with st.form("update_form"):
                        # Selectbox is searchable by default, format_func makes ID visible
                        target_id = st.selectbox(
                            "Select Item (Type to search Name or ID)", 
                            [i["id"] for i in active_items],
                            format_func=lambda x: f"{x} : {next(i['name'] for i in active_items if i['id'] == x)}"
                        )
                        item = next(i for i in active_items if i["id"] == target_id)
                        up = st.number_input("New Price", value=float(item["price"]), min_value=0.0)
                        us = st.number_input("New Stock", value=int(item["stock"]), min_value=0)
                        
                        if st.form_submit_button("Update Item"):
                            inv_service.update_product(target_id, up, us)
                            st.rerun()
                else:
                    st.info("No active items to update.")

        elif st.session_state["role"] == "Employee":
            st.title("Employee Dashboard")
            st.dataframe(active_items, use_container_width=True)
            
            st.subheader("Record Sale")
            if active_items:
                with st.form("sale_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        sell_id = st.selectbox(
                            "Item Sold (Type to search Name or ID)", 
                            [i["id"] for i in active_items],
                            format_func=lambda x: f"{x} : {next(i['name'] for i in active_items if i['id'] == x)}"
                        )
                    with col2:
                        sell_q = st.number_input("Qty", min_value=1)
                    
                    if st.form_submit_button("Record Sale", use_container_width=True):
                        if inv_service.record_sale(sell_id, sell_q):
                            st.success("Sale Recorded")
                            st.rerun()
                        else:
                            st.error("Insufficient stock or invalid item.")
            else:
                st.info("No active items available.")

        st.divider()
        st.subheader("AI Business Assistant")
        st.info("Ask the AI for advice on restocking or inventory trends.")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hi! Ask me about the inventory."}]

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        user_input = st.chat_input("How can I help you?")
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with chat_container.chat_message("user"):
                st.markdown(user_input)
                
            with chat_container.chat_message("assistant"):
                with st.spinner("Consulting the AI..."):
                    current_data = inv_service.get_all_inventory_dicts()
                    answer = ai_assistant.generate_response(current_data, st.session_state.messages)
                    st.markdown(answer)
                    
            st.session_state.messages.append({"role": "assistant", "content": answer})

    elif current_page == "Archive Management":
        st.title("Archive Management")
        st.write("Manage discontinued or inactive products.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Archived Items")
            if archived_items:
                st.dataframe(archived_items, use_container_width=True)
            else:
                st.info("No items are currently archived.")
                
        with col2:
            st.subheader("Toggle Archive Status")
            if inventory_list:
                with st.form("archive_form"):
                    archive_id = st.selectbox(
                        "Select Product (Type to search Name or ID)", 
                        [i["id"] for i in inventory_list],
                        format_func=lambda x: f"{x} : {next(i['name'] for i in inventory_list if i['id'] == x)} (Archived: {next(i.get('archived', False) for i in inventory_list if i['id'] == x)})"
                    )
                    selected_item = next(i for i in inventory_list if i["id"] == archive_id)
                    is_archived = selected_item.get("archived", False)
                    
                    button_label = "Unarchive Item" if is_archived else "Archive Item"
                    if st.form_submit_button(button_label):
                        inv_service.toggle_archive(archive_id, not is_archived)
                        st.rerun()

    elif current_page == "Account Settings":
        st.title("Account Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Update Credentials")
            with st.form("update_account_form"):
                new_username = st.text_input("New Username (Leave blank to keep current)", value=st.session_state["username"])
                new_password = st.text_input("New Password (Leave blank to keep current)", type="password")
                
                if st.form_submit_button("Update Account"):
                    current_user = st.session_state["username"]
                    pwd_hash = hash_password(new_password) if new_password.strip() else None
                    target_user = new_username.strip() if new_username.strip() else current_user
                    
                    success, msg = service_layer.update_user_account(current_user, target_user, pwd_hash, users, dm)
                    
                    if success:
                        st.session_state["username"] = target_user
                        st.success(msg)
                    else:
                        st.error(msg)
                        
        with col2:
            st.subheader("Danger Zone")
            with st.expander("Delete Account"):
                st.warning("This action cannot be undone. All your data will be permanently removed.")
                st.write(f"To confirm, type your username (**{st.session_state['username']}**) below:")
                
                with st.form("delete_account_form"):
                    confirm_text = st.text_input("Confirm Username")
                    delete_submitted = st.form_submit_button("Delete My Account", type="primary", use_container_width=True)
                    
                    if delete_submitted:
                        if confirm_text == st.session_state["username"]:
                            if service_layer.delete_account(st.session_state["username"], users, dm):
                                st.session_state.clear()
                                st.rerun()
                        else:
                            st.error("Username does not match. Account deletion cancelled.")