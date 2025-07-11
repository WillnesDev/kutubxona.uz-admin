from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import PyPDF2
import re
from datetime import datetime

# Asosiy sayt uchun Flask app
app = Flask(__name__)

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
                "pdf_url": f"/pdf/{filename}",
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
def index():
    return render_template('index.html')

@app.route('/api/books')
def get_books():
    global books_data
    
    if not books_data:
        books_data = scan_books_folder()
    
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    
    filtered_books = books_data
    
    if search:
        search_lower = search.lower()
        filtered_books = [
            book for book in filtered_books
            if (search_lower in book['title']['uz'].lower() or
                search_lower in book['author']['uz'].lower())
        ]
    
    if category:
        filtered_books = [
            book for book in filtered_books
            if category.lower() in book['category']['uz'].lower()
        ]
    
    return jsonify(filtered_books)

@app.route('/api/categories')
def get_categories():
    global books_data
    
    if not books_data:
        books_data = scan_books_folder()
    
    categories = set()
    for book in books_data:
        categories.add(book['category']['uz'])
    
    return jsonify(list(categories))

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    return send_from_directory('static/books', filename, as_attachment=False)

if __name__ == '__main__':
    os.makedirs('static/books', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Asosiy sayt ishga tushmoqda...")
    print("📚 Kitoblar yuklanmoqda...")
    books_data = scan_books_folder()
    print(f"✅ {len(books_data)} ta kitob topildi!")
    print("🌐 Asosiy sayt: http://localhost:8080")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
