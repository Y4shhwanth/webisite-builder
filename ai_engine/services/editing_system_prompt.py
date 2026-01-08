"""
Editing System Prompt Builder

Builds context-aware system prompts for the editing agent that include
design constraints, typography rules, color palette, and element context.
"""

from typing import Optional


def build_editing_system_prompt(
    design_context: Optional[dict] = None,
    selected_element: Optional[dict] = None
) -> str:
    """
    Build a context-aware editing system prompt.

    Args:
        design_context: Extracted design metadata (fonts, colors, sections, tokens)
        selected_element: Currently selected element info (selector, tag, classes, etc.)

    Returns:
        Complete system prompt string for the editing agent
    """
    prompt_parts = [BASE_EDITING_PROMPT]

    # Add design system constraints if available
    if design_context:
        prompt_parts.append(build_design_constraints(design_context))

    # Add selected element context if available
    if selected_element:
        prompt_parts.append(build_element_context(selected_element))

    # Add editing rules
    prompt_parts.append(EDITING_RULES)

    return '\n\n'.join(prompt_parts)


BASE_EDITING_PROMPT = """You are an expert website editor agent. Your job is to make precise edits to HTML websites.

## CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE:

1. **ALWAYS USE TOOLS** - Never just describe what to do. You MUST use the tools to make actual changes.
2. **ALWAYS CALL finalize_edit** - Every edit session MUST end with a finalize_edit call.
3. **USE modify_class FOR TAILWIND** - For Tailwind CSS class changes (like colors, spacing), use the modify_class tool.
4. **USE find_and_replace FOR DIRECT CHANGES** - If selectors don't work, use find_and_replace for direct string changes.

## AVAILABLE TOOLS:
- **modify_class**: Replace one CSS class with another (e.g., 'bg-primary' → 'bg-green-500', 'text-white' → 'text-red-500')
- **find_and_replace**: Direct string replacement in HTML
- **edit_text**: Change text content of an element
- **edit_style**: Add inline styles
- **finalize_edit**: REQUIRED - Call this when done to return the edited HTML

## WORKFLOW:
1. Understand the edit instruction
2. Use modify_class or find_and_replace to make the change
3. ALWAYS call finalize_edit with a summary

IMPORTANT: Do NOT just explain what you would do - actually DO IT using the tools!

## CRITICAL - NEVER USE PLACEHOLDERS:
- NEVER put "[Previous HTML content...]" or similar placeholders in the HTML
- NEVER truncate the HTML - use find_and_replace or modify_class to change specific parts
- When calling finalize_edit, you do NOT need to pass the full HTML - just pass a summary
- The system will automatically use the modified HTML from your edit tools"""


