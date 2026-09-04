"""
Project Pukar - Portable On-Device Tokenizer
Provides character & subword n-gram tokenization with vocabulary serialization
for multilingual disaster messages (English, Hindi, Hinglish).
Zero external C++ binary dependencies to guarantee Android TFLite compatibility.
"""

import json
import re
import unicodedata
from pathlib import Path


class CrisisTokenizer:
    def __init__(
        self,
        vocab_size: int = 5000,
        max_seq_len: int = 64,
        pad_token: str = "<PAD>",
        unk_token: str = "<UNK>",
    ):
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.pad_token = pad_token
        self.unk_token = unk_token

        self.vocab: dict[str, int] = {pad_token: 0, unk_token: 1}
        self.inv_vocab: dict[int, str] = {0: pad_token, 1: unk_token}

    def normalize(self, text: str) -> str:
        """
        Normalizes Unicode, lowercases Latin characters, and cleans excessive whitespace.
        """
        if not text:
            return ""
        # Unicode NFKC normalization (crucial for Devanagari and accented text)
        normalized = unicodedata.normalize("NFKC", text.strip())
        normalized = normalized.lower()
        # Keep alphanumeric, Devanagari Unicode block (\u0900-\u097F), and basic punctuation
        normalized = re.sub(r"[^\w\s\u0900-\u097F\.,!?-]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenizes normalized text into word and subword components.
        """
        norm = self.normalize(text)
        if not norm:
            return []
        # Word split with punctuation detachment
        tokens = re.findall(r"[\w\u0900-\u097F]+|[.,!?-]", norm)
        return tokens

    def fit_on_texts(self, texts: list[str]) -> None:
        """
        Builds vocabulary from a list of disaster training messages.
        """
        freq: dict[str, int] = {}
        for text in texts:
            tokens = self.tokenize(text)
            for token in tokens:
                freq[token] = freq.get(token, 0) + 1

        # Sort tokens by frequency
        sorted_tokens = sorted(freq.items(), key=lambda item: item[1], reverse=True)

        # Populate vocabulary up to vocab_size
        self.vocab = {self.pad_token: 0, self.unk_token: 1}
        self.inv_vocab = {0: self.pad_token, 1: self.unk_token}

        for token, _ in sorted_tokens:
            if len(self.vocab) >= self.vocab_size:
                break
            idx = len(self.vocab)
            self.vocab[token] = idx
            self.inv_vocab[idx] = token

    def encode(self, text: str) -> list[int]:
        """
        Encodes string into fixed-length integer token ID sequence with padding/truncation.
        """
        tokens = self.tokenize(text)
        unk_idx = self.vocab[self.unk_token]
        pad_idx = self.vocab[self.pad_token]

        token_ids = [self.vocab.get(t, unk_idx) for t in tokens][: self.max_seq_len]
        
        # Pad sequence to max_seq_len
        if len(token_ids) < self.max_seq_len:
            token_ids.extend([pad_idx] * (self.max_seq_len - len(token_ids)))

        return token_ids

    def save_vocab(self, file_path: str | Path) -> None:
        """
        Saves vocabulary mapping to JSON.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "vocab_size": len(self.vocab),
                    "max_seq_len": self.max_seq_len,
                    "pad_token": self.pad_token,
                    "unk_token": self.unk_token,
                    "vocab": self.vocab,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def load_vocab(self, file_path: str | Path) -> None:
        """
        Loads vocabulary mapping from JSON.
        """
        path = Path(file_path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            self.vocab_size = data.get("vocab_size", len(data.get("vocab", {})))
            self.max_seq_len = data.get("max_seq_len", 64)
            self.pad_token = data.get("pad_token", "<PAD>")
            self.unk_token = data.get("unk_token", "<UNK>")
            self.vocab = data.get("vocab", {})
            self.inv_vocab = {v: k for k, v in self.vocab.items()}
