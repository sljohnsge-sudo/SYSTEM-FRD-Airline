import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the YouTube iframe
    content = re.sub(r'<div class="video-background">.*?</div>', '', content, flags=re.DOTALL)
    
    # We will add the custom montage before the overlay
    montage_html = """
    <!-- Custom Unbranded Background Montage -->
    <div class="custom-montage">
        <div class="slide slide-1"></div>
        <div class="slide slide-2"></div>
        <div class="slide slide-3"></div>
    </div>
    """
    
    if "custom-montage" not in content:
        content = content.replace('<div class="overlay"></div>', montage_html + '\n    <div class="overlay"></div>')

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
        
        /* 1. Flight is flying */
        .slide-1 {
            background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 0s;
        }
        
        /* 2. Nice travel destination */
        .slide-2 {
            background-image: url('https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=2000&q=80'); /* Paris / Beautiful Destination */
            animation-delay: 8s;
        }
        
        /* 3. Professional service providing by staff */
        .slide-3 {
            background-image: url('https://images.unsplash.com/photo-1556745753-b2904692b3cd?auto=format&fit=crop&w=2000&q=80'); /* Professional Concierge / Staff */
            animation-delay: 16s;
        }
        
        @keyframes kenburns-crossfade {
            0% { opacity: 0; transform: scale(1.0); }
            10% { opacity: 1; }
            25% { opacity: 1; transform: scale(1.05); }
            35% { opacity: 0; transform: scale(1.08); }
            100% { opacity: 0; transform: scale(1.0); }
        }
        
        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(136, 18, 59, 0.55) 0%, rgba(0, 59, 149, 0.65) 100%);
            z-index: -1;
        }
    """
    
    # Replace the old video css blocks
    content = re.sub(r'\.video-background\s*{[^}]+}', '', content)
    content = re.sub(r'\.video-background iframe\s*{[^}]+}', '', content)
    content = re.sub(r'\.overlay\s*{[^}]+}', '', content)
    
    if "custom-montage" not in content:
        # Just in case we didn't add it yet
        pass
        
    if ".custom-montage {" not in content:
        content = content.replace('</style>', montage_css + '\n</style>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
