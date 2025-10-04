import inspect

class BaseController:
    def __init__(self, client):
        self.client = client
    
    @staticmethod
    def request(method, path):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                # Args in kwargs umwandeln
                sig = inspect.signature(func)
                bound_args = sig.bind(self, *args, **kwargs)
                bound_args.apply_defaults()
                
                # Entferne 'self' aus den arguments
                all_kwargs = dict(bound_args.arguments)
                all_kwargs.pop('self', None)
                
                gen = func(self, **all_kwargs)
                
                try:
                    # Pre-request: bis zum yield ausführen
                    request_data = next(gen)
                    # veränderte parmeter übernehmen
                    for arg in all_kwargs.copy():
                        # gi_frame HACK
                        all_kwargs[arg] = gen.gi_frame.f_locals[arg]
                    
                    response = self.client.request(method, path, all_kwargs)
                    
                    # Post-request: Generator weiterlaufen lassen mit response
                    try:
                        gen.send(response)
                    except StopIteration as e:
                        return e.value
                    
                except StopIteration:
                    return None
                    
            wrapper.__name__ = func.__name__
            return wrapper
        return decorator

    @staticmethod
    def get(path):
        return BaseController.request('get', path)

    @staticmethod
    def post(path):
        return BaseController.request('post', path)