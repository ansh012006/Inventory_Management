from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from datetime import date,timedelta,datetime
from collections import defaultdict
from flask_mail import Mail, Message
import firebase_admin

from firebase_admin import credentials, messaging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///inventory.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'srms.inventory@gmail.com'
app.config['MAIL_PASSWORD'] = 'ilslkasxuyqcqnke'  # Use app password, NOT your login
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

def group_by_name(items):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.name].append(item)
    return grouped

def group_by_id(items):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.m_id].append(item)
    return grouped



def check_and_notify_due_services():
    today = date.today()

    machines = Machine.query.filter(Machine.ls_date != None, Machine.interval != None).all()
    parts = Mpart.query.filter(Mpart.ls_date != None, Mpart.interval != None).all()

    # Check single-unit machines
    for m in machines:
        next_date = m.ls_date + timedelta(days=m.interval)
        days_left = (next_date - today).days
        if days_left <= 10:
            msg = f"[MACHINE] {m.name} service due on {next_date} (in {days_left} days)"
            notify("cjueTYrUs6cl8tlC-Np5P5:APA91bEt1rvCe9CA0dVPSRbAqQE1EQ3YTyCfih4dw5fB6r7iKnJiuAEz_PKJgzchyF7YGW4dd37uhLvCGldXJyRH8cu9l0oGLZhCCku-i8Slg2i6OUevFtc",msg)
            if days_left < 3:
                send_email_alert(msg)

    # Check assembled machine parts
    for p in parts:
        next_date = p.ls_date + timedelta(days=p.interval)
        days_left = (next_date - today).days
        if days_left <= 10:
            m = Machine.query.filter_by(sno=p.m_id).first()
            msg = f"[PART] machine/id:{m.name}/{m.sno} {p.name} (Machine ID: {p.m_id}) service due on {next_date} (in {days_left} days)"
            notify("cjueTYrUs6cl8tlC-Np5P5:APA91bEt1rvCe9CA0dVPSRbAqQE1EQ3YTyCfih4dw5fB6r7iKnJiuAEz_PKJgzchyF7YGW4dd37uhLvCGldXJyRH8cu9l0oGLZhCCku-i8Slg2i6OUevFtc",msg)
            if days_left < 3:
                send_email_alert(msg)


def notificationlist():
    today = date.today()
    notifi = []

    machines = Machine.query.filter(Machine.ls_date != None, Machine.interval != None).all()
    parts = Mpart.query.filter(Mpart.ls_date != None, Mpart.interval != None).all()

    # Check single-unit machines
    for m in machines:
        next_date = m.ls_date + timedelta(days=m.interval)
        days_left = (next_date - today).days
        if days_left <= 10:
            msg = f"[MACHINE] {m.name} service due on {next_date} (in {days_left} days)"
            notifi.append(msg)


    # Check assembled machine parts
    for p in parts:
        next_date = p.ls_date + timedelta(days=p.interval)
        days_left = (next_date - today).days
        if days_left <= 10:
            m = Machine.query.filter_by(sno = p.m_id).first()
            msg = f"[PART] machine/id:{m.name}/{m.sno} {p.name} (Machine ID: {p.m_id}) service due on {next_date} (in {days_left} days)"
            notifi.append(msg)

    return notifi



def send_email_alert(body):
    subject = "🔴 Machine Service Due Soon"
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=["vishnoiunnati811@gmail.com"])
    msg.body = body
    try:
        mail.send(msg)
        print("✅ Email sent:", body)
    except Exception as e:
        print("❌ Failed to send email:", e)



def notify(t, msg):
    from firebase_admin import get_app, _apps
    print("hi it",msg)

    # Only initialize the app if it hasn't been initialized yet
    if not _apps:
        cred = credentials.Certificate('/Users/unnativishnoi/Downloads/inventory/fb_notify.json')
        firebase_admin.initialize_app(cred)

    message = messaging.Message(
        notification=messaging.Notification(
            title='Service due',
            body=msg
        ),
        token=t
    )
    try:
        response = messaging.send(message)
        print("✅ Notification sent to the:", response)
    except Exception as e:
        print("❌ Failed to send notification:", e)

def update_last_service(sno, date_str, t):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    if t == "machine":
        record = Machine.query.get(sno)
    else:
        record = Mpart.query.get(sno)

    if record:
        record.ls_date = date_obj
        db.session.commit()
        add_log(f"Updated last service date for {t} '{record.name}' (ID {sno}) to {date_obj}.")


