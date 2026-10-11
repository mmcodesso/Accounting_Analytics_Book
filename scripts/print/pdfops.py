"""A small tokenizer for PDF content streams, shared by the figure recoloring and the preflight.

It reads only what the book's PDFs contain (LuaLaTeX pages and Draw.io figures): numbers, names, literal
and hex strings, arrays, dictionaries and operators, and inline images, which it skips whole. Each
operator is returned with its operands and the byte span they cover, so a caller can rewrite one
operator in place.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DELIMITERS = b'()<>[]{}/%'
WHITESPACE = b' \t\r\n\f\x00'
NUMBER = re.compile(rb'[+-]?(?:\d+\.?\d*|\.\d+)$')


@dataclass
class Operation:
    operator: str
    operands: list[bytes]
    start: int  # first byte of the first operand (or of the operator when there is none)
    end: int    # one past the last byte of the operator

    def numbers(self) -> list[float] | None:
        """The operands as numbers, or None if any operand is not a number."""
        if not all(NUMBER.match(operand) for operand in self.operands):
            return None
        return [float(operand) for operand in self.operands]


def _skip_string(data: bytes, i: int) -> int:
    """i is at '('; returns the index after the matching ')'."""
    depth, i = 0, i
    while i < len(data):
        c = data[i]
        if c == 0x5C:  # backslash escapes the next byte
            i += 2
            continue
        if c == 0x28:
            depth += 1
        elif c == 0x29:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unterminated string in content stream')


def operations(data: bytes):
    """Yield every Operation of a content stream, in order."""
    i, n = 0, len(data)
    operands: list[bytes] = []
    start = None
    depth = 0  # inside [ ] or << >>, which are operands as a whole
    group_start = None
    while i < n:
        c = data[i]
        if c in WHITESPACE:
            i += 1
            continue
        if c == 0x25:  # comment
            while i < n and data[i] not in b'\r\n':
                i += 1
            continue
        token_start = i
        if c == 0x28:
            i = _skip_string(data, i)
        elif data.startswith(b'<<', i):
            if depth == 0:
                group_start = i
            depth += 1
            i += 2
            continue
        elif data.startswith(b'>>', i):
            depth -= 1
            i += 2
            if depth == 0:
                operands.append(data[group_start:i])
                start = group_start if start is None else start
            continue
        elif c == 0x3C:  # hex string
            i = data.index(b'>', i) + 1
        elif c == 0x5B:
            if depth == 0:
                group_start = i
            depth += 1
            i += 1
            continue
        elif c == 0x5D:
            depth -= 1
            i += 1
            if depth == 0:
                operands.append(data[group_start:i])
                start = group_start if start is None else start
            continue
        elif c == 0x2F:  # name
            i += 1
            while i < n and data[i] not in WHITESPACE and data[i] not in DELIMITERS:
                i += 1
        else:
            while i < n and data[i] not in WHITESPACE and data[i] not in DELIMITERS:
                i += 1
            if i == token_start:  # a stray delimiter such as '{' or ')'
                i += 1
        token = data[token_start:i]
        if depth:
            continue
        if c in b'(<[/' or NUMBER.match(token) or token in (b'true', b'false', b'null'):
            operands.append(token)
            start = token_start if start is None else start
            continue
        operator = token.decode('latin-1')
        if operator == 'BI':  # inline image: skip to EI
            match = re.compile(rb'\sEI(?=[\s]|$)').search(data, i)
            if not match:
                raise ValueError('unterminated inline image in content stream')
            i = match.end()
            yield Operation('BI', [], token_start, i)
        else:
            yield Operation(operator, operands, token_start if start is None else start, i)
        operands, start = [], None


COLOR_OPERATORS = {'rg', 'RG', 'g', 'G', 'k', 'K', 'sc', 'SC', 'scn', 'SCN', 'cs', 'CS'}
