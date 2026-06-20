from dataclasses import dataclass
from collections.abc import Iterable
from typing import Callable
from bs4 import Tag
from .text import Text
import os
from tqdm.auto import tqdm
from os import path
from .line import Line
from itertools import chain
from logging import getLogger
logger = getLogger(__name__)

PROCESSED_FILE_LOGGER_NAME = 'processed_files'
processed_file_logger = getLogger(PROCESSED_FILE_LOGGER_NAME)
SKIPPED_FILE_LOGGER_NAME = 'skipped_files'
skipped_file_logger = getLogger(SKIPPED_FILE_LOGGER_NAME)

def to_be_procecced(triple: tuple[str, list[str], list[str]]) -> bool:
  dirpath, dirnames, filenames = triple
  _, folder = path.split(dirpath)
  return True

@dataclass
class Corpus:
  input_directory: str

  def paragraphs(self, on_text_end: Callable[[Text], None]) -> Iterable[Iterable[tuple[Tag, str]]]:
    for text in self.texts:
      for paragraph in text.paragraphs:
        yield paragraph
      on_text_end(text)

  @property
  def texts(self) -> Iterable[Text]:
    walk = list(filter(to_be_procecced, os.walk(self.input_directory)))
    progress_bar = tqdm(walk)
    for dirpath, dirnames, filenames in progress_bar:
      rel_path = dirpath.removeprefix(self.input_directory).removeprefix(os.sep)
      processed_file_logger.info(rel_path)
      _, folder = path.split(dirpath)
      progress_bar.set_postfix_str(folder)
      for filename in filenames:
        text_id, ext = path.splitext(filename)
        if ext == '.xml':
          rel_name = path.join(rel_path, filename)
          infile = path.join(dirpath, filename)
          try:
            with open(infile, 'r', encoding='utf-8') as fin:
              text = Text.parse(rel_path, text_id, fin)
            if text is None:
              skipped_file_logger.info(rel_name)
            else:
              yield text
          except (KeyError, ValueError, AssertionError):
            skipped_file_logger.info(rel_name)
            logger.exception(
              'A text could not be read from the file %s because of the following exception:', rel_name
            )
