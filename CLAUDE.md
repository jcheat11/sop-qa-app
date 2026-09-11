# SOP Question-Answering App

Single-document SOP Q&A tool. Personal/small-team use, not org-wide.

## Purpose

User uploads one SOP document (.docx, .pdf, .txt, .md), then asks questions
in a chat interface. The app answers ONLY from that document's content — it
must never fall back to general knowledge.

## Stack

- Python 3.11+, Streamlit for the UI
- Anthropic API, model `claude-sonnet-4-6`. API key comes from the
  `ANTHROPIC_API_KEY` environment variable — never hardcode it, never log it.
- Extraction: `python-docx` (.docx), `pypdf` (.pdf), plain file read (.txt/.md)
- Dependencies are kept minimal (see requirements.txt).

## File structure

- `app.py` — Streamlit UI and session flow
- `extract.py` — one function per format, plus a dispatcher that picks by
  file extension. Returns plain text. Kept isolated because it will be
  swapped/extended later.
- `qa.py` — builds the system prompt and calls the API
- `requirements.txt`, `README.md` (run instructions only)
- `logs/questions.log` — optional append-only log (timestamp, filename,
  question, first 100 chars of answer). No document text is ever logged.

## Behavior

1. Sidebar: file uploader (.docx, .pdf, .txt, .md). Shows filename,
   page/word count, and a warning if the document exceeds ~150k tokens
   (estimated as characters/4). Uploading a new file clears the chat.
2. Main area: chat interface. Every answer must cite the section heading or
   step number it came from.
3. System prompt rules:
   - Answer solely from the provided document text. If the document does
     not contain the answer, say "The document doesn't cover this" and do
     not guess or use general knowledge.
   - If a question is only partially covered, answer the covered part and
     explicitly state what the document does not address.
   - If the relevant step references an image (marked `[image omitted]`),
     say the document relies on a screenshot for that step.
4. The full document text is sent as context on every API call, along with
   chat history, so follow-up questions work. There is no chunking or
   retrieval — the whole document goes in every time.

## Extraction requirements

- `.docx`: preserve heading hierarchy and numbered lists as text (headings
  prefixed with `#`, repeated per level e.g. `##`). Insert the literal
  marker `[image omitted]` wherever an inline image appears. Tables are
  extracted row by row, pipe-separated.
- `.pdf`: if extracted text is empty or under ~50 characters, show the error
  "This PDF appears to be scanned or image-only. Text extraction isn't
  supported for it yet." and do not send it to the model.
- No persistence beyond the optional log described above. Document text
  itself is never written to disk by the app (only held in Streamlit session
  state for the duration of the session).

## Explicitly out of scope

Do not build any of: multiple documents, SharePoint/OneDrive integration,
user accounts, image analysis (only the `[image omitted]` marker), vector
search/embeddings, chunking. If one of these ever looks necessary, stop and
raise it instead of building it — the single-document, whole-text-in-context
design is intentional given expected SOP sizes.

## Assumptions made during initial build

- No `sample.docx` was provided in the project folder, so one was generated
  with `python-docx` (headings, a numbered list, a table, and an inline
  image) purely to validate `extract.py` before `app.py` was written. Delete
  or replace it freely.
- Word count for .docx/.txt/.md is a simple whitespace split; "page count"
  for PDFs comes from `len(reader.pages)` via pypdf.
- Chat history sent to the API is the full session's messages (no trimming)
  since SOPs and chats are expected to be small enough to fit the 150k-token
  budget alongside the document.
- The token-estimate warning is advisory only; it does not block upload or
  Q&A.
