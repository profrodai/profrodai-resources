# 09 · Document processing (class notebooks, 27 October 2026)

Three notebooks for the ITAM class of 27 October 2026, all about the same made-up story: Lucy's delivery notes and the phone number that disappeared. The delivery notes, the phone number "55 0100" and the companies are made up. Run the cells of one notebook in order.

| Notebook | What it is |
|---|---|
| `itam_1027_document_processing_lab.ipynb` | The class notebook. Follows one delivery note through a document pipeline, from the page to the field an assistant would use. Every result is labeled LIVE (computed by the cell) or RECORDED (read from a saved earlier run). Its first cell installs pinned packages (several minutes) and downloads the files in `bundle/`, checking each against `bundle/MANIFEST.json`. |
| `itam_1027_lucys_document_workshop_self_contained_v3.ipynb` | Lucy's document workshop, a self-contained version: three supplier documents (selectable text, a scan, and one with an incorrect invisible text layer), where you build a reader that notices the difference before recommending a contact. |
| `itam_1027_lucys_missing_digits_guided_lab.ipynb` | Lucy's missing digits, a guided lab you can do without having attended the class: you investigate the failure, write two small functions and compare results. No API keys needed for the core lab. |

## Open in Colab

These links name the merge commit, so they open exactly the files in this folder:

- [Open `itam_1027_document_processing_lab.ipynb` in Colab](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/b13a6d8402232a312c3a04624bb3f0116f21431c/courses/zeo-itam-autumn-2026/labs/09-document-processing-2026-10-27/itam_1027_document_processing_lab.ipynb)
- [Open `itam_1027_lucys_document_workshop_self_contained_v3.ipynb` in Colab](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/b13a6d8402232a312c3a04624bb3f0116f21431c/courses/zeo-itam-autumn-2026/labs/09-document-processing-2026-10-27/itam_1027_lucys_document_workshop_self_contained_v3.ipynb)
- [Open `itam_1027_lucys_missing_digits_guided_lab.ipynb` in Colab](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/b13a6d8402232a312c3a04624bb3f0116f21431c/courses/zeo-itam-autumn-2026/labs/09-document-processing-2026-10-27/itam_1027_lucys_missing_digits_guided_lab.ipynb)

None of the three notebooks has been run in Colab yet. If a cell fails there, tell the instructor which one.

Two cells in the class notebook that call a hosted model replay saved answers, because they need keys that students do not have.
