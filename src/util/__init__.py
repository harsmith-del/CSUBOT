import os
import sys
from pathlib import Path

main_repo_path = str(Path(os.path.abspath(__file__)).parents[1]).replace('\\', '/')
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from util.util_funcs import connect_to_docstore, retriever_to_index
from util.vars import CONTEXT, FRAGMENT_TO_CONTEXT