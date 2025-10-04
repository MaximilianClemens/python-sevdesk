

class BasicsController(BaseController):
    
    @BaseController.post('/booking')
    def booking(self, param1, param2=None, paramx3='default'):
        param1 = 'xxxx'
        return (yield)

    @BaseController.get('/booking/{param1}/list')
    def list_bookings(self, param1):
        return (yield)
    


x = BasicsController(client=RestClient('x'))
result = x.booking('zz', 'value2')


result = x.list_bookings(1)
#print(f"\nResult: {result}")
