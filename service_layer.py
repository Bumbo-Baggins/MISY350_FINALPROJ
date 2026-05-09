import uuid

class Product:
    def __init__(self, name, price, stock, id=None):
        self.id = id if id else str(uuid.uuid4())[:8]
        self.name = name
        self.price = float(price)
        self.stock = int(stock)

    def to_dict(self):
        return vars(self)

class InventoryService:
    def __init__(self, data_manager):
        self.dm = data_manager
        # Load raw data and convert to Product objects
        raw_data = self.dm.load_data(self.dm.inventory_file, [])
        self.products = [Product(**p) for p in raw_data]

    def get_all_inventory_dicts(self):
        return [p.to_dict() for p in self.products]

    def add_product(self, name, price, stock):
        new_prod = Product(name, price, stock)
        self.products.append(new_prod)
        self.save()

    def update_product(self, name, price, stock):
        for p in self.products:
            if p.name == name:
                p.price = price
                p.stock = stock
                self.save()
                return True
        return False

    def record_sale(self, name, qty):
        for p in self.products:
            if p.name == name and p.stock >= qty:
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