import os

replacements = {
    'food-ordering-system/frontend/templates/restaurant/index.html': [
        ('<title>Dabba - Restaurant Dashboard</title>', '<title>CraveBites - Restaurant Dashboard</title>'),
        ('Dabba <span style="color:#FFC233">Kitchen</span>', 'CraveBites <span style="color:#FFC233">Restaurant</span>'),
        ('Dabba Kitchen', 'CraveBites Restaurant')
    ],
    'food-ordering-system/design/dabba-restaurant.html': [
        ('<title>Dabba - Restaurant dashboard</title>', '<title>CraveBites - Restaurant Dashboard</title>'),
        ('Dabba <span style="color:#FFC233">Kitchen</span>', 'CraveBites <span style="color:#FFC233">Restaurant</span>'),
        ('Dabba Kitchen', 'CraveBites Restaurant')
    ],
    'food-ordering-system/design/dabba-customer.html': [
        ('<title>Dabba - Customer app</title>', '<title>CraveBites - Customer App</title>')
    ],
    'food-ordering-system/design/dabba-delivery.html': [
        ('<title>Dabba - Delivery partner app</title>', '<title>Crave Rider - Delivery Partner App</title>')
    ],
    'food-ordering-system/frontend/templates/auth/login.html': [
        ('<title>Dabba - Login</title>', '<title>CraveBites - Login</title>'),
        ('Dabba <span>Online</span>', 'CraveBites <span>Online</span>'),
        ('Sign in to your college food ordering account', 'Sign in to your CraveBites account')
    ],
    'food-ordering-system/frontend/templates/auth/signup.html': [
        ('<title>Dabba - Create Account</title>', '<title>CraveBites - Create Account</title>'),
        ('Dabba <span>Sign Up</span>', 'CraveBites <span>Sign Up</span>'),
        ('Join the campus food network', 'Join the CraveBites food network')
    ],
    'food-ordering-system/frontend/templates/customer/index.html': [
        ('<title>Dabba - Customer App</title>', '<title>CraveBites - Customer App</title>'),
        ('Dabba Coins', 'Crave Coins')
    ],
    'food-ordering-system/frontend/templates/delivery/index.html': [
        ('<title>Dabba - Delivery Partner App</title>', '<title>Crave Rider - Delivery Partner App</title>')
    ],
    'food-ordering-system/backend/app.py': [
        ('Starting Dabba Server', 'Starting CraveBites Server'),
        ("'service': 'dabba-backend'", "'service': 'cravebites-backend'")
    ],
    'START_SERVERS.bat': [
        ('title Dabba Server Launcher', 'title CraveBites Server Launcher'),
        ('start "Dabba Backend (Port 5000)"', 'start "CraveBites Backend (Port 5000)"'),
        ('start "Dabba Restaurant Web (Port 5002)"', 'start "CraveBites Restaurant Web (Port 5002)"'),
        ('DABBA SERVERS ARE NOW RUNNING', 'CRAVEBITES SERVERS ARE NOW RUNNING')
    ],
    'food-ordering-system/START_SERVERS.bat': [
        ('title Dabba Server Launcher', 'title CraveBites Server Launcher'),
        ('start "Dabba Backend (Port 5000)"', 'start "CraveBites Backend (Port 5000)"'),
        ('start "Dabba Restaurant Web (Port 5002)"', 'start "CraveBites Restaurant Web (Port 5002)"'),
        ('STARTING DABBA SERVERS', 'STARTING CRAVEBITES SERVERS'),
        ('DABBA SERVERS ARE NOW RUNNING', 'CRAVEBITES SERVERS ARE NOW RUNNING')
    ],
    'RUN_BACKEND.bat': [
        ('title Dabba Backend (Port 5000)', 'title CraveBites Backend (Port 5000)')
    ],
    'food-ordering-system/backend/run_backend.bat': [
        ('title Dabba Backend (Port 5000)', 'title CraveBites Backend (Port 5000)')
    ],
    'RUN_RESTAURANT_WEB.bat': [
        ('title Dabba Restaurant Web (Port 5002)', 'title CraveBites Restaurant Web (Port 5002)')
    ],
    'food-ordering-system/restaurant-web/run_restaurant.bat': [
        ('title Dabba Restaurant Web (Port 5002)', 'title CraveBites Restaurant Web (Port 5002)')
    ],
    'food-ordering-system/customer-app/index.html': [
        ('Dabba', 'CraveBites')
    ],
    'dabba-customer.html': [
        ('Dabba', 'CraveBites')
    ]
}

for path, r_list in replacements.items():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for old, new in r_list:
            content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {path}')
print('Done!')
