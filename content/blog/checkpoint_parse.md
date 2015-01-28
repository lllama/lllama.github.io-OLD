Title: Parsing Checkpoint files
Date: 2013-05-16
kind: article
status: draft
---

# Parsing CheckPoint config files

Firewall reviews are something that has changed over the years. Reviews used to
be simple enough: check that the rulebase followed a certain pattern (VPN
rules, noisy rules, stealth rules, site specific rules, then a drop all rule
that logged everything), and could be done be hand well enough. The reviews
could be done manually, mainly because clients only had one firewall.

Things then started to get more complicated; the number of firewalls increased,
as did the number of rules. Clients started using different vendors, and each
vendor had a different config file and management interface.

So testers started to automate things, and a variety of tools appeared. These
are, by in large, rubbish. At least rubbish from a testers point of view.
Testers need tools that run tests that they can understand (or dig into code to
understand), and produce results in a format that can be included in their
company's own reporting format. Most tools fail at this in one way or another,
either the output is not in the right format, the tool will not read the input
you have, or the tests run are not good enough or comprehensive enough.

As preparation for a separate project I decided that I should learn to use
a 'proper' parsing library. I will admit to not knowing enough about parsers to
know whether I should use top-down, bottom-up, recursive-decent, peg, or any of
the other things listed on Wikipedia. But I use Python, and Python has
[PLY](http://www.dabeaz.com/ply/).

Parsing with PLY is split into two parts: lexing and parsing. The lexing part
will chop the input up into tokens and the parsing will consume the tokens and
turn them into something useful. The lexing/tokenising of the input is done
using regular expressions. The following code will tokenise a Checkpoint config
file (either `objects_5_0.C`, or `rulebases_5_0.fws`).

    import ply.lex as lex

    tokens = [
    "WORD",
    "QUOTED_WORD",
    "GROUP_START",
    "GROUP_END",
    "COLON",
    ]

    t_WORD = r'[-_a-zA-Z0-9.@]+'
    t_QUOTED_WORD = r'"[-0-9A-Za-z !#$%&\'()*+,./:;<=>?@^_`{|}~[\]\\]+"'
    t_GROUP_START = r'\('
    t_GROUP_END = r'\)'
    t_COLON = r':'
    t_ignore = ' \t\n'

    def t_error(t):
        pass

    lexer = lex.lex()

    DATA = open(r"objects_5_0.C", encoding="windows-1252").read()
    lexer.input(DATA)

    while True:
        tok = lexer.token()
        if not tok: break
        print(tok)

The code will print out the various tokens from the input file. Checkpoint
files are have syntax similar to the following:

    (
        :anyobj (Any
            :color (Blue)
        )
        :superanyobj (
            : (Any
                :color (Blue)
            )
        )
    )

The whole file is enclosed in a pair of parenthesis. Stanzas have a name, which
will start with a colon and can be empty (i.e. just a colon). Stanzas can then
contain lists of other stanzas. The lexer needs definitions for the various
tokens that make up the file. `t_GROUP_START` and `t_GROUP_END` should be simple
enough to understand. `t_ignore` is a special directive that the lexer will use
to skip over the unimportant parts. We do not care about whitespace, so we
ignore all of it. `t_WORD` is used for stanzas with simple names.
`t_QUOTED_WORD` is used when the names are more complicated and require
quoting. Colons can have special meaning, and so we define a token for when we
need to express that meaning.

Note that all of our tokens have been defined as simple regular expressions.
PLY does allow tokens to defined as functions. These allow you to do type
conversions or similar, or to record some state in the lexer object. The docs
provide some examples, but we don't need to use them here.

The next step is write the parser.

    import ply.yacc as yacc

    def p_config(p):
        'config : GROUP_START rulelist GROUP_END'
        p[0] = p[2]

    def p_rulelist(p):
        '''rulelist :
        | rulelist rule'''
        if(len(p) < 3):
            p[0] = ('RULELIST', [])
        else:
            p[1][1].append(p[2])
            p[0] = p[1]

    def p_rule_with_desc(p):
        '''rule : desc name GROUP_START rulelist GROUP_END'''
        p[0] = ("Named rulelist with description", (p[1], p[2], p[4]))

    def p_rule_with_name(p):
        '''rule : name GROUP_START rulelist GROUP_END'''
        p[0] = ("Named rulelist", (p[1], p[3]))

    def p_rule_just_desc(p):
        '''rule : desc'''
        p[0] = ("Description", p[1])

    def p_name(p):
        '''name : COLON WORD'''
        p[0] = ("Name", p[1]+p[2])

    def p_quoted_name(p):
        '''name : COLON QUOTED_WORD'''
        p[0] = ("Quoted Name", p[1]+p[2])

    def p_empty_name(p):
        '''name : COLON'''
        p[0] = ("Empty Name", p[1])

    def p_desc(p):
        '''desc : WORD
                | QUOTED_WORD'''
        p[0] = ("Descriptor", p[1])

    def p_error(p):
        print("Syntax error at '%s'" % p)

    parser = yacc.yacc()

Here we define the various rules that make up the parser. Given that the config
can be described as a set of rules that consist of tokens I believe that makes
the config syntax a context-free language.

The first definition defines the whole config. The config is a `GROUP_START`
token, a `rulelist`, and then a `GROUP_END`. Tokens are specified in all-caps,
other rules are defined as lowercase elements. The next definition
(`p_rulelist`) states that a `rulelist` consists of either nothing (important
this part, otherwise you could get trapped in a loop), or a `rulelist` and
a `rule`. Rules can take various forms, which we describe with the other
definitions. In each definition we set `p[0]` to be a tuple containing what we
found, plus the important parts from the config. The `p` object is provided by
the parser. The various elements that make up the object are set to the parts
that make up the definition. The code below shows how one of the rule
definitions causes the `p` object to be populated.

        '''rule : desc name GROUP_START rulelist GROUP_END'''
           p[0]   p[1] p[2] p[3]        p[4]     p[5]
