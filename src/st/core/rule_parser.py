"""Parser and evaluator for '.st' rule files.

A rules file is a sequence of 'INCLUDE(<expr>)', 'EXCLUDE(<expr>)'
(for the moment)

'<expr>' is a boolean expression combining two kinds of leaf
predicates with 'AND', 'OR', 'NOT' and parentheses:

- 'ATTRIBUTE=value': glob-matches ('*', '?', '[...]') the attribute
  against 'value'.
- 'CONTAIN(ATTRIBUTE, "substring")': True if the attribute's value contains
  'substring' as a literal substring.

'ATTRIBUTE' is one of the 'IconElement' attributes:
    INCLUDE(NAME="file_name" AND EXTENSION=".svg")
    EXCLUDE(NAME="file_name*")
    EXCLUDE(CONTAIN(PATH, "user"))

Matching is case sensitive.

'INCLUDE' acts as a filter in
'EXCLUDE' acts as a filter out

'EXCLUDE(NOT NAME="file_name.svg") will include the file_name.svg and
exclude all the others.
I'm not sure if this is the best approach, but i wrote it like this.

Todo:
    * Let the user define attributes of the theme element using some sort of rules
        For example:
        IF(CONTAIN(NAME, "icon")) THEN SET_ATTRIBUTE(NAME="stroke", COLOR="#ff0000")
"""

import pathlib
from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from st.core.model import IconElement
from st.utils.pretty_print import print_verbose


_STAR = object()
_ANY_CHAR = object()


class SyntaxError(ValueError):
    """Raised when a syntax error is encountered."""


class _TokenKind(Enum):
    """Dictionary of token kinds for st grammar."""

    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    CONTAIN = "CONTAIN"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EQUALS = "EQUALS"
    COMMA = "COMMA"
    WORD = "WORD"


_KEYWORDS = {
    "INCLUDE": _TokenKind.INCLUDE,
    "EXCLUDE": _TokenKind.EXCLUDE,
    "AND": _TokenKind.AND,
    "OR": _TokenKind.OR,
    "NOT": _TokenKind.NOT,
    "CONTAIN": _TokenKind.CONTAIN,
}


@dataclass(frozen=True)
class _Token:
    """Base token class for the grammar."""

    kind: _TokenKind
    value: str


def _tokenize(text: str) -> list[_Token]:
    """Split rules file text into a flat list of tokens.

    Args:
        text (str): The raw contents of a rules file.

    Returns:
        list[_Token]: The tokens found, in order.
    """
    tokens: list[_Token] = []
    index = 0
    length = len(text)

    while index < length:
        char = text[index]

        if char.isspace():  # This checks for both " ", "\t", "\n", "\r", "\v", and "\f"
            index += 1  # Skip whitespace characters
            continue

        if char == "(":
            tokens.append(_Token(_TokenKind.LPAREN, char))
            index += 1
            continue

        if char == ")":
            tokens.append(_Token(_TokenKind.RPAREN, char))
            index += 1
            continue

        if char == "=":
            tokens.append(_Token(_TokenKind.EQUALS, char))
            index += 1
            continue

        if char == ",":
            tokens.append(_Token(_TokenKind.COMMA, char))
            index += 1
            continue

        if char in ('"', "'"):
            quote = char
            # Find the matching closing quote
            # find() returns -1 if the substring is not found, or the index of the first
            # occurrence if an int is passed, we want to find the next occurrence after
            # the current index
            end = text.find(quote, index + 1)
            if end == -1:
                raise SyntaxError(
                    f"Unterminated quoted value starting at index {index}."
                )
            tokens.append(_Token(_TokenKind.WORD, text[index + 1 : end]))
            index = end + 1
            continue

        start = index
        while (
            index < length and not text[index].isspace() and text[index] not in "()=,"
        ):
            index += 1
        word = text[start:index]
        # TODO: not sure this is the best approach
        # what happen here is that everything that is not a keyword
        # is considered a keyword.
        # Maybe there is a clever way to handle this, but i can't think about it now
        # >^.^<
        keyword = _KEYWORDS.get(word.upper())
        if keyword is not None:
            tokens.append(_Token(keyword, word))
        else:
            tokens.append(_Token(_TokenKind.WORD, word))

    return tokens


