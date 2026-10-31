# 08 · Lucy's survey desk: from a stack of paper to evidence an assistant can use (class notebook, 29 October 2026)

The notebook for the ITAM class of 29 October 2026. Lucy runs an ice cream shop and has six scanned paper surveys. You build the path from the scans to question and answer records, measure how well each way of cutting the text lets a program find the right answer, and run a small assistant that has to show its evidence before it prepares a local memory proposal. The central question: what must stay together for an answer to mean what the customer intended?

## Open it in Colab

- [Open `itam_1029_survey_chunking_lab.ipynb` in Colab](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/courses/zeo-itam-autumn-2026/labs/08-survey-chunking-2026-10-29/itam_1029_survey_chunking_lab.ipynb)

Choose a CPU runtime. The core needs no GPU and no API key. Run the preparation cells first, then work one cell at a time. The notebook is a self-paced route of about 90 minutes of active work, with a "ready to move on when" cue for every stop.

## What you do

You write three small functions: `fixed_chunks`, `qa_records` and `tick_status`. Everything else is provided, and cells are marked **Provided** or **Edit**. Each exercise follows the same rhythm: predict, run, inspect, change one thing, explain. The exercises come with provided guidance, hints or guided steps, and a worked explanation to open after you commit to an answer. A blank exercise reports itself as incomplete and never counts as done.

## What is real here

- The text reading is live: Tesseract reads the six pages in your session, in English, Spanish and German. The numbers you see may differ a little from the class slides if Colab installs a different Tesseract version. If Tesseract cannot be installed in your session, a boxed warning says so and the notebook goes on with readings recorded on the instructor's machine, each labeled RECORDED; the numbers then come from those readings and may differ from a live run on your pages.
- The survey, the respondents and every answer are fictional. The handwriting-like marks are drawn with two fonts, Caveat and Reenie Beanie, both under the SIL Open Font License 1.1. The notebook fetches both from one pinned commit of github.com/google/fonts, checks each file against its sha256 and refuses a file that differs; the license texts come with them. The pages teach document structure and controlled failures. They do not measure how well any system reads real handwriting.
- The assistant is a small rule based program with real local tools. It is not a language model. An optional extension at the end lets Jev propose the next tool through your own key, added as a Colab Secret named `TYPESAFE_API_KEY`. It is off by default, the notebook contains no key, and a hosted service may incur charges.
- The survey pages are drawn by the notebook itself. Setup is nine short cells that each print what they did and how many seconds it took, starting with a report of what your session runs on, and a failed step prints what failed and the one next step; it needs Internet for the Tesseract and pypdf packages, the language data and the two fonts. The optional Docling and PaddleOCR extensions install their own packages and download their models separately, in their own cells, and are off by default.

## Checks and limits

The notebook checks its own exercises and prints how many required cases pass. It was run from top to bottom on a Mac with Tesseract 5.5.1, both with blank exercises and with reference solutions in place, and once more with the live reader switched off and the recorded readings in its place, which gave the same numbers. A run in Colab itself is still to come, so treat any difference you see there as useful information and say what you saw. Six forms show mechanisms. They say nothing about real customers. Two readings from one engine are not independent verification, and a lexical search is not a semantic one.

Like notebooks 05 to 07, this one is not part of `make verify`.
