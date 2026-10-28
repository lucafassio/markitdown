import time
from process_pdfs import INPUT_DIR, convert_all_pdfs


DEBOUNCE_SECONDS = 5
POLL_SECONDS = 0.5


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
    print(f'mirando {INPUT_DIR} (ctrl+c para salir)')
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
                print('\r' + ' ' * 40 + '\r', end='')
                convert_all_pdfs()
                previous = snapshot_pdfs()
                deadline = None
                last_shown = None
            else:
                shown = int(remaining) + 1
                if shown != last_shown:
                    print(f'\rconvirtiendo en {shown}s...  ', end='', flush=True)
                    last_shown = shown

        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    try:
        watch()
    except KeyboardInterrupt:
        print('\nchau')
