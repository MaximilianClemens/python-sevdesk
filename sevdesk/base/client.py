import re

class RestClient:

    def __init__(self, api_token):
        self.api_token = api_token

    def request(self, method, path, params):
        print(f'{method.upper()}: {path}')
        print(params)

        placeholders = re.findall(r"{(\w+)}", path)
        formatted_path = path.format(**params)
        query_params = {k: v for k, v in params.items() if k not in placeholders}

        print('formatted_path:', formatted_path)
        print('query_params:', query_params)