#!/usr/bin/env python3
"""
Generate an HTML representation of a codeplug from plug.yaml
"""

import yaml
import sys
from pathlib import Path
from html import escape


# Parameter descriptions from QDMR manual
PARAM_DESCRIPTIONS = {
    # General settings
    "introLine1": "First line of text shown on startup screen",
    "introLine2": "Second line of text shown on startup screen",
    "micLevel": "Microphone sensitivity level (1-10)",
    "speech": "Enable/disable speech synthesis",
    "power": "Transmit power level",
    "squelch": "Squelch level - minimum signal strength to open audio",
    "vox": "Voice-activated transmission sensitivity",
    "tot": "Transmit timeout timer in seconds (0 = disabled)",
    "defaultID": "Default radio ID to use",
    # Contact fields
    "name": "Display name",
    "type": "Contact type: PrivateCall, GroupCall, or AllCall",
    "number": "DMR ID number",
    "ring": "Enable ring tone for incoming calls",
    # Channel fields
    "rxFrequency": "Receive frequency in MHz",
    "txFrequency": "Transmit frequency in MHz",
    "timeout": "Transmit timeout timer",
    "rxOnly": "Receive-only mode (no transmission)",
    "scanList": "Scan list assignment",
    "admit": "Admission criteria for transmission",
    "bandwidth": "Channel bandwidth (Wide/Narrow for analog)",
    "aprs": "APRS system to use on this channel",
    "colorCode": "DMR color code (0-15)",
    "timeSlot": "DMR time slot (1 or 2)",
    "groupList": "RX group list for filtering incoming calls",
    "contact": "Default transmit contact",
    # Zone fields
    "A": "Channels assigned to VFO A",
    "B": "Channels assigned to VFO B",
    # Group list fields
    "contacts": "List of contacts in this group",
    # Roaming
    "roamingZone": "Roaming zone for automatic repeater switching",
}


def get_description(key):
    """Get description for a parameter"""
    return PARAM_DESCRIPTIONS.get(key, "")


def format_value(value, key=None, context=None):
    """Format a value for HTML display"""
    if value is None:
        return '<span class="null">null</span>'
    elif isinstance(value, bool):
        return f'<span class="bool">{str(value).lower()}</span>'
    elif isinstance(value, (int, float)):
        return f'<span class="number">{value}</span>'
    elif isinstance(value, str):
        # Check if this is a reference to another item
        if context and key in [
            "contact",
            "scanList",
            "aprs",
            "groupList",
            "roamingZone",
        ]:
            # It's a reference - create a link
            section_map = {
                "contact": "contacts",
                "scanList": "scanLists",
                "groupList": "groupLists",
                "roamingZone": "roamingZones",
                "aprs": "positioning",
            }
            section = section_map.get(key, "")
            if section:
                ref_name = context.get("ref_names", {}).get(f"{section}-{value}", value)
                return f'<a href="#{section}-{escape(value)}" class="ref-link">{escape(ref_name)}</a>'
        return f'<span class="string">{escape(value)}</span>'
    else:
        return escape(str(value))


def format_reference_list(items, section, context):
    """Format a list of references as links"""
    if not items:
        return '<span class="empty-list">[]</span>'

    html = '<span class="ref-list">'
    links = []
    for item in items:
        ref_name = context.get("ref_names", {}).get(f"{section}-{item}", item)
        links.append(
            f'<a href="#{section}-{escape(item)}" class="ref-link">{escape(ref_name)}</a>'
        )
    html += ", ".join(links)
    html += "</span>"
    return html


