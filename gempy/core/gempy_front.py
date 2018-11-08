"""
    This file is part of gempy.

    gempy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Foobar is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with gempy.  If not, see <http://www.gnu.org/licenses/>.


    Created on 10/10 /2018

    @author: Miguel de la Varga
"""

from os import path
import sys

# This is for sphenix to find the packages
sys.path.append(path.dirname( path.dirname( path.abspath(__file__) ) ) )

import numpy as _np
from numpy import ndarray
from pandas import DataFrame
from gempy.core.model import *
from typing import Union
from gempy.utils.meta import _setdoc

# This warning comes from numpy complaining about a theano optimization
warnings.filterwarnings("ignore",
                        message='.* a non-tuple sequence for multidimensional indexing is deprecated; use*.',
                        append=True)


# region Model
@_setdoc(Model.__doc__)
def create_model(project_name='default_project'):
    """
    Create Model Object


    Returns:
        Model
    """

    return Model(project_name)


@_setdoc(Model.save_model.__doc__)
def save_model(model: Model, path=None):

    model.save_model(path)
    return True


@_setdoc(Model.load_model.__doc__)
def load_model(path):
    """
    Read InputData object from python pickle.

    Args:
       path (str): path where save the pickle

    Returns:
        :class:`gempy.data_management.InputData`

    """
    return Model.load_model(path)
# endregion


# region Series functionality
@_setdoc(Series.__doc__)
def create_series(series_distribution=None, order=None):
    return Series(series_distribution=series_distribution, order=order)


def set_series(model: Model, series_distribution, order_series=None, order_formations=None,
               values_to_default=True, verbose=0):
    """
    Function to set in place the different series of the project with their correspondent formations

    Args:
        model (:class:`gempy.core.model.Model`)
        series_distribution (dict or :class:`DataFrame`): with the name of the series as key and the name of the
          formations as values.
        order_series(Optional[list]): only necessary if passed a dict (python < 3.6)order of the series by default takes the
             dictionary keys which until python 3.6 are random. This is important to set the erosion relations between the different series
        order_formations(Optional[list]): only necessary if passed a dict (python < 3.6)order of the series by default takes the
            dictionary keys which until python 3.6 are random. This is important to set the erosion relations between the different series
        values_to_default (bool): If true set values to default
            - Interfaces and orientations: From csv files and prepare structure to GemPy's
            - Formations :class:`gempy.core.data.Formations`: Using formations read in the csv file
            - Series :class:`gempy.core.data.Series`: Using formations read in the csv file
            - Faults :class:`gempy.core.data.Faults`: Using formations read in the csv file. If fault string is contained in
              the name
        verbose(int): if verbose is True plot the sequential pile
    """

    model.series.set_series_categories(series_distribution, order=order_series)
    if values_to_default is True:
        warnings.warn("values_to_default option will get deprecated in the next version of gempy. It still exist only "
                      "to keep the behaviour equal to older version. See set_values_to_default.", FutureWarning)

        set_values_to_default(model, order_formations=None, set_faults=True,
                              map_formations_from_series=True, call_map_to_data=True)

    update_additional_data(model)

    if verbose > 0:
        return get_sequential_pile(model)
    else:
        return True


def select_series(geo_data, series):
    """
    Return the formations of a given serie in string

    Args:
        geo_data (:class:`gempy.data_management.InputData`)
        series(list of int or list of str): Subset of series to be selected

    Returns:
         :class:`gempy.data_management.InputData`: New object only containing the selected series
    """
    import copy
    new_geo_data = copy.deepcopy(geo_data)

    if type(series) == int or type(series[0]) == int:
        new_geo_data.interfaces = geo_data.interfaces[geo_data.interfaces['order_series'].isin(series)]
        new_geo_data.orientations = geo_data.orientations[geo_data.orientations['order_series'].isin(series)]
    elif type(series[0]) == str:
        new_geo_data.interfaces = geo_data.interfaces[geo_data.interfaces['series'].isin(series)]
        new_geo_data.orientations = geo_data.orientations[geo_data.orientations['series'].isin(series)]

    # Count df
    new_geo_data.set_faults(new_geo_data.count_faults())

    # Change the dataframe with the series
    new_geo_data.series = new_geo_data.series[new_geo_data.interfaces['series'].unique().
        remove_unused_categories().categories].dropna(how='all')
    new_geo_data.formations = new_geo_data.formations.loc[new_geo_data.interfaces['formation'].unique().
        remove_unused_categories().categories]
    new_geo_data.update_df()
    return new_geo_data


