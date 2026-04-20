from database.db import get_connection
from datetime import date, timedelta

conn = get_connection()

martin = conn.execute("SELECT id FROM users WHERE email='martin@gmail.com'").fetchone()
book   = conn.execute("SELECT id,title FROM books WHERE id=2").fetchone()

loan_date = (date.today() - timedelta(days=15)).isoformat()
due_date  = (date.today() - timedelta(days=5)).isoformat()

conn.execute(
    "INSERT INTO loan_records (member_id,book_id,loan_date,due_date,status) VALUES (?,?,?,?,'active')",
    (martin['id'], book['id'], loan_date, due_date)
)
conn.execute('UPDATE books SET available_copies=available_copies-1 WHERE id=?', (book['id'],))
conn.commit()
conn.close()

print('==========================================')
print('       OVERDUE LOAN CREATED!')
print('==========================================')
print(f'  Book         : {book["title"]}')
print(f'  Borrowed     : {loan_date}  (15 days ago)')
print(f'  Loan Period  : 10 days')
print(f'  Due Date     : {due_date}  (5 days ago)')
print(f'  Days Overdue : 5 days')
print(f'  Fine Rate    : $0.50 per day')
print(f'  Expected Fine: 5 x $0.50 = $2.50')
print('==========================================')
