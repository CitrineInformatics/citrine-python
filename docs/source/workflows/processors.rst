Processors
==========

A processor defines how a :doc:`design space <design_spaces>` is searched.
There are two processors:

-  `EnumeratedProcessor <#enumerated-processor>`__ enumerates up to a fixed number of materials from a finite, enumerable space.
-  `GridProcessor <#grid-processor>`__ creates finite, enumerable space from a (semi)-continuous one by discretizing the continuous variables and enumerating the finite variables.

Enumerated processor
--------------------

An enumerated processor takes up to a maximum number of materials from a :doc:`design space <design_spaces>` and processes each independently.
The maximum number of candidates sampled from the design space is defined by the optional ``max_size`` parameter when creating an :class:`~citrine.informatics.processors.EnumeratedProcessor` using the python SDK.
To be valid, enumerated processors must have a maximum size of at least 1.

An enumerated processor can be used with finite and infinite design spaces.
A finite space can be defined using an :class:`~citrine.informatics.design_spaces.EnumeratedDesignSpace` or a :class:`~citrine.informatics.design_spaces.ProductDesignSpace` composed only of :class:`EnumeratedDimensions <citrine.informatics.dimensions.EnumeratedDimension>`.
In these cases, the processor will systematically pull up to ``max_size`` samples from the space.

An infinite design space is created when a :class:`~citrine.informatics.design_spaces.ProductDesignSpace` contains one or more continuous dimensions.
When an enumerated processor is combined with an infinite design space, ``max_size`` samples are always pulled from the domain.
If all dimensions of a design pace are continuous, samples are created by randomly sampling from each dimension.
If there mixed continuous and enumerated dimensions in the design space, samples are created by combining the outer product of enumerated dimensions with random samples from continuous dimensions.
Finite elements repeat once the outer product is exhausted.

The following demonstrates how to create an enumerated processor that takes up to 100 samples from a design space, register it with a project and view validation results:

.. code:: python

   from time import sleep
   from citrine import Citrine
   from citrine.informatics.processors import EnumeratedProcessor

   # create a session with citrine using API variables
   session = Citrine(API_KEY, API_SCHEME, API_HOST, API_PORT)

   project = session.projects.register('Example project')

   # create an enumerated processor and register it with the project
   processor = project.processors.register(
       EnumeratedProcessor(
           name='Enumerated processor',
           description='Samples up to 100 items from a design space',
           max_size=100
       )
   )

   # wait until the processor is no longer validating
   # we must get the processor every time we wish to fetch the latest status
   while project.processors.get(processor.uid).status != "VALIDATING":
       sleep(10)

   # print final validation status and status information
   validated_processor = project.processors.get(processor.uid)
   print(validated_processor.status)
   print(processor.status_info)

Grid processor
--------------

A grid processor generates samples from the outer product of finite dimensions.
This processor can only be used with a :class:`~citrine.informatics.design_spaces.ProductDesignSpace`.
To create a finite set of materials from continuous dimensions, a uniform grid is created between the bounds of the descriptor.
The number of points is specified by ``grid_sizes``.
``grid_sizes`` is a map from descriptor key to the number of points to select between bounds of the dimension.
For example, if the dimension is bounded by 0 and 10 and the grid size is 11, points are taken from 0 to 10 in increments of 1.
Each continuous dimension in the design space must be given a grid size.
Enumerated dimensions cannot be given a grid size because it is not clear how to downsample or create a grid for a finite dimension.

The following demonstrates how to create a grid processor that searches
a 2D design space of enumerated x values and continuous y values:

.. code:: python

   from citrine.informatics.descriptors import RealDescriptor
   from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension
   from citrine.informatics.processors import GridProcessor

   # create descriptors for x and y
   x = RealDescriptor(key='x', lower_bound=0, upper_bound=10)
   y = RealDescriptor(key='y', lower_bound=0, upper_bound=100)

   # enumerate x and create a continuous dimension for y
   # note the upper bound on y is lower than that of the descriptor to restrict the search domain
   x_dim = EnumeratedDimension(x, ['0', '5', '10'])
   y_dim = ContinuousDimension(y, lower_bound=0, upper_bound=10)

   # create a design space from x and y dimensions
   design_space = ProductDesignSpace(
       name='2D coordinate system',
       description='Design space that contains (x, y) points',
       dimensions=[x_dim, y_dim]
   )

   # define a processor that will create a grid of 11 points over the y dimension
   # a grid size for x is not specified since it is already finite
   processor = GridProcessor(
       name='Grid processor',
       description='Creates a grid over y',
       grid_sizes={'y': 11}
   )
