# -*- coding: utf-8 -*-
import os.path
from nltk.stem import SnowballStemmer
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from string import punctuation
from preprocess import unicode_to_ascii


class Tokenizer(object):

    def __init__(self, language='english', stopwords=None, stemming=True):
        if stemming:
            self._stemmer = SnowballStemmer(language)
        else:
            self._stemmer = None

        if isinstance(stopwords, list):
            self._stopwords = stopwords
        elif isinstance(stopwords, (str, unicode)):
            # stopwords argument is a path
            try:
                self._stopwords = self._load_stopwords(stopwords)
            except IOError:
                raise IOError('stopwords argument must be a path to a .txt file, a list of word strings '
                              'or None (which loads the default list)')
        else:
            # Load built-in stopwords
            stopwords_dir = 'stopwords/{}.txt'.format(language.lower())
            application_root = os.path.dirname(__file__)
            stopwords_file = os.path.join(application_root, '..', stopwords_dir)
            self._stopwords = self._load_stopwords(stopwords_file)

    @property
    def stopwords(self):
        return self._stopwords

    @property
    def stemmer(self):
        return self._stemmer

    @staticmethod
    def _load_stopwords(file_path):
        try:
            with open(file_path, 'rb') as stopwords_file:
                stopwords = [word.strip('\n') for word in stopwords_file.readlines()]
        except IOError:
            stopwords = []

        return stopwords

    def remove_stopwords(self, tokens):
        """Remove all stopwords from a list of word tokens or a string of text."""
        if isinstance(tokens, (list, tuple)):
            return [word for word in tokens if word.lower() not in self._stopwords]
        else:
            return ' '.join(
                [word for word in tokens.split(' ') if word.lower() not in self._stopwords]
            )

    def stem(self, word):
        if self.stemmer:
            return unicode_to_ascii(self._stemmer.stem(word))
        else:
            return word

    def stem_tokens(self, tokens):
        """Perform snowball (Porter2) stemming on a list of word tokens."""
        return [self.stem(word) for word in tokens]

    @staticmethod
    def strip_punctuation(text, exclude='', include=''):
        """Strip leading and trailing punctuation from an input string."""
        chars_to_strip = ''.join(
            set(list(punctuation)).union(set(list(include))) - set(list(exclude))
        )
        return text.strip(chars_to_strip)

    def tokenize_words(self, text):
        """Tokenize an input string into a list of words (with punctuation removed)."""
        return [
            self.strip_punctuation(word) for word in text.split(' ')
            if self.strip_punctuation(word)
        ]

    def sanitize_text(self, text):
        tokens = self.tokenize_words(text.lower())
        tokens = self.remove_stopwords(tokens)
        tokens = self.stem_tokens(tokens)
        sanitized_text = ' '.join(tokens)
        return sanitized_text

    @staticmethod
    def _remove_whitespace(text):
        while True:
            old_text = text
            text = text.replace('  ', ' ')
            if text == old_text:
                return text

    def tokenize_sentences(self, text, word_threshold=5):
        punkt_params = PunktParameters()
        # Not using set literal to allow compatibility with Python 2.6
        punkt_params.abbrev_types = set([
            'dr', 'vs', 'mr', 'mrs', 'ms', 'prof', 'mt', 'inc', 'i.e', 'e.g'
        ])
        sentence_splitter = PunktSentenceTokenizer(punkt_params)

        # 1. TOKENIZE "UNPROCESSED" SENTENCES FOR DISPLAY
        # Need to adjust quotations for correct sentence splitting
        text_unprocessed = text.replace('?"', '? "').replace('!"', '! "').replace('."', '. "')

        # Treat line breaks as end of sentence (needed in cases where titles don't have a full stop)
        text_unprocessed = text_unprocessed.replace('\n', ' . ')

        # Perform sentence splitting
        unprocessed_sentences = sentence_splitter.tokenize(text_unprocessed)

        # Now that sentences have been split we can return them back to their normal formatting
        for ndx, sentence in enumerate(unprocessed_sentences):
            sentence = unicode_to_ascii(sentence)  # Sentence splitter returns unicode strings
            sentence = sentence.replace('? " ', '?" ').replace('! " ', '!" ').replace('. " ', '." ')
            sentence = self._remove_whitespace(sentence)  # Remove excess whitespace
            sentence = sentence[:-2] if (sentence.endswith(' .') or sentence.endswith(' . ')) else sentence
            unprocessed_sentences[ndx] = sentence

        # 2. PROCESS THE SENTENCES TO PERFORM STEMMING, STOPWORDS REMOVAL ETC. FOR MATRIX COMPUTATION
        processed_sentences = [self.sanitize_text(sen) for sen in unprocessed_sentences]

        # Sentences should contain at least 'word_threshold' significant terms
        filter_sentences = [i for i in range(len(processed_sentences))
                            if len(processed_sentences[i].replace('.', '').split(' ')) > word_threshold]

        processed_sentences = [processed_sentences[i] for i in filter_sentences]
        unprocessed_sentences = [unprocessed_sentences[i] for i in filter_sentences]

        return processed_sentences, unprocessed_sentences