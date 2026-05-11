import uuid
import openai

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

    def get_all_inventory_dicts(self):
        return [p.to_dict() for p in self.products]

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

    def record_sale(self, prod_id, qty):
        for p in self.products:
            if p.id == prod_id and p.stock >= qty and not p.archived:
                p.stock -= qty
                self.save()
                return True
        return False

    def save(self):
        data = [p.to_dict() for p in self.products]
        self.dm.save_data(self.dm.inventory_file, data)

def delete_account(username, users_dict, dm):
    if username in users_dict:
        del users_dict[username]
        dm.save_data(dm.users_file, users_dict)
        return True
    return False

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
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2 
            )
            return response.choices[0].message.content
        except openai.APIError:
            return "The AI service is experiencing difficulties. Please try again later."
        except Exception:
            return "An unexpected issue occurred while processing your request."