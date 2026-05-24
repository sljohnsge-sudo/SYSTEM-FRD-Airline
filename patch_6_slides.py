import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to replace the old montage with the new 6-slide montage
    old_montage_html = """    <div class="custom-montage">
        <div class="slide slide-1"></div>
        <div class="slide slide-2"></div>
        <div class="slide slide-3"></div>
    </div>"""
    
    new_montage_html = """    <div class="custom-montage">
        <div class="slide slide-1"></div>
        <div class="slide slide-2"></div>
        <div class="slide slide-3"></div>
        <div class="slide slide-4"></div>
        <div class="slide slide-5"></div>
        <div class="slide slide-6"></div>
    </div>"""

    # We also need to update the CSS. We'll replace the entire CSS block.
    # We can do this by regex replacing everything between /* Custom Background Montage (Unbranded) */ and .overlay {
    new_css = """        /* Custom Background Montage (Unbranded) */
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
            animation: kenburns-crossfade 48s infinite;
        }
        
        /* 1. Epic Flight in Clouds */
        .slide-1 {
            background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 0s;
        }
        
        /* 2. Passenger Travelling / Airport */
        .slide-2 {
            background-image: url('https://images.unsplash.com/photo-1494515843206-f3117d3a5d49?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 8s;
        }
        
        /* 3. Beautiful Tropical Destination */
        .slide-3 {
            background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 16s;
        }
        
        /* 4. Airplane Takeoff / Flying */
        .slide-4 {
            background-image: url('https://images.unsplash.com/photo-1518066000714-58c45f1a2c0a?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 24s;
        }
        
        /* 5. Beautiful City Destination */
        .slide-5 {
            background-image: url('https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 32s;
        }
        
        /* 6. Professional Staff Service */
        .slide-6 {
            background-image: url('https://images.unsplash.com/photo-1556745753-b2904692b3cd?auto=format&fit=crop&w=2000&q=80');
            animation-delay: 40s;
        }
        
        @keyframes kenburns-crossfade {
            0% { opacity: 0; transform: scale(1.0); }
            4.16% { opacity: 1; }
            16.66% { opacity: 1; transform: scale(1.06); }
            20.83% { opacity: 0; transform: scale(1.08); }
            100% { opacity: 0; transform: scale(1.0); }
        }
"""
    
    content = content.replace(old_montage_html, new_montage_html)
    content = re.sub(r'/\*\s*Custom Background Montage \(Unbranded\).*?@keyframes kenburns-crossfade.*?\}[^\S\n]*\n', new_css, content, flags=re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
