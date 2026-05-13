import uuid
import openai
import datetime
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_initial_data(dm, inv_service):
    users = dm.load_data(dm.users_file, {})
    needs_save = False
    
    if "admin" not in users:
        users["admin"] = {"password": hash_password("admin123"), "role": "Admin"}
        needs_save = True
    if "staff" not in users:
        users["staff"] = {"password": hash_password("staff123"), "role": "Employee"}
        needs_save = True
        
    if needs_save:
        dm.save_data(dm.users_file, users)

    if not inv_service.get_all_inventory_dicts():
        inv_service.add_product("Premium Coffee Beans", 18.99, 45)
        inv_service.add_product("Ceramic Mug", 12.50, 8)
        inv_service.add_product("Paper Filters (100ct)", 4.99, 120)
        inv_service.add_product("Espresso Machine Cleaner", 22.00, 3)

def validate_login(username, password, users_dict):
    if username in users_dict and users_dict[username]["password"] == hash_password(password):
        return True, users_dict[username]["role"]
    return False, None

def register_user(username, password, role, users_dict, dm):
    if not username.strip() or not password.strip():
        return False, "Username and password cannot be empty."
    if username in users_dict:
        return False, "Username already exists."
    
    users_dict[username] = {"password": hash_password(password), "role": role}
    dm.save_data(dm.users_file, users_dict)
    return True, "Account created! You can now log in."

def update_user_account(old_username, new_username, new_password_raw, users_dict, dm):
    if old_username != new_username:
        if new_username in users_dict:
            return False, "Username already taken."
        users_dict[new_username] = users_dict.pop(old_username)
    
    if new_password_raw:
        users_dict[new_username]["password"] = hash_password(new_password_raw)
        
    dm.save_data(dm.users_file, users_dict)
    return True, "Account updated successfully."

def delete_account(username, users_dict, dm):
    if username in users_dict:
        del users_dict[username]
        dm.save_data(dm.users_file, users_dict)
        return True
    return False

class Product:
    def __init__(self, name, price, stock, id=None, archived=False):
        self.id = id if id else str(uuid.uuid4())[:8]
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
        self.archived = bool(archived)

    def to_dict(self):
        return vars(self)

class InventoryService:
    def __init__(self, data_manager):
        self.dm = data_manager
        raw_data = self.dm.load_data(self.dm.inventory_file, [])
        self.products = [Product(**p) for p in raw_data]
        self.sales = self.dm.load_data("sales.json", [])

    def get_all_inventory_dicts(self):
        return [p.to_dict() for p in self.products]

    def get_all_sales(self):
        return self.sales

    def add_product(self, name, price, stock):
        new_prod = Product(name, price, stock)
        self.products.append(new_prod)
        self.save()

    def toggle_archive(self, prod_id, archive_status):
        for p in self.products:
            if p.id == prod_id:
                p.archived = archive_status
                self.save()
                return True
        return False

    def update_product(self, prod_id, price, stock):
        for p in self.products:
            if p.id == prod_id:
                if p.archived:
                    return False
                p.price = price
                p.stock = stock
                self.save()
                return True
        return False

    def record_sale(self, prod_id, qty, employee_username):
        for p in self.products:
            if p.id == prod_id and p.stock >= qty and not p.archived:
                p.stock -= qty
                self.save()
                
                sale_record = {
                    "sale_id": str(uuid.uuid4())[:8],
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "item_id": p.id,
                    "item_name": p.name,
                    "quantity": qty,
                    "total_price": float(p.price * qty),
                    "employee": employee_username
                }
                self.sales.append(sale_record)
                self.dm.save_data("sales.json", self.sales)
                
                return True
        return False

    def save(self):
        data = [p.to_dict() for p in self.products]
        self.dm.save_data(self.dm.inventory_file, data)

class AIChatAssistant:
    def __init__(self, api_key=None):
        self.client = openai.OpenAI(api_key=api_key) if api_key else None

    def _build_system_prompt(self, inventory_data):
        return {
            "role": "system",
            "content": (
                "You are an expert business consultant for a small retail shop.\n"
                f"Current Inventory Data: {inventory_data}\n"
                "Provide concise, professional advice on restocking or pricing."
            )
        }

    def _format_history(self, chat_history):
        return [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    def generate_response(self, inventory_data, chat_history):
        if not self.client:
            return "The AI assistant is currently offline. Please configure a valid API key."

        messages = [self._build_system_prompt(inventory_data)]
        messages.extend(self._format_history(chat_history[-10:]))

        try:
            response = self.client.chat.completions.create(
                model="GPT-5.4 mini",
                messages=messages,
                temperature=0.2 
            )
            return response.choices[0].message.content
        except openai.APIError:
            return "The AI service is experiencing difficulties. Please try again later."
        except Exception:
            return "An unexpected issue occurred while processing your request."