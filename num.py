import sqlite3 as sql
import datetime

# Database connection
try:
    c = sql.connect('inventory.db')
    co = c.cursor()
    print('DATABASE CONNECTION BUILT SUCCESSFULLY')

except sql.Error as e:
    print(f"Error connecting to the database: {e}")
    exit()

# Create database and tables
try:
    co.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name VARCHAR(255) NOT NULL UNIQUE
        )
    ''')
    
    co.execute('''
        CREATE TABLE IF NOT EXISTS machine (
            sno INTEGER PRIMARY KEY AUTOINCREMENT, 
            name VARCHAR(200) NOT NULL, 
            m_uid INTEGER, 
            typee VARCHAR(500) NOT NULL, 
            interval INTEGER, 
            date_of_addition DATE, 
            last_service_date DATE,
            next_service_date DATE,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')

    co.execute('''
        CREATE TABLE IF NOT EXISTS machine_type (
            sno INTEGER PRIMARY KEY AUTOINCREMENT, 
            name VARCHAR(200) NOT NULL, 
            typee VARCHAR(500) NOT NULL, 
            interval INTEGER
        )
    ''')

    co.execute('''
        CREATE TABLE IF NOT EXISTS machine_parts (
            sno INTEGER PRIMARY KEY AUTOINCREMENT, 
            name VARCHAR(200) NOT NULL, 
            m_id INTEGER NOT NULL, 
            interval INTEGER, 
            last_service_date DATE,
            next_service_date DATE,
            FOREIGN KEY(m_id) REFERENCES machine (sno)
        )
    ''')
    
    co.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            sno INTEGER PRIMARY KEY AUTOINCREMENT, 
            name VARCHAR(200) NOT NULL, 
            m_id INTEGER NOT NULL, 
            interval INTEGER, 
            FOREIGN KEY(m_id) REFERENCES machine_type (sno)
        )
    ''')
    
    c.commit()
    print("Database and tables are ready.")
    
except sql.Error as e:
    print(f"Error creating database/tables: {e}")
    c.rollback()

def calculate_next_service_date(last_date, interval):
    if last_date and interval:
        try:
            last_date_obj = datetime.datetime.strptime(str(last_date), "%Y-%m-%d")
            return (last_date_obj + datetime.timedelta(days=int(interval))).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    return None

def add_department():
    try:
        department_name = input("Enter department name: ").strip()
        if not department_name:
            print("Department name cannot be empty.")
            return

        co.execute("INSERT INTO departments (department_name) VALUES (?)", (department_name,))
        c.commit()
        print(f"Department '{department_name}' added successfully.")
    except sql.IntegrityError:
        print("Error: A department with this name already exists.")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def add_machine():
    try:
        name = input("Enter machine name: ").strip()
        m_uid = input("Enter machine UID: ").strip()
        typee = input("Enter machine type: ").strip()
        interval = input("Enter service interval in days: ").strip()
        date_of_addition = input("Enter date of addition (YYYY-MM-DD): ").strip()
        last_service_date = input("Enter last service date (YYYY-MM-DD): ").strip()
        department_name = input("Enter department name for the machine: ").strip()

        if not all([name, m_uid, typee, interval, date_of_addition, last_service_date, department_name]):
            print("All fields must be filled.")
            return

        co.execute("SELECT id FROM departments WHERE department_name = ?", (department_name,))
        department = co.fetchone()
        if not department:
            print("Department not found. Please add the department first.")
            return
        department_id = department[0]

        next_service_date = calculate_next_service_date(last_service_date, interval)
        
        co.execute("""
            INSERT INTO machine (name, m_uid, typee, interval, date_of_addition, last_service_date, next_service_date, department_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, m_uid, typee, interval, date_of_addition, last_service_date, next_service_date, department_id))
        
        c.commit()
        print(f"Machine '{name}' added successfully.")
    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def add_machine_part():
    try:
        name = input("Enter part name: ").strip()
        m_id = input("Enter the machine 'sno' this part belongs to: ").strip()
        interval = input("Enter service interval in days: ").strip()
        last_service_date = input("Enter last service date (YYYY-MM-DD): ").strip()

        if not all([name, m_id, interval, last_service_date]):
            print("All fields must be filled.")
            return
            
        co.execute("SELECT sno FROM machine WHERE sno = ?", (m_id,))
        if not co.fetchone():
            print("Machine with this 'sno' not found. Please add the machine first.")
            return
            
        next_service_date = calculate_next_service_date(last_service_date, interval)

        co.execute("""
            INSERT INTO machine_parts (name, m_id, interval, last_service_date, next_service_date)
            VALUES (?, ?, ?, ?, ?)
        """, (name, m_id, interval, last_service_date, next_service_date))
        
        c.commit()
        print(f"Part '{name}' added successfully.")
    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def add_menu():
    while True:
        print("\nAdd Menu:")
        print("1. Add a Department")
        print("2. Add a Machine")
        print("3. Add a Machine Part")
        print("4. Back to Main Menu")
        add_choice = input("Enter your choice: ").strip()
        
        if add_choice == '1':
            add_department()
        elif add_choice == '2':
            add_machine()
        elif add_choice == '3':
            add_machine_part()
        elif add_choice == '4':
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

def update_machine():
    try:
        machine_name = input("Enter the machine name to update: ").strip()
        m_uid = input("Enter the machine UID: ").strip()
        
        co.execute("SELECT * FROM machine WHERE name = ? AND m_uid = ?", (machine_name, m_uid))
        machine_record = co.fetchone()
        if not machine_record:
            print("Machine not found.")
            return

        print("\nColumns available for update:")
        print("1. name\n2. m_uid\n3. typee\n4. interval\n5. date_of_addition\n6. last_service_date\n7. next_service_date\n8. department_id")
        choice = input("Enter the column number to update: ")
        
        column_map = {
            '1': 'name', '2': 'm_uid', '3': 'typee', '4': 'interval', 
            '5': 'date_of_addition', '6': 'last_service_date', '7': 'next_service_date', '8': 'department_id'
        }
        
        if choice not in column_map:
            print("Invalid choice.")
            return
            
        column = column_map[choice]
        new_value = input(f"Enter the new value for '{column}': ").strip()
        
        if not new_value:
            print("New value cannot be empty.")
            return

        if column in ['date_of_addition', 'last_service_date', 'next_service_date']:
            try:
                datetime.datetime.strptime(new_value, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
                return

        if column in ['last_service_date', 'interval']:
            if column == 'last_service_date':
                last_service_date = new_value
                interval = machine_record[4]
            else:
                last_service_date = machine_record[6]
                interval = new_value
            
            next_service = calculate_next_service_date(last_service_date, interval)
            
            if next_service:
                co.execute(f"UPDATE machine SET {column} = ?, next_service_date = ? WHERE name = ? AND m_uid = ?", (new_value, next_service, machine_name, m_uid))
            else:
                co.execute(f"UPDATE machine SET {column} = ? WHERE name = ? AND m_uid = ?", (new_value, machine_name, m_uid))
        else:
            co.execute(f"UPDATE machine SET {column} = ? WHERE name = ? AND m_uid = ?", (new_value, machine_name, m_uid))
        
        c.commit()
        print(f"Machine '{machine_name}' successfully updated.")

    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def update_part():
    try:
        part_name = input("Enter the part name to update: ").strip()
        m_id = input("Enter the machine ID (m_id) associated with the part: ").strip()
        
        co.execute("SELECT * FROM machine_parts WHERE name = ? AND m_id = ?", (part_name, m_id))
        part_record = co.fetchone()
        if not part_record:
            print("Part not found.")
            return

        print("\nColumns available for update:")
        print("1. name\n2. interval\n3. last_service_date\n4. next_service_date")
        choice = input("Enter the column number to update: ")
        
        column_map = {
            '1': 'name', '2': 'interval', '3': 'last_service_date', '4': 'next_service_date'
        }

        if choice not in column_map:
            print("Invalid choice.")
            return
            
        column = column_map[choice]
        new_value = input(f"Enter the new value for '{column}': ").strip()
        
        if not new_value:
            print("New value cannot be empty.")
            return

        if column in ['last_service_date', 'next_service_date']:
            try:
                datetime.datetime.strptime(new_value, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
                return

        if column in ['last_service_date', 'interval']:
            if column == 'last_service_date':
                last_service_date = new_value
                interval = part_record[3]
            else:
                last_service_date = part_record[4]
                interval = new_value
            
            next_service = calculate_next_service_date(last_service_date, interval)
            
            if next_service:
                co.execute(f"UPDATE machine_parts SET {column} = ?, next_service_date = ? WHERE name = ? AND m_id = ?", (new_value, next_service, part_name, m_id))
            else:
                co.execute(f"UPDATE machine_parts SET {column} = ? WHERE name = ? AND m_id = ?", (new_value, part_name, m_id))
        else:
            co.execute(f"UPDATE machine_parts SET {column} = ? WHERE name = ? AND m_id = ?", (new_value, part_name, m_id))
        
        c.commit()
        print(f"Part '{part_name}' successfully updated.")

    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def update_menu():
    while True:
        print("\nUpdate Menu:")
        print("1. Update a Machine")
        print("2. Update a Machine Part")
        print("3. Back to Main Menu")
        update_choice = input("Enter your choice: ").strip()
        
        if update_choice == '1':
            update_machine()
        elif update_choice == '2':
            update_part()
        elif update_choice == '3':
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            
def delete_machine():
    try:
        machine_name = input("Enter the machine name to delete: ").strip()
        m_uid = input("Enter the machine UID: ").strip()
        
        co.execute("SELECT sno FROM machine WHERE name = ? AND m_uid = ?", (machine_name, m_uid))
        machine_sno = co.fetchone()
        
        if not machine_sno:
            print("Machine not found.")
            return
        
        machine_sno = machine_sno[0]
        
        confirm = input(f"Are you sure you want to delete machine '{machine_name}' and all its parts? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return

        co.execute("DELETE FROM machine_parts WHERE m_id = ?", (machine_sno,))
        co.execute("DELETE FROM machine WHERE sno = ?", (machine_sno,))
        
        c.commit()
        print(f"Machine '{machine_name}' and all its parts have been deleted successfully.")

    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def delete_part():
    try:
        part_name = input("Enter the part name to delete: ").strip()
        m_id = input("Enter the machine ID (m_id) associated with the part: ").strip()

        co.execute("SELECT * FROM machine_parts WHERE name = ? AND m_id = ?", (part_name, m_id))
        if not co.fetchone():
            print("Part not found.")
            return
            
        confirm = input(f"Are you sure you want to delete part '{part_name}' from machine ID {m_id}? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return

        co.execute("DELETE FROM machine_parts WHERE name = ? AND m_id = ?", (part_name, m_id))
        
        c.commit()
        print(f"Part '{part_name}' deleted successfully.")

    except sql.Error as e:
        print(f"Database error: {e}")
        c.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        c.rollback()

def delete_menu():
    while True:
        print("\nDelete Menu:")
        print("1. Delete a Machine (and all its parts)")
        print("2. Delete a Machine Part")
        print("3. Back to Main Menu")
        delete_choice = input("Enter your choice: ").strip()
        
        if delete_choice == '1':
            delete_machine()
        elif delete_choice == '2':
            delete_part()
        elif delete_choice == '3':
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def display_all_records():
    """Displays all departments, machines, and their associated parts."""
    try:
        print("\n--- Current Inventory Records ---")
        
        co.execute("SELECT id, department_name FROM departments ORDER BY department_name")
        departments = co.fetchall()
        
        if not departments:
            print("No departments found.")
            return

        for dept_id, dept_name in departments:
            print(f"\nDepartment: {dept_name} (ID: {dept_id})")
            print("-" * (len(dept_name) + 15))

            co.execute("SELECT sno, name, m_uid, typee, last_service_date, next_service_date FROM machine WHERE department_id = ? ORDER BY name", (dept_id,))
            machines = co.fetchall()

            if not machines:
                print("  No machines in this department.")
                continue

            for sno, name, m_uid, typee, last_date, next_date in machines:
                print(f"  Machine: {name} (SNO: {sno}, UID: {m_uid})")
                print(f"    - Type: {typee}")
                print(f"    - Last Service: {last_date} | Next Service: {next_date}")
                
                co.execute("SELECT name, interval, last_service_date, next_service_date FROM machine_parts WHERE m_id = ? ORDER BY name", (sno,))
                parts = co.fetchall()
                
                if parts:
                    print("    - Parts:")
                    for part_name, part_interval, part_last_date, part_next_date in parts:
                        print(f"      - Part: {part_name} | Interval: {part_interval} days | Last: {part_last_date} | Next: {part_next_date}")
                else:
                    print("    - No parts found for this machine.")
                    
    except sql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    while True:
        print("\n    INVENTORY MANAGEMENT SYSTEM    ")
        print("1. Add a Record")
        print("2. Display All Records")
        print("3. Update Records")
        print("4. Delete Records")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            add_menu()
        elif choice == '2':
            display_all_records()
        elif choice == '3':
            update_menu()
        elif choice == '4':
            delete_menu()
        elif choice == '5':
            print("Thank you for using the Inventory Management System!")
            break
        else:
            print("Invalid choice. Please enter a number between 1-5.")
            
    try:
        if c.is_connected():
            co.close()
            c.close()
            print("Database connection closed successfully.")
    except:
        pass

if __name__ == "__main__":
    main()
