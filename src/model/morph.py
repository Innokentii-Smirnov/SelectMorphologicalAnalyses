from __future__ import annotations
from logging import getLogger
logger = getLogger(__name__)

sep = '@'

def split_at_single(value: str, split_string: str,
                    split_at_last: bool=False) -> tuple[str, str | None]:
  if split_at_last:
    split_index = value.rfind(split_string)
  else:
    split_index = value.find(split_string)
  if split_index >= 0:
    return (value[:split_index].strip(), value[split_index + len(split_string):].strip())
  else:
    return value, None

def read_enclitics_chain(enclitics_chain: str) -> Morph | None:
  split_enclitics_chain = list(map(str.strip, enclitics_chain.split(sep)))
  if len(split_enclitics_chain) < 2:
    return None
  enclitics, analyses_string = split_enclitics_chain[:2]
  if in_braces(analyses_string):
    enclitics_tags = parseMorphTags(analyses_string)
    return MultiMorph(enclitics, '', enclitics_tags, '', '', None)
  else:
    return SingleMorph(enclitics, '', analyses_string, '', '', None)

class Morph:

    def __init__(self,
                 segmentation: str,
                 translation: str,
                 pos: str,
                 det: str,
                 enclitics_analysis: Morph | None):
        self.segmentation = segmentation
        self.translation = translation
        self.pos = pos
        self.det = det
        self.enclitics_analysis = enclitics_analysis
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        return (self.segmentation == other.segmentation and
                self.translation == other.translation and
                self.pos == other.pos and
                self.det == other.det)
    
    @property
    def morph_info(self) -> str:
        raise NotImplementedError
    
    def __tuple__(self) -> tuple[str, str, str, str, str]:
        return self.segmentation, self.translation, self.morph_info, self.pos, self.det
    
    def __str__(self) -> str:
        return ' @ '.join(self.__tuple__())
    
    def __hash__(self) -> int:
        return self.__tuple__().__hash__()
    
    def to_multi(self, index: str) -> MultiMorph:
        raise NotImplementedError

    """Return the morphological tag if it is the only morphological tag option
    for this analysis. Log a warning if a morphological tag index
    is requiered by the analysis' type (but not specified).
    If the analysis has multiple options, log an error and return None.
    :return: The morphological tag if the morphological analysis contains
    exactly one morphological tag option, None otherwise.
    """
    @property
    def single_morph_tag(self) -> str | None:
      raise NotImplementedError

    """Return the morphological with the specified index.
    Log a warning if the analysis does not support multiple
    morphological tag options and an error if the index
    does not occur in the dictionary containing the
    morphological tag options for this analysis.
    :return: The morphological analysis with the specified index
    if the index is found or the only morphological tag if the analysis
    does not support multiple options, None otherwise.
    """
    def __getitem__(self, index: str) -> str | None:
      raise NotImplementedError

    def get_morph_tag(self, index: str | None) -> str | None:
      """Return the morphological tag with the specified index.
      :param index: A letter indicating the required morphological tag, or None
      if the analysis does not support multiple morphological tag options.
      :return: The morphological tag with the specified index or the only morphological tag,
      if it is possible to retrieve it; None otherwise.
      """
      if index is None:
        morph_tag = self.single_morph_tag
      else:
        morph_tag = self.__getitem__(index)
      return morph_tag

    @classmethod
    def parse(cls, content: str) -> Morph | None:
      segmentation, rest_without_segmentation = split_at_single(content, sep)
      if rest_without_segmentation is None:
        return None
      translation, rest_without_translation = split_at_single(
        rest_without_segmentation, sep
      )
      if rest_without_translation is None:
        return None
      morph_info, rest_without_morph_info = split_at_single(
        rest_without_translation, sep
      )
      if rest_without_morph_info is None:
        return None
      other_string, determinative_string = split_at_single(
        rest_without_morph_info, sep, True
      )
      if determinative_string is not None:
        det = determinative_string
      else:
        det = ''
      pos, enclitics_chain = split_at_single(other_string, '+=')
      if enclitics_chain is None or enclitics_chain == '':
        enclitics_analysis = None
      else:
        enclitics_analysis = read_enclitics_chain(enclitics_chain)
      if in_braces(morph_info):
        morph_tags = parseMorphTags(morph_info)
        return MultiMorph(segmentation, translation, morph_tags, pos, det, enclitics_analysis)
      else:
        return SingleMorph(segmentation, translation, morph_info, pos, det, enclitics_analysis)
        
