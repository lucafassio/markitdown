import ctypes
import math
import sys
import time
from process_pdfs import BASE_DIR, INPUT_DIR, convert_all_pdfs


DEBOUNCE_SECONDS = 5
POLL_SECONDS = 0.5
LOG_PATH = BASE_DIR / 'watch.log'
ERROR_ALREADY_EXISTS = 183


def snapshot_pdfs():
    '''
    Devuelve el conjunto (nombre, tamano, mtime) de los pdf en input/. Si un archivo se sigue copiando cambia el tamano o el mtime.
    '''
    entries = set()
    for pdf_path in INPUT_DIR.glob('*.pdf'):
        try:
            stat = pdf_path.stat()
        except FileNotFoundError:
            continue
        entries.add((pdf_path.name, stat.st_size, stat.st_mtime_ns))
    return entries


def watch():
    '''
    Mira input/ y convierte cuando pasan DEBOUNCE_SECONDS sin que entre nada nuevo. Cada archivo nuevo o modificado reinicia el contador.
    '''
    INPUT_DIR.mkdir(exist_ok=True)
    # el contador solo tiene sentido en consola, no en el log
    interactive = sys.stdout.isatty()
    print(f'mirando {INPUT_DIR} (ctrl+c para salir)', flush=True)
    previous = set()
    deadline = None
    last_shown = None

    while True:
        current = snapshot_pdfs()
        # solo altas o cambios reinician el contador, los borrados no
        if current - previous:
            deadline = time.monotonic() + DEBOUNCE_SECONDS
        previous = current

        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if interactive:
                    print('\r' + ' ' * 40 + '\r', end='')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'convirtiendo', flush=True)
                convert_all_pdfs()
                sys.stdout.flush()
                previous = snapshot_pdfs()
                deadline = None
                last_shown = None
            else:
                shown = math.ceil(remaining)
                if interactive and shown != last_shown:
                    print(f'\rconvirtiendo en {shown}s...  ', end='', flush=True)
                    last_shown = shown

        time.sleep(POLL_SECONDS)


def already_running():
    '''
    Usa un mutex con nombre de windows para que no corran dos watchers a la vez sobre input/.
    '''
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    # el handle no se cierra nunca, asi que el mutex vive lo que vive el proceso
    kernel32.CreateMutexW(None, False, 'markitdown_watch_input')
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


if __name__ == '__main__':
    # con pythonw no hay consola, todo va a watch.log
    if sys.stdout is None:
        log_file = open(LOG_PATH, 'a', encoding='utf-8', buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file

    if already_running():
        print('ya hay un watcher corriendo, salgo', flush=True)
        sys.exit(0)

    try:
        watch()
    except KeyboardInterrupt:
        print('\nchau')
