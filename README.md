# FreeCADAgent

## ⚡ Installation & Setup

### 0. Install FreeCAD
FreeCADAgent requires **FreeCAD 1.0.0+** (we did not test any versions before 1.0.0).
Download and install it from the official site:
👉 [https://www.freecad.org/downloads.php](https://www.freecad.org/downloads.php)


### 1. Clone the repository
```
git clone https://github.com/SA21005060/FreeCADAgent.git
cd FreeCADAgent
```

### 2. Create a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows PowerShell
```

### 3. Install dependencies
```
pip install -r requirements.txt
```



### 4. Run FreeCAD in your terminal
For Mac:
```
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD
```

## 🚀 Usage in FreeCAD
1. Open FreeCAD → Macro...
   - Update the `User macros location:` to `your-downloaded-repo-path/macros`
     - Execute `AutoLoadMyWorkbench.FCMacro` to launch FreeCADAgent
   - Switch to FreeCADAgent AI Assistant workbench
   - Click on `AI` icon to launch FreeCADAgent
2. Use the docked panel:
    - Type a prompt and press 🚀 Send
    - Record a speech prompt with 🎙 Speak
    - Upload a reference image with 🖼 Image
3. The generated macro will:
   - Be executed in FreeCAD automatically,
   - Appear in the Response box,
   - Be available for refinement or manual execution.
4. Confirm good results with 👍 Good (cached), reject with 👎 Poor.
