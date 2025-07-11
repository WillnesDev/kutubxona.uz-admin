from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import PyPDF2
import re
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Admin panel uchun Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-2024'

# Admin ma'lumotlari
ADMIN_USERNAME = 'willnes'
ADMIN_PASSWORD = 'WillnesDev'

# Upload sozlamalari
UPLOAD_FOLDER = 'static/books'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_info(pdf_path):
    """PDF fayldan ma'lumot olish"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            metadata = pdf_reader.metadata
            title = ""
            author = ""
            
            if metadata:
                title = metadata.get('/Title', '') or ""
                author = metadata.get('/Author', '') or ""
            
            if not title:
                title = os.path.splitext(os.path.basename(pdf_path))[0]
                title = title.replace('_', ' ').replace('-', ' ').title()
            
            pages = len(pdf_reader.pages)
            
            return {
                'title': title,
                'author': author or "Noma'lum muallif",
                'pages': pages
            }
    except Exception as e:
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        return {
            'title': filename.replace('_', ' ').replace('-', ' ').title(),
            'author': "Noma'lum muallif",
            'pages': 0
        }

def get_category_name(category, lang):
    """Kategoriya nomini tilga qarab qaytarish"""
    category_names = {
        'adabiyot': {'uz': 'Adabiyot', 'en': 'Literature', 'ru': 'Литература'},
        'tarix': {'uz': 'Tarix', 'en': 'History', 'ru': 'История'},
        'fan': {'uz': 'Fan', 'en': 'Science', 'ru': 'Наука'},
        'din': {'uz': 'Din', 'en': 'Religion', 'ru': 'Религия'},
        'dasturlash': {'uz': 'Dasturlash', 'en': 'Programming', 'ru': 'Программирование'},
        'tibbiyot': {'uz': 'Tibbiyot', 'en': 'Medicine', 'ru': 'Медицина'},
        'iqtisod': {'uz': 'Iqtisod', 'en': 'Economics', 'ru': 'Экономика'},
        'falsafa': {'uz': 'Falsafa', 'en': 'Philosophy', 'ru': 'Философия'},
        'boshqa': {'uz': 'Boshqa', 'en': 'Other', 'ru': 'Другое'}
    }
    
    return category_names.get(category, category_names['boshqa'])[lang]

def scan_books_folder():
    """static/books papkasidagi barcha PDF fayllarni skanerlash"""
    books_folder = "static/books"
    books = []
    
    if not os.path.exists(books_folder):
        os.makedirs(books_folder, exist_ok=True)
        return books
    
    pdf_files = []
    for root, dirs, files in os.walk(books_folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    categories = {
        'adabiyot': ['adabiyot', 'roman', 'hikoya', 'she\'r', 'poetry', 'novel', 'literature'],
        'tarix': ['tarix', 'history', 'historical'],
        'fan': ['fan', 'science', 'matematik', 'fizika', 'kimyo'],
        'din': ['din', 'islam', 'quran', 'hadis', 'religion'],
        'dasturlash': ['programming', 'python', 'javascript', 'code'],
        'tibbiyot': ['tibbiyot', 'medical', 'medicine', 'health'],
        'iqtisod': ['iqtisod', 'economics', 'business', 'finance'],
        'falsafa': ['falsafa', 'philosophy', 'thinking'],
    }
    
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            pdf_info = extract_pdf_info(pdf_path)
            filename = os.path.basename(pdf_path)
            
            filename_lower = filename.lower()
            detected_category = 'boshqa'
            
            for category, keywords in categories.items():
                if any(keyword in filename_lower for keyword in keywords):
                    detected_category = category
                    break
            
            year_match = re.search(r'(19|20)\d{2}', filename)
            year = int(year_match.group()) if year_match else 2020
            
            file_size = os.path.getsize(pdf_path)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            
            book = {
                "id": i,
                "title": {
                    "uz": pdf_info['title'],
                    "en": pdf_info['title'],
                    "ru": pdf_info['title']
                },
                "author": {
                    "uz": pdf_info['author'],
                    "en": pdf_info['author'],
                    "ru": pdf_info['author']
                },
                "category": {
                    "uz": get_category_name(detected_category, 'uz'),
                    "en": get_category_name(detected_category, 'en'),
                    "ru": get_category_name(detected_category, 'ru')
                },
                "pages": pdf_info['pages'],
                "year": year,
                "file": filename,
                "file_size": file_size_mb,
                "pdf_url": f"http://localhost:8080/pdf/{filename}",
                "upload_date": datetime.fromtimestamp(os.path.getctime(pdf_path)).strftime('%Y-%m-%d %H:%M')
            }
            
            books.append(book)
            
        except Exception as e:
            print(f"Xatolik {pdf_path}: {e}")
            continue
    
    return books

# Global o'zgaruvchi
books_data = []

# Routes
@app.route('/')
def login():
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        flash('Muvaffaqiyatli kirdingiz!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Noto\'g\'ri username yoki parol!', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Tizimdan chiqdingiz!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    
    global books_data
    books_data = scan_books_folder()
    
    total_books = len(books_data)
    total_size = sum(book['file_size'] for book in books_data) if books_data else 0
    categories_count = len(set(book['category']['uz'] for book in books_data)) if books_data else 0
    
    stats = {
        'total_books': total_books,
        'total_size': round(total_size, 2),
        'categories_count': categories_count,
        'recent_books': sorted(books_data, key=lambda x: x['upload_date'], reverse=True)[:5] if books_data else []
    }
    
    return render_template('dashboard.html', books=books_data, stats=stats)

@app.route('/upload', methods=['POST'])
def upload():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Login talab qilinadi'})
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Fayl tanlanmagan'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Fayl tanlanmagan'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Faqat PDF fayllar ruxsat etilgan'})
        
        filename = secure_filename(file.filename)
        
        counter = 1
        original_filename = filename
        upload_path = app.config['UPLOAD_FOLDER']
        
        while os.path.exists(os.path.join(upload_path, filename)):
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{counter}{ext}"
            counter += 1
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        global books_data
        books_data = scan_books_folder()
        
        return jsonify({'success': True, 'message': f'Kitob muvaffaqiyatli yuklandi: {filename}'})
    
    except Exception as e:
        print(f"Upload xatosi: {e}")
        return jsonify({'success': False, 'message': f'Server xatosi: {str(e)}'})

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Login talab qilinadi'})
    
    global books_data
    if not books_data:
        books_data = scan_books_folder()
    
    book = next((b for b in books_data if b['id'] == book_id), None)
    if not book:
        return jsonify({'success': False, 'message': 'Kitob topilmadi'})
    
    try:
        file_path = os.path.join('static/books', book['file'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        books_data = scan_books_folder()
        
        return jsonify({'success': True, 'message': 'Kitob muvaffaqiyatli o\'chirildi'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Xatolik: {str(e)}'})

@app.route('/refresh')
def refresh():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    
    global books_data
    books_data = scan_books_folder()
    flash(f'{len(books_data)} ta kitob yangilandi!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    os.makedirs('static/books', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("🔐 Admin panel ishga tushmoqda...")
    print("📚 Kitoblar yuklanmoqda...")
    books_data = scan_books_folder()
    print(f"✅ {len(books_data)} ta kitob topildi!")
    print("👤 Admin: username='admin', password='admin123'")
    print("⚙️ Admin panel: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
