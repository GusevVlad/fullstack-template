from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import hashlib, uuid, asyncio
from collections import defaultdict

app = FastAPI()

# Data
products = [
    {'id': 1, 'name': 'Joy Pill', 'description': 'Instant happiness in a pill', 'price': 999, 'image': '💊'},
    {'id': 2, 'name': 'Laugh Gas', 'description': 'Giggle for hours', 'price': 1499, 'image': '😂'},
    {'id': 3, 'name': 'Dream Serum', 'description': 'Sweet dreams guaranteed', 'price': 1999, 'image': '💭'},
    {'id': 4, 'name': 'Confidence Boost', 'description': 'Unstoppable self-esteem', 'price': 2499, 'image': '💪'},
    {'id': 5, 'name': 'Love Potion', 'description': 'Attraction magnet', 'price': 2999, 'image': '❤️'},
    {'id': 6, 'name': 'Peace Essence', 'description': 'Inner tranquility', 'price': 3499, 'image': '🧘'},
]

carts = defaultdict(lambda: {'items': [], 'total': 0})
lock = asyncio.Lock()
robokassa = {'login': 'test_merchant', 'pass1': 'test_password_1', 'pass2': 'test_password_2', 'test': 1}

# Models
class CartItem(BaseModel):
    productId: int
    quantity: int = 1

class PaymentReq(BaseModel):
    sessionId: str
    email: str
    phone: Optional[str] = None

# Helpers
def sig(params, pwd):
    return hashlib.md5(':'.join(params[k] for k in sorted(params)).encode() + f':{pwd}'.encode()).hexdigest()

def find_product(pid):
    return next((p for p in products if p['id'] == pid), None)

def calc_total(cart):
    cart['total'] = sum(i['price'] * i['quantity'] for i in cart['items'])

# Routes
@app.get('/')
async def index():
    with open('templates/index.html', 'r') as f:
        return HTMLResponse(content=f.read())

@app.get('/api/products')
async def get_products():
    return products

@app.get('/api/products/{pid}')
async def get_product(pid: int):
    p = find_product(pid)
    if not p:
        raise HTTPException(404, 'Product not found')
    return p

@app.get('/api/cart/{sid}')
async def get_cart(sid: str):
    return carts[sid]

@app.post('/api/cart/{sid}/add')
async def add_to_cart(sid: str, item: CartItem):
    async with lock:
        p = find_product(item.productId)
        if not p:
            raise HTTPException(404, 'Product not found')
        cart = carts[sid]
        for i in cart['items']:
            if i['productId'] == item.productId:
                i['quantity'] += item.quantity
                calc_total(cart)
                return cart
        cart['items'].append({'productId': p['id'], 'name': p['name'], 'price': p['price'], 'image': p['image'], 'quantity': item.quantity})
        calc_total(cart)
    return cart

@app.delete('/api/cart/{sid}/item/{pid}')
async def remove_from_cart(sid: str, pid: int):
    async with lock:
        cart = carts[sid]
        cart['items'] = [i for i in cart['items'] if i['productId'] != pid]
        calc_total(cart)
    return cart

@app.put('/api/cart/{sid}/item/{pid}')
async def update_quantity(sid: str, pid: int, item: CartItem):
    async with lock:
        cart = carts[sid]
        if item.quantity <= 0:
            cart['items'] = [i for i in cart['items'] if i['productId'] != pid]
        else:
            for i in cart['items']:
                if i['productId'] == pid:
                    i['quantity'] = item.quantity
                    break
        calc_total(cart)
    return cart

@app.delete('/api/cart/{sid}')
async def clear_cart(sid: str):
    async with lock:
        carts[sid] = {'items': [], 'total': 0}
    return carts[sid]

@app.post('/api/payment/create')
async def create_payment(req: PaymentReq):
    async with lock:
        cart = carts.get(req.sessionId)
    if not cart or not cart['items']:
        raise HTTPException(400, 'Cart is empty')
    from urllib.parse import quote
    oid = f"ORD-1-{uuid.uuid4().hex[:8]}"
    params = {'MrchLogin': robokassa['login'], 'OutSum': str(cart['total']), 'InvId': oid, 'IsTest': str(robokassa['test'])}
    s = sig(params, robokassa['pass1'])
    url = f"https://auth.robokassa.ru/Merchant/Index.aspx?MrchLogin={robokassa['login']}&OutSum={cart['total']}&InvId={oid}&Description={quote('Artificial Happiness')}&SignatureValue={s}&IsTest={robokassa['test']}&Email={quote(req.email)}&Culture=ru"
    return {'orderId': oid, 'amount': cart['total'], 'paymentUrl': url, 'items': cart['items']}

@app.post('/api/payment/result')
async def payment_result(request: Request):
    params = {'OutSum': (await request.form()).get('OutSum', ''), 'InvId': (await request.form()).get('InvId', '')}
    if sig(params, robokassa['pass2']).lower() == (await request.form()).get('SignatureValue', '').lower():
        return f"OK{params['InvId']}"
    return "Bad signature"

@app.get('/api/payment/success')
async def payment_success(InvId: str, OutSum: str, SignatureValue: str):
    params = {'OutSum': OutSum, 'InvId': InvId}
    if sig(params, robokassa['pass1']).lower() == SignatureValue.lower():
        return {'success': True, 'orderId': InvId, 'amount': OutSum}
    raise HTTPException(400, 'Invalid signature')

@app.get('/api/payment/fail')
async def payment_fail():
    return {'success': False, 'error': 'Payment failed'}

if __name__ == '__main__':
    import uvicorn
    print("Server starting on :9000")
    uvicorn.run(app, host='0.0.0.0', port=9000)
