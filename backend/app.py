import os
import tempfile
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from weasyprint import HTML

# конфигурация
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///karman_prorab.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# константы
PROJECT_STATUSES = ['На этапе согласования', 'В работе', 'Завершённые', 'Отложенные']


@app.context_processor
def inject_globals():
    return {'project_statuses': PROJECT_STATUSES}


# модели 

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    status = db.Column(db.String(20), default='В работе')
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(50))
    actual_end_date = db.Column(db.String(20))


class ProjectTimeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, unique=True)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    project = db.relationship('Project', backref=db.backref('timeline', uselist=False))


class ProjectWork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    project = db.relationship('Project', backref='works')
    service = db.relationship('Service')


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    project = db.relationship('Project', backref='expenses')


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    is_purchased = db.Column(db.Boolean, default=False)
    project = db.relationship('Project', backref='purchases')


class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500))
    category = db.relationship('ProductCategory', backref=db.backref('products', lazy=True))


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=True)

    @staticmethod
    def get(key, default=''):
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()


#вспомогательный функции 

def calculate_progress(project):
    timeline = ProjectTimeline.query.filter_by(project_id=project.id).first()
    if not timeline or not timeline.start_date or not timeline.end_date:
        return 0
    
    try:
        start = datetime.strptime(timeline.start_date, '%Y-%m-%d')
        end = datetime.strptime(timeline.end_date, '%Y-%m-%d')
        today = datetime.now()
        
        if today >= end:
            return 100
        if today <= start:
            return 0
        
        total_days = (end - start).days
        days_passed = (today - start).days
        return min(100, int((days_passed / total_days) * 100)) if total_days > 0 else 0
    except (ValueError, TypeError):
        return 0


def get_progress_color(progress):
    if progress < 30:
        return '#dc3545'
    if progress < 50:
        return '#fd7e14'
    if progress < 70:
        return '#ffc107'
    if progress < 90:
        return '#20c997'
    return '#198754'


# маршруты 

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/services')
def services():
    return render_template('services.html', services=Service.query.all())


