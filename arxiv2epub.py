import os, sys, subprocess, os.path
import lxml.html as html
import tempfile
import argparse
import requests
import glob
import re

def get_geom_dict(width, height, margin):
        w = str(width) + 'in'
        h = str(height) + 'in'
        m = str(margin) + 'in'
        return dict(paperwidth=w, paperheight=h, margin=m)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloads and generates EPUB from Arxiv paper')
    parser.add_argument('--id', type=str, help='Arxiv ID')
    parser.add_argument('--width', type=float, default=5.5, help='Target screen width in inch')
    parser.add_argument('--height', type=float, default=7.7, help='Target screen height in inch')
    parser.add_argument('--margin', type=float, default=.2, help='Target screen margin in inch')
    parser.add_argument('--landscape', action='store_true', help='Generate EPUB for landscape mode')
    args = parser.parse_args()
    landscape = args.landscape
    if args.landscape:
        geom_settings = get_geom_dict(args.height, args.width, args.margin)
    else:
        geom_settings = get_geom_dict(args.width, args.height, args.margin)
    arxiv_abs = 'https://arxiv.org/abs/' + args.id
    arxiv_pdf = 'https://arxiv.org/pdf/' + args.id
    arxiv_pgtitle = html.fromstring(requests.get(arxiv_abs).text.encode('utf8')).xpath('/html/head/title/text()')[0]
    arxiv_title = re.sub(r'\s+', ' ', re.sub(r'^\[[^]]+\]\s*', '', arxiv_pgtitle), re.DOTALL)
    arxiv_title_scrubbed = re.sub('[^-_A-Za-z0-9]+', '_', arxiv_title, re.DOTALL)
    print('Generating EPUB for:', arxiv_title)

    d = tempfile.mkdtemp(prefix='arxiv2epub_')
    url = 'https://arxiv.org/e-print/' + args.id
    command = ['wget', '-O', os.path.join(d, 'src.tar.gz'), '--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/02100101 Firefox/21.0"', url]
    subprocess.run(command)
    os.chdir(d)
    subprocess.run(['tar', 'xf', 'src.tar.gz'])

    texfiles = glob.glob(os.path.join(d, '*.tex'))
    for texfile in texfiles:
        with open(texfile, 'r') as f:
            src = f.readlines()
        if 'documentclass' in src[0]:
            print('correct file:', texfile)
            break
    # filter comments/newlines for easier debugging:
    src = [line for line in src if line[0] != '%' and len(line.strip()) > 0]

    # strip font size, column stuff, and paper size stuff in documentclass line:
    src[0] = re.sub(r'\b\d+pt\b', '', src[0])
    src[0] = re.sub(r'\b\w+column\b', '', src[0])
    src[0] = re.sub(r'\b\w+paper\b', '', src[0])
    src[0] = re.sub(r'(?<=\[),', '', src[0]) # remove extraneous starting commas
    src[0] = re.sub(r',(?=[\],])', '', src[0]) # remove extraneous middle/ending commas

    # find begin{document}:
    begindocs = [i for i, line in enumerate(src) if line.startswith(r'\begin{document}')]
    assert(len(begindocs) == 1)
    src.insert(begindocs[0], '\\usepackage['+','.join(k+'='+v for k,v in geom_settings.items())+']{geometry}\n')
    src.insert(begindocs[0], '\\usepackage{times}\n')
    src.insert(begindocs[0], '\\pagestyle{empty}\n')
    if landscape:
        src.insert(begindocs[0], '\\usepackage{pdflscape}\n')

    # shrink figures to be at most the size of the page:
    for i in range(len(src)):
        line = src[i]
        m = re.search(r'\\includegraphics\[width=([.\d]+)\\(line|text)width\]', line)
        if m:
            mul = m.group(1)
            src[i] = re.sub(r'\\includegraphics\[width=([.\d]+)\\(line|text)width\]',
                       r'\\includegraphics[width={mul}\\textwidth,height={mul}\\textheight,keepaspectratio]'.format(mul=mul),
                       line)

    os.rename(texfile, texfile+'.bak')
    with open(texfile, 'w') as f:
        f.writelines(src)
    subprocess.run(['pdflatex', texfile], stdout=subprocess.DEVNULL)
    subprocess.run(['pdflatex', texfile], stdout=subprocess.DEVNULL)
    subprocess.run(['pdflatex', texfile], stdout=subprocess.DEVNULL)
    pdffilename = texfile[:-4] + '.pdf'
    print('File saved under', os.path.join(d, pdffilename))
