# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from aimsgb import GrainBoundary, Grain, GBInformation
from ase.build import bulk
from ase.build import (
        add_adsorbate,
        add_vacuum,
        bcc100,
        bcc110,
        bcc111,
        diamond100,
        diamond111,
        fcc100,
        fcc110,
        fcc111,
        fcc211,
        hcp0001,
        hcp10m10,
        mx2,
        hcp0001_root,
        fcc111_root,
        bcc111_root,
        root_surface,
        root_surface_analysis,
        surface as ase_surf,
        cut as ase_cut,
        stack as ase_stack
    )
from ase.spacegroup import crystal as ase_crystal
from ase.io import read
import numpy as np
from pymatgen import Structure, Lattice, PeriodicSite
from pyiron_atomistics.atomistics.structure.pyironase import publication as publication_ase
from pyiron_atomistics.atomistics.structure.atoms import CrystalStructure, ase_to_pyiron, pyiron_to_pymatgen, pymatgen_to_pyiron, Atoms
from pyiron_atomistics.atomistics.structure.periodic_table import PeriodicTable
from pyiron_base import Settings, PyironFactory
import types
from functools import wraps

__author__ = "Sudarsan Surendralal"
__copyright__ = (
    "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "1.0"
__maintainer__ = "Sudarsan Surendralal"
__email__ = "surendralal@mpie.de"
__status__ = "production"
__date__ = "May 1, 2020"

s = Settings()


class AseFactory:
    @wraps(ase_cut)
    def cut(self, *args, **kwargs):
        """
        Returns an ASE's cut result, wrapped as a `pyiron_atomistics.atomstic.structure.atoms.Atoms` object.

        ase.build.cut docstring:

        """
        s.publication_add(publication_ase())
        return ase_to_pyiron(ase_cut(*args, **kwargs))

    @wraps(ase_stack)
    def stack(self, *args, **kwargs):
        """
        Returns an ASE's stack result, wrapped as a `pyiron_atomistics.atomstic.structure.atoms.Atoms` object.

        ase.build.stack docstring:

        """
        s.publication_add(publication_ase())
        return ase_to_pyiron(ase_stack(*args, **kwargs))

    @wraps(ase_crystal)
    def crystal(self, *args, **kwargs):
        """
        Returns an ASE's crystal result, wrapped as a `pyiron_atomistics.atomstic.structure.atoms.Atoms` object.

        ase.spacegroup.crystal docstring:

        """
        s.publication_add(publication_ase())
        return ase_to_pyiron(ase_crystal(*args, **kwargs))


class StructureFactory(PyironFactory):
    def __init__(self):
        self.ase = AseFactory()

    def cut(self, *args, **kwargs):
        return self.ase.cut(*args, **kwargs)
    cut.__doc__ = AseFactory.cut.__doc__

    def stack(self, *args, **kwargs):
        return self.ase.stack(*args, **kwargs)
    stack.__doc__ = AseFactory.stack.__doc__

    def ase_read(self, *args, **kwargs):
        """
        Returns a ASE's read result, wrapped as a `pyiron_atomistics.atomstic.structure.atoms.Atoms` object.

        ase.io.read docstring:
        """
        return ase_to_pyiron(read(*args, **kwargs))
    ase_read.__doc__ += read.__doc__

    @staticmethod
    def surface(
        element, surface_type, size=(1, 1, 1), vacuum=1.0, center=False, pbc=True, **kwargs
    ):
        """
        Generate a surface based on the ase.build.surface module.

        Args:
            element (str): Element name
            surface_type (str): The string specifying the surface type generators available through ase (fcc111,
            hcp0001 etc.)
            size (tuple): Size of the surface
            vacuum (float): Length of vacuum layer added to the surface along the z direction
            center (bool): Tells if the surface layers have to be at the center or at one end along the z-direction
            pbc (list/numpy.ndarray): List of booleans specifying the periodic boundary conditions along all three
                                      directions.
            **kwargs: Additional, arguments you would normally pass to the structure generator like 'a', 'b',
            'orthogonal' etc.

        Returns:
            pyiron_atomistics.atomistics.structure.atoms.Atoms instance: Required surface

        """
        # https://gitlab.com/ase/ase/blob/master/ase/lattice/surface.py
        if pbc is None:
            pbc = True
        s.publication_add(publication_ase())
        for surface_class in [
            add_adsorbate,
            add_vacuum,
            bcc100,
            bcc110,
            bcc111,
            diamond100,
            diamond111,
            fcc100,
            fcc110,
            fcc111,
            fcc211,
            hcp0001,
            hcp10m10,
            mx2,
            hcp0001_root,
            fcc111_root,
            bcc111_root,
            root_surface,
            root_surface_analysis,
            ase_surf,
        ]:
            if surface_type == surface_class.__name__:
                surface_type = surface_class
                break
        if isinstance(surface_type, types.FunctionType):
            if center:
                surface = surface_type(
                    symbol=element, size=size, vacuum=vacuum, **kwargs
                )
            else:
                surface = surface_type(symbol=element, size=size, **kwargs)
                z_max = np.max(surface.positions[:, 2])
                surface.cell[2, 2] = z_max + vacuum
            surface.pbc = pbc
            return ase_to_pyiron(surface)
        else:
            return None

    @staticmethod
    def surface_hkl(lattice, hkl, layers, vacuum=1.0, center=False, pbc=True):
        """
        Use ase.build.surface to build a surface with surface normal (hkl).

        Args:
            lattice (pyiron_atomistics.atomistics.structure.atoms.Atoms/str): bulk Atoms
                instance or str, e.g. "Fe", from which to build the surface
            hkl (list): miller indices of surface to be created
            layers (int): # of atomic layers in the surface
            vacuum (float): vacuum spacing
            center (bool): shift all positions to center the surface
                in the cell

        Returns:
            pyiron_atomistics.atomistics.structure.atoms.Atoms instance: Required surface
        """
        # https://gitlab.com/ase/ase/blob/master/ase/lattice/surface.py
        s.publication_add(publication_ase())

        surface = ase_surf(lattice, hkl, layers)
        z_max = np.max(surface.positions[:, 2])
        surface.cell[2, 2] = z_max + vacuum
        if center:
            surface.positions += 0.5 * surface.cell[2] - [0, 0, z_max/2]
        surface.pbc = pbc
        return ase_to_pyiron(surface)

    @staticmethod
    def crystal(element, bravais_basis, lattice_constant):
        """
        Create a crystal structure using pyiron's native crystal structure generator

        Args:
            element (str): Element name
            bravais_basis (str): Basis type
            lattice_constant (float/list): Lattice constants

        Returns:
            pyiron.atomistics.structure.atoms.Atoms: The required crystal structure
        """
        return CrystalStructure(
            element=element,
            bravais_basis=bravais_basis,
            lattice_constants=[lattice_constant],
        )

    @staticmethod
    def ase_bulk(
        name,
        crystalstructure=None,
        a=None,
        c=None,
        covera=None,
        u=None,
        orthorhombic=False,
        cubic=False,
    ):
        """
        Creating bulk systems using ASE bulk module. Crystal structure and lattice constant(s) will be guessed if not
        provided.

        name (str): Chemical symbol or symbols as in 'MgO' or 'NaCl'.
        crystalstructure (str): Must be one of sc, fcc, bcc, hcp, diamond, zincblende,
                                rocksalt, cesiumchloride, fluorite or wurtzite.
        a (float): Lattice constant.
        c (float): Lattice constant.
        c_over_a (float): c/a ratio used for hcp.  Default is ideal ratio: sqrt(8/3).
        u (float): Internal coordinate for Wurtzite structure.
        orthorhombic (bool): Construct orthorhombic unit cell instead of primitive cell which is the default.
        cubic (bool): Construct cubic unit cell if possible.

        Returns:
            pyiron.atomistics.structure.atoms.Atoms: Required bulk structure
        """
        s.publication_add(publication_ase())
        return ase_to_pyiron(bulk(
            name=name,
            crystalstructure=crystalstructure,
            a=a,
            c=c,
            covera=covera,
            u=u,
            orthorhombic=orthorhombic,
            cubic=cubic,
        ))

    @staticmethod
    def atoms(
            symbols=None,
            positions=None,
            numbers=None,
            tags=None,
            momenta=None,
            masses=None,
            magmoms=None,
            charges=None,
            scaled_positions=None,
            cell=None,
            pbc=None,
            celldisp=None,
            constraint=None,
            calculator=None,
            info=None,
            indices=None,
            elements=None,
            dimension=None,
            species=None,
            **qwargs
    ):
        """
        Creates a atomistics.structure.atoms.Atoms instance.

        Args:
            elements (list/numpy.ndarray): List of strings containing the elements or a list of
                                atomistics.structure.periodic_table.ChemicalElement instances
            numbers (list/numpy.ndarray): List of atomic numbers of elements
            symbols (list/numpy.ndarray): List of chemical symbols
            positions (list/numpy.ndarray): List of positions
            scaled_positions (list/numpy.ndarray): List of scaled positions (relative coordinates)
            pbc (boolean): Tells if periodic boundary conditions should be applied
            cell (list/numpy.ndarray): A 3x3 array representing the lattice vectors of the structure
            momenta (list/numpy.ndarray): List of momentum values
            tags (list/numpy.ndarray): A list of tags
            masses (list/numpy.ndarray): A list of masses
            magmoms (list/numpy.ndarray): A list of magnetic moments
            charges (list/numpy.ndarray): A list of point charges
            celldisp:
            constraint (list/numpy.ndarray): A list of constraints
            calculator: ASE calculator
            info (list/str): ASE compatibility
            indices (list/numpy.ndarray): The list of species indices
            dimension (int): Dimension of the structure
            species (list): List of species

        Returns:
            pyiron.atomistics.structure.atoms.Atoms: The required structure instance
        """
        if pbc is None:
            pbc = True
        return Atoms(
            symbols=symbols,
            positions=positions,
            numbers=numbers,
            tags=tags,
            momenta=momenta,
            masses=masses,
            magmoms=magmoms,
            charges=charges,
            scaled_positions=scaled_positions,
            cell=cell,
            pbc=pbc,
            celldisp=celldisp,
            constraint=constraint,
            calculator=calculator,
            info=info,
            indices=indices,
            elements=elements,
            dimension=dimension,
            species=species,
            **qwargs
        )

    @staticmethod
    def element(parent_element, new_element_name=None, spin=None, potential_file=None):
        """

        Args:
            parent_element (str, int): The parent element eq. "N", "O", "Mg" etc.
            new_element_name (str): The name of the new parent element (can be arbitrary)
            spin (float): Value of the magnetic moment (with sign)
            potential_file (str): Location of the new potential file if necessary

        Returns:
            atomistics.structure.periodic_table.ChemicalElement instance
        """
        periodic_table = PeriodicTable()
        if new_element_name is None:
            if spin is not None:
                new_element_name = (
                        parent_element + "_spin_" + str(spin).replace(".", "_")
                )
            else:
                new_element_name = parent_element + "_1"
        if potential_file is not None:
            if spin is not None:
                periodic_table.add_element(
                    parent_element=parent_element,
                    new_element=new_element_name,
                    spin=str(spin),
                    pseudo_potcar_file=potential_file,
                )
            else:
                periodic_table.add_element(
                    parent_element=parent_element,
                    new_element=new_element_name,
                    pseudo_potcar_file=potential_file,
                )
        elif spin is not None:
            periodic_table.add_element(
                parent_element=parent_element,
                new_element=new_element_name,
                spin=str(spin),
            )
        else:
            periodic_table.add_element(
                parent_element=parent_element, new_element=new_element_name
            )
        return periodic_table.element(new_element_name)

    @staticmethod
    def aimsgb_info(axis, max_sigma):
        """
        Provides a list of possible GB structures for a given rotational axis and upto the given maximum sigma value.

        Args:
            axis : Rotational axis for the GB you want to construct (for example, axis=[1,0,0])
            max_sigma (int) : The maximum value of sigma upto which you want to consider for your
            GB (for example, sigma=5)

        Returns:
            A list of possible GB structures in the format:

            {sigma value: {'theta': [theta value],
                'plane': the GB planes")
                'rot_matrix': array([the rotational matrix]),
                'csl': [array([the csl matrix])]}}

        To construct the grain boundary select a GB plane and sigma value from the list and pass it to the
        GBBuilder.gb_build() function along with the rotational axis and initial bulk structure.
        """
        return GBInformation(axis=axis, max_sigma=max_sigma)

    @staticmethod
    def aimsgb_build(axis, sigma, plane, initial_struct, to_primitive=False,
                 delete_layer='0b0t0b0t', add_if_dist=0.0):
        """
        Generate a grain boundary structure based on the aimsgb.GrainBoundary module.

        Args:
            axis : Rotational axis for the GB you want to construct (for example, axis=[1,0,0])
            sigma (int) : The sigma value of the GB you want to construct (for example, sigma=5)
            plane: The grain boundary plane of the GB you want to construct (for example, plane=[2,1,0])
            initial_struct : Initial bulk structure from which you want to construct the GB (a pyiron
                            structure object).
            delete_layer : To delete layers of the GB. For example, delete_layer='1b0t1b0t'. The first
                           4 characters is for first grain and the other 4 is for second grain. b means
                           bottom layer and t means top layer. Integer represents the number of layers
                           to be deleted. The first t and second b from the left hand side represents
                           the layers at the GB interface. Default value is delete_layer='0b0t0b0t', which
                           means no deletion of layers.
            add_if_dist : If you want to add extra interface distance, you can specify add_if_dist.
                           Default value is add_if_dist=0.0
            to_primitive : To generate primitive or non-primitive GB structure. Default value is
                            to_primitive=False

        Returns:
            :class:`.Atoms`: final grain boundary structure
        """
        basis_pymatgen = pyiron_to_pymatgen(initial_struct)
        grain_init = Grain(basis_pymatgen.lattice, basis_pymatgen.species, basis_pymatgen.frac_coords)
        gb_obj = GrainBoundary(axis=axis, sigma=sigma, plane=plane, initial_struct=grain_init)

        return pymatgen_to_pyiron(gb_obj.build_gb(to_primitive=to_primitive, delete_layer=delete_layer,
                                                  add_if_dist=add_if_dist))
