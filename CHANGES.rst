1.1 2020-12-21
~~~~~~~~~~~~~~

* Added support for Auxiliary S5P products.

* Made orbit, collection, and processor_version namespace attributes optional.
  This will require a migration of the database::

    ALTER TABLE s5p ALTER COLUMN orbit DROP NOT NULL;
    ALTER TABLE s5p ALTER COLUMN collection DROP NOT NULL;
    ALTER TABLE s5p ALTER COLUMN processor_version DROP NOT NULL;
