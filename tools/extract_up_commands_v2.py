"""
tools/extract_up_commands_v2.py
Extract UP protocol commands from specification PDF (string-based protocol format).
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    print("Install with: pip install pdfplumber")
    sys.exit(1)


def extract_commands_from_pdf(pdf_path: Path) -> dict:
    """
    Extract UP protocol commands from PDF specification.

    This handles the string-based format: ID:N/Command/Module/Submodule/Parameter
    """

    commands = []
    modules = defaultdict(list)

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

        # Find all command examples in format: ID:N/Command/Module/...
        command_pattern = r'ID:\d+/(Command|Query|Ack|Reply|Nac)/([^/\n]+)(?:/([^/\n]+))?(?:/([^\n]+))?'

        lines = full_text.split('\n')

        for i, line in enumerate(lines):
            # Look for command pattern
            matches = re.findall(command_pattern, line)
            for match in matches:
                msg_type, module, submodule, parameter = match

                # Get context (description is usually on same line or previous line)
                context = ""
                if i > 0:
                    context = lines[i-1].strip()

                command_info = {
                    'message_type': msg_type,
                    'module': module,
                    'submodule': submodule if submodule else None,
                    'parameter': parameter if parameter else None,
                    'full_command': line.strip(),
                    'context': context
                }

                commands.append(command_info)
                modules[module].append(command_info)

        print(f"\nFound {len(commands)} command examples")
        print(f"Found {len(modules)} unique modules")

    return {
        'commands': commands,
        'modules': dict(modules),
        'module_list': sorted(modules.keys()),
        'source_file': str(pdf_path),
        'protocol_type': 'string-based',
        'format': 'ID:N/MessageType/Module/Submodule/Parameter'
    }


def generate_markdown_report(data: dict) -> str:
    """Generate markdown report of extracted commands."""

    output = []
    output.append("# UP Protocol Commands - Extracted from PDF\n")
    output.append(f"**Source:** {data['source_file']}")
    output.append(f"**Protocol Type:** {data['protocol_type']}")
    output.append(f"**Format:** `{data['format']}`")
    output.append(f"**Total Commands Found:** {len(data['commands'])}")
    output.append(f"**Total Modules:** {len(data['modules'])}\n")

    output.append("## Module List\n")
    for module_name in data['module_list']:
        count = len(data['modules'][module_name])
        output.append(f"- **{module_name}** ({count} commands)")

    output.append("\n## Commands by Module\n")

    for module_name in sorted(data['modules'].keys()):
        output.append(f"\n### {module_name} Module\n")
        output.append(f"Found {len(data['modules'][module_name])} command examples:\n")

        # Group by submodule
        submodules = defaultdict(list)
        for cmd in data['modules'][module_name]:
            sub = cmd['submodule'] if cmd['submodule'] else "(root)"
            submodules[sub].append(cmd)

        for submodule_name in sorted(submodules.keys()):
            if submodule_name != "(root)":
                output.append(f"\n#### {module_name}/{submodule_name}\n")

            for cmd in submodules[submodule_name]:
                output.append(f"**Command:** `{cmd['full_command']}`")
                if cmd['context']:
                    output.append(f"  - *Description:* {cmd['context']}")
                output.append("")

    return '\n'.join(output)


def generate_implementation_guide(data: dict) -> str:
    """Generate implementation guide for adding commands to the application."""

    output = []
    output.append("# UP Protocol Implementation Guide\n")
    output.append("## Protocol Overview\n")
    output.append(f"The External UP Protocol uses a **string-based format**, not binary:\n")
    output.append(f"```")
    output.append(f"{data['format']}")
    output.append(f"```\n")
    output.append("### Message Types\n")
    output.append("- **Command**: Trigger action or set parameter")
    output.append("- **Query**: Request current value")
    output.append("- **Reply**: Response to Query with data")
    output.append("- **Ack**: Acknowledgment of successful Command")
    output.append("- **Nac**: Negative acknowledgment (error)\n")

    output.append("### Communication\n")
    output.append("- **Protocol**: UDP or TCP")
    output.append("- **Default Port**: 34030 (UDP) or 34030 (TCP)")
    output.append("- **Format**: ASCII strings ending with '\\n'\n")

    output.append("## Key Modules\n")

    for module_name in sorted(data['modules'].keys()):
        output.append(f"\n### {module_name}\n")
        output.append(f"Total commands: {len(data['modules'][module_name])}\n")

        # Show a few example commands
        examples = data['modules'][module_name][:5]
        output.append("Example commands:")
        for cmd in examples:
            output.append(f"- `{cmd['full_command']}`")

        if len(data['modules'][module_name]) > 5:
            output.append(f"  *(and {len(data['modules'][module_name]) - 5} more...)*")
        output.append("")

    output.append("\n## Implementation Steps\n")
    output.append("1. **Update network layer** to support string-based commands")
    output.append("2. **Create command builders** for each module/submodule")
    output.append("3. **Add parsers** for Reply messages")
    output.append("4. **Update GUI** to add new control buttons")
    output.append("5. **Test** with actual hardware\n")

    output.append("## Current Implementation Status\n")
    output.append("Your current `network/up_protocol.py` uses **binary format** (magic bytes 0x5550).")
    output.append("The PDF describes **string-based format** (ID:N/Command/...).\n")
    output.append("**ACTION REQUIRED:** Verify which protocol format your MK4 hardware actually uses:")
    output.append("- Binary (current implementation)")
    output.append("- String-based (from PDF specification)")
    output.append("- Both (depending on port or configuration)\n")

    return '\n'.join(output)


def main():
    """Main entry point."""

    print("=" * 60)
    print("UP Protocol Command Extractor v2 (String-Based)")
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

    # Create tools directory if needed
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)

    # Save raw JSON
    json_output = tools_dir / "extracted_commands_v2.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n[OK] Saved raw data to: {json_output}")

    # Generate markdown report
    report_output = tools_dir / "UP_COMMANDS_REPORT.md"
    with open(report_output, 'w', encoding='utf-8') as f:
        f.write(generate_markdown_report(data))
    print(f"[OK] Saved command report to: {report_output}")

    # Generate implementation guide
    guide_output = tools_dir / "UP_IMPLEMENTATION_GUIDE.md"
    with open(guide_output, 'w', encoding='utf-8') as f:
        f.write(generate_implementation_guide(data))
    print(f"[OK] Saved implementation guide to: {guide_output}")

    print("\n" + "=" * 60)
    print("Extraction Complete!")
    print("=" * 60)
    print(f"\nFound {len(data['commands'])} command examples")
    print(f"Found {len(data['modules'])} unique modules:")
    for module in data['module_list']:
        print(f"  - {module} ({len(data['modules'][module])} commands)")

    print("\n" + "!" * 60)
    print("IMPORTANT: Protocol Format Mismatch Detected!")
    print("!" * 60)
    print("\nYour current implementation uses BINARY format (0x5550 magic bytes).")
    print("The PDF spec describes STRING-BASED format (ID:N/Command/...).")
    print("\nPlease verify which format your MK4 hardware actually uses before")
    print("implementing new commands from this specification.")
    print("\nSee UP_IMPLEMENTATION_GUIDE.md for details.")


if __name__ == "__main__":
    main()
