import data_layer

def delete_account(username, users_dict, file_path):
    if username in users_dict:
        del users_dict[username]
        data_layer.save_json(file_path, users_dict)
        return True
    return False