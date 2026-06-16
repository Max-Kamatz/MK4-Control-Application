"""
tools/extract_up_commands.py
Extract UP protocol commands from specification PDF and generate structured command list.
"""

import sys
import json
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    print("Install with: pip install pdfplumber")
    sys.exit(1)


def extract_commands_from_pdf(pdf_path: Path) -> dict:
    """
    Extract UP protocol commands from PDF specification.

    Returns:
        Dictionary with command information
    """
    commands = {}
    responses = {}

    print(f"Opening PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")

        full_text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}/{len(pdf.pages)}...", end='\r')
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        print(f"\nExtracted {len(full_text)} characters of text")

        # Save sample of extracted text for debugging
        sample_output = Path("tools/pdf_text_sample.txt")
        sample_output.parent.mkdir(exist_ok=True)
        with open(sample_output, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("FIRST 5000 CHARACTERS OF EXTRACTED TEXT\n")
            f.write("=" * 60 + "\n\n")
            f.write(full_text[:5000])
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("SEARCHING FOR 'command' (case-insensitive):\n")
            f.write("=" * 60 + "\n\n")
            # Find lines containing "command"
            command_lines = [line for line in full_text.split('\n') if 'command' in line.lower()]
            f.write('\n'.join(command_lines[:50]))  # First 50 matches
        print(f"Saved text sample to: {sample_output}")

        # Parse commands using common patterns in UP protocol specs
        # Look for command definitions like:
        # "Command ID: 0x01" or "Command: 1" or "ID: 1"
        # Followed by description and payload info

        lines = full_text.split('\n')

        current_section = None
        current_command = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Look for command ID patterns
            # Pattern 1: "Command ID: 0x01" or "Command ID: 1"
            match = re.search(r'Command\s+ID[:\s]+(?:0x)?([0-9A-Fa-f]+)', line, re.IGNORECASE)
            if match:
                cmd_id = int(match.group(1), 16 if '0x' in line else 10)
                current_command = {
                    'id': cmd_id,
                    'raw_text': line,
                    'description': '',
                    'payload': '',
                    'context': []
                }
                # Grab surrounding context (next 5 lines)
                for j in range(1, 6):
                    if i + j < len(lines):
                        current_command['context'].append(lines[i + j].strip())

                # Try to extract description from same line or next line
                desc_match = re.search(r'(?:Description|Name|Command)[:\s]+(.+)', line, re.IGNORECASE)
                if desc_match:
                    current_command['description'] = desc_match.group(1).strip()

                commands[cmd_id] = current_command

            # Look for response ID patterns
            match = re.search(r'Response\s+ID[:\s]+(?:0x)?([0-9A-Fa-f]+)', line, re.IGNORECASE)
            if match:
                resp_id = int(match.group(1), 16 if '0x' in line else 10)
                current_response = {
                    'id': resp_id,
                    'raw_text': line,
                    'description': '',
                    'context': []
                }
                for j in range(1, 5):
                    if i + j < len(lines):
                        current_response['context'].append(lines[i + j].strip())

                responses[resp_id] = current_response

        print(f"\nFound {len(commands)} commands and {len(responses)} responses")

    return {
        'commands': commands,
        'responses': responses,
        'source_file': str(pdf_path)
    }


def generate_command_table(data: dict) -> str:
    """Generate a markdown table of commands."""

    output = []
    output.append("# UP Protocol Commands Extracted from PDF\n")
    output.append(f"Source: {data['source_file']}\n")
    output.append(f"Total Commands: {len(data['commands'])}")
    output.append(f"Total Responses: {len(data['responses'])}\n")

    # Commands table
    output.append("## Commands\n")
    output.append("| ID (Dec) | ID (Hex) | Description | Context |")
    output.append("|----------|----------|-------------|---------|")

    for cmd_id in sorted(data['commands'].keys()):
        cmd = data['commands'][cmd_id]
        hex_id = f"0x{cmd_id:02X}"
        desc = cmd['description'] if cmd['description'] else cmd['raw_text']
        context = ' '.join(cmd['context'][:2])  # First 2 lines of context

        # Clean up for markdown
        desc = desc.replace('|', '\\|')[:80]
        context = context.replace('|', '\\|')[:100]

        output.append(f"| {cmd_id} | {hex_id} | {desc} | {context} |")

    # Responses table
    output.append("\n## Responses\n")
    output.append("| ID (Dec) | ID (Hex) | Description | Context |")
    output.append("|----------|----------|-------------|---------|")

    for resp_id in sorted(data['responses'].keys()):
        resp = data['responses'][resp_id]
        hex_id = f"0x{resp_id:02X}"
        desc = resp['description'] if resp['description'] else resp['raw_text']
        context = ' '.join(resp['context'][:2])

        desc = desc.replace('|', '\\|')[:80]
        context = context.replace('|', '\\|')[:100]

        output.append(f"| {resp_id} | {hex_id} | {desc} | {context} |")

    return '\n'.join(output)


def generate_detailed_report(data: dict) -> str:
    """Generate detailed report with all context."""

    output = []
    output.append("# UP Protocol Commands - Detailed Report\n")
    output.append(f"Source: {data['source_file']}\n")

    output.append("## Commands (with full context)\n")

    for cmd_id in sorted(data['commands'].keys()):
        cmd = data['commands'][cmd_id]
        output.append(f"\n### Command ID: {cmd_id} (0x{cmd_id:02X})")
        output.append(f"**Raw Text:** {cmd['raw_text']}")
        output.append(f"**Description:** {cmd['description']}")
        output.append(f"**Context:**")
        for line in cmd['context']:
            if line:
                output.append(f"  - {line}")
        output.append("")

    output.append("\n## Responses (with full context)\n")

    for resp_id in sorted(data['responses'].keys()):
        resp = data['responses'][resp_id]
        output.append(f"\n### Response ID: {resp_id} (0x{resp_id:02X})")
        output.append(f"**Raw Text:** {resp['raw_text']}")
        output.append(f"**Context:**")
        for line in resp['context']:
            if line:
                output.append(f"  - {line}")
        output.append("")

    return '\n'.join(output)


def main():
    """Main entry point."""

    print("=" * 60)
    print("UP Protocol Command Extractor")
    print("=" * 60 + "\n")

    # Default path to the UP protocol PDF
    default_pdf = Path("Reference Material/External_UP_protocol_v2.4.7.pdf")

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = default_pdf

    if not pdf_path.exists():
        print(f"ERROR: PDF not found at: {pdf_path}")
        print(f"\nUsage: python {sys.argv[0]} [path_to_pdf]")
        print(f"Default: {default_pdf}")
        sys.exit(1)

    # Extract commands
    data = extract_commands_from_pdf(pdf_path)

    # Save raw JSON
    json_output = Path("tools/extracted_commands.json")
    json_output.parent.mkdir(exist_ok=True)
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n[OK] Saved raw data to: {json_output}")

    # Generate markdown table
    table_output = Path("tools/UP_COMMANDS_TABLE.md")
    with open(table_output, 'w', encoding='utf-8') as f:
        f.write(generate_command_table(data))
    print(f"[OK] Saved command table to: {table_output}")

    # Generate detailed report
    detailed_output = Path("tools/UP_COMMANDS_DETAILED.md")
    with open(detailed_output, 'w', encoding='utf-8') as f:
        f.write(generate_detailed_report(data))
    print(f"[OK] Saved detailed report to: {detailed_output}")

    print("\n" + "=" * 60)
    print("Extraction Complete!")
    print("=" * 60)
    print(f"\nFound {len(data['commands'])} commands and {len(data['responses'])} responses")
    print("\nNext steps:")
    print("1. Review the generated markdown files")
    print("2. Manually verify command IDs and descriptions")
    print("3. Update config/up_protocol_commands.json with correct values")
    print("4. Implement new command builders in network/up_protocol.py")


if __name__ == "__main__":
    main()
