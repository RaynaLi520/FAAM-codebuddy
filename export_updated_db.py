import sqlite3

conn = sqlite3.connect('faam_products.db')
cursor = conn.cursor()

with open('database_data.sql', 'w', encoding='utf-8') as f:
    # Products table
    cursor.execute('SELECT * FROM products')
    columns = [desc[0] for desc in cursor.description]
    
    f.write('-- Products table\n')
    f.write('DROP TABLE IF EXISTS products;\n')
    f.write('CREATE TABLE products (' + ', '.join(columns) + ');\n')
    
    for row in cursor.fetchall():
        values = []
        for v in row:
            if v is None:
                values.append('NULL')
            elif isinstance(v, int):
                values.append(str(v))
            elif isinstance(v, float):
                values.append(str(v))
            else:
                values.append("'" + str(v).replace("'", "''") + "'")
        f.write('INSERT INTO products VALUES (' + ', '.join(values) + ');\n')
    
    # Daily new arrivals table
    cursor.execute('SELECT * FROM daily_new_arrivals')
    columns = [desc[0] for desc in cursor.description]
    
    f.write('\n-- Daily new arrivals table\n')
    f.write('DROP TABLE IF EXISTS daily_new_arrivals;\n')
    f.write('CREATE TABLE daily_new_arrivals (' + ', '.join(columns) + ');\n')
    
    for row in cursor.fetchall():
        values = []
        for v in row:
            if v is None:
                values.append('NULL')
            elif isinstance(v, int):
                values.append(str(v))
            elif isinstance(v, float):
                values.append(str(v))
            else:
                values.append("'" + str(v).replace("'", "''") + "'")
        f.write('INSERT INTO daily_new_arrivals VALUES (' + ', '.join(values) + ');\n')

conn.close()
print("Database exported to database_data.sql")
