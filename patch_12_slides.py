import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Expand the HTML to 12 slides
    new_montage_html = """    <div class="custom-montage">
        <div class="slide slide-1"></div>
        <div class="slide slide-2"></div>
        <div class="slide slide-3"></div>
        <div class="slide slide-4"></div>
        <div class="slide slide-5"></div>
        <div class="slide slide-6"></div>
        <div class="slide slide-7"></div>
        <div class="slide slide-8"></div>
        <div class="slide slide-9"></div>
        <div class="slide slide-10"></div>
        <div class="slide slide-11"></div>
        <div class="slide slide-12"></div>
    </div>"""

    content = re.sub(r'<div class="custom-montage">.*?</div>', new_montage_html, content, flags=re.DOTALL)

    # Expand the CSS to 12 slides
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
            animation: kenburns-crossfade 36s infinite;
        }
        
        /* 1. Epic Flight in Clouds */
        .slide-1 { background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=80'); animation-delay: 0s; }
        
        /* 2. Passenger Travelling / Airport */
        .slide-2 { background-image: url('https://images.unsplash.com/photo-1494515843206-f3117d3a5d49?auto=format&fit=crop&w=2000&q=80'); animation-delay: 3s; }
        
        /* 3. Beautiful Tropical Destination */
        .slide-3 { background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80'); animation-delay: 6s; }
        
        /* 4. Airplane Takeoff / Flying */
        .slide-4 { background-image: url('https://images.unsplash.com/photo-1518066000714-58c45f1a2c0a?auto=format&fit=crop&w=2000&q=80'); animation-delay: 9s; }
        
        /* 5. Beautiful City Destination (Paris) */
        .slide-5 { background-image: url('https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=2000&q=80'); animation-delay: 12s; }
        
        /* 6. Professional Staff Service */
        .slide-6 { background-image: url('https://images.unsplash.com/photo-1556745753-b2904692b3cd?auto=format&fit=crop&w=2000&q=80'); animation-delay: 15s; }
        
        /* 7. People travelling in Airport Terminal */
        .slide-7 { background-image: url('https://images.unsplash.com/photo-1473625247510-8ceb1760943f?auto=format&fit=crop&w=2000&q=80'); animation-delay: 18s; }
        
        /* 8. Majestic Unbranded Airplane flying */
        .slide-8 { background-image: url('https://images.unsplash.com/photo-1551381373-c827361ab8b7?auto=format&fit=crop&w=2000&q=80'); animation-delay: 21s; }
        
        /* 9. Luxury Destination (Dubai) */
        .slide-9 { background-image: url('https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=2000&q=80'); animation-delay: 24s; }
        
        /* 10. Passengers with Luggage */
        .slide-10 { background-image: url('https://images.unsplash.com/photo-1530521954074-e64f6810b32d?auto=format&fit=crop&w=2000&q=80'); animation-delay: 27s; }
        
        /* 11. Airplane flying at sunset */
        .slide-11 { background-image: url('https://images.unsplash.com/photo-1506012787146-f92b2d7d6d96?auto=format&fit=crop&w=2000&q=80'); animation-delay: 30s; }
        
        /* 12. Crystal clear tropical water destination */
        .slide-12 { background-image: url('https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?auto=format&fit=crop&w=2000&q=80'); animation-delay: 33s; }
        
        @keyframes kenburns-crossfade {
            0% { opacity: 0; transform: scale(1.0); }
            2.77% { opacity: 1; }
            8.33% { opacity: 1; transform: scale(1.03); }
            11.11% { opacity: 0; transform: scale(1.05); }
            100% { opacity: 0; transform: scale(1.0); }
        }
"""
    
    content = re.sub(r'/\*\s*Custom Background Montage \(Unbranded\).*?@keyframes kenburns-crossfade.*?\}[^\S\n]*\n', new_css, content, flags=re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
