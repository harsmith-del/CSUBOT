import os
import sys
from pathlib import Path
main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from extractor.doc_extractor import DOCExtractorDefault, Fragment
from extractor.text_preprocessing import preprocessing_pipeline