import random
from faker import Faker
import sqlite3

class CustomerGenerator:
    def __init__(self):
        self.customer_id = []
        self.fake_en = Faker('en_US')
    
    def generate_customer(self, num_customers):
        """Generates a list of customer dictionaries with realistic data"""
        customers = []
        for i in range(num_customers):
            # Generate a unique customer ID in the format 'cust_00001', 'cust_00002', etc.
            cust_id = f"cust_{i+1:05d}"
            self.customer_id.append(cust_id)
            # Using Faker to generate realistic names, phone numbers, and emails
            name = self.fake_en.name()
            phone_number = random.choices([None, self.fake_en.numerify('###-###-####')], 
                                          weights=[0.15, 0.85])[0]
            email = random.choices([None, self.fake_en.ascii_email()], 
                                   weights=[0.1, 0.9])[0]
            age = random.randint(18,61)
            customers.append({
                'customer_id': cust_id,
                'name': name,
                'age': age,
                'phone_number': phone_number,
                'email': email,
                # Initialize total_spent to 0 and customer_tier to 'Bronze' 
                # for all customers to fill in later when generating transactions
                'total_spent': 0,
                'customer_tier': 'Bronze'
            })
        return customers
    
class TransactionGenerator:
    def __init__(self):
        self.transaction_id = set()
    # Helper function to determine if a year is a leap year
    def _is_leap_year(self, year):
        if year % 4 != 0:
            return False
        if year % 100 != 0:
            return True
        return year % 400 == 0
    
    def generate_transaction(self, item_table, customer_table):
        """Generates a list of transaction dictionaries with realistic data"""
        customer_map = {c['customer_id']: c for c in customer_table}
        valid_customer_ids = list(customer_map.keys())

        total_per_transaction = {}
        # Calculate the total amount for each transaction by 
        # summing up the unit price multiplied by quantity for each item in the transaction
        for i in item_table:
            t_id = i['transaction_id']
            cumulative_price = i['unit_price'] * i['quantity']
            if t_id in total_per_transaction:
                total_per_transaction[t_id] += cumulative_price
            else:
                total_per_transaction[t_id] = cumulative_price
        
        transaction_id = list(total_per_transaction.keys())

        if not valid_customer_ids:
            raise ValueError('List of customer is blank!')
        
        transaction = []
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for i in range(len(transaction_id)):
            # Generate a random date for the transaction between 2021 and 2025, 
            # ensuring that the day is valid for the month and year (considering leap years)
            year = random.randint(2021,2025)
            month = random.randint(1,12)
            max_day = days_in_month[month - 1]
            if month == 2 and self._is_leap_year(year):
                max_day = 29
            day = random.randint(1,max_day)
            date = f'{year}-{month:02d}-{day:02d}'
            # Randomly assign a customer ID to the transaction from the list of valid customer IDs
            random_customer = random.choice(valid_customer_ids)
            
            transaction_amount = total_per_transaction[transaction_id[i]]

            transaction.append({
                'transaction_id': transaction_id[i],
                'customer_id': random_customer,
                'transaction_date': date,
                'transaction_amount': transaction_amount
            })
            # Update the total_spent for the customer and determine their customer tier based on the total amount spent
            customer_map[random_customer]['total_spent'] += transaction_amount
            if customer_map[random_customer]['total_spent'] < 1200:
                customer_map[random_customer]['customer_tier'] = 'Bronze'
            elif customer_map[random_customer]['total_spent'] < 2200:
                customer_map[random_customer]['customer_tier'] = 'Silver'
            elif customer_map[random_customer]['total_spent'] < 2800:
                customer_map[random_customer]['customer_tier'] = 'Gold'
            else:
                customer_map[random_customer]['customer_tier'] = 'Premium'
        return transaction

