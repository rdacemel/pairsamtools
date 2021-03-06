#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import pipes
import click

from . import _io, _pairsam_format, cli, _headerops

UTIL_NAME = 'pairsam_markasdup'

@cli.command()
@click.argument(
    'pairsam_path', 
    type=str,
    required=False)
@click.option(
    "-o", "--output", 
    type=str, 
    default="", 
    help='output .pairsam file.'
        ' If the path ends with .gz, the output is bgzip-compressed.'
        ' By default, the output is printed into stdout.')

def markasdup(pairsam_path, output):
    '''tag all pairsam entries with a duplicate tag.

    PAIRSAM_PATH : input .pairsam file. If the path ends with .gz, the input is
    gzip-decompressed. By default, the input is read from stdin.
    '''
    markasdup_py(pairsam_path, output)

def markasdup_py(pairsam_path, output):
    instream = (_io.open_bgzip(pairsam_path, mode='r') 
                if pairsam_path else sys.stdin)
    outstream = (_io.open_bgzip(output, mode='w') 
                 if output else sys.stdout)
 

    header, body_stream = _headerops.get_header(instream)
    header = _headerops.append_new_pg(header, ID=UTIL_NAME, PN=UTIL_NAME)
    outstream.writelines((l+'\n' for l in header))


    for line in body_stream:
        cols = line[:-1].split(_pairsam_format.PAIRSAM_SEP)
        cols[_pairsam_format.COL_PTYPE] = 'DD'
        
        if (len(cols) > _pairsam_format.COL_SAM1) and (len(cols) > _pairsam_format.COL_SAM2):
            for i in (_pairsam_format.COL_SAM1,
                      _pairsam_format.COL_SAM2):
                    
                # split each sam column into sam entries, tag and assemble back
                cols[i] = _pairsam_format.INTER_SAM_SEP.join(
                    [mark_sam_as_dup(sam) 
                     for sam in cols[i].split(_pairsam_format.INTER_SAM_SEP)
                    ])

        outstream.write(_pairsam_format.PAIRSAM_SEP.join(cols))
        outstream.write('\n')

    if instream != sys.stdin:
        instream.close()
    if outstream != sys.stdout:
        outstream.close()

def mark_sam_as_dup(sam):
    '''Tag the binary flag and the optional pair type field of a sam entry
    as a PCR duplicate.'''
    samcols = sam.split(_pairsam_format.SAM_SEP)

    if len(samcols) == 1:
        return sam

    samcols[1] = str(int(samcols[1]) | 1024)

    for j in range(11, len(samcols)):
        if samcols[j].startswith('Yt:Z:'):
            samcols[j] = 'Yt:Z:DD'
    return _pairsam_format.SAM_SEP.join(samcols)


if __name__ == '__main__':
    markasdup()