@app.route('/services/add', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        service = Service(
            name=request.form['name'],
            unit=request.form['unit'],
            price=float(request.form['price'])
        )
        db.session.add(service)
        db.session.commit()
        return redirect(url_for('services'))
    return render_template('add_service.html')


@app.route('/services/edit/<int:id>', methods=['GET', 'POST'])
def edit_service(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.name = request.form['name']
        service.unit = request.form['unit']
        service.price = float(request.form['price'])
        db.session.commit()
        return redirect(url_for('services'))
    return render_template('edit_service.html', service=service)


@app.route('/services/delete/<int:id>')
def delete_service(id):
    db.session.delete(Service.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('services'))


@app.route('/categories')
def categories():
    return render_template('categories.html', categories=ProductCategory.query.all())


@app.route('/categories/add', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        db.session.add(ProductCategory(name=request.form['name']))
        db.session.commit()
        return redirect(url_for('categories'))
    return render_template('add_category.html')


@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    category = ProductCategory.query.get_or_404(id)
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        return redirect(url_for('categories'))
    return render_template('edit_category.html', category=category)


@app.route('/categories/delete/<int:id>')
def delete_category(id):
    Product.query.filter_by(category_id=id).delete()
    db.session.delete(ProductCategory.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('categories'))


@app.route('/products')
def products():
    return render_template('products.html', 
                         products=Product.query.all(),
                         categories=ProductCategory.query.all())


@app.route('/products/by-category/<int:category_id>')
def products_by_category(category_id):
    products = Product.query.filter_by(category_id=category_id).all()
    return jsonify([{'id': p.id, 'name': p.name, 'unit': p.unit, 'price': p.price} for p in products])


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product = Product(
            category_id=int(request.form['category_id']),
            name=request.form['name'],
            unit=request.form['unit'],
            price=float(request.form['price']),
            description=request.form.get('description', '')
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('add_product.html', categories=ProductCategory.query.all())


@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.category_id = int(request.form['category_id'])
        product.name = request.form['name']
        product.unit = request.form['unit']
        product.price = float(request.form['price'])
        product.description = request.form.get('description', '')
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product, categories=ProductCategory.query.all())


@app.route('/products/delete/<int:id>')
def delete_product(id):
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('products'))


@app.route('/projects')
def projects():
    projects_list = Project.query.all()
    for p in projects_list:
        p.progress = calculate_progress(p)
    return render_template('projects.html', projects=projects_list)


@app.route('/projects/add', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        project = Project(
            name=request.form['name'],
            address=request.form['address'],
            status=request.form.get('status', 'В работе'),
            client_name=request.form.get('client_name'),
            client_phone=request.form.get('client_phone')
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('projects'))
    return render_template('add_project.html')


@app.route('/projects/delete/<int:id>')
def delete_project(id):
    db.session.delete(Project.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('projects'))


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    progress = calculate_progress(project)
    
    return render_template('project_detail.html',
                         project=project,
                         services=Service.query.all(),
                         categories=ProductCategory.query.all(),
                         works=ProjectWork.query.filter_by(project_id=project_id).all(),
                         expenses=Expense.query.filter_by(project_id=project_id).all(),
                         purchases=Purchase.query.filter_by(project_id=project_id).all(),
                         timeline=ProjectTimeline.query.filter_by(project_id=project_id).first(),
                         progress=progress,
                         progress_color=get_progress_color(progress),
                         total=sum(w.total_price for w in ProjectWork.query.filter_by(project_id=project_id).all()))


@app.route('/project/<int:project_id>/save_all', methods=['POST'])
def save_all(project_id):
    project = Project.query.get_or_404(project_id)
    
    project.name = request.form['name']
    project.address = request.form['address']
    project.status = request.form['status']
    project.client_name = request.form.get('client_name', '')
    project.client_phone = request.form.get('client_phone', '')
    project.actual_end_date = request.form.get('actual_end_date')
    
    timeline = ProjectTimeline.query.filter_by(project_id=project.id).first()
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if timeline:
        timeline.start_date = start_date or None
        timeline.end_date = end_date or None
    elif start_date or end_date:
        db.session.add(ProjectTimeline(
            project_id=project.id,
            start_date=start_date or None,
            end_date=end_date or None
        ))
    
    for work in project.works:
        qty_key = f'work_qty_{work.id}'
        if qty_key in request.form:
            work.quantity = float(request.form[qty_key])
            work.total_price = work.service.price * work.quantity
    
    for expense in project.expenses:
        name_key = f'expense_name_{expense.id}'
        amount_key = f'expense_amount_{expense.id}'
        if name_key in request.form and amount_key in request.form:
            expense.name = request.form[name_key]
            expense.amount = float(request.form[amount_key])
    
    if request.form.get('add_work'):
        service_id = request.form.get('new_service_id')
        quantity = request.form.get('new_quantity')
        if service_id and quantity:
            service = Service.query.get(int(service_id))
            qty = float(quantity)
            db.session.add(ProjectWork(
                project_id=project.id,
                service_id=service.id,
                quantity=qty,
                total_price=service.price * qty
            ))
    
    if request.form.get('add_expense'):
        name = request.form.get('new_expense_name')
        amount = request.form.get('new_expense_amount')
        if name and amount:
            db.session.add(Expense(
                project_id=project.id,
                name=name,
                amount=float(amount)
            ))
    
    if request.form.get('add_purchase'):
        purchase_name = request.form.get('new_purchase_name')
        if purchase_name:
            db.session.add(Purchase(
                project_id=project.id,
                name=purchase_name
            ))
    
    for purchase in project.purchases:
        purchase.is_purchased = f'purchased_{purchase.id}' in request.form
    
    db.session.commit()
    
    active_tab = request.form.get('active_tab', 'main')
    return redirect(url_for('project_detail', project_id=project_id, tab=active_tab))


@app.route('/project/<int:project_id>/add_product_work', methods=['POST'])
def add_product_work(project_id):
    product = Product.query.get_or_404(request.form['product_id'])
    quantity = float(request.form['quantity'])
    
    service = Service(
        name=product.name,
        unit=product.unit,
        price=product.price
    )
    db.session.add(service)
    db.session.commit()
    
    db.session.add(ProjectWork(
        project_id=project_id,
        service_id=service.id,
        quantity=quantity,
        total_price=product.price * quantity
    ))
    db.session.commit()
    
    return redirect(url_for('project_detail', project_id=project_id, tab='estimate'))


@app.route('/project/<int:project_id>/copy')
def copy_project(project_id):
    original = Project.query.get_or_404(project_id)
    
    new_project = Project(
        name=f"{original.name} (копия)",
        address=original.address,
        status="В работе",
        client_name=original.client_name,
        client_phone=original.client_phone,
        actual_end_date=original.actual_end_date
    )
    db.session.add(new_project)
    db.session.commit()
    
    if original.timeline:
        db.session.add(ProjectTimeline(
            project_id=new_project.id,
            start_date=original.timeline.start_date,
            end_date=original.timeline.end_date
        ))
    
    for work in original.works:
        db.session.add(ProjectWork(
            project_id=new_project.id,
            service_id=work.service_id,
            quantity=work.quantity,
            total_price=work.total_price
        ))
    
    for expense in original.expenses:
        db.session.add(Expense(
            project_id=new_project.id,
            name=expense.name,
            amount=expense.amount
        ))
    
    for purchase in original.purchases:
        db.session.add(Purchase(
            project_id=new_project.id,
            name=purchase.name
        ))
    
    db.session.commit()
    return redirect(url_for('project_detail', project_id=new_project.id))


@app.route('/project/<int:project_id>/delete_work/<int:work_id>')
def delete_work(project_id, work_id):
    db.session.delete(ProjectWork.query.get_or_404(work_id))
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id, tab='estimate'))


@app.route('/project/<int:project_id>/delete_expense/<int:expense_id>')
def delete_expense(project_id, expense_id):
    db.session.delete(Expense.query.get_or_404(expense_id))
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id, tab='estimate'))


