# Arxiv2Epub

This repository provides a simple script to download and compile latex sources from Arxiv papers and convert it to your e-reader format.

## Usage

Here is an example of the usage. The paper ID can be found in the paper URL.

```shell
python3 arxiv2epub.py --id 1807.10543 --landscape
```

The command will end giving you the path to the epub file located in tmp folder.

The _--help_ option can provide you with more detailed options.

Defaults are set for the Kobo Aura One.

## Requirements

Requirements can be installed via:

```shell
pip3 install -r requirements.txt
```

The system also needs texlive-full package.
