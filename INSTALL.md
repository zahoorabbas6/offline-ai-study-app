"""
INSTALLATION GUIDE - Offline AI Study Engine

Follow these steps to get the application running on your machine.
"""

STEP_BY_STEP_SETUP = """
═══════════════════════════════════════════════════════════════════════════
  OFFLINE AI STUDY ENGINE - COMPLETE SETUP GUIDE
═══════════════════════════════════════════════════════════════════════════

STEP 1: VERIFY PYTHON INSTALLATION
───────────────────────────────────
Open a terminal/command prompt and run:
    python --version

Required: Python 3.8 or higher
If you don't have Python, download from https://www.python.org/

STEP 2: NAVIGATE TO PROJECT DIRECTORY
──────────────────────────────────────
    cd path/to/ai_flashcard_maker

STEP 3: CREATE VIRTUAL ENVIRONMENT (RECOMMENDED)
─────────────────────────────────────────────────
This keeps your project isolated from system Python.

Windows:
    python -m venv venv
    venv\Scripts\activate

macOS/Linux:
    python3 -m venv venv
    source venv/bin/activate

You should see (venv) at the start of your terminal line.

STEP 4: INSTALL PYTHON DEPENDENCIES
────────────────────────────────────
    pip install -r requirements.txt

This installs:
  • spacy (NLP processing)
  • PyPDF2 (PDF extraction)
  • numpy & scikit-learn (optional, advanced features)

Installation takes ~2-3 minutes depending on internet speed.

STEP 5: DOWNLOAD SPACY NLP MODEL
─────────────────────────────────
This is a one-time download (~40MB):

    python -m spacy download en_core_web_sm

If you want advanced features, you can also download:
    python -m spacy download en_core_web_md    # ~40MB, better accuracy
    python -m spacy download en_core_web_lg    # ~740MB, best accuracy

For most users, en_core_web_sm is sufficient.

STEP 6: VERIFY INSTALLATION
───────────────────────────
Run this test script:
    python -c "import spacy; print('✓ spacy ready'); import PyPDF2; print('✓ PyPDF2 ready')"

Expected output:
    ✓ spacy ready
    ✓ PyPDF2 ready

STEP 7: LAUNCH THE APPLICATION
───────────────────────────────

GUI MODE (Recommended for most users):
    python main.py

CLI MODE (Command-line for automation):
    python main.py --cli

The GUI window should open automatically.

═══════════════════════════════════════════════════════════════════════════
  TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════

Issue: "Python not found"
→ Solution: Install Python from https://www.python.org/
           Make sure to CHECK "Add Python to PATH" during installation

Issue: "ModuleNotFoundError: No module named 'spacy'"
→ Solution: Make sure virtual environment is activated
           Run: pip install -r requirements.txt

Issue: "Can't find spacy model"
→ Solution: Run: python -m spacy download en_core_web_sm

Issue: "GUI won't open"
→ Solution: Try CLI mode: python main.py --cli
           Or: pip install tk

Issue: "PDF extraction not working"
→ Solution: Make sure PDF is text-based (not scanned image)
           Try: pip install --upgrade PyPDF2

Issue: "Out of memory" on low-end machines
→ Solution: Reduce number of flashcards to generate
           Close other applications

═══════════════════════════════════════════════════════════════════════════
  SYSTEM RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════

Minimum:
  • RAM: 4GB
  • Disk Space: 500MB
  • Python: 3.8+

Recommended:
  • RAM: 8GB
  • Disk Space: 1GB
  • Python: 3.9+

Performance on Low-End Devices:
  • Use CLI mode instead of GUI
  • Generate fewer flashcards (25-50 instead of 100)
  • Use smaller spaCy model (en_core_web_sm)
  • Close other applications

═══════════════════════════════════════════════════════════════════════════
  QUICK COMMANDS REFERENCE
═══════════════════════════════════════════════════════════════════════════

Activate virtual environment:
  Windows: venv\Scripts\activate
  macOS/Linux: source venv/bin/activate

Deactivate virtual environment:
  deactivate

Update dependencies:
  pip install --upgrade -r requirements.txt

Check installed packages:
  pip list

Run in GUI mode:
  python main.py

Run in CLI mode:
  python main.py --cli

═══════════════════════════════════════════════════════════════════════════
  FIRST USE WALKTHROUGH
═══════════════════════════════════════════════════════════════════════════

1. Launch the app: python main.py

2. Load study material:
   - Click "Load PDF" or "Load Text"
   - Or use "Enter Text" from menu

3. Generate flashcards:
   - Click "Generate Flashcards" button
   - Wait for processing (~2-5 seconds per 50 cards)

4. View results:
   - Check preview in output panel
   - Click "Export Flashcards" to save

5. Predict exam questions:
   - Click "Predict Exam Questions"
   - Review ranked by probability

6. Create a quiz:
   - Click "Create Quiz"
   - Answer questions
   - See your score

═══════════════════════════════════════════════════════════════════════════
  IMPORTANT NOTES
═══════════════════════════════════════════════════════════════════════════

✓ 100% Offline - No internet required after installation
✓ No Data Collected - All processing happens locally
✓ No Hallucinations - Uses only content from your materials
✓ Free - Open source, no licensing fees
✓ Fast - Optimized for low-end laptops

═══════════════════════════════════════════════════════════════════════════

NEED HELP? Check:
  • README.md - Comprehensive documentation
  • QUICKSTART.md - Quick reference guide
  • Module docstrings - In-code documentation

Ready to start? Run: python main.py

═══════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(STEP_BY_STEP_SETUP)
