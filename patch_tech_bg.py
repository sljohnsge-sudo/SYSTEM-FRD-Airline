import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to remove the custom montage HTML
    content = re.sub(r'<div class="custom-montage">.*?</div>\n        <div class="slide slide-2">.*?</div>', '', content, flags=re.DOTALL)
    # The regex above might be too strict. Let's just regex all `<div class="custom-montage">...</div>`
    # In welcome.html there are duplicated closing divs due to previous patching issues:
    # <div class="custom-montage"> ... </div>
    #    <div class="slide slide-2"></div>
    #    <div class="slide slide-3"></div>
    #    ... </div>
    # Let's clean up all of that and just inject the video background.
    
    # We'll locate <div class="overlay"></div> and replace everything before it up to the body tag
    match = re.search(r'(<body[^>]*>).*?(<div class="overlay"></div>)', content, flags=re.DOTALL)
    if match:
        video_html = """
    <!-- Global Data Network Background Video -->
    <div class="video-background">
        <iframe src="https://www.youtube.com/embed/J_ayOglYUpU?autoplay=1&mute=1&loop=1&controls=0&showinfo=0&playlist=J_ayOglYUpU&rel=0&modestbranding=1&playsinline=1" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>
    </div>
    """
        content = content[:match.start(0)] + match.group(1) + video_html + "\n    " + match.group(2) + content[match.end(0):]
    
    # Now for CSS: we remove .custom-montage and .slide css
    content = re.sub(r'/\*\s*Custom Background Montage \(Unbranded\).*?@keyframes kenburns-crossfade.*?\}[^\S\n]*\n', '', content, flags=re.DOTALL)
    
    # Add video background CSS back
    video_css = """
        /* Video Background */
        body {
            background-color: #000;
        }
        
        .video-background {
            position: fixed;
            top: 0; right: 0; bottom: 0; left: 0;
            z-index: -2;
            overflow: hidden;
            background: #000;
        }
        
        .video-background iframe {
            position: absolute;
            top: 50%; left: 50%;
            width: 100vw; height: 56.25vw; /* 16:9 ratio */
            min-height: 100vh; min-width: 177.77vh; /* 16:9 ratio */
            transform: translate(-50%, -50%);
            pointer-events: none;
            filter: brightness(0.65); /* Dimmed for tech look */
        }
    """
    
    if ".video-background {" not in content:
        content = content.replace("</style>", video_css + "\n</style>")

    # The CSS might have extra junk from previous patches.
    # Let's clean up any lingering 'body { background-color: #000; }' duplicates
    # and extra slides
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
