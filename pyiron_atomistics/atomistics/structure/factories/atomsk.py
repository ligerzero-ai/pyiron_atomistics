# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import io
import subprocess
import tempfile
import os.path

from pyiron_atomistics.atomistics.structure.atoms import ase_to_pyiron

from ase.io import read, write

class AtomskBuilder:

    def __init__(self):
        self._options = []
        self._structure = None

    @classmethod
    def create(cls, lattice, a, *species, c=None, hkl=None):
        """
        See https://atomsk.univ-lille.fr/doc/en/mode_create.html
        """

        self = cls()

        a_and_c = str(a) if c is None else f"{a} {c}"
        line = f"--create {lattice} {a_and_c} {' '.join(species)}"
        if hkl is not None:
            if len(hkl) != 3:
                raise ValueError(f"hkl must have exactly three entries, not {len(hkl)}!")
            if any(len(i) != 3 for i in hkl):
                raise ValueError(f"Every entry in hkl must have exactly three entries not {hkl}!")
            line += f" orient {' '.join(hkl[0])} {' '.join(hkl[1])} {' '.join(hkl[2])}"
        # TODO: check len(species) etc. with the document list of supported phases
        self._options.append(line)
        return self

    @classmethod
    def modify(cls, structure):
        self = cls()
        self._structure = structure
        self._options.append("input.exyz")
        return self

    def duplicate(self, nx, ny=None, nz=None):
        """
        See https://atomsk.univ-lille.fr/doc/en/option_duplicate.html
        """
        if ny is None: ny = nx
        if nz is None: nz = ny
        self._options.append(f"-duplicate {nx} {ny} {nz}")
        return self

    def orthogonal(self):
        """
        See https://atomsk.univ-lille.fr/doc/en/option_orthocell.html
        """
        self._options.append("-orthogonal-cell")
        return self

    def build(self):
        self._options.append("- exyz") # output to stdout as exyz format
        with tempfile.TemporaryDirectory() as temp_dir:
            if self._structure is not None:
                write(os.path.join(temp_dir, "input.exyz"), self._structure, format="extxyz")
            proc = subprocess.run(["atomsk", *" ".join(self._options).split()],
                                  capture_output=True, cwd=temp_dir)
            return ase_to_pyiron(read(io.StringIO(proc.stdout.decode("utf8")), format="extxyz"))

    def __getattr__(self, name):
        def meth(*args, **kwargs):
            args_str = " ".join(map(str, args))
            kwargs_str = " ".join(f"{k} {v}" for k, v in kwargs.items())
            self._options.append(f"-{name.replace('_', '-')} {args_str} {kwargs_str}")
            return self
        return meth

class AtomskFactory:
    """
    Wrapper around the atomsk CLI.

    Use :method:`.create()` to create a new structure and :method:`.modify()` to pass an existing structure to atomsk.
    Both of them return a :class:`.AtomskBuilder`, which has methods named like the flags of atomsk.  Calling them with
    the appropriate arguments adds the flags to the command line.  Once you added all flags, call
    :method:`.AtomskBuilder.build()` to create the new structure.

    >>> from pyiron_atomistics import Project
    >>> pr = Project('atomsk')
    >>> pr.create.structure.atomsk.create("fcc", 3.6, "Cu").duplicate(2).build()
    Cu: [0. 0. 0.]
    Cu: [1.8 1.8 0. ]
    Cu: [0.  1.8 1.8]
    Cu: [1.8 0.  1.8]
    Cu: [3.6 0.  0. ]
    Cu: [5.4 1.8 0. ]
    Cu: [3.6 1.8 1.8]
    Cu: [5.4 0.  1.8]
    pbc: [ True  True  True]
    cell: 
    Cell([7.2, 3.6, 3.6])
    >>> s = pr.create.structure.atomsk.create("fcc", 3.6, "Cu").duplicate(2).build()
    >>> pr.create.structure.atomsk.modify(s).cell("add", 3, "x").build()
    Cu: [0. 0. 0.]
    Cu: [1.8 1.8 0. ]
    Cu: [0.  1.8 1.8]
    Cu: [1.8 0.  1.8]
    Cu: [3.6 0.  0. ]
    Cu: [5.4 1.8 0. ]
    Cu: [3.6 1.8 1.8]
    Cu: [5.4 0.  1.8]
    pbc: [ True  True  True]
    cell: 
    Cell([10.2, 3.6, 3.6])
    """

    def create(self, lattice, a, *species, c=None, hkl=None):
        return AtomskBuilder.create(lattice, a, *species, c=c, hkl=hkl)

    def modify(self, structure):
        return AtomskBuilder.modify(structure)
