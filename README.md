loopc.py
========

An experimental LOOP/WHILE-to-Python-Compiler in Python3.

Syntax
------

- Everything is inside a function
- Functions end with END

See `example.loop` and the following links for more information.

- http://de.wikipedia.org/wiki/LOOP-Programm
- http://en.wikipedia.org/wiki/LOOP_(programming_language)
- http://de.wikipedia.org/wiki/WHILE-Programm

Usage
-----
    loopc ➤ ./loopc.py example.loop > example.py
    loopc ➤ python -i example.py
    >>> add(4, 5)
    9
    >>> mult(4, 5)
    20
    >>> fac(3)
