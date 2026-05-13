import streamlit as st
import data_layer
import service_layer
import os
from dotenv import load_dotenv
import time

# Setup and Initialization
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
ai_assistant = service_layer.AIChatAssistant(api_key)

dm = data_layer.DataManager()
inv_service = service_layer.InventoryService(dm)

service_layer.seed_initial_data(dm, inv_service)
users = dm.load_data(dm.users_file, {})

st.set_page_config("Inventory Manager", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# UI Rendering

def render_login_register():
    st.title("Small Business Inventory Manager")
    
    with st.expander("View Test Accounts", expanded=True):
        st.info("* Admin: `admin` | Pass: `admin123`\n* Employee: `staff` | Pass: `staff123`")
    
    tab1, tab2 = st.tabs(["Log In", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                success, role = service_layer.validate_login(u, p, users)
                if success:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.session_state["role"] = role
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            ru = st.text_input("New Username")
            rp = st.text_input("New Password", type="password")
            rr = st.selectbox("Role", ["Employee", "Admin"])
            if st.form_submit_button("Register"):
                success, msg = service_layer.register_user(ru, rp, rr, users, dm)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

def render_sidebar():
    with st.sidebar:
        with st.container(border=True):
            st.write(f"User: {st.session_state['username']}")
            st.write(f"Role: {st.session_state['role']}")
        
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Dashboard"

        nav_options = ["Dashboard", "Account Settings"]
        if st.session_state["role"] == "Admin":
            nav_options.insert(1, "Recent Sales")
            nav_options.insert(2, "Archive Management")
            
        st.subheader("Navigation")
        for option in nav_options:
            btn_type = "primary" if st.session_state["current_page"] == option else "secondary"
            if st.button(option, use_container_width=True, type=btn_type):
                st.session_state["current_page"] = option
                st.rerun()
                
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

def display_ai_assistant(active_items):
    st.divider()
    with st.expander("💬 Chat with AI Business Assistant"):
        st.info("Ask for advice on restocking or inventory trends.")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hi! Ask me about inventory."}]

        chat_container = st.container(height=300)
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
                with st.spinner("Consulting..."):
                    low_stock = [i['name'] for i in active_items if i['stock'] < 10]
                    summary = f"Total active items: {len(active_items)}. Items with stock under 10: {', '.join(low_stock) if low_stock else 'None'}."
                    
                    answer = ai_assistant.generate_response(summary, st.session_state.messages)
                    st.markdown(answer)
                    
            st.session_state.messages.append({"role": "assistant", "content": answer})

def render_admin_dashboard(active_items):
    st.title("Admin Dashboard")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Products", len(active_items))
    m2.metric("Low Stock (< 10)", len([i for i in active_items if i['stock'] < 10]))
    out_of_stock = len([i for i in active_items if i["stock"] == 0])
    m3.metric("Out of Stock", out_of_stock)
    
    tab1, tab2, tab3 = st.tabs(["📦 View Inventory", "➕ Add Product", "✏️ Update Product"])
    
    with tab1:
        st.dataframe(
            active_items, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "id": st.column_config.TextColumn("ID", width="small")
            }
        )
        
    with tab2:
        with st.form("add_form"):
            n = st.text_input("Name")
            p = st.number_input("Price", min_value=0.0, step=0.50)
            s = st.number_input("Stock", min_value=0)
            if st.form_submit_button("Add Item"):
                if n.strip():
                    inv_service.add_product(n, p, s)
                    st.rerun()
                else:
                    st.error("Product name required.")

    with tab3:
        if active_items:
            with st.form("update_form"):
                target_id = st.selectbox(
                    "Select Item", 
                    [i["id"] for i in active_items],
                    format_func=lambda x: f"{x} : {next(i['name'] for i in active_items if i['id'] == x)}"
                )
                item = next(i for i in active_items if i["id"] == target_id)
                up = st.number_input("New Price", value=float(item["price"]), min_value=0.0, step=0.50)
                us = st.number_input("New Stock", value=int(item["stock"]), min_value=0)
                
                if st.form_submit_button("Update Item"):
                    inv_service.update_product(target_id, up, us)
                    st.rerun()
        else:
            st.info("No active items to update.")

    display_ai_assistant(active_items)

def render_employee_dashboard(active_items):
    st.title("Employee Dashboard")
    
    st.dataframe(
        active_items, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "id": st.column_config.TextColumn("ID", width="small")
        }
    )
    
    st.subheader("Record Sale")
    if active_items:
        with st.form("sale_form"):
            col1, col2 = st.columns(2)
            with col1:
                sell_id = st.selectbox(
                    "Item Sold", 
                    [i["id"] for i in active_items],
                    format_func=lambda x: f"{x} : {next(i['name'] for i in active_items if i['id'] == x)}"
                )
            with col2:
                sell_q = st.number_input("Qty", min_value=1)
            
            if st.form_submit_button("Record Sale", use_container_width=True):
                if inv_service.record_sale(sell_id, sell_q, st.session_state["username"]):
                    st.toast("Sale recorded successfully!", icon="✅")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Insufficient stock or invalid item.")
    else:
        st.info("No active items available.")

    display_ai_assistant(active_items)

def render_recent_sales():
    st.title("Recent Sales")
    sales_data = inv_service.get_all_sales()
    
    if not sales_data:
        st.info("No sales have been recorded yet.")
        return

    col1, col2 = st.columns(2)
    with col1:
        emp_options = ["All"] + list(set([s["employee"] for s in sales_data]))
        selected_emp = st.selectbox("Filter by Employee", emp_options)
    with col2:
        item_options = ["All"] + list(set([s["item_name"] for s in sales_data]))
        selected_item = st.selectbox("Filter by Item", item_options)
        
    filtered_sales = sales_data
    if selected_emp != "All":
        filtered_sales = [s for s in filtered_sales if s["employee"] == selected_emp]
    if selected_item != "All":
        filtered_sales = [s for s in filtered_sales if s["item_name"] == selected_item]
        
    if filtered_sales:
        total_revenue = sum([s["total_price"] for s in filtered_sales])
        total_items = sum([s["quantity"] for s in filtered_sales])
        m1, m2 = st.columns(2)
        m1.metric("Filtered Revenue", f"${total_revenue:.2f}")
        m2.metric("Filtered Items Sold", total_items)
        
        st.dataframe(
            filtered_sales, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "total_price": st.column_config.NumberColumn("Total", format="$%.2f")
            }
        )
    else:
        st.warning("No sales match these filters.")

