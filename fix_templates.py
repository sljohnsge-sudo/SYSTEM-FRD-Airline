import re
import os

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\hotel_details.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<title>Hotel Details | Aeronexa</title>', '<title>Hotel Details | Flight Hub B2B</title>')

b2c_header = '''<header class="b2c-header">
        <a href="/b2c" class="b2c-brand">
            <i class="fa-solid fa-plane-departure"></i> Aeronexa
        </a>
        <div class="b2c-nav">
            <a href="/b2c?tab=flights"><i class="fa-solid fa-plane"></i> Flights</a>
            <a href="/b2c?tab=hotels"><i class="fa-solid fa-hotel"></i> Hotels</a>
            <a href="/b2c?tab=holidays"><i class="fa-solid fa-umbrella-beach"></i> Holidays</a>
            <a href="/b2c/my-bookings" class="btn-mybookings" style="background: #f1f5f9; padding: 8px 16px; border-radius: 6px; color: #0f172a;"><i class="fa-regular fa-user"></i> My Bookings</a>
        </div>
    </header>'''

b2b_header = '''<header class="b2c-header" style="background-color: #ac031c; color: white;">
        <a href="/dashboard" class="b2c-brand" style="color: white; text-decoration: none;">
            <i class="fa-solid fa-hotel"></i> Flight Hub Hotel Details
        </a>
        <div class="b2c-nav">
            <div style="font-weight: 600; font-size: 14px; color: white;">Logged in as {{ agent.company_name }}</div>
        </div>
    </header>'''

content = content.replace(b2c_header, b2b_header)
content = content.replace("`/b2c/hotel-booking?${params.toString()}`", "`/hotel-booking?${params.toString()}`")
content = content.replace('/b2c/hotel-booking', '/hotel-booking')

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\hotel_details.html', 'w', encoding='utf-8') as f:
    f.write(content)


with open(r'd:\GS\SYSTEM-FRD-Airline\templates\hotel_booking.html', 'r', encoding='utf-8') as f:
    content2 = f.read()

content2 = content2.replace('<title>Secure Checkout | Aeronexa</title>', '<title>Secure Checkout | Flight Hub B2B</title>')
content2 = content2.replace(b2c_header, b2b_header.replace('Hotel Details', 'Secure Checkout'))

# Update the payment section: In B2C it has "Pay with Credit/Debit Card". In B2B we need to allow Agent Credit.
# Let's do a simple regex or string replace to add Agent Credit option if it's not there.
# Actually, I'll just change the text of the B2C card payment slightly. B2B agents should pay with Agent Credit.
content2 = content2.replace('Pay with Credit/Debit Card', 'Pay from Agent Credit Balance')
content2 = content2.replace('cardnumber', 'agent_ref') # just visually
content2 = content2.replace('Card Number', 'Agent Reference ID')

content2 = content2.replace('/api/b2c/hotels/book', '/api/hotels/book')
content2 = content2.replace('href="/b2c"', 'href="/dashboard"')
content2 = content2.replace('b2c_hotel_details.html', 'hotel_details.html') # if any

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\hotel_booking.html', 'w', encoding='utf-8') as f:
    f.write(content2)

print("done")