def render_compact_item(item, item_type, context):
    """Render an item in compact table format"""
    if not isinstance(item, dict):
        return ""

    # Extract the actual data (skip wrapper keys like 'digital', 'analog', 'dmr')
    data = item
    for key in ["digital", "analog", "dmr"]:
        if key in item and isinstance(item[key], dict):
            data = item[key]
            break

    if not isinstance(data, dict):
        return ""

    # Define compact display based on item type
    if item_type == "channel":
        # Compact channel display
        fields = [
            ("name", data.get("name", "")),
            ("rxFrequency", f"{data.get('rxFrequency', '')} MHz"),
            ("txFrequency", f"{data.get('txFrequency', '')} MHz"),
            ("power", data.get("power", "")),
        ]

        # Add type-specific fields
        if "colorCode" in data:  # Digital
            fields.extend(
                [
                    ("colorCode", f"CC{data.get('colorCode', '')}"),
                    ("timeSlot", f"TS{data.get('timeSlot', '')}"),
                    ("contact", data.get("contact", "")),
                ]
            )
        elif "bandwidth" in data:  # Analog
            fields.append(("bandwidth", data.get("bandwidth", "")))

    elif item_type == "contact":
        fields = [
            ("name", data.get("name", "")),
            ("type", data.get("type", "")),
            ("number", data.get("number", "")),
        ]

    elif item_type == "groupList":
        contacts_list = data.get("contacts", [])
        fields = [
            ("name", data.get("name", "")),
            ("contacts", f"{len(contacts_list)} contacts"),
        ]

    elif item_type == "zone":
        a_channels = data.get("A", [])
        b_channels = data.get("B", [])
        fields = [
            ("name", data.get("name", "")),
            ("channels", f"{len(a_channels) + len(b_channels)} channels"),
        ]

    else:
        # Generic compact view
        fields = [(k, v) for k, v in list(data.items())[:4]]

    html = '<div class="compact-fields">'
    for key, value in fields:
        if value:
            html += f'<span class="field"><strong>{escape(str(key))}:</strong> '
            if key in ["contact", "scanList", "groupList"]:
                html += format_value(value, key, context)
            else:
                html += escape(str(value))
            html += "</span>"
    html += "</div>"

    return html


def render_dict(data, level=0, context=None):
    """Render a dictionary as HTML"""
    html = '<dl class="properties">\n'
    for key, value in data.items():
        desc = get_description(key)
        html += f"<dt>{escape(str(key))}"
        if desc:
            html += f' <span class="desc">— {escape(desc)}</span>'
        html += "</dt>\n"
        html += "<dd>"

        if isinstance(value, dict):
            html += render_dict(value, level + 1, context)
        elif isinstance(value, list):
            # Check if it's a reference list
            if key == "contacts" and all(isinstance(v, str) for v in value):
                html += format_reference_list(value, "contacts", context)
            elif key in ["A", "B"] and all(isinstance(v, str) for v in value):
                html += format_reference_list(value, "channels", context)
            else:
                html += render_list(value, level + 1, context)
        else:
            html += format_value(value, key, context)
        html += "</dd>\n"
    html += "</dl>\n"
    return html


def render_list(items, level=0, context=None):
    """Render a list as HTML"""
    if not items:
        return '<span class="empty-list">[]</span>'

    html = '<ul class="items">\n'
    for item in items:
        html += "<li>"
        if isinstance(item, dict):
            html += render_dict(item, level + 1, context)
        elif isinstance(item, list):
            html += render_list(item, level + 1, context)
        else:
            html += format_value(item, context=context)
        html += "</li>\n"
    html += "</ul>\n"
    return html


def get_item_id(item):
    """Extract ID from a codeplug item"""
    if isinstance(item, dict):
        # Direct id field
        if "id" in item:
            return item["id"]
        # Try nested structures
        for key in item.keys():
            if isinstance(item[key], dict):
                item_data = item[key]
                if "id" in item_data:
                    return item_data["id"]
                elif "name" in item_data:
                    return item_data["name"]
    return None


def get_item_name(item):
    """Extract name from a codeplug item"""
    if isinstance(item, dict):
        # Direct name field
        if "name" in item:
            return item["name"]
        # Try nested structures
        for key in item.keys():
            if isinstance(item[key], dict):
                item_data = item[key]
                if "name" in item_data:
                    return item_data["name"]
                elif "id" in item_data:
                    return item_data["id"]
    return None


def build_reference_map(data):
    """Build a map of all IDs to names for reference resolution"""
    ref_map = {}

    # Map contacts
    if "contacts" in data:
        for contact in data["contacts"]:
            contact_id = get_item_id(contact)
            contact_name = get_item_name(contact)
            if contact_id:
                ref_map[f"contacts-{contact_id}"] = contact_name or contact_id

    # Map channels
    if "channels" in data:
        for channel in data["channels"]:
            channel_id = get_item_id(channel)
            channel_name = get_item_name(channel)
            if channel_id:
                ref_map[f"channels-{channel_id}"] = channel_name or channel_id

    # Map group lists
    if "groupLists" in data:
        for gl in data["groupLists"]:
            gl_id = get_item_id(gl)
            gl_name = get_item_name(gl)
            if gl_id:
                ref_map[f"groupLists-{gl_id}"] = gl_name or gl_id

    # Map zones
    if "zones" in data:
        for zone in data["zones"]:
            zone_id = get_item_id(zone)
            zone_name = get_item_name(zone)
            if zone_id:
                ref_map[f"zones-{zone_id}"] = zone_name or zone_id

    return ref_map


