import sys, os, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve() / 'src'))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
from src.core.settings import Settings
from src.core.image_library import ImageLibrary
from src.core.wallpaper_manager import WallpaperManager
from src.core.scheduler import Scheduler
from src.app.window import MainWindow

app = QApplication([])
settings = Settings()
library = ImageLibrary(directories=[], extensions=set())
wm = WallpaperManager()
scheduler = Scheduler(mode='manual')
scheduler.set_dependencies(library, wm)
window = MainWindow(settings=settings, library=library, wallpaper_manager=wm, scheduler=scheduler)

tmp = tempfile.TemporaryDirectory()
tmpdir = Path(tmp.name)
for i in range(500):
    (tmpdir / f'image_{i}.jpg').write_text('dummy')
print('before add_dir')
t0 = time.time()
ok = window._library.add_directory(str(tmpdir))
t1 = time.time()
print('after add_dir', ok, t1 - t0)
t0 = time.time()
images = window._library.scan()
t1 = time.time()
print('after scan all', len(images), t1 - t0)
tmp.cleanup()
print('done')
