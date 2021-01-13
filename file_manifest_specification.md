
Specification of a file manifest, for the purposes of BICCN archives
--------------------------------------------------------------------

-The file manifest will follow a tabular data model, with one table. If a name for the table is needed, `file_manifest` or **File manifest** may be used.
-Ideally, it will be hosted somehow by the R24 archives. CSV/TSV file download is acceptable in the short-term. A web API is acceptable, if it simulates the flat table structure effectively.
-Each record in the table should pertain to exactly 1 "digital asset". This term is meant to be incrementally more inclusive than "file". A major additional inclusion is directory *contents* with respect to standard file system. Allowing directory contents may drastically reduce the number of records needed in certain cases. It may also sometimes avert the need for the creation of archive files (e.g. ZIP or TAR files) in addition to original files.
-Each record should include the following fields (if marked "optional", it may be empty to indicate that the value is not known):
  1. **Filename**. `filename`. (*Optional*). The file basename, without directory information. This field is marked optional in order to allow for the situation that the filenames themselves may be subject to change, or the data submitters wish for the complexity of these strings to remain hidden within a private scope.
  2. **File ID**. `file_id`. This identifier may be an archive-specific, archive-issued identifier, or an identifier supplied by a data submitter
  3. **Project ID**. `project_id`. 
  4. **Publication state**. `publication_state`. (*Optional*). 
  4. **URI**. `uri`.
  5. **URL**. `url`.
  6. **Data type**. `data_type`. (*Optional*)
  7. **Checksum**. `checksum`.
  8. **Checksum type**. `checksum_type`.
  9. **Size**. `size`.

-In all non-empty fields, the only characters allowed are the printable ASCII characters. No trailing or prepending spaces are allowed. A regex enforcing these requirements is: `[!-~][ -~]*[!-~]` .
-Archives and data submitters jointly decide which records to include in the manifest. For example, the archives or the data submitters may wish to have a policy that excludes some deposited files from appearing on this "BICCN-scoped" manifest, for simplicity.