def add_log(message):
    try:
        log_entry = Slog(msg=message)
        db.session.add(log_entry)
        db.session.commit()
        print(f"📝 Log added: {message}")
    except Exception as e:
        print(f"❌ Failed to log: {e}")


class Dep(db.Model):
    __tablename__ = 'dep'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)


class MType(db.Model):
    __tablename__ = 'm_type'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    typee = db.Column(db.String(500), nullable=False)
    interval = db.Column(db.Integer, nullable=True)


class Parts(db.Model):
    __tablename__ = 'parts'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    m_id = db.Column(db.Integer, db.ForeignKey('m_type.sno'), nullable=False)
    interval = db.Column(db.Integer)


# NEW: Manufacturer model for the manufacturer management feature
class Manufacturer(db.Model):
    __tablename__ = 'manufacturer'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(500), nullable=True)  # Phone, email, or address
    specialization = db.Column(db.String(300), nullable=True)  # Industrial equipment, electronics, etc.
    created_date = db.Column(db.Date, default=date.today)


class Machine(db.Model):
    __tablename__ = 'machine'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    m_uid = db.Column(db.Integer, unique=True)  # Added unique constraint for serial ID
    department = db.Column(db.Integer, db.ForeignKey('dep.sno'), nullable=False)
    typee = db.Column(db.String(500), nullable=False)
    interval = db.Column(db.Integer, nullable=True)
    up_date = db.Column(db.Date)  # Acquisition/Purchase date
    ls_date = db.Column(db.Date, nullable=True)  # Last service date
    # NEW FIELDS:
    manufacturer = db.Column(db.Integer, db.ForeignKey('manufacturer.sno'), nullable=True)
    service_location = db.Column(db.String(500), nullable=True)  # Where to send for service


class Mpart(db.Model):
    __tablename__ = 'mpart'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    m_id = db.Column(db.Integer, db.ForeignKey('machine.sno'), nullable=False)
    interval = db.Column(db.Integer, nullable=True)
    ls_date = db.Column(db.Date)


class Slog(db.Model):
    __tablename__ = 'slog'
    sno = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    msg = db.Column(db.String(1000))


# Optional: Add relationships for easier querying (recommended)

