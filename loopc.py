#! /usr/bin/python

import re
import sys
import collections

def LexemeGenerator(text):
    LEXEME = ['WHILE', 'LOOP', 'DO',  'END', ':=', '!=']
    operator_re = re.compile('\+|-')
    ident_re = re.compile('x\d+')
    func_re = re.compile('\w+')
    num_re = re.compile('\d+')

    for (lno, line) in enumerate(text.splitlines(), start = 1):
        for (wno, word) in enumerate(line.split(), start = 1):
            semicolon = False
            if word.endswith(';'):
                semicolon = True
                word = word.strip(';')

            ret = ((lno, wno), word)
            if word in LEXEME: yield (word, ret)
            elif operator_re.match(word): yield ('OP', ret)
            elif ident_re.match(word): yield ('IDENT', ret)
            elif num_re.match(word): yield ('NUM', ret)
            elif func_re.match(word): yield ('FUNC', ret)
            else: raise ValueError('Unknown Symbol: ' + word)
            if semicolon: yield (';', ((lno, wno+1), ';'))
    yield (None, ((None, None), None))

Loop = collections.namedtuple('Loop', 'var type body')
Call = collections.namedtuple('Call', 'name parameter')
Assignment = collections.namedtuple('Assignment', 'lval body')
Function = collections.namedtuple('Function', 'name parameter body')
Expression = collections.namedtuple('Expression', 'left operator right')

class SyntaxAnalysis:
    def __init__(self, generator):
        self.generator = generator
        self.pos = (0, 0)
        self.symbol = self.word = ''
        self.next()

    def next(self):
        word = self.word
        (self.symbol, (self.pos, self.word)) = next(self.generator)
        return word

    def expect(self, symbol, next_symbol = False):
        tmpl = 'Expected {0}, was {1} (at line {2[0]}, word {2[1]})'
        if self.symbol != symbol:
            raise ValueError(tmpl.format(symbol, self.symbol, self.pos))
        elif next_symbol: return self.next()

    def parse_program(self):
        while self.symbol == 'FUNC':
            function = Function(self.next(), list(), list())
            while self.symbol == 'IDENT':
                function.parameter.append(self.next())
            self.expect('DO', True)
            function.body.extend(self.parse_statements())
            self.expect('END', True)
            yield function
        self.expect(None)

    def parse_statements(self):
        while True:
            if self.symbol in ('LOOP', 'WHILE'): yield self.parse_loop()
            else: yield self.parse_statement()
            if self.symbol == ';': self.next()
            else: break

    def parse_loop(self):
        ltype = self.next()
        loop = Loop(self.expect('IDENT', True), ltype, list())
        if ltype == 'WHILE':
            self.expect('!=', True)
            self.expect('NUM', True)
        self.expect('DO', True)
        loop.body.extend(self.parse_statements())
        self.expect('END', True)
        return loop

    def parse_statement(self):
        lval = self.expect('IDENT', True)
        self.expect(':=', True)
        if self.symbol == 'FUNC':
            body = Call(self.next(), list())
            while self.symbol == 'IDENT':
                body.parameter.append(self.next())
        else:
            body = Expression(self.expect('IDENT', True),
                              self.expect('OP', True),
                              self.expect('NUM', True))
        return Assignment(lval, body)

class Synthesis:
    INDENT = '    '
    DATA = 'class Data:\n' \
        + INDENT + 'def __getattr__(self, name):\n' \
        + INDENT + INDENT + 'if not name in self.__dict__:\n' \
        + INDENT + INDENT + INDENT + 'self.__dict__[name] = 0\n' \
        + INDENT + INDENT + 'return self.__dict__.get(name, 0)\n\n' \
        + INDENT + 'def plus(self, a, b): return a + b\n' \
        + INDENT + 'def minus(self, a, b): return 0 if b > a else a - b\n\n'

    def __init__(self, program):
        self.program = program

    def generate(self):
        return self.DATA + '\n'.join(self.functions())

    def functions(self):
        tmpl1 = 'def {}({}):'
        tmpl2 = self.INDENT + 'data.{0} = {0}'
        for function in self.program:
            yield tmpl1.format(function.name, ', '.join(function.parameter))
            yield self.INDENT + 'data = Data()'
            for par in function.parameter: yield tmpl2.format(par)
            for stat in self.statements(function.body): yield self.INDENT + stat
            yield self.INDENT + 'return data.x0\n'

    def statements(self, body):
        for stat in body:
            if hasattr(stat, 'type'):
                for l in self.loop(stat): yield l
            else:
                for a in self.assignment(stat): yield a

    def assignment(self, stat):
        tmpl = 'data.{} = {}'
        if hasattr(stat.body, 'operator'):
            yield tmpl.format(stat.lval, self.expression(stat.body))
        else:
            yield tmpl.format(stat.lval, self.call(stat.body))

    def expression(self, body):
        tmpl = 'data.{}(data.{}, {})'
        if body.operator == '+':
            return tmpl.format('plus', body.left, body.right)
        else:
            return tmpl.format('minus', body.left, body.right)

    def call(self, body):
        tmpl = '{}({})'
        param = ', '.join('data.' + x for x in body.parameter)
        return tmpl.format(body.name, param)

    def loop(self, stat):
        tmpl_loop = 'for _ in range(data.{}):'
        tmpl_while = 'while data.{}:'
        if stat.type == 'LOOP': yield tmpl_loop.format(stat.var)
        else: yield tmpl_while.format(stat.var)
        for statb in self.statements(stat.body): yield self.INDENT + statb

def main():
    if len(sys.argv) == 1:
        print('Usage: {} path/to/loop/program'.format(sys.argv[0]))
    else:
        with open(sys.argv[1], 'r') as fob:
            generator = LexemeGenerator(fob.read())
            analysis = SyntaxAnalysis(generator)
            program = analysis.parse_program()
            code = Synthesis(program)
            print(code.generate())

if __name__ == '__main__':
    try: main()
    except Exception as e: print(e)
