import sys
from pathlib import Path
from markitdown import MarkItDown


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / 'input'
OUTPUT_DIR = BASE_DIR / 'out'

# la consola de windows usa cp1252 por default y rompe con nombres de archivo con tildes
# con pythonw no hay consola y stdout es None
if sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')


def convert_all_pdfs():
    '''
    Convierte todos los pdf de input/ a markdown en out/ y borra el original si el markdown se escribio bien.
    '''
    OUTPUT_DIR.mkdir(exist_ok=True)
    markitdown = MarkItDown()
    pdf_paths = sorted(INPUT_DIR.glob('*.pdf'))

    if len(pdf_paths) == 0:
        print('no hay pdfs en input/')
        return

    for pdf_path in pdf_paths:
        output_path = OUTPUT_DIR / f'{pdf_path.stem}.md'
        try:
            result = markitdown.convert(pdf_path)
        except Exception as error:
            print(f'error convirtiendo {pdf_path.name}: {error}')
            continue

        output_path.write_text(result.markdown, encoding='utf-8')
        pdf_path.unlink()
        print(f'ok: {pdf_path.name} -> {output_path.name}')


if __name__ == '__main__':
    convert_all_pdfs()