def _parse_char_class(content: str) -> tuple[bool, frozenset[str]]:
    """Parse the inside of a [...] glob character class.

    Args:
        content (str): The text between the brackets. Exclude the brackets.

    Returns:
        tuple[bool, frozenset[str]]: Whether the class is negated (`!`/`^`
            prefix), and the set of characters it contains. `-` denotes an
            inclusive range, e.g. `a-z`.
    """
    # Check for negation at the start of the character class
    negate = content[:1] in ("!", "^")
    # If it is a negated class, start parsing from the next character
    index = 1 if negate else 0

    chars: set[str] = set()
    length = len(content)
    while index < length:
        if index + 2 < length and content[index + 1] == "-":
            for code_point in range(ord(content[index]), ord(content[index + 2]) + 1):
                chars.add(chr(code_point))
            index += 3
        else:
            chars.add(content[index])
            index += 1
    return negate, frozenset(chars)


def _compile_glob(pattern: str) -> list[object]:
    """Compile a glob pattern into a list of single-position matchers.

    Supported syntax:
        - `*`: Matches any sequence of characters (also none).
        - `?`: Matches any single character.
        - `[abc]`: Matches any single character in the set.
        - `[!abc]`: Matches any single character NOT in the set.

    Consecutive `*` are collapsed into one.

    Args:
        pattern (str): The glob pattern to compile.

    Returns:
        list[object]: The sequence of matchers tuple for a character class.
    """
    matchers: list[object] = []
    index = 0
    length = len(pattern)
    while index < length:
        char = pattern[index]
        if char == "*":
            if not matchers or matchers[-1] is not _STAR:
                matchers.append(_STAR)
            index += 1
        elif char == "?":
            matchers.append(_ANY_CHAR)
            index += 1
        elif char == "[":
            closing = pattern.find("]", index + 1)
            if closing == -1:
                matchers.append(char)
                index += 1
            else:
                matchers.append(_parse_char_class(pattern[index + 1 : closing]))
                index = closing + 1
        else:
            matchers.append(char)
            index += 1
    return matchers


def _matcher_matches(matcher: object, char: str) -> bool:
    """Check if a single-position matcher matches a character.

    Args:
        matcher (object): The matcher to check.
        char (str): The character to match against.

    Returns:
        bool: True if the matcher matches the character.
    """
    if matcher is _ANY_CHAR:
        return True
    if isinstance(matcher, tuple):
        negate, charset = matcher
        return (char in charset) != negate
    return matcher == char


def glob_match(text: str, pattern: str) -> bool:
    """Match a string against a glob pattern.

    Uses the standard greedy two-pointer wildcard-matching algorithm: on a
    mismatch, it backtracks to the most recent `*` and lets it consume one
    more character.

    Args:
        text (str): The string to match.
        pattern (str): The glob pattern (`*`, `?`, `[...]`) to match against.

    Returns:
        bool: True if the whole of `text` matches `pattern`.
    """
    matchers = _compile_glob(pattern)
    text_index = 0
    text_length = len(text)
    matcher_index = 0
    matcher_length = len(matchers)
    star_index = -1
    star_text_index = 0

    # This is the standard greedy two-pointer wildcard-matching algorithm
    # Not sure if this is the most efficient way to do this
    # but it works >^.^<
    while text_index < text_length:
        if matcher_index < matcher_length and matchers[matcher_index] is _STAR:
            star_index = matcher_index
            star_text_index = text_index
            matcher_index += 1
        elif matcher_index < matcher_length and _matcher_matches(
            matchers[matcher_index], text[text_index]
        ):
            matcher_index += 1
            text_index += 1
        elif star_index != -1:
            star_text_index += 1
            text_index = star_text_index
            matcher_index = star_index + 1
        else:
            return False

    while matcher_index < matcher_length and matchers[matcher_index] is _STAR:
        matcher_index += 1
    return matcher_index == matcher_length


# This dict maps attribute names to functions that retrieve the corresponding
# attribute from an IconElement. So if the IconElement should change in the future
# we only need to chanfe this dict here
_ATTRIBUTE_GETTERS: dict[str, Callable[[IconElement], str]] = {
    "NAME": lambda element: element.name,
    "EXTENSION": lambda element: element.extension,
    "PATH": lambda element: element.path.as_posix(),
}


class Expression(ABC):
    """Base class for nodes in a parsed rule's boolean expression tree."""

    @abstractmethod
    def matches(self, element: IconElement) -> bool:
        """Evaluate this expression against an icon element.

        Args:
            element (IconElement): The element to test.

        Returns:
            bool: True if the expression matches the given element.
        """