def get_series(model: Model):
    return model.series


def get_sequential_pile(model: Model):
    """
    Visualize an interactive stratigraphic pile to move around the formations and the series. IMPORTANT NOTE:
    To have the interactive properties it is necessary the use of an interactive backend. (In notebook use:
    %matplotlib qt5 or notebook)

    Args:
        model (:class:`gempy.core.model.Model`)

    Returns:
        :class:`matplotlib.pyplot.Figure`
    """
    return model.series.sequential_pile.figure
# endregion


# region Formations functionality
@_setdoc(Formations.__doc__)
def create_formations(values_array=None, values_names=np.empty(0), formation_names=np.empty(0)):
    f = Formations(values_array=values_array, properties_names=values_names, formation_names=formation_names)
    return f


def set_formations(model: Model, formation_names=None, formations_order=None, values_array=None,
                   properties_names=None):
    """
    Function to order and change the value of the model formation_names. The values of the formation_names will be the final
    numerical value that each formation will take in the interpolated geological model (lithology block)

    Args:
        model (:class:`gempy.core.model.Model`)
        values_array (np.ndarray): values of the formation_names will be the final
            numerical value that each formation will take in the interpolated geological model (lithology block)
        properties_names (list or np.ndarray): list containing the names of each properties
        formations_order (list of str): List with a given order of the formation_names. Due to the interpolation algorithm
            this order is only relevant to keep consistent the colors of layers and input data. The order ultimately is
            determined by the geometric sedimentary order
        formation_names (list of str): same as formation_names order. you can use any
        values_array (list of floats or int):

    Returns:
        :class:`DataFrame`: formation_names dataframe already updated in place

    """
    if formation_names and not formations_order:
        formations_order = formation_names
    if formations_order is not None and values_array is not None:
        model.formations.set_formations_values(values_array, formation_order=formations_order,
                                               properties_names=properties_names)
    elif formations_order is not None:
        model.formations.set_formation_order(formations_order)
        model.formations.set_id()

    return True


def set_order_formations(geo_model, formation_order):
    warnings.warn("set_order_formations will be removed in version 1.2, "
                  "use gempy.set_formations function instead", FutureWarning)
    set_formations(geo_model, formations_order=formation_order)


def get_formations(model: Model):
    return model.formations
# endregion


# region Fault functionality
@_setdoc(Faults.__doc__)
def create_faults(series: Series, series_fault=None, rel_matrix=None):
    return Faults(series=series, series_fault=series_fault, rel_matrix=rel_matrix)


def set_faults(model: Model, faults: Faults):
    model.faults = faults


def get_faults(model: Model):
    return model.faults
# endregion


# region Grid functionality
@_setdoc(GridClass.__doc__)
def create_grid(grid_type: str, **kwargs):
    return GridClass(grid_type=grid_type, **kwargs)


@_setdoc(Model.set_grid.__doc__)
def set_grid(model: Model, grid: GridClass, only_model=False):
    model.set_grid(grid=grid, only_model=only_model)


def get_grid(model: Model):
    """
    Coordinates can be found in :class:`gempy.core.data.GridClass.values`

     Args:
        model (:class:`gempy.core.model.Model`)

     Returns:
        :class:`gempy.data_management.GridClass`
    """
    return model.grid


def get_resolution(model: Model):
    return model.grid.resolution


def get_extent(model: Model):
    return model.grid.extent


# def update_grid(model, grid_type: str, **kwargs):
#     model.grid.__init__(grid_type=grid_type, **kwargs)
# endregion


# region Point-Orientation functionality
@_setdoc([Interfaces.read_interfaces.__doc__, Orientations.read_orientations.__doc__])
def read_data(model: Model, path_i=None, path_o=None, **kwargs):

    if path_i:
        model.interfaces.read_interfaces(path_i, inplace=True, **kwargs)
    if path_o:
        model.orientations.read_orientations(path_o, inplace=True, **kwargs)

    model.formations.set_formation_names(model.interfaces)

    model.rescaling.rescale_data()
    update_additional_data(model)