@app.route('/project/<int:project_id>/delete_purchase/<int:purchase_id>')
def delete_purchase(project_id, purchase_id):
    db.session.delete(Purchase.query.get_or_404(purchase_id))
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id, tab='estimate'))


# настройки 

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        Setting.set('company_name', request.form.get('company_name', ''))
        Setting.set('company_phone', request.form.get('company_phone', ''))
        Setting.set('company_email', request.form.get('company_email', ''))
        Setting.set('company_inn', request.form.get('company_inn', ''))
        return redirect(url_for('settings'))
    
    return render_template('settings.html',
                         company_name=Setting.get('company_name', ''),
                         company_phone=Setting.get('company_phone', ''),
                         company_email=Setting.get('company_email', ''),
                         company_inn=Setting.get('company_inn', ''))


# PDF генерация 

@app.route('/project/<int:project_id>/estimate/pdf')
def project_estimate_pdf(project_id):
    project = Project.query.get_or_404(project_id)
    works = ProjectWork.query.filter_by(project_id=project_id).all()
    timeline = ProjectTimeline.query.filter_by(project_id=project_id).first()
    
    total_income = sum(w.total_price for w in works)
    
    works_list = []
    for i, w in enumerate(works, 1):
        works_list.append({
            'num': i,
            'name': w.service.name,
            'unit': w.service.unit,
            'quantity': w.quantity,
            'price': w.service.price,
            'total': w.total_price
        })
    
    html_content = render_template('pdf_estimate.html',
                                 project=project,
                                 works=works_list,
                                 total_income=total_income,
                                 timeline=timeline,
                                 company_name=Setting.get('company_name', 'ИП | Строительство и ремонт'),
                                 company_phone=Setting.get('company_phone', '+7(XXX)XXX-XX-XX'),
                                 company_email=Setting.get('company_email', 'company@example.com'),
                                 company_inn=Setting.get('company_inn', ''))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        HTML(string=html_content).write_pdf(tmp.name)
        tmp_path = tmp.name
    
    return send_file(tmp_path, as_attachment=True, download_name=f'Смета_{project.name}.pdf')


# AJAX маршруты для автосохранения 

