import os

os.makedirs('assets/images', exist_ok=True)
os.makedirs('assets/diagrams', exist_ok=True)

# 1. assets/images/skyforge-icon.svg
icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="navyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#061A40"/>
      <stop offset="50%" stop-color="#0353A4"/>
      <stop offset="100%" stop-color="#002244"/>
    </linearGradient>
    <linearGradient id="electricGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4"/>
      <stop offset="50%" stop-color="#00A6FB"/>
      <stop offset="100%" stop-color="#4CC9F0"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Background Circle -->
  <circle cx="256" cy="256" r="240" fill="url(#navyGrad)" stroke="url(#electricGrad)" stroke-width="6"/>
  <circle cx="256" cy="256" r="215" fill="none" stroke="#4CC9F0" stroke-width="1.5" stroke-dasharray="6 6" opacity="0.6"/>

  <!-- Targeting Reticle Outer Ring -->
  <circle cx="256" cy="256" r="170" fill="none" stroke="#00F5D4" stroke-width="2" opacity="0.4"/>
  <path d="M 256 60 L 256 90 M 256 422 L 256 452 M 60 256 L 90 256 M 422 256 L 452 256" stroke="#00F5D4" stroke-width="3" stroke-linecap="round"/>

  <!-- Drone Diagonal Rotor Arms -->
  <g stroke="url(#electricGrad)" stroke-width="14" stroke-linecap="round">
    <line x1="130" y1="130" x2="382" y2="382"/>
    <line x1="382" y1="130" x2="130" y2="382"/>
  </g>

  <!-- Drone Rotor Pods -->
  <g fill="#061A40" stroke="#00F5D4" stroke-width="4" filter="url(#glow)">
    <circle cx="130" cy="130" r="34"/>
    <circle cx="382" cy="130" r="34"/>
    <circle cx="130" cy="382" r="34"/>
    <circle cx="382" cy="382" r="34"/>
  </g>
  
  <!-- Rotor Blades -->
  <g stroke="#4CC9F0" stroke-width="3" opacity="0.9">
    <ellipse cx="130" cy="130" rx="24" ry="7" transform="rotate(30 130 130)" fill="none"/>
    <ellipse cx="382" cy="130" rx="24" ry="7" transform="rotate(-30 382 130)" fill="none"/>
    <ellipse cx="130" cy="382" rx="24" ry="7" transform="rotate(-30 130 382)" fill="none"/>
    <ellipse cx="382" cy="382" rx="24" ry="7" transform="rotate(30 382 382)" fill="none"/>
  </g>

  <!-- Central Fuselage / Aerospace Shield -->
  <polygon points="256,160 330,220 330,300 256,360 182,300 182,220" fill="#061A40" stroke="url(#electricGrad)" stroke-width="5"/>

  <!-- Optical Camera Aperture / AI Eye -->
  <circle cx="256" cy="256" r="42" fill="#0353A4" stroke="#00F5D4" stroke-width="4"/>
  <circle cx="256" cy="256" r="26" fill="#00A6FB"/>
  <circle cx="256" cy="256" r="12" fill="#00F5D4" filter="url(#glow)"/>
  <circle cx="262" cy="250" r="5" fill="#F8FBFF"/>

  <!-- Aerospace HUD Wing Flairs -->
  <path d="M 182 256 L 140 256 L 110 275" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
  <path d="M 330 256 L 372 256 L 402 275" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round" opacity="0.7"/>

  <!-- HUD Reticle Corner Brackets -->
  <path d="M 220 200 L 200 200 L 200 220" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round"/>
  <path d="M 292 200 L 312 200 L 312 220" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round"/>
  <path d="M 200 292 L 200 312 L 220 312" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round"/>
  <path d="M 312 292 L 312 312 L 292 312" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round"/>
