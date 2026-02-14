# Petrol Pump V2 - Print Format Style Guide

> **IMPORTANT**: Read this file BEFORE creating any new print format for this app.
> Every report must follow this exact structure and styling to maintain consistency.

---

## 1. File Structure

Each print format lives in its own folder under `print_format/`:

```
print_format/
  __init__.py
  PRINT_FORMAT_GUIDE.md          <-- THIS FILE
  {report_name}/
    __init__.py
    {report_name}.json           <-- Print Format definition
    {report_name}.html           <-- Jinja HTML template
```

### JSON Definition Template

```json
{
  "align_labels_right": 0,
  "creation": "YYYY-MM-DD HH:MM:SS.000000",
  "custom_format": 1,
  "disabled": 0,
  "doc_type": "TARGET DOCTYPE NAME",
  "docstatus": 0,
  "doctype": "Print Format",
  "font_size": 0,
  "line_breaks": 0,
  "modified": "YYYY-MM-DD HH:MM:SS.000000",
  "modified_by": "Administrator",
  "module": "Petrol Pump V2",
  "name": "PRINT FORMAT DISPLAY NAME",
  "owner": "Administrator",
  "print_format_type": "Jinja",
  "raw_printing": 0,
  "show_section_headings": 1,
  "standard": "Yes"
}
```

---

## 2. HTML Template Structure

Every report HTML must follow this exact skeleton:

```
1. Jinja variables (company lookup)
2. <style> block (all CSS)
3. <div class="{prefix}-report">
   a. HEADER (company info + title bar)
   b. DOCUMENT INFO GRID (4-6 cells in a row)
   c. BODY SECTIONS (tables, summary boxes, etc.)
   d. FOOTER (fixed at bottom - signatures + page info + page number)
</div>
```

### Company Lookup (Line 1-2 of every template)

```jinja
{%- set company = frappe.db.get_default("company") -%}
{%- set company_doc = frappe.get_doc("Company", company) -%}
```

> **NEVER** use `frappe.defaults.get_defaults()` — it does not work in Jinja context.

---

## 3. CSS Conventions

### 3.1 Page Setup (MANDATORY in every report)

```css
@page {
    size: A4;
    margin: 12mm 10mm 35mm 10mm;  /* extra bottom for fixed footer */
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #999;
    }
}
@media print {
    .print-format { padding: 0 !important; }
    .page-break { page-break-before: always; }
}
```

### 3.2 Footer (normal flow — NOT fixed)

The footer sits at the end of the content (NOT position: fixed). It flows naturally after all body sections:

```css
.{prefix}-footer {
    margin-top: 25px;
    border-top: 2px solid {theme_color};
    padding-top: 10px;
}
```

### 3.3 Force Exact Print Colors (MANDATORY)

Browsers strip background colors when printing by default. Always add these to the report wrapper:

```css
.{prefix}-report {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: #333;
    line-height: 1.4;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
}
```

### 3.4 Class Prefix Convention

Each report uses a unique 2-4 letter prefix to avoid CSS collisions:

| Report               | Prefix  | Theme Color |
|----------------------|---------|-------------|
| Day Closing          | `dc-`   | `#2c3e50` (Dark Blue)   |
| Shift Reading        | `sr-`   | `#1a5276` (Navy Blue)   |
| Dip Reading          | `dip-`  | `#1e8449` (Green)       |
| Fuel Testing         | `ft-`   | `#7d3c98` (Purple)      |
| Fuel Transfer        | `ftr-`  | `#d35400` (Orange)      |
| _New Report_         | `xx-`   | _Pick unused color_     |

### 3.5 Standard Font Sizes

| Element              | Size   |
|----------------------|--------|
| Company name         | 18pt   |
| Report title bar     | 13pt   |
| Info value           | 10pt   |
| Body / table cell    | 9pt    |
| Table header         | 8pt    |
| Info label           | 7pt    |
| Page info / watermark| 7.5pt  |
| Signature label      | 8.5pt  |

---

## 4. Header Block (MANDATORY)

```html
<div class="{prefix}-header">
    <div class="{prefix}-header-top">
        <div class="{prefix}-company-info">
            <p class="{prefix}-company-name">{{ company_doc.company_name or company }}</p>
            {% if company_doc.address %}
                <p class="{prefix}-company-address">{{ company_doc.address }}</p>
            {% endif %}
        </div>
        <div class="{prefix}-pump-info">
            <div class="{prefix}-pump-label">Petrol Pump</div>
            <p class="{prefix}-pump-name">{{ doc.petrol_pump }}</p>
            {% if company_doc.company_logo %}
                <img class="{prefix}-logo" src="{{ company_doc.company_logo }}" alt="Logo">
            {% endif %}
        </div>
    </div>
    <div class="{prefix}-title">REPORT TITLE HERE</div>
</div>
```

