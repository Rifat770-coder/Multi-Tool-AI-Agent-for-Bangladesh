# Dataset rights and provenance

Verified 2026-11-01 using the Hugging Face dataset API and downloads at the revisions below. Code licensing does not grant dataset rights. No LICENSE file existed at audit start; the maintainer must choose the code license and copyright holder.

## institutions

Uploader/publisher: Mahadih534. Original creator and uploader ownership have not been independently verified.

Source: https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh

Revision: `6965701210fe390b19e5d2a05ca11874304a7b7f`. Declared license: **unknown**.

No redistribution permission established. Do not describe this dataset as MIT licensed. Maintainer action: obtain permission or approve removal of the bundled institutions database from future distributions; removing it locally does not remove historical copies. Existing data is retained pending that decision.

## hospitals

Uploader/publisher: Mahadih534. Original creator and uploader ownership have not been independently verified.

Source: https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals

Revision: `6e5943b83cb9f9fb407efe87269afcd118e3bf93`. Declared license: **cc-by-2.0**.

License terms: https://creativecommons.org/licenses/by/2.0/ . Attribute Mahadih534 and the linked dataset, retain license links, and indicate changes. This records the uploader declaration, not a legal determination of ownership.

## restaurants

Uploader/publisher: Mahadih534. Original creator and uploader ownership have not been independently verified.

Source: https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data

Revision: `a0b97e645dfe7ac6780a15b1d38f6137cf5801ee`. Declared license: **cc-by-2.0**.

License terms: https://creativecommons.org/licenses/by/2.0/ . Attribute Mahadih534 and the linked dataset, retain license links, and indicate changes. This records the uploader declaration, not a legal determination of ownership.

## Transformations and reproduction

`convert_data.py` converts CSV to SQLite, normalizes headers to lowercase underscores, disambiguates duplicates, and corrects `geogrpycal_status` to `geographical_status`. Identifiers and contact fields remain TEXT; inferred numeric columns become INTEGER/REAL, empty numeric cells NULL. Every converted record and database integrity are checked. No records are deliberately filtered. `data/schema.json` records bundled schema/types/counts. `data/sources.json` holds pinned revisions and SHA-256 hashes calculated from actual downloads; all three downloads matched existing local CSVs.

Rebuild into a separate directory first: `python convert_data.py --output-dir .cache/rebuild`. Default setup uses bundled databases without downloads. `--overwrite` explicitly permits replacing existing files. Each database replacement is atomic; the three databases and schema manifest are not one atomic transaction. A failed run can leave a mixture of successfully rebuilt and old files; prefer a new output directory and inspect before replacing production data.

No fresh distribution should be represented as fully licensed until the institutions permission and code license are resolved. Tests can use temporary synthetic SQLite tables; synthetic data must never be labeled as real Bangladesh coverage.
