Muninn S5P extension
====================

This module provides a namespace extension and a product type extension for
Sentinel-5P products for use in Muninn archives. It requires Muninn version 5.0
or higher.

You can use this module as-is, but you can also use it as a template.
Depending on your use case you might want to adapt the module and use a
different product type naming convention (e.g. without mission and/or file
class components), have the ``analyze()`` function return properties for
additional namespaces that you may have, etc.