@dataclass(frozen=True)
class AttributeExpr(Expression):
    """Leaf expression: a glob pattern matched against one element attribute."""

    attribute: str
    pattern: str

    def matches(self, element: IconElement) -> bool:
        """See base class."""
        value = _ATTRIBUTE_GETTERS[self.attribute](element)
        return glob_match(value, self.pattern)


@dataclass(frozen=True)
class ContainExpr(Expression):
    """Leaf expression: True if an attribute's value contains a substring."""

    attribute: str
    substring: str

    def matches(self, element: IconElement) -> bool:
        """See base class."""
        value = _ATTRIBUTE_GETTERS[self.attribute](element)
        return self.substring in value


@dataclass(frozen=True)
class AndExpr(Expression):
    """Composite expression: both sub-expressions must match."""

    left: Expression
    right: Expression

    def matches(self, element: IconElement) -> bool:
        """See base class."""
        return self.left.matches(element) and self.right.matches(element)


@dataclass(frozen=True)
class OrExpr(Expression):
    """Composite expression: either sub-expression may match."""

    left: Expression
    right: Expression

    def matches(self, element: IconElement) -> bool:
        """See base class."""
        return self.left.matches(element) or self.right.matches(element)


@dataclass(frozen=True)
class NotExpr(Expression):
    """Composite expression: negates a sub-expression."""

    inner: Expression

    def matches(self, element: IconElement) -> bool:
        """See base class."""
        return not self.inner.matches(element)


@dataclass(frozen=True)
class Statement:
    """A single top-level `INCLUDE(...)` or `EXCLUDE(...)` statement."""

    kind: _TokenKind
    expression: Expression


class _Parser:
    """Recursive-descent parser for the rules grammar."""

    def __init__(self, tokens: list[_Token]):
        """Initialize the parser with a token stream."""
        self._tokens = tokens
        self._position = 0

    def _peek(self) -> _Token | None:
        """Return the next token in the stream without consuming it.

        Returns:
            _Token | None: The next token, or None if at the end of the stream
        """
        return (
            self._tokens[self._position] if self._position < len(self._tokens) else None
        )

    def _advance(self) -> _Token:
        """Consume and return the next token in the stream.

        Returns:
            _Token: The next token in the stream.

        Raises:
            SyntaxError: If the end of the stream is reached.
        """
        token = self._peek()
        if token is None:
            raise SyntaxError("Unexpected end of rules file.")
        self._position += 1
        return token

    def _expect(self, kind: _TokenKind) -> _Token:
        """Consume and return the next token if it matches the expected kind.

        Args:
            kind (_TokenKind): The expected token kind.

        Returns:
            _Token: The next token in the stream.

        Raises:
            SyntaxError: If the next token does not match the expected kind.
        """
        token = self._peek()
        if token is None or token.kind is not kind:
            found = token.value if token is not None else "end of input"
            raise SyntaxError(f"Expected {kind.value}, found {found!r}.")
        return self._advance()

    def parse_statements(self) -> list[Statement]:
        """Parse the full token stream into a list of statements.

        Returns:
            list[Statement]: The list of parsed statements.
        """
        statements = []
        while self._peek() is not None:
            statements.append(self._parse_statement())
        return statements

    def _parse_statement(self) -> Statement:
        """Parse a single statement.

        Returns:
            Statement: The parsed statement.

        Raises:
            SyntaxError: If the statement is invalid.
        """
        token = self._peek()
        if token is None or token.kind not in (_TokenKind.INCLUDE, _TokenKind.EXCLUDE):
            found = token.value if token is not None else "end of input"
            raise SyntaxError(f"Expected INCLUDE or EXCLUDE, found {found!r}.")
        kind = self._advance().kind
        self._expect(_TokenKind.LPAREN)
        expression = self._parse_or()
        self._expect(_TokenKind.RPAREN)
        return Statement(kind=kind, expression=expression)

    def _parse_or(self) -> Expression:
        """Parse an OR expression.

        Returns:
            Expression: The parsed OR expression.
        """
        left = self._parse_and()
        while self._peek() is not None and (self._peek().kind is _TokenKind.OR):
            self._advance()
            left = OrExpr(left, self._parse_and())
        return left

    def _parse_and(self) -> Expression:
        """Parse an AND expression.

        Returns:
            Expression: The parsed AND expression.
        """
        left = self._parse_not()
        while self._peek() is not None and self._peek().kind is _TokenKind.AND:
            self._advance()
            left = AndExpr(left, self._parse_not())
        return left

    def _parse_not(self) -> Expression:
        """Parse a NOT expression.

        Returns:
            Expression: The parsed NOT expression.
        """
        if self._peek() is not None and self._peek().kind is _TokenKind.NOT:
            self._advance()
            return NotExpr(self._parse_not())
        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        token = self._peek()
        if token is None:
            raise SyntaxError("Unexpected end of rules file.")
        if token.kind is _TokenKind.LPAREN:
            self._advance()
            expression = self._parse_or()
            self._expect(_TokenKind.RPAREN)
            return expression
        if token.kind is _TokenKind.CONTAIN:
            return self._parse_contain_expr()
        if token.kind is _TokenKind.WORD:
            return self._parse_attribute_expr()
        raise SyntaxError(f"Unexpected token {token.value!r}.")

    def _resolve_attribute(self, token: _Token) -> str:
        """Resolve an attribute token to its canonical name.

        Args:
            token (_Token): The token representing the attribute.

        Returns:
            str: The canonical attribute name.
        """
        attribute = token.value.upper()
        if attribute not in _ATTRIBUTE_GETTERS:
            supported = ", ".join(sorted(_ATTRIBUTE_GETTERS))
            raise SyntaxError(
                f"Unknown attribute {token.value!r}. Supported attributes: {supported}."
            )
        return attribute

    def _parse_attribute_expr(self) -> Expression:
        """Parse an ATTRIBUTE=value expression."""
        attribute_token = self._expect(_TokenKind.WORD)
        attribute = self._resolve_attribute(attribute_token)
        self._expect(_TokenKind.EQUALS)
        value_token = self._expect(_TokenKind.WORD)
        return AttributeExpr(attribute=attribute, pattern=value_token.value)

    def _parse_contain_expr(self) -> Expression:
        """Parse a CONTAIN(ATTRIBUTE, "substring") expression.

        Returns:
            Expression: The parsed CONTAIN expression.
        """
        self._expect(_TokenKind.CONTAIN)
        self._expect(_TokenKind.LPAREN)
        attribute_token = self._expect(_TokenKind.WORD)
        attribute = self._resolve_attribute(attribute_token)
        self._expect(_TokenKind.COMMA)
        substring_token = self._expect(_TokenKind.WORD)
        self._expect(_TokenKind.RPAREN)
        return ContainExpr(attribute=attribute, substring=substring_token.value)


