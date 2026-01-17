# Username Search Tool

A simple Python CLI tool to check if a specific username is taken or exists across multiple social media websites.

## Prerequisites

- [Python 3.7+](https://www.python.org/downloads/) installed on your system.
- `pip` (Python package installer).

## Installation

1.  Open your terminal or command prompt.
2.  Navigate to the project directory:
    ```bash
    cd "d:/Detective"
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To search for a username, run the `main.py` script followed by the username you want to check:

```bash
python main.py <username>
```

**Example:**

```bash
python main.py johndoe
```

The tool will scan the sites listed in `sites.json` and report where a profile was found.

## Customization

You can add or remove websites by editing the `sites.json` file.
Each entry looks like this:

```json
{
  "name": "Site Name",
  "url": "https://example.com/user/{}",
  "check_type": "status_code",
  "expected_status": 200
}
```

- `url`: The profile URL structure. Use `{}` as a placeholder for the username.
- `check_type`: Currently supports `status_code` (checks if the page returns 200 OK).