def render_section(
    title, data, section_id, show_index=True, compact=False, context=None
):
    """Render a major section with table of contents"""
    html = f'<section id="{section_id}">\n'
    html += f"<h2>{escape(title)}</h2>\n"

    if isinstance(data, list) and data and show_index:
        # Create an index for list items
        html += '<div class="index">\n'
        html += "<h3>Index</h3>\n"
        html += '<ul class="index-list">\n'
        for i, item in enumerate(data):
            item_id = get_item_id(item)
            item_name = get_item_name(item)
            if item_id:
                anchor = f"{section_id}-{item_id}"
                display_name = item_name or item_id
                html += f'<li><a href="#{anchor}">{escape(display_name)}</a></li>\n'
        html += "</ul>\n"
        html += "</div>\n"

        # Render items with anchors
        html += '<div class="items-container">\n'

        # Determine item type for compact rendering
        item_type_map = {
            "channels": "channel",
            "contacts": "contact",
            "groupLists": "groupList",
            "zones": "zone",
            "roamingChannels": "roamingChannel",
            "roamingZones": "roamingZone",
        }
        item_type = item_type_map.get(section_id, None)

        for i, item in enumerate(data):
            item_id = get_item_id(item)
            if item_id:
                anchor = f"{section_id}-{item_id}"
                html += f'<div class="item {"compact-item" if compact else ""}" id="{anchor}">\n'

                # Compact header with key info
                if compact and item_type:
                    html += f'<div class="item-header">'
                    html += f"<h4>{escape(get_item_name(item) or item_id)}</h4>"
                    html += render_compact_item(item, item_type, context)
                    html += "</div>"
                else:
                    html += f"<h4>{escape(get_item_name(item) or item_id)}</h4>\n"
            else:
                html += f'<div class="item {"compact-item" if compact else ""}">\n'
                html += f"<h4>Item {i+1}</h4>\n"

            # Details (collapsible for compact items)
            if compact:
                html += '<details class="item-details">'
                html += "<summary>Details</summary>"

            if isinstance(item, dict):
                html += render_dict(item, context=context)
            else:
                html += format_value(item, context=context)

            if compact:
                html += "</details>"

            html += "</div>\n"
        html += "</div>\n"
    elif isinstance(data, dict):
        html += render_dict(data, context=context)
    elif isinstance(data, list):
        html += render_list(data, context=context)
    else:
        html += format_value(data, context=context)

    html += "</section>\n"
    return html