def set_interfaces(geo_data, interf_dataframe, append=False):
    """
     Method to change or append a Dataframe to interfaces in place.

     Args:
         geo_data(:class:`gempy.data_management.InputData`)
         interf_dataframe (:class:`DataFrame`)
         append (Bool): if you want to append the new data frame or substitute it
     """
    geo_data.set_interfaces(interf_dataframe, append=append)


def get_interfaces(model: Model):
    return model.interfaces


def set_orientations(geo_data, orient_dataframe, append=False):
    """
    Method to change or append a dataframe to orientations in place.  A equivalent Pandas Dataframe with
    ['X', 'Y', 'Z', 'dip', 'azimuth', 'polarity', 'formation'] has to be passed.

    Args:
         geo_data(:class:`gempy.data_management.InputData`)
         orient_dataframe (:class:`DataFrame`)
         append (Bool): if you want to append the new data frame or substitute it
    """

    geo_data.set_orientations(orient_dataframe, append=append)


def set_orientation_from_interfaces(geo_data, indices_array):
    """
    Create and set orientations from at least 3 points of the :attr:`gempy.data_management.InputData.interfaces`
     Dataframe
    Args:
        geo_data (:class:`gempy.data_management.InputData`)
        indices_array (array-like): 1D or 2D array with the pandas indices of the
          :attr:`gempy.data_management.InputData.interfaces`. If 2D every row of the 2D matrix will be used to create an
          orientation


    Returns:
        :attr:`gempy.data_management.InputData.orientations`: Already updated inplace
    """

    if _np.ndim(indices_array) is 1:
        indices = indices_array
        form = geo_data.interfaces['formation'].loc[indices].unique()
        assert form.shape[0] is 1, 'The interface points must belong to the same formation'
        form = form[0]
        print()
        ori_parameters = geo_data.create_orientation_from_interfaces(indices)
        geo_data.add_orientation(X=ori_parameters[0], Y=ori_parameters[1], Z=ori_parameters[2],
                                 dip=ori_parameters[3], azimuth=ori_parameters[4], polarity=ori_parameters[5],
                                 G_x=ori_parameters[6], G_y=ori_parameters[7], G_z=ori_parameters[8],
                                 formation=form)
    elif _np.ndim(indices_array) is 2:
        for indices in indices_array:
            form = geo_data.interfaces['formation'].loc[indices].unique()
            assert form.shape[0] is 1, 'The interface points must belong to the same formation'
            form = form[0]
            ori_parameters = geo_data.create_orientation_from_interfaces(indices)
            geo_data.add_orientation(X=ori_parameters[0], Y=ori_parameters[1], Z=ori_parameters[2],
                                     dip=ori_parameters[3], azimuth=ori_parameters[4], polarity=ori_parameters[5],
                                     G_x=ori_parameters[6], G_y=ori_parameters[7], G_z=ori_parameters[8],
                                     formation=form)

    geo_data.update_df()
    return geo_data.orientations


def get_orientations(model: Model):
    return model.orientations


def rescale_data(model: Model, rescaling_factor=None, centers=None):
    """

    object between 0 and 1 due to stability problem of the float32.

    Args:
        model (:class:`gempy.core.model.Model`)
        rescaling_factor(float): factor of the rescaling. Default to maximum distance in one the axis

    Returns:
        True
    """

    model.rescaling.rescale_data(rescaling_factor, centers)
    return True
# endregion


# region Interpolator functionality
@_setdoc([Interpolator.__doc__,
         Interpolator.set_theano_shared_parameters.__doc__])
def set_interpolation_data(model: Model, inplace=True, compile_theano: bool=True, output='geology',
                           theano_optimizer='fast_compile', verbose:list=np.nan):
    """

    Args:
        model:
        inplace:
        compile_theano

    Returns:

    """
    model.additional_data.options.at['output', 'values'] = output
    model.additional_data.options.at['theano_optimizer', 'values'] = theano_optimizer
    model.additional_data.options.at['verbosity', 'values'] = verbose

    # TODO add kwargs
    model.rescaling.rescale_data()
    update_additional_data(model)
    model.interfaces.sort_table()
    model.orientations.sort_table()

    model.interpolator.set_theano_graph(model.interpolator.create_theano_graph())
    model.interpolator.set_theano_shared_parameters()

    if compile_theano is True:
        model.interpolator.compile_th_fn(inplace=inplace)

    return model.additional_data.options


def get_interpolator(model: Model):
    return model.interpolator


