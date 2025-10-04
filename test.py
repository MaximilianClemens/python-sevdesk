from functools import wraps

# def a_new_decorator(a_func):
#     @wraps(a_func)
#     def wrapTheFunction():
#         print("I am doing some boring work before executing a_func()")
#         a_func()
#         print("I am doing some boring work after executing a_func()")
#     return wrapTheFunction

# @a_new_decorator
# def a_function_requiring_decoration():
#     """Hey yo! Decorate me!"""
#     print("I am the function which needs some decoration to "
#           "remove my foul smell")

# print(a_function_requiring_decoration.__name__)
# a_function_requiring_decoration()
# # Output: a_function_requiring_decoration

# class BaseController:

#     def __init__(self, client):
#         self.client = client

#     @classmethod
#     def post(cls, path):
#         def decorator(func):
#             def wrapper(cls, *args, **kwargs):
#                 params = func(cls, *args, **kwargs)
#                 print(f"GET {path}")
#                 print(f"Client: {cls.client}")
#                 print(f"Parameters: {params}")
#                 return params
#             wrapper.__name__ = func.__name__
#             return wrapper
            
#             # print(path, func.__name__)
#         return decorator

# class BasicsController(BaseController):

#     @BaseController.post('/x')
#     def boooking(self, parm1):
#         pass

# x = BasicsController("test")
# x.boooking('z')


####
class BaseController:
    def __init__(self, client):
        self.client = client
    
    @staticmethod  # staticmethod ist besser als classmethod hier
    def post(path):
        print('A')
        def decorator(func):
            print('B')
            def wrapper(self, *args, **kwargs):  # self, nicht cls!
                print('C')
                params = func(self, *args, **kwargs)
                print('D')
                print(f"POST {path}")
                print(f"Client: {self.client}")
                print(f"Parameters: {params}")
                print(f"Args: {args}")
                print(f"Kwargs: {kwargs}")
                return params
            print('E')
            wrapper.__name__ = func.__name__
            return wrapper
        print('F')
        return decorator


class BasicsController(BaseController):
    
    @BaseController.post('/x')
    def booking(self, param1):
        print(f"In booking function, param1={param1}")
        return {'par2am1': param1}


# Test
x = BasicsController("test")
result = x.booking('z')
# print(f"\nResult: {result}")