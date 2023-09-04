# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class Geography(metaclass=ABCMeta):
    """Geographical information about a field or data unit"""

    @abstractmethod
    def latitudes(self, dtype=None):
        r"""Return the latitudes.

        Parameters
        ----------
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def longitudes(self, dtype=None):
        r"""Return the longitudes.

        Parameters
        ----------
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def x(self, dtype=None):
        r"""Return the x coordinates in the original CRS.

        Parameters
        ----------
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def y(self, dtype=None):
        r"""Return the y coordinates in the original CRS.

        Parameters
        ----------
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
        """
        pass

    @property
    @abstractmethod
    def shape(self):
        r"""Return the shape of the grid or data values.

        Returns
        -------
        tuple
        """
        pass

    @abstractmethod
    def _unique_grid_id(self):
        r"""Return a unique id of the grid of a field."""
        pass

    @abstractmethod
    def projection(self):
        r"""Return information about projection.

        Returns
        -------
        :obj:`Projection`
        """
        pass

    @abstractmethod
    def bounding_box(self):
        r"""Return the bounding box.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        pass

    @abstractmethod
    def gridspec(self):
        r"""Return the grid specification.

        Returns
        -------
        :class:`~data.core.gridspec.GridSpec>`
        """
        pass