def render_archive(inventory_list, archived_items):
    st.title("Archive Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Archived Items")
        if archived_items:
            st.dataframe(archived_items, use_container_width=True, hide_index=True)
        else:
            st.info("No items are currently archived.")
            
    with col2:
        st.subheader("Toggle Status")
        if inventory_list:
            with st.form("archive_form"):
                archive_id = st.selectbox(
                    "Select Product", 
                    [i["id"] for i in inventory_list],
                    format_func=lambda x: f"{x} : {next(i['name'] for i in inventory_list if i['id'] == x)} (Archived: {next(i.get('archived', False) for i in inventory_list if i['id'] == x)})"
                )
                selected_item = next(i for i in inventory_list if i["id"] == archive_id)
                is_archived = selected_item.get("archived", False)
                
                button_label = "Unarchive Item" if is_archived else "Archive Item"
                if st.form_submit_button(button_label):
                    inv_service.toggle_archive(archive_id, not is_archived)
                    st.rerun()

def render_settings():
    st.title("Account Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Update Credentials")
        with st.form("update_account_form"):
            new_username = st.text_input("New Username", value=st.session_state["username"])
            new_password = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Update Account"):
                current_user = st.session_state["username"]
                target_user = new_username.strip() if new_username.strip() else current_user
                
                success, msg = service_layer.update_user_account(current_user, target_user, new_password, users, dm)
                if success:
                    st.session_state["username"] = target_user
                    st.success(msg)
                else:
                    st.error(msg)
                    
    with col2:
        st.subheader("Account Deletion")
        with st.expander("Delete Account", icon="⚠️"):
            st.write(f"Type your username (**{st.session_state['username']}**) below:")
            with st.form("delete_account_form"):
                confirm_text = st.text_input("Confirm Username")
                if st.form_submit_button("Delete My Account", type="primary", use_container_width=True):
                    if confirm_text == st.session_state["username"]:
                        if service_layer.delete_account(st.session_state["username"], users, dm):
                            st.session_state.clear()
                            st.rerun()
                    else:
                        st.error("Username does not match.")

# Main App

if not st.session_state["logged_in"]:
    render_login_register()
else:
    render_sidebar()
    
    inventory_list = inv_service.get_all_inventory_dicts()
    active_items = [i for i in inventory_list if not i.get("archived", False)]
    archived_items = [i for i in inventory_list if i.get("archived", False)]
    current_page = st.session_state.get("current_page", "Dashboard")

    if current_page == "Dashboard":
        if st.session_state["role"] == "Admin":
            render_admin_dashboard(active_items)
        elif st.session_state["role"] == "Employee":
            render_employee_dashboard(active_items)
    elif current_page == "Recent Sales":
        render_recent_sales()
    elif current_page == "Archive Management":
        render_archive(inventory_list, archived_items)
    elif current_page == "Account Settings":
        render_settings()