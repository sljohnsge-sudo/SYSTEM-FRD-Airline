with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        # Get new balance
        cursor.execute("SELECT credit_balance, company_name FROM users WHERE id = %s", (agent_id,))
        res = cursor.fetchone()
        new_balance = float(res[0])
        company_name = res[1]
        
        cursor.close()
        conn.close()'''

replacement = '''        # Get new balance
        cursor.execute("SELECT credit_balance, company_name FROM users WHERE id = %s", (agent_id,))
        res = cursor.fetchone()
        new_balance = float(res[0])
        company_name = res[1]
        
        # Generate popup notification for the agent
        amt_float = float(amount)
        action_text = "added to" if amt_float > 0 else "deducted from"
        message_text = f"Credit Update: ${abs(amt_float):.2f} has been {action_text} your account wallet. New Balance: ${new_balance:.2f}. Reason: {description}"
        cursor.execute("INSERT INTO popups (message_text, is_active, created_at, agent_id) VALUES (%s, 1, NOW(), %s)", (message_text, agent_id))
        conn.commit()
        
        cursor.close()
        conn.close()'''

new_content = content.replace(target, replacement)
with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Replaced content in app.py successfully')
