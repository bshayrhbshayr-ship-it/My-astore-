import os
import sqlite3
from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from jinja2 import Template

app = FastAPI()

# إعداد الجلسة (Session) لتسجيل الدخول
app.add_middleware(SessionMiddleware, secret_key="store_secret_2026")

# بيانات الدخول التي طلبتها
ADMIN_USER = "donkey"
ADMIN_PASS = "789523"

# إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect('store.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY, title TEXT, price TEXT, img TEXT, pdf TEXT, vid TEXT)''')
    conn.commit()
    conn.close()

init_db()

# فلاتر تحويل روابط جوجل درايف للعرض المباشر
def dr_img(u): 
    if 'drive.google.com' in u:
        return u.replace('file/d/', 'uc?export=view&id=').split('/view')[0]
    return u

def dr_vid(u):
    if 'drive.google.com' in u:
        return u.replace('view?usp=sharing', 'preview').replace('file/d/', 'file/d/')
    return u

def dr_dl(u):
    if 'drive.google.com' in u:
        return u.replace('view?usp=sharing', 'export=download')
    return u

# --- واجهة المتجر الرئيسية ---
INDEX_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجري الذكي</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .search-box { background: #1e3a8a; padding: 20px; position: sticky; top: 0; z-index: 50; }
        .product-card { transition: 0.3s; border: 1px solid #eee; }
        .product-card:hover { transform: translateY(-5px); shadow: lg; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="search-box shadow-xl text-center">
        <input type="text" id="search" onkeyup="filter()" placeholder="🔍 ابحث عن منتج أو رقم..." 
               class="w-full max-w-md p-3 rounded-full border-2 border-yellow-400 outline-none text-lg">
    </div>

    <div class="container mx-auto p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-6">
        {% for p in products %}
        <div class="product-card bg-white rounded-3xl overflow-hidden shadow-sm item-node" data-info="{{ p[1] }} {{ p[0] }}">
            {% if p[3] %}<img src="{{ dr_img(p[3]) }}" class="w-full h-64 object-cover">{% endif %}
            <div class="p-6">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-gray-400 text-sm">#{{ p[0] }}</span>
                    <span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold">كتاب رقمي</span>
                </div>
                <h3 class="text-xl font-bold text-gray-800 mb-2">{{ p[1] }}</h3>
                <p class="text-green-600 font-black text-2xl mb-4">{{ p[2] }} ريال</p>
                
                {% if p[5] %}
                <div class="rounded-xl overflow-hidden border-2 border-gray-100 mb-4">
                    <iframe src="{{ dr_vid(p[5]) }}" class="w-full h-48" allow="autoplay"></iframe>
                </div>
                {% endif %}

                <div class="flex gap-2">
                    <a href="https://wa.me/966569127524?text=طلب المنتج: {{ p[1] }} ({{ p[0] }})" 
                       class="flex-grow bg-green-500 hover:bg-green-600 text-white text-center py-3 rounded-2xl font-bold shadow-md">طلب واتساب</a>
                    {% if p[4] %}
                    <a href="{{ dr_dl(p[4]) }}" class="bg-blue-50 text-blue-600 p-3 rounded-2xl flex items-center justify-center border border-blue-100">
                        <i class="fas fa-download text-xl"></i>
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        function filter() {
            let val = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('.item-node').forEach(card => {
                card.style.display = card.getAttribute('data-info').toLowerCase().includes(val) ? '' : 'none';
            });
        }
    </script>
</body>
</html>
"""

# --- صفحة تسجيل الدخول ---
LOGIN_HTML = """
<body dir="rtl" style="font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#f0f2f5;">
    <form action="/login" method="post" style="background:white; padding:40px; border-radius:20px; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:100%; max-width:400px;">
        <h2 style="text-align:center; color:#1e3a8a;">دخول الإدارة</h2>
        <input name="username" type="text" placeholder="اسم المستخدم" style="width:100%; padding:12px; margin:10px 0; border:1px solid #ddd; border-radius:10px;" required>
        <input name="password" type="password" placeholder="كلمة المرور" style="width:100%; padding:12px; margin:10px 0; border:1px solid #ddd; border-radius:10px;" required>
        <button type="submit" style="width:100%; padding:12px; background:#1e3a8a; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">دخول</button>
    </form>
</body>
"""

# --- لوحة التحكم ---
DASHBOARD_HTML = """
<body dir="rtl" style="font-family:sans-serif; background:#f8fafc; padding:20px;">
    <div style="max-width:600px; margin:auto; background:white; padding:30px; border-radius:25px; shadow:lg;">
        <h2 style="color:#1e3a8a; border-bottom:2px solid #eee; padding-bottom:10px;">إضافة منتج جديد 🚀</h2>
        <form action="/add_product" method="post" style="display:grid; gap:15px; margin-top:20px;">
            <input name="id" type="number" placeholder="الرقم التسلسلي" style="padding:12px; border:1px solid #ccc; border-radius:10px;" required>
            <input name="title" type="text" placeholder="اسم الكتاب" style="padding:12px; border:1px solid #ccc; border-radius:10px;" required>
            <input name="price" type="text" placeholder="السعر" style="padding:12px; border:1px solid #ccc; border-radius:10px;" required>
            <input name="img" type="text" placeholder="رابط صورة جوجل درايف" style="padding:12px; border:1px solid #ccc; border-radius:10px;">
            <input name="pdf" type="text" placeholder="رابط PDF جوجل درايف" style="padding:12px; border:1px solid #ccc; border-radius:10px;">
            <input name="vid" type="text" placeholder="رابط فيديو جوجل درايف" style="padding:12px; border:1px solid #ccc; border-radius:10px;">
            <button type="submit" style="background:#10b981; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold;">نشر المنتج الآن</button>
        </form>
        <div style="margin-top:30px; border-top:1px solid #eee; padding-top:20px; text-align:center;">
            <a href="/logout" style="color:red; text-decoration:none;">تسجيل الخروج</a>
        </div>
    </div>
</body>
"""

# --- المسارات البرمجية ---

@app.get("/", response_class=HTMLResponse)
async def home():
    conn = sqlite3.connect('store.db')
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return HTMLResponse(Template(INDEX_HTML).render(products=products, dr_img=dr_img, dr_vid=dr_vid, dr_dl=dr_dl))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(LOGIN_HTML)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session['admin'] = True
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<p style='color:red; text-align:center;'>خطأ في البيانات!</p>" + LOGIN_HTML)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get('admin'):
        return RedirectResponse(url="/login")
    return HTMLResponse(DASHBOARD_HTML)

@app.post("/add_product")
async def add_product(request: Request, id: int = Form(...), title: str = Form(...), price: str = Form(...), 
                      img: str = Form(""), pdf: str = Form(""), vid: str = Form("")):
    if not request.session.get('admin'): return RedirectResponse(url="/login")
    conn = sqlite3.connect('store.db')
    conn.execute('INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?)', (id, title, price, img, pdf, vid))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
