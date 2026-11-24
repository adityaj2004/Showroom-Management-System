"""Start the backend and static dashboard on one origin."""
import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')
if __name__ == '__main__':
    uvicorn.run('backend.main:app', host=os.getenv('HOST','127.0.0.1'),
                port=int(os.getenv('PORT','8000')), reload=False)