def get_th_fn(model: Model):
    """
    Get the compiled theano function

    Args:
        model (:class:`gempy.core.model.Model`)

    Returns:
        :class:`theano.compile.function_module.Function`: Compiled function if C or CUDA which computes the interpolation given the input data
            (XYZ of dips, dip, azimuth, polarity, XYZ ref interfaces, XYZ rest interfaces)
    """
    assert getattr(model.interpolator, 'theano_function', False) is not None, 'Theano has not been compiled yet'

    return model.interpolator.theano_function
# endregion


# region Additional data functionality
def update_additional_data(model: Model, update_structure=True, update_rescaling=True, update_kriging=True):
    if update_structure is True:
        model.additional_data.update_structure()
    if update_rescaling is True:
        model.additional_data.update_rescaling_data()
    if update_kriging is True:
        model.additional_data.update_default_kriging()

    return model.additional_data


def get_additional_data(model: Model):
    return model.additional_data


def get_kriging_parameters(model: Model):
    """
    Print the kringing parameters

    Args:
        model (:obj:`gempy.core.data.Model`)

    Returns:
        None
    """
    return model.additional_data.kriging_data
# endregion


# region Computing the model
def compute_model(model: Model, compute_mesh=True)-> Solution:
    """
    Computes the geological model and any extra output given in the additional data option.

    Args:
        model (:obj:`gempy.core.data.Model`)
        compute_mesh (bool): If true compute polydata

    Returns:
        gempy.core.data.Solution

    """
    # with warnings.catch_warnings(record=True):
    #     warnings.filterwarnings("ignore",
    #                             message='.* a non-tuple sequence for multidimensional indexing is deprecated; use*.',
    #                             append=True)

    # TODO: Assert frame by frame that all data is like is supposed. Otherwise,
    # return clear messages
    i = model.interpolator.get_input_matrix()

    assert model.additional_data.len_formations_i.min() > 1,  \
        'To compute the model is necessary at least 2 interface points per layer'

    sol = model.interpolator.theano_function(*i)
    model.solutions.set_values(sol, compute_mesh=compute_mesh)

    return model.solutions


def compute_model_at(new_grid_array: ndarray, model: Model):
    """
    This function does the same as :func:`gempy.core.gempy_front.compute_model` plus the addion functionallity of
     passing a given array of points where evaluate the model instead of using the :class:`gempy.core.data.GridClass`.

    Args:
        model:
        new_grid_array (:class:`_np.array`): 2D array with XYZ (columns) coorinates

    Returns:
        gempy.core.data.Solution
    """
    #TODO create backup of the mesh and a method to go back to it
    set_grid(model, create_grid('custom_grid', custom_grid=new_grid_array))

    # Now we are good to compute the model again only in the new point
    sol = compute_model(model, compute_mesh=False)
    return sol
# endregion


# region Solution
# TODO compute, set? Right now is computed always
def get_surfaces(model: Model):
    """
    gey vertices and simplices of the interfaces for its vtk visualization and further
    analysis

    Args:
       model (:class:`gempy.core.model.Model`)


    Returns:
        vertices, simpleces
    """
    return model.solutions.vertices, model.solutions.edges
# endregion


# region Model level functions
@_setdoc([Series.set_series_categories.__doc__, Faults.set_is_fault.__doc__])
def set_values_to_default(model: Model, series_distribution=None, order_series=None, order_formations=None,
                          set_faults=True, map_formations_from_series=True, call_map_to_data=True, verbose=0) -> bool:
    """
    Set the attributes of most of the objects to its default value to be able to compute a geological model.

    - Interfaces and orientations: From csv files and prepare structure to GemPy's
    - Formations :class:`gempy.core.data.Formations`: Using formations read in the csv file
    - Series :class:`gempy.core.data.Series`: Using formations read in the csv file
    - Faults :class:`gempy.core.data.Faults`: Using formations read in the csv file. If fault string is contained in
      the name

    Args:
        model:
        series_distribution:
        order_series:
        order_formations:
        set_faults:
        map_formations_from_series:
        call_map_to_data:
        verbose:

    Returns:
        True

    ---------
    See Also:
    ---------

    """
    if series_distribution:
        model.formations.map_series(series_distribution)
        print('line 574')

    if set_faults is True:
        model.faults.set_is_fault()

    if map_formations_from_series is True:
       # model.formations.map_formations_from_series(model.series)
        model.formations.df = model.formations.set_id(model.formations.df)
        try:
            model.formations.add_basement()
            model.series.add_basement()
        except AssertionError:
            print('already basement')
            pass
    if order_formations is not None:
        warnings.warn(" ", FutureWarning)
        model.formations.set_formation_order(order_formations)

    if call_map_to_data is True:
        map_to_data(model, model.series, model.formations, model.faults)

    if verbose > 0:
        return get_sequential_pile(model)
    else:
        return True