Header layout:
- **Left side**: Company name, address, phone, email
- **Right side**: Petrol Pump name (prominent, 14pt) + company logo below it
- Bottom border: 3px solid {theme_color}
- Title bar: background {theme_color}, white text, centered, uppercase, letter-spacing 1px

---

## 5. Document Info Grid (MANDATORY)

```html
<div class="{prefix}-info-grid">
    <div class="{prefix}-info-cell">
        <div class="{prefix}-info-label">LABEL</div>
        <div class="{prefix}-info-value">VALUE</div>
    </div>
    <!-- repeat for each info field -->
</div>
```

- Grid: `display: flex; flex-wrap: wrap; border: 1px solid #ddd;`
- Cells: `flex: 1 1 25%; min-width: 140px; padding: 6px 10px;`
- Labels: uppercase, 7pt, color #888
- Values: 10pt, font-weight 600, theme color

---

## 6. Section Titles

```html
<div class="{prefix}-section-title">SECTION NAME</div>
```

CSS: `background: {light_theme_color}; border-left: 4px solid {theme_color};`
- Uppercase, 10pt, bold, theme color text
- Light backgrounds per theme (e.g., #ecf0f1 for dark blue, #d6eaf8 for navy, etc.)

---

## 7. Tables

```html
<table class="{prefix}-table">
    <thead>
        <tr><th>#</th><th>Column</th><th class="text-right">Amount</th></tr>
    </thead>
    <tbody>
        {% for row in doc.child_table %}
        <tr>
            <td class="text-center">{{ loop.index }}</td>
            <td>{{ row.field }}</td>
            <td class="text-right">{{ frappe.format_value(row.amount, {"fieldtype": "Currency"}) }}</td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        <tr>
            <td colspan="X" class="text-right"><strong>Total</strong></td>
            <td class="text-right"><strong>TOTAL VALUE</strong></td>
        </tr>
    </tfoot>
</table>
```

- Header: background {theme_color}, white text, 8pt uppercase
- Rows: alternating #f9f9f9
- Footer: background {light_theme_color}, border-top 2px solid {theme_color}
- Always include row numbers (#) as first column
- Always include totals row in tfoot

### Accumulating Totals in Jinja

```jinja
{% set totals = {"liters": 0, "amount": 0} %}
{% for row in doc.table %}
{% if totals.update({"liters": totals.liters + (row.liters or 0), "amount": totals.amount + (row.amount or 0)}) %}{% endif %}
<!-- row content -->
{% endfor %}
```

---

## 8. Summary Boxes

```html
<div class="{prefix}-summary-grid">
    <div class="{prefix}-summary-box">
        <div class="{prefix}-summary-box-title">BOX TITLE</div>
        <div class="{prefix}-summary-box-body">
            <div class="{prefix}-summary-row">
                <span class="{prefix}-summary-row-label">Label</span>
                <span class="{prefix}-summary-row-value">Value</span>
            </div>
        </div>
    </div>
</div>
```

- Grid: `display: flex; gap: 10px;`
- Box title: background {theme_color}, white text, 8pt uppercase
- Rows: `display: flex; justify-content: space-between; border-bottom: 1px dotted #e0e0e0;`

---

## 9. Footer Block (MANDATORY — normal flow, end of content)

```html
<div class="{prefix}-footer">
    <div class="{prefix}-signatures">
        <div class="{prefix}-signature-block">
            <div class="{prefix}-signature-line">Role Name</div>
        </div>
        <!-- 3-4 signature blocks -->
    </div>

    <div class="{prefix}-page-info">
        {{ doc.name }} | {{ frappe.format_value(doc.reading_date, {"fieldtype": "Date"}) }} | {{ doc.petrol_pump }}
        <br>
        Printed on {{ frappe.format_value(frappe.utils.now_datetime(), {"fieldtype": "Datetime"}) }} by {{ frappe.session.user }}
    </div>

    <div class="{prefix}-page-number">
        <!-- CSS counter handles "Page X of Y" -->
    </div>

    <div class="{prefix}-watermark">
        {{ company_doc.company_name or company }}
    </div>
</div>
```

Footer CSS:
```css
.{prefix}-footer {
    margin-top: 25px;
    border-top: 2px solid {theme_color};
    padding-top: 10px;
}
.{prefix}-signatures {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}
.{prefix}-signature-block { text-align: center; width: 30%; }
.{prefix}-signature-line {
    border-top: 1px solid #333;
    padding-top: 5px;
    font-size: 8.5pt;
    font-weight: 600;
    color: #555;
    margin-top: 30px;
}
.{prefix}-page-info {
    text-align: center;
    font-size: 7.5pt;
    color: #999;
    padding-top: 5px;
    border-top: 1px solid #e0e0e0;
}
.{prefix}-page-number {
    text-align: center;
    font-size: 8pt;
    color: #999;
    margin-top: 3px;
}
.{prefix}-watermark {
    font-size: 7pt;
    color: #ccc;
    text-align: center;
    margin-top: 2px;
}
```

---

## 10. Resolving Link Field Names (IMPORTANT)

Link fields store the `name` (ID) of linked documents (e.g., "FUEL-TYPE-00001"). Always resolve them to display names:

```jinja
{# Fuel Type → fuel_type_name #}
{{ frappe.db.get_value("Fuel Type", row.fuel_type, "fuel_type_name") or row.fuel_type or "—" }}

{# Fuel Tank → tank_name (also show fuel type) #}
{%- set tank_name = frappe.db.get_value("Fuel Tank", doc.fuel_tank, "tank_name") or doc.fuel_tank -%}
{%- set tank_fuel = frappe.db.get_value("Fuel Tank", doc.fuel_tank, "fuel_type") -%}
{%- set fuel_name = frappe.db.get_value("Fuel Type", tank_fuel, "fuel_type_name") if tank_fuel else "" -%}
{{ tank_name }}{% if fuel_name %} ({{ fuel_name }}){% endif %}

{# Dispenser → dispenser_name #}
{{ frappe.db.get_value("Dispenser", row.dispenser, "dispenser_name") or row.dispenser }}
```

| Link DocType | Name Field      | Display Field       |
|-------------|-----------------|---------------------|
| Fuel Type   | FUEL-TYPE-00001 | `fuel_type_name`    |
| Fuel Tank   | TANK-00001      | `tank_name`         |
| Dispenser   | DISP-00001      | `dispenser_name`    |
| Nozzle      | NOZ-00001       | `nozzle_name`       |

---

## 11. Formatting Values

Always use `frappe.format_value()` for proper locale-aware formatting:

```jinja
{{ frappe.format_value(value, {"fieldtype": "Currency"}) }}
{{ frappe.format_value(value, {"fieldtype": "Float", "precision": 2}) }}
{{ frappe.format_value(value, {"fieldtype": "Date"}) }}
{{ frappe.format_value(value, {"fieldtype": "Datetime"}) }}
```

---

## 12. Conditional Sections

Only show child table sections if data exists:

```jinja
{% if doc.child_table and doc.child_table|length > 0 %}
    <!-- section content -->
{% endif %}
```

---

## 13. Color Coding Conventions

| Meaning       | Color     | Usage                                |
|---------------|-----------|--------------------------------------|
| Positive      | `#27ae60` | Excess, Pass, Zero variance          |
| Negative      | `#e74c3c` | Short, Fail, Expenses                |
| Warning       | `#d35400` | Pending                              |
| Neutral       | `#2c3e50` | Default text                         |
| Muted         | `#888`    | Labels, secondary info               |

---

## 14. Checklist Before Finalizing a New Report

- [ ] Company lookup uses `frappe.db.get_default("company")`
- [ ] CSS class prefix is unique and not used by other reports
- [ ] Theme color is distinct from existing reports
- [ ] `-webkit-print-color-adjust: exact` on report wrapper
- [ ] Header has company name (left) and petrol pump name (right) + logo
- [ ] Info grid has Document No, Date, and key identifiers
- [ ] All Link fields resolved to display names (fuel_type_name, tank_name, etc.)
- [ ] All tables have row numbers and totals
- [ ] Footer in normal flow (NOT position: fixed)
- [ ] Signatures section has 3-4 role-appropriate blocks
- [ ] Page info shows doc name, date, and print timestamp
- [ ] Page number element included
- [ ] Values use `frappe.format_value()` formatting
- [ ] JSON definition has correct `doc_type` and `module`
- [ ] `__init__.py` exists in both `print_format/` and subfolder
