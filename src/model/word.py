from __future__ import annotations
from dataclasses import dataclass
from more_itertools import first
from .selection import Selection
from .morph import Morph, SingleMorph, MultiMorph
from re import compile
from bs4 import Tag
from bs4.element import NavigableString
from os.path import exists
from os import remove
from logging import getLogger
logger = getLogger(__name__)

def get_postdet(tag: Tag) -> str | None:
  children = list(tag.children)
  if len(children) > 1:
    postdets = list[str]()
    for child in children[1:]:
      if isinstance(child, Tag) and child.name == 'd':
        postdets.append(child.text)
      elif isinstance(child, NavigableString) and '˽' in child:
        break
    if len(postdets) > 0:
      if len(postdets) > 1:
        logger.error('Ignoring non-first postdeterminatives in %s',
                     tag.decode_contents())
      return first(postdets)
  return None

@dataclass(frozen=True)
class Word:
  transliteration: str
  lang: str
  transcription: str | None
  selections: list[Selection | None]
  analyses: dict[int, str]
  det: str | None
  postdet: str | None
  MRP = compile(r'mrp(\d+)')

  @classmethod
  def parse(cls, tag: Tag, default_lang: str) -> Word:
    assert tag.name == 'w'
    transliteration = tag.decode_contents()
    lang = tag.attrs.get('lg', default_lang)
    if not isinstance(lang, str):
      raise ValueError('The attribute lg had a list as a value.')
    if 'trans' in tag.attrs:
      transcription = tag['trans']
      assert isinstance(transcription, str)
    else:
      logger.warning('A word has no transcription attribute: %s.', tag)
      transcription = None
    if 'mrp0sel' in tag.attrs:
      mrp0sel = tag['mrp0sel']
      assert isinstance(mrp0sel, str)
      selections = list(map(Selection.parse, mrp0sel.split()))
    else:
      logger.warning('A word has no selection attribute: %s.', tag)
      selections = []
    analyses = dict[int, str]()
    for attr, value in tag.attrs.items():
      if (match := cls.MRP.fullmatch(attr)) is not None:
        number = int(match.group(1))
        if not isinstance(value, str):
          raise ValueError('The attribute {0} had a list as a value.'.format(attr))
        analyses[number] = value
    children = list(tag.children)
    if (len(children) > 0 and
        isinstance(children[0], Tag) and
        children[0].name == 'd'):
      det = children[0].text
    else:
      det = None
    postdet = get_postdet(tag)
    return Word(transliteration, lang, transcription, selections, analyses, det, postdet)

  def __getitem__(self, number: int) -> Morph | None:
    return Morph.parse(self.analyses[number])