class ItemGenerator:
    def __init__(self):
        self.transaction_id = set()

    def generate_item(self, num_transaction):
        """Generates a list of item dictionaries with realistic data"""
        # Generate unique transaction IDs in the format of 17-digit numbers, ensuring that there are no duplicates
        while len(self.transaction_id) < num_transaction:
            min_val = 10 ** 16
            max_val = (10 ** 17) - 1

            transaction = random.randint(min_val, max_val)
            self.transaction_id.add(transaction)
        
        transaction_id_collection = list(self.transaction_id)
        items = []
        category_list = {111:'Food',
                         222:'Clothing',
                         333:'Electronics',
                         444:'Books',
                         555:'Home & Garden',
                         666:'Health & Beauty',
                         777:'Game'}
        
        transaction_category = [111,222,333,444,555,666,777]
        category_weight = [0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05]
        
        for i in range(num_transaction):
            bought_items = set()
            for j in range(random.randint(1,5)):
                # Generate a random unit price between $3 and $120 and 
                # a random quantity between 1 and 3 for each item in the transaction
                unit_price = random.randint(3,120)
                quantity = random.randint(1, 3)
                # Randomly select a category for the item based on the defined categories and their corresponding weights, 
                # ensuring that the same category is not selected more than once for the same transaction
                while True:
                    category_id = random.choices(transaction_category, weights=category_weight, k=1)[0]
                    if category_id not in bought_items:
                        bought_items.add(category_id)
                        break
                category_name = category_list[category_id]
                items.append({
                    'transaction_id': transaction_id_collection[i],
                    'category_id': category_id,
                    'category_name':category_name,
                    'unit_price':unit_price,
                    'quantity':quantity
                })
        return items

    def get_transaction_id(self):
        return self.transaction_id

class DatabaseManager:
    def __init__(self, db_name='sales_database.db'):
        self.db_name = db_name

    def create_schema(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Create the Customers, Transactions, and Transaction_Items tables with appropriate columns and data types, 
        # ensuring that primary keys and foreign key relationships are properly defined
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            phone_number TEXT,
            email TEXT,
            total_spent REAL,
            customer_tier TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transactions (
            transaction_id INTEGER PRIMARY KEY,
            customer_id TEXT,
            transaction_date TEXT,
            transaction_amount REAL,
            FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transaction_Items (
            transaction_id INTEGER,
            category_id INTEGER,
            category_name TEXT,
            unit_price REAL,
            quantity INTEGER,
            PRIMARY KEY (transaction_id, category_id),
            FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        )
        ''')

        conn.commit()
        conn.close()
        print(f"Schema created successfully in {self.db_name}.")

    def insert_data(self, customers, transactions, items):
        """Inserts the generated Python dictionaries into the SQLite database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        customer_sql = '''INSERT INTO Customers 
                          (customer_id, name, age, phone_number, email, total_spent, customer_tier)
                          VALUES (?, ?, ?, ?, ?, ?, ?)'''
        for c in customers:
            cursor.execute(customer_sql, (c['customer_id'], c['name'], c['age'], c['phone_number'], 
                                          c['email'], c['total_spent'], c['customer_tier']))

        transaction_sql = '''INSERT INTO Transactions 
                             (transaction_id, customer_id, transaction_date, transaction_amount)
                             VALUES (?, ?, ?, ?)'''
        for t in transactions:
            cursor.execute(transaction_sql, (t['transaction_id'], t['customer_id'], 
                                             t['transaction_date'], t['transaction_amount']))

        item_sql = '''INSERT INTO Transaction_Items 
                      (transaction_id, category_id, category_name, unit_price, quantity)
                      VALUES (?, ?, ?, ?, ?)'''
        for i in items:
            cursor.execute(item_sql, (i['transaction_id'], i['category_id'], i['category_name'], 
                                      i['unit_price'], i.get('quantity', 1)))

        conn.commit()
        conn.close()
        print("All data inserted successfully!")

def __main__():
    num_customers = 1000  
    num_transactions = 4000

    print("Generating data...")
    customer_gen = CustomerGenerator()
    customers_data = customer_gen.generate_customer(num_customers)

    item_gen = ItemGenerator()
    items_data = item_gen.generate_item(num_transactions)

    transaction_gen = TransactionGenerator()
    transactions_data = transaction_gen.generate_transaction(items_data, customers_data)

    db_manager = DatabaseManager('sales_database.db')
    db_manager.create_schema()
    db_manager.insert_data(customers_data, transactions_data, items_data)
    
if __name__ == "__main__":
    __main__()