def build_design_constraints(design_context: dict) -> str:
    """Build design system constraints section."""
    lines = ["## DESIGN SYSTEM CONSTRAINTS (DO NOT VIOLATE)"]

    # Typography constraints
    fonts = design_context.get("fonts", {})
    if fonts.get("display") or fonts.get("body"):
        lines.append("\n### Typography")
        if fonts.get("display"):
            lines.append(f"- Display/Heading font: **{fonts['display']}**")
        if fonts.get("body"):
            lines.append(f"- Body/Text font: **{fonts['body']}**")
        if fonts.get("all_fonts"):
            lines.append(f"- All available fonts: {', '.join(fonts['all_fonts'])}")
        lines.append("- RULE: Do NOT introduce new fonts. Only use fonts listed above.")
        lines.append("- RULE: Maintain font hierarchy (headings use display font, body uses body font)")

    # Color palette constraints
    colors = design_context.get("colors", {})
    has_colors = any(colors.get(k) for k in ["primary", "accent", "background", "text", "surface"])
    if has_colors:
        lines.append("\n### Color Palette")
        if colors.get("primary"):
            lines.append(f"- Primary: `{colors['primary']}`")
        if colors.get("accent"):
            lines.append(f"- Accent: `{colors['accent']}`")
        if colors.get("background"):
            lines.append(f"- Background: `{colors['background']}`")
        if colors.get("surface"):
            lines.append(f"- Surface: `{colors['surface']}`")
        if colors.get("text"):
            lines.append(f"- Text: `{colors['text']}`")

        # List all CSS variables if available
        all_colors = colors.get("all_colors", {})
        if all_colors:
            lines.append(f"- CSS Variables available: {', '.join(f'--{k}' for k in list(all_colors.keys())[:10])}")

        lines.append("- RULE: ONLY use colors from this palette. Do not introduce new colors.")
        lines.append("- RULE: Use CSS variables (var(--color-name)) when available.")

    # Section structure
    sections = design_context.get("sections", [])
    if sections:
        section_types = [s.get("type") or s.get("tag") for s in sections]
        section_types = [s for s in section_types if s]  # Filter None
        if section_types:
            lines.append("\n### Page Structure")
            lines.append(f"Current sections: {' → '.join(section_types)}")
            lines.append("- RULE: Do not reorder sections unless explicitly asked.")
            lines.append("- RULE: Do not delete sections unless explicitly asked.")

    # Design tokens
    tokens = design_context.get("tokens", {})
    if tokens:
        lines.append("\n### Design Tokens")
        if tokens.get("spacing_strategy") and tokens["spacing_strategy"] != "unknown":
            lines.append(f"- Spacing style: **{tokens['spacing_strategy']}** (maintain this feel)")
        if tokens.get("border_radius") and tokens["border_radius"] != "unknown":
            lines.append(f"- Border radius: **{tokens['border_radius']}** (use consistently)")
        if tokens.get("shadow_style") and tokens["shadow_style"] != "unknown":
            lines.append(f"- Shadow style: **{tokens['shadow_style']}** (match existing)")

    # Template info
    template_id = design_context.get("template_id")
    if template_id and template_id != "unknown":
        lines.append(f"\n### Template: {template_id}")
        lines.append("- RULE: Edits should feel consistent with this template's aesthetic.")

    return '\n'.join(lines)


def build_element_context(selected_element: dict) -> str:
    """Build selected element context section."""
    lines = ["## TARGET ELEMENT"]

    if selected_element.get("selector"):
        lines.append(f"- Selector: `{selected_element['selector']}`")

    if selected_element.get("tag"):
        lines.append(f"- HTML Tag: `<{selected_element['tag']}>`")

    if selected_element.get("classes"):
        classes = selected_element["classes"]
        if isinstance(classes, list):
            classes = ' '.join(classes)
        lines.append(f"- CSS Classes: `{classes}`")

    # Show color-related classes specifically (important for color edits)
    if selected_element.get("color_classes"):
        color_classes = selected_element["color_classes"]
        if isinstance(color_classes, list) and color_classes:
            lines.append(f"- **Current color classes**: `{' '.join(color_classes)}`")
            lines.append("  (Use modify_class to change these for color edits)")

    if selected_element.get("parent_selector"):
        lines.append(f"- Parent: `{selected_element['parent_selector']}`")

    if selected_element.get("text"):
        text = selected_element["text"][:100]  # Truncate long text
        if len(selected_element.get("text", "")) > 100:
            text += "..."
        lines.append(f"- Text content: \"{text}\"")

    if selected_element.get("attributes"):
        attrs = selected_element["attributes"]
        if attrs:
            # Filter out 'class' since we show it above
            filtered_attrs = {k: v for k, v in attrs.items() if k != 'class'}
            if filtered_attrs:
                attr_str = ', '.join(f'{k}="{v}"' for k, v in list(filtered_attrs.items())[:5])
                lines.append(f"- Attributes: {attr_str}")

    # Include element's actual HTML for precise editing
    if selected_element.get("outer_html"):
        html = selected_element["outer_html"]
        if len(html) <= 500:
            lines.append(f"\n### Element HTML:\n```html\n{html}\n```")
        else:
            # Truncate but show beginning and end
            lines.append(f"\n### Element HTML (truncated):\n```html\n{html[:400]}...\n```")

    lines.append("\n**IMPORTANT**: Focus your edits on this element unless the instruction specifies otherwise.")
    lines.append("If the instruction is vague, assume it applies to this selected element.")
    lines.append("For color changes, use the modify_class tool with the exact class names shown above.")

    return '\n'.join(lines)