</svg>"""

with open('assets/images/skyforge-icon.svg', 'w', encoding='utf-8') as f:
    f.write(icon_svg)
print('Generated assets/images/skyforge-icon.svg')

# 2. assets/images/skyforge-logo.svg
logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 220" width="100%" height="100%">
  <defs>
    <linearGradient id="logoNavyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#061A40"/>
      <stop offset="100%" stop-color="#0353A4"/>
    </linearGradient>
    <linearGradient id="logoTextGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F8FBFF"/>
      <stop offset="40%" stop-color="#4CC9F0"/>
      <stop offset="80%" stop-color="#00F5D4"/>
      <stop offset="100%" stop-color="#00A6FB"/>
    </linearGradient>
    <linearGradient id="electricGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4"/>
      <stop offset="100%" stop-color="#00A6FB"/>
    </linearGradient>
    <filter id="glow2" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Background Card -->
  <rect x="5" y="5" width="950" height="210" rx="20" fill="#061A40" stroke="#0353A4" stroke-width="2"/>
  <rect x="15" y="15" width="930" height="190" rx="16" fill="none" stroke="#00A6FB" stroke-width="1" stroke-dasharray="10 5" opacity="0.3"/>

  <!-- Icon Section (Left) -->
  <g transform="translate(30, 15) scale(0.37)">
    <circle cx="256" cy="256" r="235" fill="url(#logoNavyGrad)" stroke="url(#electricGrad2)" stroke-width="7"/>
    <circle cx="256" cy="256" r="210" fill="none" stroke="#4CC9F0" stroke-width="2" stroke-dasharray="8 8" opacity="0.6"/>
    
    <path d="M 256 60 L 256 95 M 256 417 L 256 452 M 60 256 L 95 256 M 417 256 L 452 256" stroke="#00F5D4" stroke-width="4" stroke-linecap="round"/>

    <g stroke="url(#electricGrad2)" stroke-width="16" stroke-linecap="round">
      <line x1="130" y1="130" x2="382" y2="382"/>
      <line x1="382" y1="130" x2="130" y2="382"/>
    </g>

    <g fill="#061A40" stroke="#00F5D4" stroke-width="5" filter="url(#glow2)">
      <circle cx="130" cy="130" r="34"/>
      <circle cx="382" cy="130" r="34"/>
      <circle cx="130" cy="382" r="34"/>
      <circle cx="382" cy="382" r="34"/>
    </g>

    <polygon points="256,160 330,220 330,300 256,360 182,300 182,220" fill="#061A40" stroke="url(#electricGrad2)" stroke-width="6"/>
    
    <circle cx="256" cy="256" r="40" fill="#0353A4" stroke="#00F5D4" stroke-width="5"/>
    <circle cx="256" cy="256" r="24" fill="#00A6FB"/>
    <circle cx="256" cy="256" r="12" fill="#00F5D4" filter="url(#glow2)"/>
    <circle cx="261" cy="251" r="5" fill="#F8FBFF"/>
  </g>

  <!-- Divider Line -->
  <line x1="240" y1="30" x2="240" y2="190" stroke="#00A6FB" stroke-width="2" stroke-dasharray="6 4" opacity="0.5"/>

  <!-- Typography (Right) -->
  <text x="270" y="82" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="52" font-weight="900" letter-spacing="5" fill="url(#logoTextGrad)">SKYFORGE</text>
  
  <text x="275" y="118" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16" font-weight="700" letter-spacing="2.5" fill="#4CC9F0">AI-ASSISTED ESP32 TINY DRONE</text>
  
  <text x="275" y="148" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="500" letter-spacing="3" fill="#00F5D4">BEYOND FLIGHT. INTO INTELLIGENT VISION.</text>
  
  <!-- Badges -->
  <rect x="275" y="165" width="140" height="24" rx="5" fill="#0353A4" opacity="0.8"/>
  <text x="285" y="181" font-family="'Segoe UI', sans-serif" font-size="11" font-weight="600" fill="#F8FBFF" letter-spacing="1">GLA UNIVERSITY</text>

  <rect x="425" y="165" width="105" height="24" rx="5" fill="#0353A4" opacity="0.8"/>
  <text x="435" y="181" font-family="'Segoe UI', sans-serif" font-size="11" font-weight="600" fill="#00F5D4" letter-spacing="1">TEAM ID: 87</text>

  <rect x="540" y="165" width="130" height="24" rx="5" fill="#0353A4" opacity="0.8"/>
  <text x="550" y="181" font-family="'Segoe UI', sans-serif" font-size="11" font-weight="600" fill="#4CC9F0" letter-spacing="1">CSE // AIML LAB</text>

  <!-- Technical Reticle Marker in Corner -->
  <path d="M 915 25 L 935 25 L 935 45" fill="none" stroke="#00F5D4" stroke-width="2"/>
  <path d="M 935 175 L 935 195 L 915 195" fill="none" stroke="#00F5D4" stroke-width="2"/>
</svg>"""

