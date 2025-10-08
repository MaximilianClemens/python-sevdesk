import requests
import re

from sevdesk.controllers.contact_controller import ContactController

class Client:

    def __init__(self, api_token, api_base='https://my.sevdesk.de/api/v1', session=None):
        self.api_token = api_token
        self.api_base = api_base
        self.session = session
        if not self.session:
            self.session = requests.Session()

        self.contact = ContactController(self)

    def request(self, method, path, params):
        url_params = re.findall(r"{(\w+)}", path)
        request_path = path.format(**params)
        
        request_params = {
            k: v for k, v in params.items()
            if k not in url_params and
            k != 'body' and
            v} # v not None
        request_url = f'{self.api_base}{request_path}'
        request_body = params.get('body', None)
        if request_body:
            request_body = request_body.model_dump()

        print('request_params', request_params)
        print('request_url', request_url)
        print('request_body', request_body)

        response = self.session.request(
            method=method,
            url=request_url,
            params=request_params,
            json=request_body,
            headers={
                'Authorization': self.api_token
            }
        )
        print(response.status_code)
        print(response.text)
        return response.json()