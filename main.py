import argparse
import subprocess

parser = argparse.ArgumentParser(description='Select OCR engine')
parser.add_argument('--ocr-engine', type=str, default='app', choices=['app', 'app_llm'], help='OCR engine to use')
args = parser.parse_args()

if args.ocr_engine == 'app':
    subprocess.run(['streamlit', 'run', 'app.py'])
elif args.ocr_engine == 'app_llm':
    subprocess.run(['streamlit', 'run', 'app_llm.py'])
else:
    print(f"Unknown OCR engine: {args.ocr_engine}")