with open('assets/images/skyforge-logo.svg', 'w', encoding='utf-8') as f:
    f.write(logo_svg)
print('Generated assets/images/skyforge-logo.svg')

# 3. assets/images/architecture-overview.svg
arch_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#061A40"/>
      <stop offset="100%" stop-color="#0A2558"/>
    </linearGradient>
    <linearGradient id="droneBoxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0353A4" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#061A40" stop-opacity="0.85"/>
    </linearGradient>
    <linearGradient id="gsBoxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00A6FB" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#061A40" stop-opacity="0.85"/>
    </linearGradient>
    <filter id="glowArch" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1280" height="720" fill="url(#bgGrad)"/>
  
  <!-- Grid Lines -->
  <g stroke="#0353A4" stroke-width="0.8" opacity="0.35">
    <line x1="0" y1="80" x2="1280" y2="80"/>
    <line x1="0" y1="160" x2="1280" y2="160"/>
    <line x1="0" y1="240" x2="1280" y2="240"/>
    <line x1="0" y1="320" x2="1280" y2="320"/>
    <line x1="0" y1="400" x2="1280" y2="400"/>
    <line x1="0" y1="480" x2="1280" y2="480"/>
    <line x1="0" y1="560" x2="1280" y2="560"/>
    <line x1="0" y1="640" x2="1280" y2="640"/>
    <line x1="160" y1="0" x2="160" y2="720"/>
    <line x1="320" y1="0" x2="320" y2="720"/>
    <line x1="480" y1="0" x2="480" y2="720"/>
    <line x1="640" y1="0" x2="640" y2="720"/>
    <line x1="800" y1="0" x2="800" y2="720"/>
    <line x1="960" y1="0" x2="960" y2="720"/>
    <line x1="1120" y1="0" x2="1120" y2="720"/>
  </g>

  <!-- Title Header -->
  <text x="50" y="48" font-family="'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="800" letter-spacing="2" fill="#F8FBFF">SKYFORGE SYSTEM ARCHITECTURE</text>
  <text x="50" y="70" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="500" letter-spacing="1.5" fill="#00F5D4">ESP32 ONBOARD FLIGHT PLATFORM ⟷ WI-FI TELEMETRY &amp; VIDEO ⟷ GROUND STATION AIML PIPELINE</text>
  
  <!-- Status Badge -->
  <rect x="1080" y="32" width="150" height="30" rx="6" fill="#0353A4" stroke="#00F5D4" stroke-width="1.5"/>
  <text x="1098" y="52" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#00F5D4">RESEARCH v1.0</text>

  <!-- ================= SECTION 1: DRONE HARDWARE (LEFT) ================= -->
  <rect x="40" y="95" width="480" height="585" rx="14" fill="url(#droneBoxGrad)" stroke="#0353A4" stroke-width="2"/>
  <rect x="50" y="105" width="460" height="32" rx="6" fill="#0353A4" opacity="0.6"/>
  <text x="65" y="126" font-family="'Segoe UI', sans-serif" font-size="15" font-weight="700" fill="#00F5D4" letter-spacing="1">✈ ONBOARD DRONE HARDWARE SUBSYSTEM</text>

  <!-- Block 1: Camera Module -->
  <rect x="65" y="155" width="430" height="70" rx="8" fill="#061A40" stroke="#00A6FB" stroke-width="1.5"/>
  <text x="85" y="180" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="#F8FBFF">Compact Camera Module (OV2640 / Compatible)</text>
  <text x="85" y="202" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">DVP Interface • Terrain Capture • Low-Weight Mounting</text>

  <!-- Flow Arrow -->
  <path d="M 280 225 L 280 250" stroke="#00F5D4" stroke-width="2" marker-end="url(#arrow)"/>
  <polygon points="276,245 280,253 284,245" fill="#00F5D4"/>

  <!-- Block 2: ESP32 Flight Controller & Comm -->
  <rect x="65" y="255" width="430" height="150" rx="8" fill="#061A40" stroke="#00F5D4" stroke-width="2"/>
  <text x="85" y="280" font-family="'Segoe UI', sans-serif" font-size="15" font-weight="800" fill="#00F5D4">ESP32 / ESP32-S3 Dual-Core SoC</text>
  <line x1="85" y1="290" x2="475" y2="290" stroke="#0353A4" stroke-width="1"/>
  
  <rect x="85" y="300" width="185" height="50" rx="5" fill="#0353A4" opacity="0.5"/>
  <text x="95" y="320" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#F8FBFF">Core 0: Flight Control</text>
  <text x="95" y="338" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">IMU fusion, PID loop (250Hz)</text>

  <rect x="285" y="300" width="190" height="50" rx="5" fill="#0353A4" opacity="0.5"/>
  <text x="295" y="320" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#F8FBFF">Core 1: Vision / Comms</text>
  <text x="295" y="338" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">Frame streaming, UDP server</text>

  <text x="85" y="380" font-family="'Segoe UI', sans-serif" font-size="12" fill="#E2E8F0">Independent Flight Loop: Deterministic stabilization priority</text>
  <text x="85" y="396" font-family="'Segoe UI', sans-serif" font-size="11" fill="#64748B">Failsafe: Auto-disarm on Wi-Fi loss / tilt threshold exceeded</text>

  <!-- Flight Peripherals Section -->
  <g transform="translate(65, 420)">
    <!-- IMU -->
    <rect x="0" y="0" width="205" height="60" rx="6" fill="#061A40" stroke="#4CC9F0" stroke-width="1.2"/>
    <text x="12" y="24" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">MPU6050 6-DoF IMU</text>
    <text x="12" y="44" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">I2C Fast Mode (400kHz)</text>

    <!-- Power -->
    <rect x="225" y="0" width="205" height="60" rx="6" fill="#061A40" stroke="#4CC9F0" stroke-width="1.2"/>
    <text x="237" y="24" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">1S Li-Po (3.7V 380-500mAh)</text>
    <text x="237" y="44" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">LDO 3.3V + Voltage Divider</text>

    <!-- Motor Drivers -->
    <rect x="0" y="70" width="430" height="60" rx="6" fill="#061A40" stroke="#00A6FB" stroke-width="1.2"/>
    <text x="12" y="94" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">4x MOSFET Power Stages (SI2302 / AO3400)</text>
    <text x="12" y="114" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">PWM Driving 4x Coreless Brushed Motors (CW / CCW Propellers)</text>
  </g>

  <!-- Future Option Box -->
  <rect x="65" y="565" width="430" height="95" rx="6" fill="#061A40" stroke="#64748B" stroke-dasharray="6 4" stroke-width="1.2"/>
  <text x="80" y="588" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#F8FBFF">Optional Future Expansion (Post-v1.0):</text>
  <text x="80" y="608" font-family="'Segoe UI', sans-serif" font-size="11" fill="#64748B">• Raspberry Pi Zero 2 W companion computer via UART for edge compute</text>
  <text x="80" y="626" font-family="'Segoe UI', sans-serif" font-size="11" fill="#64748B">• Downward optical-flow sensor for autonomous hovering</text>
  <text x="80" y="644" font-family="'Segoe UI', sans-serif" font-size="11" fill="#64748B">• Flight controller remains ESP32 for deterministic hard real-time safety</text>

  <!-- ================= LINK (MIDDLE) ================= -->
  <g transform="translate(535, 230)">
    <!-- Wireless Wave Link -->
    <rect x="0" y="0" width="170" height="150" rx="10" fill="#061A40" stroke="#00F5D4" stroke-width="1.5"/>
    <text x="20" y="28" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#00F5D4">WI-FI LINK</text>
    <text x="20" y="48" font-family="'Segoe UI', sans-serif" font-size="11" fill="#F8FBFF">802.11 b/g/n (2.4GHz)</text>
    
    <line x1="15" y1="60" x2="155" y2="60" stroke="#0353A4" stroke-width="1"/>
    
    <text x="15" y="80" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">→ JPEG / MJPEG Stream</text>
    <text x="15" y="98" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">→ Low-latency UDP/TCP</text>
    <text x="15" y="116" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">← Control Telemetry</text>
    <text x="15" y="134" font-family="'Segoe UI', sans-serif" font-size="10" fill="#00F5D4">Target: ≥5 FPS @ QVGA</text>

    <!-- Signal waves -->
    <path d="M -15 75 Q 0 65 0 75 Q 0 85 15 75" fill="none" stroke="#00F5D4" stroke-width="2"/>
    <path d="M 155 75 Q 170 65 170 75 Q 170 85 185 75" fill="none" stroke="#00F5D4" stroke-width="2"/>
  </g>

  <!-- Second ESP32 Remote Transmitter (Bottom Middle) -->
  <g transform="translate(535, 430)">
    <rect x="0" y="0" width="170" height="120" rx="10" fill="#061A40" stroke="#00A6FB" stroke-width="1.5"/>
    <text x="15" y="26" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#00A6FB">ESP32 REMOTE TX</text>
    <text x="15" y="44" font-family="'Segoe UI', sans-serif" font-size="10" fill="#64748B">Dedicated Transmitter</text>
    <line x1="15" y1="52" x2="155" y2="52" stroke="#0353A4" stroke-width="1"/>
    <text x="15" y="70" font-family="'Segoe UI', sans-serif" font-size="11" fill="#F8FBFF">• 2x Dual-Axis Joysticks</text>
    <text x="15" y="88" font-family="'Segoe UI', sans-serif" font-size="11" fill="#F8FBFF">• ESP-NOW Low Latency</text>
    <text x="15" y="106" font-family="'Segoe UI', sans-serif" font-size="11" fill="#00F5D4">• Arm / Disarm Failsafe</text>
  </g>

  <!-- ================= SECTION 2: GROUND STATION (RIGHT) ================= -->
  <rect x="720" y="95" width="520" height="585" rx="14" fill="url(#gsBoxGrad)" stroke="#00A6FB" stroke-width="2"/>
  <rect x="730" y="105" width="500" height="32" rx="6" fill="#0353A4" opacity="0.6"/>
  <text x="745" y="126" font-family="'Segoe UI', sans-serif" font-size="15" font-weight="700" fill="#00F5D4" letter-spacing="1">💻 GROUND-STATION LAPTOP AI/CV SUBSYSTEM</text>

  <!-- Module 1: Python Stream Receiver -->
  <rect x="745" y="155" width="470" height="70" rx="8" fill="#061A40" stroke="#4CC9F0" stroke-width="1.2"/>
  <text x="765" y="180" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="#F8FBFF">1. Stream Ingestion &amp; Frame Buffer</text>
  <text x="765" y="202" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">Python Socket Receiver • Decodes JPEG • Frame Rate &amp; Drop Monitor</text>

  <!-- Module 2: OpenCV Preprocessing -->
  <rect x="745" y="240" width="470" height="90" rx="8" fill="#061A40" stroke="#00A6FB" stroke-width="1.5"/>
  <text x="765" y="265" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="#00F5D4">2. OpenCV Preprocessing &amp; Feature Enhancement</text>
  <text x="765" y="287" font-family="'Segoe UI', sans-serif" font-size="12" fill="#F8FBFF">• Bilateral / Gaussian Denoising to isolate fine camouflage textures</text>
  <text x="765" y="307" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">• CLAHE (Contrast Limited Adaptive Histogram Equalization)</text>

  <!-- Module 3: Dual-Mode AIML Engine -->
  <rect x="745" y="345" width="470" height="150" rx="8" fill="#061A40" stroke="#00F5D4" stroke-width="2"/>
  <text x="765" y="370" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="800" fill="#00F5D4">3. Dual-Mode AIML Inference Engine</text>
  
  <!-- Mode A -->
  <rect x="765" y="382" width="215" height="65" rx="5" fill="#0353A4" opacity="0.6"/>
  <text x="775" y="402" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#00F5D4">PLAN A (Primary)</text>
  <text x="775" y="420" font-family="'Segoe UI', sans-serif" font-size="11" fill="#F8FBFF">Camouflaged Object /</text>
  <text x="775" y="436" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">Anomaly Detection (COD10K/CAMO)</text>

  <!-- Mode B -->
  <rect x="990" y="382" width="210" height="65" rx="5" fill="#0353A4" opacity="0.6"/>
  <text x="1000" y="402" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#FFB703">PLAN B (Fallback)</text>
  <text x="1000" y="420" font-family="'Segoe UI', sans-serif" font-size="11" fill="#F8FBFF">Pretrained Person Detection</text>
  <text x="1000" y="436" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">&amp; Bounding-Box Tracking</text>

  <text x="765" y="468" font-family="'Segoe UI', sans-serif" font-size="11" fill="#E2E8F0">Week 5 Decision Checkpoint determines operational model route</text>
  <text x="765" y="484" font-family="'Segoe UI', sans-serif" font-size="11" fill="#64748B">Target ground-station frame latency: ≤500 ms</text>

  <!-- Module 4: Output & Evaluation -->
  <rect x="745" y="510" width="470" height="150" rx="8" fill="#061A40" stroke="#4CC9F0" stroke-width="1.2"/>
  <text x="765" y="534" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="#F8FBFF">4. Visualization, Logging &amp; Evaluation</text>
  <text x="765" y="556" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">• Annotated Image Display: Bounding box / segmentation contours</text>
  <text x="765" y="576" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">• Confidence Scoring &amp; Optional Heatmap Overlay</text>
  <text x="765" y="596" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">• CSV / JSON Test Run Logging (Latency, FPS, Dropped Frames)</text>
  <text x="765" y="616" font-family="'Segoe UI', sans-serif" font-size="12" fill="#4CC9F0">• Target Metrics: IoU ≥ 0.5 (Plan A) | Det. Rate ≥ 80% (Plan B)</text>
  <text x="765" y="638" font-family="'Segoe UI', sans-serif" font-size="11" fill="#00F5D4">Storage: ground_station/results/ &amp; ground_station/logs/</text>
</svg>"""

with open('assets/images/architecture-overview.svg', 'w', encoding='utf-8') as f:
    f.write(arch_svg)
print('Generated assets/images/architecture-overview.svg')

# 4. assets/images/pipeline-overview.svg
pipe_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 400" width="100%" height="100%">
  <defs>
    <linearGradient id="pipeBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#061A40"/>
      <stop offset="100%" stop-color="#07225B"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0353A4" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#061A40" stop-opacity="0.9"/>
    </linearGradient>
  </defs>

  <rect width="1280" height="400" fill="url(#pipeBg)"/>

  <!-- Title -->
  <text x="40" y="42" font-family="'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="800" fill="#F8FBFF" letter-spacing="2">SKYFORGE END-TO-END COMPUTER VISION &amp; AI PIPELINE</text>
  <text x="40" y="64" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="500" fill="#00F5D4" letter-spacing="1">From Drone Optical Acquisition to Ground-Station Intelligent Telemetry</text>

  <!-- 5 Sequential Pipeline Stages -->
  <!-- Stage 1 -->
  <g transform="translate(40, 90)">
    <rect width="215" height="260" rx="10" fill="url(#cardGrad)" stroke="#0353A4" stroke-width="1.8"/>
    <circle cx="28" cy="30" r="14" fill="#0353A4" stroke="#00F5D4" stroke-width="2"/>
    <text x="24" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="800" fill="#00F5D4">1</text>
    <text x="52" y="35" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">CAMERA CAPTURE</text>
    <line x1="15" y1="52" x2="200" y2="52" stroke="#00A6FB" stroke-width="1" opacity="0.4"/>
    <text x="15" y="75" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Sensor: OV2640 / CMOS</text>
    <text x="15" y="95" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Resolution: QVGA / VGA</text>
    <text x="15" y="115" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Target: ≥5 FPS stream</text>
    <text x="15" y="135" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Lightweight DMA capture</text>
    <rect x="15" y="195" width="185" height="45" rx="5" fill="#061A40" stroke="#00A6FB" stroke-width="1"/>
    <text x="25" y="215" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="600" fill="#00F5D4">OUTPUT: RAW FRAMES</text>
    <text x="25" y="230" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Encoded JPEG payload</text>
  </g>

  <!-- Arrow 1->2 -->
  <path d="M 265 220 L 285 220" stroke="#00F5D4" stroke-width="2"/>
  <polygon points="283,216 291,220 283,224" fill="#00F5D4"/>

  <!-- Stage 2 -->
  <g transform="translate(295, 90)">
    <rect width="215" height="260" rx="10" fill="url(#cardGrad)" stroke="#00A6FB" stroke-width="1.8"/>
    <circle cx="28" cy="30" r="14" fill="#0353A4" stroke="#00F5D4" stroke-width="2"/>
    <text x="24" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="800" fill="#00F5D4">2</text>
    <text x="52" y="35" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">WI-FI STREAMING</text>
    <line x1="15" y1="52" x2="200" y2="52" stroke="#00A6FB" stroke-width="1" opacity="0.4"/>
    <text x="15" y="75" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Protocol: UDP / HTTP</text>
    <text x="15" y="95" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Non-blocking socket</text>
    <text x="15" y="115" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Frame buffer ring queue</text>
    <text x="15" y="135" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Drop rate monitoring</text>
    <rect x="15" y="195" width="185" height="45" rx="5" fill="#061A40" stroke="#00A6FB" stroke-width="1"/>
    <text x="25" y="215" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="600" fill="#00F5D4">OUTPUT: INGESTED STREAM</text>
    <text x="25" y="230" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Decoded NumPy BGR array</text>
  </g>

  <!-- Arrow 2->3 -->
  <path d="M 520 220 L 540 220" stroke="#00F5D4" stroke-width="2"/>
  <polygon points="538,216 546,220 538,224" fill="#00F5D4"/>

  <!-- Stage 3 -->
  <g transform="translate(550, 90)">
    <rect width="215" height="260" rx="10" fill="url(#cardGrad)" stroke="#4CC9F0" stroke-width="1.8"/>
    <circle cx="28" cy="30" r="14" fill="#0353A4" stroke="#00F5D4" stroke-width="2"/>
    <text x="24" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="800" fill="#00F5D4">3</text>
    <text x="52" y="35" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#F8FBFF">OPENCV PREPROCESS</text>
    <line x1="15" y1="52" x2="200" y2="52" stroke="#00A6FB" stroke-width="1" opacity="0.4"/>
    <text x="15" y="75" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Bilateral noise filtering</text>
    <text x="15" y="95" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• CLAHE contrast boost</text>
    <text x="15" y="115" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Multi-scale edge gradients</text>
    <text x="15" y="135" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Normalized 224x224</text>
    <rect x="15" y="195" width="185" height="45" rx="5" fill="#061A40" stroke="#00A6FB" stroke-width="1"/>
    <text x="25" y="215" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="600" fill="#00F5D4">OUTPUT: ENHANCED TENSOR</text>
    <text x="25" y="230" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Texture-highlighted input</text>
  </g>

  <!-- Arrow 3->4 -->
  <path d="M 775 220 L 795 220" stroke="#00F5D4" stroke-width="2"/>
  <polygon points="793,216 801,220 793,224" fill="#00F5D4"/>

  <!-- Stage 4 -->
  <g transform="translate(805, 90)">
    <rect width="215" height="260" rx="10" fill="url(#cardGrad)" stroke="#00F5D4" stroke-width="2"/>
    <circle cx="28" cy="30" r="14" fill="#0353A4" stroke="#00F5D4" stroke-width="2"/>
    <text x="24" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="800" fill="#00F5D4">4</text>
    <text x="52" y="35" font-family="'Segoe UI', sans-serif" font-size="13" font-weight="700" fill="#00F5D4">AIML INFERENCE</text>
    <line x1="15" y1="52" x2="200" y2="52" stroke="#00A6FB" stroke-width="1" opacity="0.4"/>
    <text x="15" y="75" font-family="'Segoe UI', sans-serif" font-size="11" fill="#00F5D4">Plan A: Camouflage Net</text>
    <text x="15" y="92" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">COD10K / CAMO segmentation</text>
    <text x="15" y="112" font-family="'Segoe UI', sans-serif" font-size="11" fill="#FFB703">Plan B: Person Detector</text>
    <text x="15" y="129" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Pretrained lightweight model</text>
    <text x="15" y="152" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Ground station latency &lt;500ms</text>
    <rect x="15" y="195" width="185" height="45" rx="5" fill="#061A40" stroke="#00F5D4" stroke-width="1"/>
    <text x="25" y="215" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="600" fill="#00F5D4">OUTPUT: PROBABILITY MAP</text>
    <text x="25" y="230" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Anomaly mask &amp; scores</text>
  </g>

  <!-- Arrow 4->5 -->
  <path d="M 1030 220 L 1050 220" stroke="#00F5D4" stroke-width="2"/>
  <polygon points="1048,216 1056,220 1048,224" fill="#00F5D4"/>

  <!-- Stage 5 -->
  <g transform="translate(1060, 90)">
    <rect width="180" height="260" rx="10" fill="url(#cardGrad)" stroke="#0353A4" stroke-width="1.8"/>
    <circle cx="28" cy="30" r="14" fill="#0353A4" stroke="#00F5D4" stroke-width="2"/>
    <text x="24" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="800" fill="#00F5D4">5</text>
    <text x="52" y="35" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#F8FBFF">ANNOTATION</text>
    <line x1="15" y1="52" x2="165" y2="52" stroke="#00A6FB" stroke-width="1" opacity="0.4"/>
    <text x="12" y="75" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Bounding Box</text>
    <text x="12" y="95" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Segmentation Mask</text>
    <text x="12" y="115" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Confidence Score</text>
    <text x="12" y="135" font-family="'Segoe UI', sans-serif" font-size="11" fill="#4CC9F0">• Heatmap Overlay</text>
    <rect x="12" y="195" width="156" height="45" rx="5" fill="#061A40" stroke="#00A6FB" stroke-width="1"/>
    <text x="20" y="215" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="600" fill="#00F5D4">RESULTS &amp; LOGS</text>
    <text x="20" y="230" font-family="'Segoe UI', sans-serif" font-size="10" fill="#E2E8F0">Saved to results/ folder</text>
  </g>
</svg>"""

with open('assets/images/pipeline-overview.svg', 'w', encoding='utf-8') as f:
    f.write(pipe_svg)
print('Generated assets/images/pipeline-overview.svg')
