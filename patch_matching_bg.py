import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to remove the YouTube iframe HTML
    content = re.sub(r'<!-- Global Data Network Background Video -->.*?</div>', '', content, flags=re.DOTALL)
    
    # We will add the custom montage before the overlay
    montage_html = """
    <!-- Custom Service-Matching Background Montage -->
    <div class="custom-montage">
        <!-- Flights -->
        <div class="slide slide-1"></div>
        <!-- Wholesale Hotels -->
        <div class="slide slide-2"></div>
        <!-- Passenger Visa Compliance -->
        <div class="slide slide-3"></div>
        <!-- Automated Tickets, Re-issues & Refunds -->
        <div class="slide slide-4"></div>
    </div>
    """
    
    # Inject it before <div class="overlay">
    match = re.search(r'(<div class="overlay"></div>)', content)
    if match and "custom-montage" not in content:
        content = content[:match.start(0)] + montage_html + "\n    " + content[match.start(0):]

    # Add the CSS for montage
    montage_css = """
        /* Custom Background Montage (Unbranded) */
        .custom-montage {
            position: fixed;
            top: 0; right: 0; bottom: 0; left: 0;
            z-index: -2;
            overflow: hidden;
            background: #000;
        }
        
        .slide {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-size: cover;
            background-position: center;
            opacity: 0;
            animation: kenburns-crossfade 24s infinite;
        }
        
        /* 1. Flights (Instantly access flights) */
        .slide-1 {
            background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 0s;
        }
        
        /* 2. Wholesale Hotels */
        .slide-2 {
            background-image: url('https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=2000&q=80'); /* Luxury Hotel Resort/Lobby */
            animation-delay: 6s;
        }
        
        /* 3. Passenger Visa Compliance */
        .slide-3 {
            background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=2000&q=80'); /* Passport / Visa Stamps */
            animation-delay: 12s;
        }
        
        /* 4. Tickets, Re-issues, Refunds */
        .slide-4 {
            background-image: url('https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=2000&q=80'); /* Agent processing data/payments */
            animation-delay: 18s;
        }
        
        @keyframes kenburns-crossfade {
            0% { opacity: 0; transform: scale(1.0); }
            4% { opacity: 1; }
            25% { opacity: 1; transform: scale(1.04); }
            30% { opacity: 0; transform: scale(1.05); }
            100% { opacity: 0; transform: scale(1.0); }
        }
    """
    
    # Clean old video background CSS
    content = re.sub(r'\.video-background\s*{[^}]+}', '', content)
    content = re.sub(r'\.video-background iframe\s*{[^}]+}', '', content)
    
    if ".custom-montage {" not in content:
        content = content.replace('</style>', montage_css + '\n</style>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