def map_to_data(model: Model, series: Series = None, formations: Formations = None, faults: Faults = None):
    # TODO this function makes sense as Model method

    if formations is not None:
        model.interfaces.map_data_from_formations(formations, 'id')
        model.orientations.map_data_from_formations(formations, 'id')

        model.interfaces.map_data_from_formations(formations, 'series')
        model.orientations.map_data_from_formations(formations, 'series')

    if series is not None:
        model.interfaces.map_data_from_series(series, 'order_series')
        model.orientations.map_data_from_series(series, 'order_series')

    if faults is not None:
        model.interfaces.map_data_from_faults(faults)
        model.orientations.map_data_from_faults(faults)


def get_data(model: Model, itype='data', numeric=False, verbosity=0):
    """
    Method to return the data stored in :class:`DataFrame` within a :class:`gempy.interpolator.InterpolatorData`
    object.

    Args:
        model (:class:`gempy.core.model.Model`)
        itype(str {'all', 'interfaces', 'orientations', 'formations', 'series', 'faults', 'faults_relations',
        additional data}): input
            data type to be retrieved.
        numeric (bool): if True it only returns numberical properties. This may be useful due to memory issues
        verbosity (int): Number of properties shown

    Returns:
        pandas.core.frame.DataFrame

    """
    return model.get_data(itype=itype, numeric=numeric, verbosity=verbosity)


@_setdoc([set_values_to_default.__doc__])
def create_data(extent: Union[list, ndarray], resolution: Union[list, ndarray] = (50, 50, 50),
                project_name: str='default_project', **kwargs) -> Model:
    """
    Create a :class:`gempy.core.model.Model` object and initialize some of the main functions such as:

    - Grid :class:`gempy.core.data.GridClass`: To regular grid.
    - read_data: Interfaces and orientations: From csv files
    - set_values to default


    Args:
        extent (list or array):  [x_min, x_max, y_min, y_max, z_min, z_max]. Extent for the visualization of data
         and default of for the grid class.
        resolution (list or array): [nx, ny, nz]. Resolution for the visualization of data
         and default of for the grid class.
        project_name (str)

    Keyword Args:
        path_i: Path to the data bases of interfaces. Default os.getcwd(),
        path_o: Path to the data bases of orientations. Default os.getcwd()

    Returns:
        :class:`gempy.data_management.InputData`

    """
    warnings.warn("create_data will get deprecated in the next version of gempy. It still exist only to keep"
                  "the behaviour equal to older version. Use init_data.", FutureWarning)
    return init_data(extent=extent, resolution=resolution, project_name=project_name, **kwargs)


@_setdoc([set_values_to_default.__doc__])
def init_data(extent: Union[list, ndarray], resolution: Union[list, ndarray] = (50, 50, 50),
                project_name: str='default_project', **kwargs) -> Model:
    """
    Create a :class:`gempy.core.model.Model` object and initialize some of the main functions such as:

    - Grid :class:`gempy.core.data.GridClass`: To regular grid.
    - read_data: Interfaces and orientations: From csv files
    - set_values to default


    Args:
        extent (list or array):  [x_min, x_max, y_min, y_max, z_min, z_max]. Extent for the visualization of data
         and default of for the grid class.
        resolution (list or array): [nx, ny, nz]. Resolution for the visualization of data
         and default of for the grid class.
        project_name (str)

    Keyword Args:

        path_i: Path to the data bases of interfaces. Default os.getcwd(),
        path_o: Path to the data bases of orientations. Default os.getcwd()

    Returns:
        :class:`gempy.data_management.InputData`

    """

    model = create_model(project_name)
    set_grid(model, create_grid(grid_type='regular_grid', extent=extent, resolution=resolution))
    read_data(model, **kwargs)
    set_values_to_default(model, series_distribution=None, order_series=None, order_formations=None,
                          set_faults=True, map_formations_from_series=True, call_map_to_data=True, verbose=0)
    update_additional_data(model)

    return model


# endregion