class SingleMorph(Morph):
    
    def __init__(self,
                 segmentation: str,
                 translation: str,
                 morph_tag: str,
                 pos: str,
                 det: str,
                 enclitics_analysis: Morph | None):
        super().__init__(segmentation, translation, pos, det, enclitics_analysis)
        self.morph_tag = morph_tag
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        if super().__eq__(other):
            if isinstance(other, MultiMorph):
                if other.is_singletone:
                    return self.morph_tag == next(iter(other.morph_tags.values()))
                else:
                    return False
            elif isinstance(other, SingleMorph):
                return self.morph_tag == other.morph_tag
            else:
                return NotImplemented
        else:
            return False
    
    @property
    def morph_info(self) -> str:
        return self.morph_tag
    
    def __hash__(self) -> int:
        return self.__tuple__().__hash__()
        
    def to_multi(self, index: str) -> MultiMorph:
        return MultiMorph(self.segmentation, self.translation,
            {index: self.morph_tag}, self.pos, self.det, self.enclitics_analysis)

    @property
    def single_morph_tag(self) -> str:
      return self.morph_tag

    def __getitem__(self, index: str) -> str:
      logger.warning('A morphological tag index (%s) is specified for a morphological analysis which does not support multiple morphological tag options (%s). The single available morphologial tag will be used.',
                     index, self)
      return self.morph_tag

class MultiMorph(Morph):
    
    def __init__(self,
                 segmentation: str,
                 translation: str,
                 morph_tags: dict[str, str],
                 pos: str,
                 det: str,
                 enclitics_analysis: Morph | None):
        super().__init__(segmentation, translation, pos, det, enclitics_analysis)
        self.morph_tags = morph_tags
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        if super().__eq__(other):
            if isinstance(other, SingleMorph):
                return self.is_singletone and next(iter(self.morph_tags.values())) == other.morph_tag
            elif isinstance(other, MultiMorph):
                return self.morph_tags == other.morph_tags
            else:
                return NotImplemented
        else:
            return False
    
    @property
    def morph_info(self) -> str:
        elements = list[str]()
        for key, value in self.morph_tags.items():
            element = '{ ' + key + ' → ' + value + '}'
            elements.append(element)
        return ' '.join(elements)
    
    @property
    def is_singletone(self) -> bool:
        return len(self.morph_tags) == 1
    
    def to_single(self) -> SingleMorph:
        return SingleMorph(self.segmentation, self.translation,
            next(iter(self.morph_tags.values())), self.pos, self.det, self.enclitics_analysis)
    
    def __hash__(self) -> int:
        if (self.is_singletone):
            return self.to_single().__hash__()
        else:
            return self.__tuple__().__hash__()
    
    def to_multi(self, index: str) -> MultiMorph:
        return self

    @property
    def single_morph_tag(self) -> str | None:
      if self.is_singletone:
        logger.warning('No morphological tag index is specified for a morphological analysis supporting multiple morphological tag options (%s). The single available option will be used.', self)
        return next(iter(self.morph_tags.values()))
      else:
        logger.error('No morphological tag index is specified for a morphological analysis supporting multiple morphological tag options (%s). Because of ambiguity, no morphological tag option will be used.', self)
        return None

    def __getitem__(self, index: str) -> str | None:
      if index in self.morph_tags:
        return self.morph_tags[index]
      else:
        logger.error('The specified morphological tag index (%s) was not found in the morphological tag option dictionary of the morphological analysis (%s). No morphological tag option will be used.', index, self)
        return None
        
def in_braces(string: str) -> bool:
    return string.startswith('{') and string.endswith('}')

def parseMorphTags(string: str) -> dict[str, str]:
    morph_tags = dict[str, str]()
    elements = string[1:-1].split('{')
    for element in elements:
        element = element.strip().removesuffix('}')
        try:
            key, value = list(map(str.strip, element.split('→')))
        except:
            raise ValueError(string)
        morph_tags[key] = value
    return morph_tags

if __name__ == '__main__':
  print('Test started')
  m1 = Morph.parse('nāli @ Rehbock @ .ABS @ noun @ ')
  print(m1)
  m2 = Morph.parse('nāli@Rehbock@{ a → .ABS}@noun@')
  print(m2)
  print(m1 == m2)
  print(m1.__hash__())
  print(m2.__hash__())
  print(m2 == m1)
