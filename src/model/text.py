from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable
from os import path
from io import TextIOBase
from logging import getLogger
from typing import Literal, Sequence
from more_itertools import split_before, split_at
from bs4 import Tag, BeautifulSoup
from bs4.dammit import EntitySubstitution
from .line import Line
from .formatter import CustomFormatter

SentenceBoundary = Literal['clb', 'parsep', 'parsep_dbl']

logger = getLogger(__name__)
extension = '.xml'

custom_formatter = CustomFormatter(entity_substitution=EntitySubstitution.substitute_xml)

def is_ao_manuscripts(tag: Tag) -> bool:
  return tag.prefix == 'AO' and tag.name == 'Manuscripts'

@dataclass
class Text:
  rel_path: str
  text_id: str
  text_tag: Tag
  text_lang: str
  soup: BeautifulSoup

  def store(self, outfile: str) -> None:
    with open(outfile, 'w', encoding='utf-8') as fout:
      outfile_text = self.soup.decode(formatter=custom_formatter)
      fout.write(outfile_text)

  @property
  def lines(self) -> Iterable[Line]:
    tokens = list[Tag]()
    for page_element in self.text_tag.children:
      if isinstance(page_element, Tag):
        tokens.append(page_element)
    if len(tokens) > 0 and is_ao_manuscripts(tokens[0]):
      tokens = tokens[1:]
    for line_elements in split_before(tokens,
                                      lambda tag: tag.name == 'lb'):
      line = Line.parse(self.rel_path, self.text_id, line_elements, self.text_lang)
      yield line

  @property
  def words_and_boundaries(self) -> Iterable[tuple[Tag, str]]:
    for line in self.lines:
      for tag in line:
        if tag.name in {'w', 'clb', 'parsep', 'parsep_dbl'}:
          yield tag, line.language

  def sentences(self, sentence_boundaries: Sequence[SentenceBoundary]) -> Iterable[Iterable[tuple[Tag, str]]]:
    return split_at(self.words_and_boundaries,
                    lambda pair: pair[0].name in sentence_boundaries)

  @classmethod
  def parse(cls, rel_path: str, text_id: str, stream: TextIOBase) -> Text | None:
    soup = BeautifulSoup(stream, 'xml')
    body_tag = soup.body
    if body_tag is None:
      logger.error('The XML tag "body" could not be found.')
      return None
    text_tag = body_tag.find('text')
    if text_tag is None:
      logger.error('The XML tag "text" could not be found.')
      return None
    if not isinstance(text_tag, Tag):
      logger.error('A string was provided instead of the XML tag "text".')
      return None
    if 'xml:lang' in text_tag.attrs and text_tag['xml:lang'] != 'XXXlang':
      text_lang = text_tag['xml:lang']
      if not isinstance(text_lang, str):
        logger.error('The text language attribute had multiple values.')
        return None
      rel_name = path.join(rel_path, text_id + extension)
      logger.info('The text language is set to %s for %s', text_lang, rel_name)
    else:
      text_lang = 'Hit'
    return cls(rel_path, text_id, text_tag, text_lang, soup)
