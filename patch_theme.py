import os

def update_welcome():
    path = r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    css_inject = """
        body {
            background-image: url('{{ url_for('static', filename='img/airline_bg.png') }}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            color: #ffffff;
        }

        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(136, 18, 59, 0.6) 0%, rgba(0, 59, 149, 0.7) 100%);
            z-index: -1;
        }

        .landing-navbar {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .hero-badge {
            background: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            color: #ffffff !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        }

        .hero-title {
            color: #ffffff !important;
            background: none !important;
            -webkit-text-fill-color: #ffffff !important;
            text-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }

        .hero-desc {
            color: rgba(255, 255, 255, 0.9) !important;
            text-shadow: 0 2px 5px rgba(0, 0, 0, 0.4);
        }

        .btn-hero-primary {
            background: var(--primary) !important;
            box-shadow: 0 4px 15px rgba(136, 18, 59, 0.5) !important;
        }

        .btn-hero-secondary {
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            color: #ffffff !important;
            backdrop-filter: blur(5px);
        }
        
        .btn-hero-secondary:hover {
            background: rgba(255, 255, 255, 0.25) !important;
            color: #ffffff !important;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        .feature-card:hover {
            background: rgba(255, 255, 255, 0.12) !important;
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
        }

        .feature-card h3 {
            color: #ffffff !important;
        }

        .feature-card p {
            color: rgba(255, 255, 255, 0.75) !important;
        }

        .feature-icon {
            background: rgba(255, 255, 255, 0.15) !important;
            color: #ffffff !important;
        }
    """
    
    if ".overlay {" not in content:
        content = content.replace("/* Specific Styles for Landing Welcome Page */", "/* Specific Styles for Landing Welcome Page */\n" + css_inject)
        content = content.replace("<body>", "<body>\n    <div class=\"overlay\"></div>")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_login():
    path = r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    css_inject = """
    <style>
        body {
            background-image: url('{{ url_for('static', filename='img/airline_bg.png') }}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }
        
        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(136, 18, 59, 0.65) 0%, rgba(0, 59, 149, 0.75) 100%);
            z-index: -1;
        }

        .auth-card {
            background: rgba(255, 255, 255, 0.92) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3) !important;
        }
    </style>
    """
    
    if ".overlay {" not in content:
        content = content.replace("</head>", css_inject + "\n</head>")
        content = content.replace("<body style=\"display:flex; align-items:center; justify-content:center;\">", "<body style=\"display:flex; align-items:center; justify-content:center;\">\n    <div class=\"overlay\"></div>")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_welcome()
    update_login()
