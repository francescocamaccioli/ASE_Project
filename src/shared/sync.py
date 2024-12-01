import os
import shutil

# USARE QUESTO FILE PER SINCRONIZZARE LE MODIFICHE FATTE AL FILE auth_utils.py IN TUTTI I MICROSERVIZI

# uso:
# cd src/shared
# python sync.py

# Path to the shared file
shared_file_path = './auth_utils.py'

# Function to copy the shared file to the target path
def copy_shared_file(target_path):
    shutil.copy2(shared_file_path, target_path)
    print(f'Copied {shared_file_path} to {target_path}')



# Walk through all directories and subdirectories
for root, dirs, files in os.walk('../'):
    
    # Skip the 'shared' directory
    dirs[:] = [d for d in dirs if d != 'shared']
    
    for file in files:
        if file == 'auth_utils.py':
            target_file_path = os.path.join(root, file)
            copy_shared_file(target_file_path)