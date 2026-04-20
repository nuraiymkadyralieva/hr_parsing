# Finance Director Lookup Project

## What It Does

This project reads a source Excel file, searches public company pages with Serper, extracts finance directors with DeepSeek, and creates a new output Excel file.

The output file contains only these columns:

- `Company`
- `RegistrationNumber`
- `Finance_Position`
- `Finance_FullName`

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## .env Setup

```powershell
copy .env.example .env
```

Then fill in:

- `SERPER_API_KEY`
- `DEEPSEEK_API_KEY`

## Run

```powershell
python main.py --input input.xlsx --output output.xlsx
python main.py --input input.xlsx --output output.xlsx --limit 10
```

## Input Excel Requirements

The input Excel file must contain these columns:

- `Company`
- `RegistrationNumber`

The script reads rows from the first worksheet and creates exactly one output row per input row.

## If Finance Director Is Not Found

If no finance director is found for a company, the script still writes the row to the output file with empty values in:

- `Finance_Position`
- `Finance_FullName`