EDITING_RULES = """## QUICK REFERENCE FOR COMMON EDITS

### ⚠️ CRITICAL: USE SELECTORS FOR TARGETED EDITS
When changing a SPECIFIC element, ALWAYS provide the selector parameter!
Otherwise, the change will apply to ALL elements with that class.

### Color Changes (Tailwind) - ALWAYS USE SELECTOR:
```
modify_class(
    selector="h1.hero-title",  // Target THIS specific element
    old_class="text-white",
    new_class="text-blue-500"
)
```

BAD (affects ALL elements):
- modify_class(old_class="text-white", new_class="text-red-500")

GOOD (affects ONLY the target element):
- modify_class(selector="h1.hero-title", old_class="text-white", new_class="text-red-500")

### IMPORTANT - Specific Color Names:
When the user asks for a specific color like "blue", "red", "green", etc., use actual Tailwind colors:
- "blue" → bg-blue-500, text-blue-500
- "red" → bg-red-500, text-red-500
- "green" → bg-green-500, text-green-500
- "yellow" → bg-yellow-500, text-yellow-500
- "purple" → bg-purple-500, text-purple-500
- "pink" → bg-pink-500, text-pink-500
- "orange" → bg-orange-500, text-orange-500
- "cyan" → bg-cyan-500, text-cyan-500
- "white" → bg-white, text-white
- "black" → bg-black, text-black

DO NOT substitute "primary" or "accent" when the user asks for a specific color name!

### Text Changes:
- Use edit_text(selector="h1.title", new_text="New Title")
- Or find_and_replace(find="Old text", replace="New text")

### Adding Classes:
- find_and_replace(find='class="existing-class"', replace='class="existing-class text-red-500"')

### REMEMBER:
- ALWAYS use the selector from TARGET ELEMENT section
- ALWAYS call finalize_edit when done
- For Tailwind class changes, use modify_class WITH SELECTOR
- If one tool fails, try find_and_replace"""


def build_user_prompt(instruction: str, html: str, design_context: Optional[dict] = None) -> str:
    """
    Build the user prompt for an edit request.

    Args:
        instruction: The user's edit instruction
        html: Current HTML (may be truncated)
        design_context: Optional design context for additional info

    Returns:
        User prompt string
    """
    # Truncate HTML if too long (preserve head and key sections)
    max_html_length = 50000
    if len(html) > max_html_length:
        html = _truncate_html_intelligently(html, max_html_length)

    prompt = f"""Please edit this website based on the following instruction:

## INSTRUCTION
{instruction}

## CURRENT HTML
```html
{html}
```

## YOUR TASK
1. First, analyze the DOM to understand the structure (use analyze_dom tool if needed)
2. Identify the exact element(s) that need to be modified
3. Make the necessary edits using the appropriate tools
4. Call finalize_edit with the updated HTML and a summary of changes

Remember: Make minimal, targeted changes. Preserve the design system."""

    return prompt


def _truncate_html_intelligently(html: str, max_length: int) -> str:
    """
    Truncate HTML while preserving structure.
    Keeps head, beginning of body, and end of body.
    """
    if len(html) <= max_length:
        return html

    # Try to find key markers
    head_end = html.find('</head>')
    body_start = html.find('<body')

    if head_end == -1 or body_start == -1:
        # Can't parse structure, do simple truncation
        return html[:max_length] + "\n\n<!-- HTML truncated for length -->"

    # Keep all of head
    head_section = html[:head_end + 7]

    # Calculate remaining space
    remaining = max_length - len(head_section) - 100  # 100 for truncation message

    # Split remaining between start and end of body
    body_content = html[body_start:]
    half = remaining // 2

    body_start_section = body_content[:half]
    body_end_section = body_content[-half:]

    return f"""{head_section}

{body_start_section}

<!-- ... HTML truncated ({len(html) - max_length} characters removed) ... -->

{body_end_section}"""
