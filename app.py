import streamlit as st
import data_layer
import service_layer
import os
from dotenv import load_dotenv

# Load secrets from .env [cite: 40]
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
ai_assistant = service_layer.AIChatAssistant(api_key)

# --- INITIALIZATION ---
# Create the Data Manager and Service objects
dm = data_layer.DataManager()
inv_service = service_layer.InventoryService(dm)

# Load users using the class method 
users = dm.load_data(dm.users_file, {})

# Ensure test accounts exist 
if "admin" not in users:
    users["admin"] = {"password": "admin123", "role": "Shop Owner"}
    dm.save_data(dm.users_file, users)
if "staff" not in users:
    users["staff"] = {"password": "staff123", "role": "Employee"}
    dm.save_data(dm.users_file, users)

st.set_page_config("Inventory Manager", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- UI LOGIC ---
if not st.session_state["logged_in"]:
    st.title("Small Business Inventory Manager")
    st.info("**Test Accounts:**\n* Owner: `admin` | Pass: `admin123`\n* Employee: `staff` | Pass: `staff123`")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Log In"):
            if u in users and users[u]["password"] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.session_state["role"] = users[u]["role"]
                st.rerun()
            else:
                st.error("Invalid credentials.")

    with tab2:
        st.subheader("Register")
        ru = st.text_input("New Username", key="r_u")
        rp = st.text_input("New Password", type="password", key="r_p")
        rr = st.selectbox("Role", ["Employee", "Shop Owner"])
        if st.button("Register"):
            if ru and rp:
                users[ru] = {"password": rp, "role": rr}
                dm.save_data(dm.users_file, users)
                st.success("Account created!")

else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.write(f"**User:** {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        if st.button("Delete Account", type="primary"):
            if service_layer.delete_account(st.session_state["username"], users, dm):
                st.session_state.clear()
                st.rerun()

    # --- ROLE-SPECIFIC DASHBOARDS ---
    inventory_list = inv_service.get_all_inventory_dicts()

    if st.session_state["role"] == "Shop Owner":
        st.title("Owner Dashboard")
        # Owner logic here...

    elif st.session_state["role"] == "Employee":
        st.title("Employee Dashboard")
        # Employee logic here...

# --- UNIVERSAL COMPONENTS ---
    st.divider()
    st.subheader("AI Business Assistant")
    st.info("Ask the AI for advice on restocking or inventory trends.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hi! Ask me a question about the inventory."
        })

    # Render visible chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # Handle new chat input [cite: 164, 169]
    user_input = st.chat_input("How can I help you?")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container.chat_message("user"):
            st.markdown(user_input)
            
        with chat_container.chat_message("assistant"):
            with st.spinner("Consulting the AI..."):
                current_data = inv_service.get_all_inventory_dicts()
                # Pass chat history to the service layer [cite: 214]
                answer = ai_assistant.generate_response(current_data, st.session_state.messages)
                st.markdown(answer)
                
        # Append AI response to state
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # --- DASHBOARDS ---
    # Get current inventory data from the service layer
    inventory_list = inv_service.get_all_inventory_dicts()

    if st.session_state["role"] == "Shop Owner":
        st.title("Owner Dashboard")
        st.dataframe(inventory_list, use_container_width=True)
        
        action = st.radio("Action", ["Add Product", "Update Product"], horizontal=True)
        
        if action == "Add Product":
            n = st.text_input("Name", key="an")
            p = st.number_input("Price", min_value=0.0, key="ap")
            s = st.number_input("Stock", min_value=0, key="as")
            if st.button("Add"):
                inv_service.add_product(n, p, s)
                st.rerun()

        elif action == "Update Product" and inventory_list:
            target = st.selectbox("Select Item", [i["name"] for i in inventory_list])
            item = next(i for i in inventory_list if i["name"] == target)
            up = st.number_input("New Price", value=float(item["price"]))
            us = st.number_input("New Stock", value=int(item["stock"]))
            if st.button("Update"):
                inv_service.update_product(target, up, us)
                st.rerun()

    elif st.session_state["role"] == "Employee":
        st.title("Employee Dashboard")
        st.dataframe(inventory_list, use_container_width=True)
        
        if inventory_list:
            sell_n = st.selectbox("Item Sold", [i["name"] for i in inventory_list])
            sell_q = st.number_input("Qty", min_value=1)
            if st.button("Record Sale"):
                if inv_service.record_sale(sell_n, sell_q):
                    st.success("Sale Recorded")
                    st.rerun()
                else:
                    st.error("Insufficient stock!")