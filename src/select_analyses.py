from argparse import ArgumentParser
import os
from os import path
import re
from udapi.block.read.conllu import Conllu
from udapi.core.node import Node
from model.corpus import Corpus
from model.text import Text
from model.word import Word
from model.morph import Morph, SingleMorph, MultiMorph

parser = ArgumentParser(prog='tag_xml.py',
                        description='Use an annotated conllu to disambiguate texts in XML')
parser.add_argument('input_directory', help='A directory with XML requiring disambiguation')
parser.add_argument('infile', help='A conllu with annotated texts')
parser.add_argument('output_directory', help='A directory to store disambiguated XML')
args = parser.parse_args()

corpus = Corpus(args.input_directory)

reader = Conllu(files=[args.infile])
document = reader.read_documents()[0]

def save_text(text: Text) -> None:
    output_subdirectory = path.join(args.output_directory, text.rel_path)
    os.makedirs(output_subdirectory, exist_ok=True)
    outfile = path.join(output_subdirectory, text.text_id + '.xml')
    text.store(outfile)

paragraphs = filter(lambda paragraph: len(paragraph) > 0, map(list, corpus.paragraphs(save_text)))

for paragraph, root in zip(paragraphs, document.trees, strict=True):
    for (word_element, line_language), token in zip(paragraph, root.token_descendants, strict=True):
        assert word_element.name == 'w'
        word = Word.parse(word_element, line_language)
        # if (word.transcription or '_') != token.form:
        #     print(root.sent_id)
        #     print(word.transcription)
        #     print(token.form)
        #     raise ValueError
        if len(word.selections) == 0:
            selection = token.misc['Selected']
            word_element['mrp0sel'] = selection