class RuleSet:
    """A parsed collection of INCLUDE/EXCLUDE statements, ready for evaluation."""

    def __init__(self, statements: list[Statement]):
        """Initialize a RuleSet from already-parsed statements."""
        self._includes = [
            s.expression for s in statements if s.kind is _TokenKind.INCLUDE
        ]
        self._excludes = [
            s.expression for s in statements if s.kind is _TokenKind.EXCLUDE
        ]

    @classmethod
    def from_text(cls, text: str) -> "RuleSet":
        """Parse a RuleSet from rules-file text.

        Args:
            text (str): The raw contents of a rules file.

        Returns:
            RuleSet: The parsed rule set.
        """
        tokens = _tokenize(text)
        statements = _Parser(tokens).parse_statements()
        return cls(statements)

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "RuleSet":
        """Parse a RuleSet from a rules file on disk.

        Args:
            path (pathlib.Path): Path to the rules file.

        Returns:
            RuleSet: The parsed rule set.
        """
        return cls.from_text(pathlib.Path(path).read_text())

    def keep(self, element: IconElement) -> bool:
        """Filte elements.

        INCLUDE statement has priority on EXCLUDE statement.

        Args:
            element (IconElement): The element to test.

        Returns:
            bool: True if the element should be kept.

        Example:
            >>> # Keep only the element with name 'filename.svg', exclude all others
            >>> rule_set = RuleSet.from_text(
            ...     "INCLUDE(NAME='filename.svg') EXCLUDE(NAME='*')"
            ... )

        """
        matched_include = any(expr.matches(element) for expr in self._includes)
        matched_exclude = any(expr.matches(element) for expr in self._excludes)

        if self._includes and not self._excludes:
            return matched_include

        return matched_include or not matched_exclude


def filter_elements(
    elements: list[IconElement],
    rule_set: RuleSet,
) -> list[IconElement]:
    """Filter icon element list according to a rule set.

    Args:
        elements (list[IconElement]): The list of elements to filter.
        rule_set (RuleSet): The rule set to apply.

    Returns:
        list[IconElement]: The filtered list of elements.
    """
    kept = []
    for element in elements:
        if rule_set.keep(element):
            kept.append(element)
        else:
            print_verbose(f"Excluded by rules: {element.full_name}")
    return kept