@app.route('/add', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'type':
            # Equipment Classification Form
            name = request.form.get('machine-type-name')
            type_ = request.form.get('type-category')

            if type_ == "single-unit":
                days = request.form.get('service-interval')
                q = MType(name=name, typee=type_, interval=int(days))
                db.session.add(q)
                db.session.commit()
                add_log(f"Registered new equipment classification '{name}' (Single Unit) with interval {days} days.")
            elif type_ == "assembled":
                q = MType(name=name, typee=type_)
                db.session.add(q)
                db.session.commit()
                add_log(f"Registered new assembly classification '{name}'.")
                i = 1
                while request.form.get(f'part-name-{i}') and request.form.get(f'part-interval-{i}'):
                    partname = request.form.get(f'part-name-{i}')
                    days = request.form.get(f'part-interval-{i}')
                    qu = Parts(name=partname, m_id=q.sno, interval=int(days))
                    db.session.add(qu)
                    add_log(f"Added component '{partname}' to classification '{name}' with interval {days} days.")
                    i += 1
                db.session.commit()
        elif form_type == 'new':
            # Equipment Registration Form
            uid = request.form.get('machine-uid')
            if not uid:
                return render_template("add.html", error="Serial ID missing")
            try:
                uid = int(uid)
            except ValueError:
                return render_template("add.html", error="Serial ID must be numeric")

            m = request.form.get('machine-type')
            # Handle possible inline equipment classification creation
            if m == "other" or request.form.get("new-type-indicator") == "yes":
                # Create new MType from inline form
                inline_name = request.form.get('inline-machine-type-name')
                inline_type = request.form.get('inline-type-category')
                inline_interval = request.form.get('inline-service-interval')
                if inline_type == "single-unit":
                    new_type = MType(name=inline_name, typee=inline_type, interval=int(inline_interval))
                else:
                    new_type = MType(name=inline_name, typee=inline_type)
                db.session.add(new_type)
                db.session.commit()
                add_log(f"Inline registered classification '{inline_name}' ({inline_type}).")
                # Add inline parts if assembled
                if inline_type == "assembled":
                    i = 1
                    while request.form.get(f'inline-part-name-{i}'):
                        partname = request.form.get(f'inline-part-name-{i}')
                        days = request.form.get(f'inline-part-interval-{i}')
                        qu = Parts(name=partname, m_id=new_type.sno, interval=int(days))
                        db.session.add(qu)
                        add_log(
                            f"Added inline component '{partname}' to classification '{inline_name}' with interval {days} days.")
                        i += 1
                    db.session.commit()
                m = new_type.sno

            date = request.form.get('purchase-date')
            s = request.form.get('last-service-indicator')
            dept_value = request.form.get("department")
            manufacturer_value = request.form.get("manufacturer")
            service_location = request.form.get("service-location")

            # Handle new department creation
            if dept_value.startswith("new:"):
                dept_name = dept_value[4:]
                new_dept = Dep(name=dept_name)
                db.session.add(new_dept)
                db.session.commit()
                add_log(f"Registered new department '{dept_name}'.")
                dept_id = new_dept.sno
            else:
                dept_id = int(dept_value)

            # Manufacturer association
            manufacturer_id = int(manufacturer_value) if manufacturer_value else None

            q = MType.query.filter_by(sno=int(m)).first()
            if not q:
                return render_template("add.html", error="Classification not found")

            if q.typee == "single-unit":
                q1 = Machine(
                    name=q.name,
                    m_uid=uid,
                    typee=q.typee,
                    department=dept_id,
                    interval=q.interval,
                    manufacturer=manufacturer_id,  # link to manufacturer if available
                    service_location=service_location,
                    up_date=datetime.strptime(date, '%Y-%m-%d'),
                    ls_date=datetime.strptime(date, '%Y-%m-%d') if s == "no" else datetime.strptime(
                        request.form.get('last-service-date'), '%Y-%m-%d')
                )
                db.session.add(q1)
                db.session.commit()
                add_log(f"Registered equipment '{q.name}' (Serial ID {uid}) in department {dept_id} (Single Unit).")
            else:
                q1 = Machine(
                    name=q.name,
                    m_uid=uid,
                    typee=q.typee,
                    department=dept_id,
                    manufacturer=manufacturer_id,
                    service_location=service_location,
                    up_date=datetime.strptime(date, '%Y-%m-%d')
                )
                db.session.add(q1)
                add_log(f"Registered assembly equipment '{q.name}' (Serial ID {uid}) in department {dept_id}.")
                q2 = Parts.query.filter_by(m_id=int(m)).all()
                ls_date_val = datetime.strptime(date, '%Y-%m-%d') if s == "no" else datetime.strptime(
                    request.form.get('last-service-date'), '%Y-%m-%d')
                for x in q2:
                    q3 = Mpart(
                        name=x.name,
                        m_id=q1.sno,
                        interval=x.interval,
                        ls_date=ls_date_val
                    )
                    db.session.add(q3)
                    add_log(
                        f"Registered component '{x.name}' for equipment '{q.name}' with interval {x.interval} days.")
                db.session.commit()
        else:
            mname = request.form.get('manufacturer-name')
            mno = request.form.get('manufacturer-contact')
            mspeci = request.form.get('manufacturer-specialization')
            q = Manufacturer(name=mname,contact=mno,specialization=mspeci)
            db.session.add(q)
            add_log(f"New manufacturer '{mname}' -- Added")
            db.session.commit()


    machines = sorted(MType.query.all(), key=lambda x: x.name.lower())
    dep = sorted(Dep.query.all(), key=lambda x: x.name.lower())
    manufacturers = sorted(Manufacturer.query.all(), key=lambda x: x.name.lower())
    return render_template("add.html", machines=machines, departments=dep, manufacturers=manufacturers)


@app.route('/check_uid', methods=['POST'])
def check_uid():
    uid = request.json.get('uid')
    print(uid)
    exists = Machine.query.filter_by(m_uid=uid).first() is not None
    return jsonify({'exists': exists})



@app.route('/view',methods=['GET', 'POST'])
def view():
    q = Machine.query.filter_by(typee="single-unit").all()
    q1 = Machine.query.filter_by(typee="assembled").all()
    q2 = Mpart.query.all()
    for m in q:
        if m.ls_date and m.interval:
            m.next_date = m.ls_date + timedelta(days=m.interval)

    for p in q2:
        if p.ls_date and p.interval:
            p.next_date = p.ls_date + timedelta(days=p.interval)

    grouped_s = group_by_name(q)
    grouped_p = group_by_name(q1)
    grouped_parts = group_by_id(q2)

    return render_template("view.html", smachines=grouped_s, pmachines=grouped_p, parts=grouped_parts, view="true", dep = Dep.query.all())



@app.route('/viewc/<sno>',methods=['GET', 'POST'])
def viewc(sno):
    q = Machine.query.filter_by(typee="single-unit" , department=int(sno)).all()
    q1 = Machine.query.filter_by(typee="assembled").all()
    q2 = Mpart.query.all()
    for m in q:
        if m.ls_date and m.interval:
            m.next_date = m.ls_date + timedelta(days=m.interval)

    for p in q2:
        if p.ls_date and p.interval:
            p.next_date = p.ls_date + timedelta(days=p.interval)

    grouped_s = group_by_name(q)
    grouped_p = group_by_name(q1)
    grouped_parts = group_by_id(q2)


    return render_template("view.html", smachines=grouped_s, pmachines=grouped_p, parts=grouped_parts)




@app.route('/check_notifications')
def check_notifications():
    check_and_notify_due_services()
    return "Notification check complete."

@app.route('/')
def indexf():
    dep = Dep.query.all()
    x = notificationlist()
    logs = Slog.query.order_by(Slog.date.desc(), Slog.sno.desc()).all()
    return render_template("home.html",departments=dep,notifi=x,n=len(x),logs=logs)

@app.route('/token')
def token():
    return render_template("index.html")



@app.route('/umachine/<int:sno>', methods=['POST'])
def machine_action( sno):
    action = request.json.get('action')
    # machine = Machine.query.get_or_404(sno)

    if action == 'update_service':
        datee = request.json.get('date')
        typo = request.json.get('typee')
        update_last_service(sno,datee,typo )

    elif action == 'delete':
        record = Machine.query.get(sno)
        db.session.delete(record)
        db.session.commit()
        uid = request.json.get('uid')
        add_log(f"Deleted machine (UID {uid}).")

    return jsonify({"status": "ok"}), 200


@app.route('/machine/<int:uid>', methods=['GET', 'POST'])
def machine_details(uid):
    if request.method == 'POST':
        try:
            data = request.get_json()
            action = data.get('action')

            # Get the machine by m_uid
            machine = Machine.query.filter_by(m_uid=uid).first()
            if not machine:
                return jsonify({'success': False, 'error': 'Machine not found'}), 404

            if action == 'update_basic_info':
                # Update basic machine information
                update_data = data.get('data', {})

                if 'name' in update_data:
                    machine.name = update_data['name']

                if 'typee' in update_data:
                    machine.typee = update_data['typee']

                if 'department' in update_data:
                    machine.department = int(update_data['department']) if update_data['department'] else None

                if 'manufacturer' in update_data:
                    machine.manufacturer = int(update_data['manufacturer']) if update_data['manufacturer'] else None

                if 'service_location' in update_data:
                    machine.service_location = update_data['service_location']

                if 'interval' in update_data:
                    machine.interval = int(update_data['interval']) if update_data['interval'] else None

                if 'up_date' in update_data and update_data['up_date']:
                    machine.up_date = datetime.strptime(update_data['up_date'], '%Y-%m-%d').date()

                # Commit changes to database
                db.session.commit()
                return jsonify({'success': True, 'message': 'Basic information updated successfully'})

            elif action == 'update_service_info':
                # Update service information
                ls_date = data.get('ls_date')
                if ls_date:
                    machine.ls_date = datetime.strptime(ls_date, '%Y-%m-%d').date()
                    db.session.commit()
                return jsonify({'success': True, 'message': 'Service information updated successfully'})

            elif action == 'update_service':
                # Quick service update
                service_date = data.get('date')
                service_notes = data.get('notes', '')

                if service_date:
                    machine.ls_date = datetime.strptime(service_date, '%Y-%m-%d').date()

                # Add service log entry
                if service_notes:
                    log_entry = Slog(
                        date=datetime.now().date(),
                        msg=f"UID:{uid} - {service_notes}"
                    )
                    db.session.add(log_entry)

                db.session.commit()
                return jsonify({'success': True, 'message': 'Service updated successfully'})

            elif action == 'add_log':
                # Add service log entry
                message = data.get('message')
                if message:
                    log_entry = Slog(
                        date=datetime.now().date(),
                        msg=message
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                return jsonify({'success': True, 'message': 'Log entry added successfully'})

            else:
                return jsonify({'success': False, 'error': 'Invalid action'}), 400

        except Exception as e:
            db.session.rollback()
            print(f"Error updating machine: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET request - render the template (your existing code)
    try:
        # Get the machine by m_uid
        machine = Machine.query.filter_by(m_uid=uid).first()
        if not machine:
            print("error")

        department = Dep.query.get(machine.department)
        manufacturer = Manufacturer.query.get(machine.manufacturer) if machine.manufacturer else None

        # Get all departments for dropdown
        all_departments = Dep.query.all()

        # Get all manufacturers for dropdown
        all_manufacturers = Manufacturer.query.all()

        # Get machine type info
        machine_type = MType.query.filter_by(name=machine.name).first()

        # Determine if it's standalone or assembled
        is_assembled = machine_type and machine_type.typee == "assembled" if machine_type else False

        # Get machine parts (if it's an assembled machine)
        machine_parts = []
        available_parts = []
        if is_assembled:
            machine_parts = Mpart.query.filter_by(m_id=machine.sno).all()
            # Get available parts that can be added
            if machine_type:
                available_parts = Parts.query.filter_by(m_id=machine_type.sno).all()

        # Get service logs for this machine
        service_logs = Slog.query.filter(
            Slog.msg.contains(f"UID:{uid}") |
            Slog.msg.contains(str(uid))
        ).order_by(Slog.date.desc()).limit(20).all()

        # Calculate next service date (only for standalone machines)
        next_service_date = None
        service_status = "Not Applicable"
        days_until_service = None

        if not is_assembled and machine.ls_date and machine.interval:
            next_service_date = machine.ls_date + timedelta(days=machine.interval)
            days_until_service = (next_service_date - date.today()).days
            if days_until_service < 0:
                service_status = "Overdue"
            elif days_until_service <= 10:
                service_status = "Due Soon"
            else:
                service_status = "Up to Date"
        elif not is_assembled:
            service_status = "Not Scheduled"

        # Calculate part next service dates
        for part in machine_parts:
            if part.ls_date and part.interval:
                part.next_date = part.ls_date + timedelta(days=part.interval)
                part.days_until = (part.next_date - date.today()).days
                if part.days_until < 0:
                    part.status = "Overdue"
                elif part.days_until <= 10:
                    part.status = "Due Soon"
                else:
                    part.status = "Up to Date"
            else:
                part.next_date = None
                part.days_until = None
                part.status = "Not Scheduled"

        return render_template('machine_details.html',
                               machine=machine,
                               department=department,
                               manufacturer=manufacturer,
                               all_departments=all_departments,
                               all_manufacturers=all_manufacturers,
                               machine_parts=machine_parts,
                               available_parts=available_parts,
                               service_logs=service_logs,
                               next_service_date=next_service_date,
                               service_status=service_status,
                               days_until_service=days_until_service,
                               is_assembled=is_assembled,
                               machine_type=machine_type)

    except Exception as e:
        print(f"Error in machine_details: {e}")
        return "An error occurred", 500

        # abort(500)


@app.route('/component/<int:component_id>', methods=['POST', 'DELETE'])
def update_component(component_id):
    if request.method == 'POST':
        try:
            data = request.get_json()
            action = data.get('action')

            component = Mpart.query.get(component_id)
            if not component:
                return jsonify({'success': False, 'error': 'Component not found'}), 404

            if action == 'update_field':
                field = data.get('field')
                value = data.get('value')

                if field == 'name':
                    component.name = value
                elif field == 'interval':
                    component.interval = int(value) if value else None
                elif field == 'ls_date' and value:
                    component.ls_date = datetime.strptime(value, '%Y-%m-%d').date()

                db.session.commit()
                return jsonify({'success': True, 'message': 'Component updated successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            component = Mpart.query.get(component_id)
            if component:
                db.session.delete(component)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Component deleted successfully'})
            else:
                return jsonify({'success': False, 'error': 'Component not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/component/<int:component_id>/service', methods=['POST'])
def service_component(component_id):
    try:
        data = request.get_json()
        service_date = data.get('date')

        component = Mpart.query.get(component_id)
        if not component:
            return jsonify({'success': False, 'error': 'Component not found'}), 404

        if service_date:
            component.ls_date = datetime.strptime(service_date, '%Y-%m-%d').date()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Component service updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/machine/<int:uid>/add-part', methods=['POST'])
def add_machine_part(uid):
    try:
        data = request.get_json()
        machine = Machine.query.filter_by(m_uid=uid).first()

        if not machine:
            return jsonify({'success': False, 'error': 'Machine not found'}), 404

        new_part = Mpart(
            m_id=machine.sno,
            name=data.get('name'),
            interval=int(data.get('interval')) if data.get('interval') else None,
            ls_date=datetime.strptime(data.get('ls_date'), '%Y-%m-%d').date() if data.get('ls_date') else None
        )

        db.session.add(new_part)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Component added successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/log/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    try:
        log = Slog.query.get(log_id)
        if log:
            db.session.delete(log)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Log deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Log not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/logs')
def logs_page():
    # Fetch latest logs first
    logs = Slog.query.order_by(Slog.date.desc(), Slog.sno.desc()).all()
    return render_template("logs.html", logs=logs)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
    app.run(debug=True)




