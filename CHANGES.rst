2.0 2021-02-17
~~~~~~~~~~~~~~

* Remove file class from product_type names. This requires a data migration of
  any existing database. This can be done using e.g.
  UPDATE core SET product_type=substr(product_type,0,15) WHERE product_type LIKE 'S5P%';

* Change default hash type to 'md5' for all products.

* Add filename_only argument to analyze() functions.

1.1 2020-12-21
~~~~~~~~~~~~~~

* Added support for Auxiliary S5P products.

* Made orbit, collection, and processor_version namespace attributes optional.
  This will require a migration of the database::

    ALTER TABLE s5p ALTER COLUMN orbit DROP NOT NULL;
    ALTER TABLE s5p ALTER COLUMN collection DROP NOT NULL;
    ALTER TABLE s5p ALTER COLUMN processor_version DROP NOT NULL;