@app.route('/project/<int:project_id>/autosave', methods=['POST'])
def autosave(project_id):
    """Универсальное автосохранение любого поля проекта"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        project = Project.query.get_or_404(project_id)
        
        # поля из вкладки "Основное"
        if field == 'name':
            project.name = value
        elif field == 'address':
            project.address = value
        elif field == 'status':
            project.status = value
        elif field == 'client_name':
            project.client_name = value
        elif field == 'client_phone':
            project.client_phone = value
        elif field == 'actual_end_date':
            project.actual_end_date = value
            
        # даты из Timeline
        elif field == 'start_date':
            timeline = ProjectTimeline.query.filter_by(project_id=project.id).first()
            if not timeline:
                timeline = ProjectTimeline(project_id=project.id)
                db.session.add(timeline)
            timeline.start_date = value
        elif field == 'end_date':
            timeline = ProjectTimeline.query.filter_by(project_id=project.id).first()
            if not timeline:
                timeline = ProjectTimeline(project_id=project.id)
                db.session.add(timeline)
            timeline.end_date = value
            
        # количество работы в смете
        elif field.startswith('work_qty_'):
            work_id = int(field.split('_')[-1])
            work = ProjectWork.query.get(work_id)
            if work:
                work.quantity = float(value)
                work.total_price = work.service.price * work.quantity
                
        # название расхода
        elif field.startswith('expense_name_'):
            expense_id = int(field.split('_')[-1])
            expense = Expense.query.get(expense_id)
            if expense:
                expense.name = value
                
        # сумма расхода
        elif field.startswith('expense_amount_'):
            expense_id = int(field.split('_')[-1])
            expense = Expense.query.get(expense_id)
            if expense:
                expense.amount = float(value)
                
        # статус покупки
        elif field.startswith('purchased_'):
            purchase_id = int(field.split('_')[-1])
            purchase = Purchase.query.get(purchase_id)
            if purchase:
                purchase.is_purchased = value == 'true' or value is True
                
        # количество покупки
        elif field.startswith('purchase_quantity_'):
            purchase_id = int(field.split('_')[-1])
            purchase = Purchase.query.get(purchase_id)
            if purchase:
                purchase.quantity = int(value)
                
        db.session.commit()
        return jsonify({'success': True, 'message': 'Сохранено'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/project/<int:project_id>/add_expense_ajax', methods=['POST'])
def add_expense_ajax(project_id):
    """Добавление расхода без перезагрузки страницы"""
    try:
        data = request.get_json()
        expense = Expense(
            project_id=project_id,
            name=data.get('name'),
            amount=float(data.get('amount'))
        )
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'expense_id': expense.id,
            'name': expense.name,
            'amount': expense.amount
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/project/<int:project_id>/add_purchase_ajax', methods=['POST'])
def add_purchase_ajax(project_id):
    """Добавление покупки без перезагрузки страницы"""
    try:
        data = request.get_json()
        purchase = Purchase(
            project_id=project_id,
            name=data.get('name'),
            quantity=data.get('quantity', 1)
        )
        db.session.add(purchase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'purchase_id': purchase.id,
            'name': purchase.name,
            'quantity': purchase.quantity
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/project/<int:project_id>/delete_expense_ajax/<int:expense_id>', methods=['DELETE'])
def delete_expense_ajax(project_id, expense_id):
    """Удаление расхода без перезагрузки страницы"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/project/<int:project_id>/delete_purchase_ajax/<int:purchase_id>', methods=['DELETE'])
def delete_purchase_ajax(project_id, purchase_id):
    """Удаление покупки без перезагрузки страницы"""
    try:
        purchase = Purchase.query.get_or_404(purchase_id)
        db.session.delete(purchase)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    
@app.route('/project/<int:project_id>/get_totals')
def get_totals(project_id):
    """Возвращает актуальные итоги по проекту (доход, расходы, прибыль)"""
    project = Project.query.get_or_404(project_id)
    works = ProjectWork.query.filter_by(project_id=project_id).all()
    expenses = Expense.query.filter_by(project_id=project_id).all()
    
    total_income = sum(w.total_price for w in works)
    total_expenses = sum(e.amount for e in expenses)
    profit = total_income - total_expenses
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'profit': profit
    })


# создание таблиц при запуске
with app.app_context():
    db.create_all()


# запуск
if __name__ == '__main__':
    app.run(debug=True)