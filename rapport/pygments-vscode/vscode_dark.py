"""Pygments style with the colours of the VS Code "Dark+" theme, used by minted in the report.

Registered through vscode_dark-1.0.dist-info/entry_points.txt: latexmkrc adds this folder
to PYTHONPATH, so pygmentize finds the style "vscode" without installing anything.
"""
from pygments.style import Style
from pygments.token import (Comment, Error, Generic, Keyword, Literal, Name, Number,
                            Operator, Punctuation, String, Text, Token)


class VSCodeDarkStyle(Style):
    name = "vscode"
    background_color = "#1e1e1e"
    highlight_color = "#264f78"

    styles = {
        Token: "#d4d4d4",
        Text: "#d4d4d4",
        Comment: "#6a9955",
        Comment.Preproc: "#c586c0",
        Comment.Hashbang: "#6a9955",
        Keyword: "#569cd6",
        Keyword.Constant: "#569cd6",
        Keyword.Type: "#4ec9b0",
        Keyword.Namespace: "#c586c0",
        Operator: "#d4d4d4",
        Operator.Word: "#569cd6",
        Punctuation: "#d4d4d4",
        Name: "#d4d4d4",
        Name.Builtin: "#dcdcaa",
        Name.Function: "#dcdcaa",
        Name.Class: "#4ec9b0",
        Name.Variable: "#9cdcfe",
        Name.Attribute: "#9cdcfe",
        Name.Tag: "#569cd6",          # YAML keys
        Name.Constant: "#4fc1ff",
        Name.Label: "#c8c8c8",
        String: "#ce9178",
        String.Escape: "#d7ba7d",
        String.Interpol: "#9cdcfe",
        Literal: "#ce9178",
        Literal.Scalar.Plain: "#ce9178",  # YAML values
        Number: "#b5cea8",
        Generic.Heading: "#569cd6",
        Generic.Subheading: "#569cd6",
        Generic.Deleted: "#ce9178",
        Generic.Inserted: "#b5cea8",
        Generic.Emph: "italic",
        Generic.Strong: "bold",
        Error: "#f44747",
    }