def generate_html(yaml_file, output_file):
    """Generate HTML from YAML codeplug file"""

    # Load YAML
    print(f"Loading {yaml_file}...")
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    # Build reference map
    print("Building reference map...")
    ref_map = build_reference_map(data)
    context = {"ref_names": ref_map}

    # Start HTML document
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMR Codeplug</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }

        header {
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            margin: -20px -20px 30px -20px;
            border-radius: 5px 5px 0 0;
        }

        h1 {
            margin: 0 0 10px 0;
        }

        .version {
            color: #95a5a6;
            font-size: 0.9em;
        }

        nav {
            background: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 20px;
            z-index: 100;
        }

        nav h2 {
            margin-top: 0;
            color: #2c3e50;
        }

        nav ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        nav li {
            display: inline;
        }

        nav a {
            color: #3498db;
            text-decoration: none;
            padding: 8px 15px;
            background: #ecf0f1;
            border-radius: 4px;
            display: inline-block;
            transition: background 0.2s;
        }

        nav a:hover {
            background: #3498db;
            color: white;
        }

        section {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }

        h3 {
            color: #34495e;
            margin-top: 20px;
        }

        h4 {
            color: #2c3e50;
            margin: 0;
            font-size: 1.1em;
        }

        .index {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }

        .index h3 {
            margin-top: 0;
        }

        .index-list {
            columns: 4;
            column-gap: 20px;
        }

        .index-list li {
            break-inside: avoid;
            margin-bottom: 5px;
            font-size: 0.9em;
        }

        .index-list a {
            color: #3498db;
            text-decoration: none;
        }

        .index-list a:hover {
            text-decoration: underline;
        }

        dl.properties {
            margin: 10px 0;
        }

        dt {
            font-weight: bold;
            color: #555;
            margin-top: 8px;
            padding: 4px 8px;
            background: #f8f9fa;
            border-radius: 3px;
            font-size: 0.9em;
        }

        dt .desc {
            font-weight: normal;
            color: #7f8c8d;
            font-size: 0.95em;
            font-style: italic;
        }

        dd {
            margin-left: 20px;
            margin-bottom: 8px;
            padding-left: 10px;
            border-left: 2px solid #ecf0f1;
        }

        .item {
            margin: 12px 0;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            scroll-margin-top: 100px;
            background: white;
        }

        .compact-item {
            padding: 10px 15px;
            margin: 8px 0;
        }

        .item-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }

        .item-header h4 {
            min-width: 200px;
            margin: 0;
        }

        .compact-fields {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 0.9em;
            flex: 1;
        }

        .compact-fields .field {
            white-space: nowrap;
        }

        .item-details {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ecf0f1;
        }

        .item-details summary {
            cursor: pointer;
            color: #3498db;
            font-size: 0.9em;
            user-select: none;
        }

        .item-details summary:hover {
            text-decoration: underline;
        }

        .item:target {
            background: #fff9e6;
            border-color: #f39c12;
        }

        ul.items {
            list-style: none;
            padding-left: 0;
        }

        ul.items > li {
            margin: 8px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .string {
            color: #27ae60;
        }

        .number {
            color: #e74c3c;
        }

        .bool {
            color: #9b59b6;
            font-weight: bold;
        }

        .null {
            color: #95a5a6;
            font-style: italic;
        }

        .empty-list {
            color: #95a5a6;
            font-style: italic;
        }

        .ref-link {
            color: #3498db;
            text-decoration: none;
            padding: 2px 6px;
            background: #ebf5fb;
            border-radius: 3px;
            font-weight: 500;
        }

        .ref-link:hover {
            background: #3498db;
            color: white;
        }

        .ref-list {
            display: inline-flex;
            flex-wrap: wrap;
            gap: 5px;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .index-list {
                columns: 1;
            }

            nav ul {
                flex-direction: column;
            }

            .item-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .compact-fields {
                flex-direction: column;
                gap: 5px;
            }
        }

        @media print {
            nav {
                position: static;
            }

            .index {
                page-break-inside: avoid;
            }

            .item {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
"""

    # Header
    version = data.get("version", "unknown")
    html += f"""
    <header>
        <h1>DMR Codeplug</h1>
        <div class="version">Version: {escape(str(version))}</div>
    </header>
"""

    # Navigation - Settings moved to last
    sections = []
    if "radioIDs" in data:
        sections.append(("radioIDs", f'Radio IDs ({len(data["radioIDs"])})'))
    if "channels" in data:
        sections.append(("channels", f'Channels ({len(data["channels"])})'))
    if "contacts" in data:
        sections.append(("contacts", f'Contacts ({len(data["contacts"])})'))
    if "groupLists" in data:
        sections.append(("groupLists", f'Group Lists ({len(data["groupLists"])})'))
    if "zones" in data:
        sections.append(("zones", f'Zones ({len(data["zones"])})'))
    if "roamingChannels" in data:
        sections.append(
            ("roamingChannels", f'Roaming Channels ({len(data["roamingChannels"])})')
        )
    if "roamingZones" in data:
        sections.append(
            ("roamingZones", f'Roaming Zones ({len(data["roamingZones"])})')
        )
    if "positioning" in data:
        sections.append(("positioning", "Positioning"))
    if "sms" in data:
        sections.append(("sms", "SMS"))
    if "settings" in data:
        sections.append(("settings", "Settings"))

    html += "<nav>\n"
    html += "<h2>Table of Contents</h2>\n"
    html += "<ul>\n"
    for section_id, title in sections:
        html += f'<li><a href="#{section_id}">{escape(title)}</a></li>\n'
    html += "</ul>\n"
    html += "</nav>\n"

    # Render sections
    for section_id, title in sections:
        # Show index and compact view for list-based sections
        show_index = section_id in [
            "channels",
            "contacts",
            "groupLists",
            "zones",
            "roamingChannels",
            "roamingZones",
        ]
        compact = section_id in [
            "channels",
            "contacts",
            "groupLists",
            "zones",
            "roamingChannels",
            "roamingZones",
        ]
        html += render_section(
            title, data[section_id], section_id, show_index, compact, context
        )

    # Close HTML
    html += """
</body>
</html>
"""

    # Write output
    print(f"Writing {output_file}...")
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Done! Generated {output_file}")
    print(f"Open it in your browser: file://{Path(output_file).absolute()}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]
    else:
        yaml_file = "plug.yaml"

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "codeplug.html"

    generate_html(yaml_file, output_file)
