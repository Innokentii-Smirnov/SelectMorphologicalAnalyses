from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterator
from bs4 import Tag
from logging import getLogger
from os.path import join

@dataclass(frozen=True)
class Line:
  text_path: str
  text_id: str
  line_id: str
  language: str
  word_elements: list[Tag]
  logger = getLogger(__name__)
  UNKNOWN_LINE_ID = 'unknown'
  UNKNOWN_LANGUAGE = 'unknown'

  def __iter__(self) -> Iterator[Tag]:
    return self.word_elements.__iter__()

  def __len__(self) -> int:
    return self.word_elements.__len__()

  @classmethod
  def parse(cls, text_path: str, text_id: str, elements: list[Tag], text_lang: str) -> Line:
    full_path = join(text_path, text_id)
    if (lb := elements[0]).name == 'lb':
      if 'lnr' in lb.attrs:
        line_id = lb['lnr']
        assert isinstance(line_id, str)
      else:
        cls.logger.error('A line in %s is not numbered.', full_path)
        line_id = cls.UNKNOWN_LINE_ID
      if 'lg' in lb.attrs:
        language = lb.attrs['lg']
      else:
        cls.logger.error('Line %s in %s is not marked for language.', line_id, full_path)
        language = text_lang
      word_elements = elements[1:]
    else:
      match lb.name:
        case 'clb':
          cls.logger.warning('The first line in %s starts with a clause boundary instead of a linebreak element.', full_path)
        case 'ParagrNr':
          cls.logger.info('The first line in %s starts with a paragraph name: %s.', full_path, lb)
        case _:
          cls.logger.error('The first line in %s does not start with a linebreak element, but with the element %s.', full_path, lb.name)
      line_id = cls.UNKNOWN_LINE_ID
      language = cls.UNKNOWN_LANGUAGE
      word_elements = elements
    return Line(text_path, text_id, line_id, language, word_elements)
