import aiofiles
from typing import Any

class AsyncFileReader:
    """Async file reader utility."""
    
    async def read_file(self, file_path: str) -> str:
        """Read a file asynchronously."""
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                return await f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
