import utils
import os

from typing import Dict, List, Union, Optional


paths = []
for file in os.listdir(directory):
    if file.endswith('json'):
        path = os.path.join(directory, file)
        paths.append(path)
        
def get_paths(directory: str):
    paths = []
    for file in os.listdir(directory):
        if file.endswith('json'):
            path = os.path.join(directory, file)
            paths.append(path)
            
def _validate_path(path :str) -> bool:
    if os.path.exists(path):
        return True
    else:
        return False

def load_data(symbol:str, directory: None) -> Optional[Dict[str, List[List[int, str]]]]:
    if directory is None:
        directory = '/Users/nnn/Desktop/DataStore/KlineData'
    if not isinstance(symbol, str):
        symbol = str(symbol)
    
    file_name = symbol.upper() + '.json'
    path = os.path.join(directory, file_name)
    
    if not os.path.exists(path):
        return None
    
    return utils._load_json(file_path=path)

if __name__ == "__main__":
    
    
    # symbol = 'BTCUSDT'
    # directory = '/Users/nnn/Desktop/DataStore/KlineData'
    # path = os.path.join(directory, symbol)
    # if not os.path.exists(path):
    #     return f'파일이 존
    