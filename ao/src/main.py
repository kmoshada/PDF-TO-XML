import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
import re
import os
import html
import flet as ft
import webbrowser
import spacy

nlp = spacy.load("en_core_web_sm")

# ----------- PDF Extraction Logic ------------
def extract_info_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):  # Reads ALL pages
            text += doc[page_num].get_text("text")

        metadata = doc.metadata
        title = metadata.get("title", "N/A")
        author = metadata.get("author", "N/A")
        subject = metadata.get("subject", "N/A")
        creator = metadata.get("creator", "N/A")
        producer = metadata.get("producer", "N/A")
        creation_date = metadata.get("creationDate", "N/A")

        # Title Extraction
        if title == "N/A" or not title:
            lines = text.split('\n')
            potential_titles = [line.strip() for line in lines[:5] if line.strip() and len(line) > 5 and not re.match(r'^\d+$', line)]
            if potential_titles:
                title = max(potential_titles, key=len)
                if len(title) > 100:
                    title = title[:100] + "..."

        # Author Extraction using spaCy
        if author == "N/A" or not author:
            search_area = "\n".join(text.split('\n')[:20])  # Top 20 lines
            nlp_doc = nlp(search_area)
            authors_found = []

            for ent in nlp_doc.ents:
                if ent.label_ == "PERSON" and ent.text.strip() not in authors_found and len(ent.text.strip()) > 3:
                    authors_found.append(ent.text.strip())

            if authors_found:
                author = ", ".join(authors_found)

        # Abstract Extraction
        abstract = "N/A"
        abstract_match = re.search(r'(?i)Abstract\s*(.*?)(?=\n\s*\n|\n\d+\.?\s|\nIntroduction|\nI\.\s*Introduction)', text, re.DOTALL)
        if abstract_match:
            abstract = re.sub(r'\s+', ' ', abstract_match.group(1)).strip()

        # Keywords Extraction
        keywords = "N/A"
        keywords_match = re.search(r'(?i)Keywords?:\s*(.*?)(?=\n\s*\n|\n[A-Z]|\n\d+\.?\s|\nIntroduction|\nI\.\s*Introduction)', text, re.DOTALL)
        if keywords_match:
            keywords = re.sub(r'\s+', ' ', keywords_match.group(1)).strip()
        else:
            alt_match = re.search(r'(?i)(author\s+keywords|Index Terms)[\s:]*\n?(.*)', text)
            if alt_match:
                keywords = alt_match.group(2).strip()

        # DOI Extraction
        doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', text, re.I)
        doi = doi_match.group(1) if doi_match else "N/A"

        doc.close()

        return {
            "title": title if title != "N/A" else "Title Not Found",
            "author": author if author != "N/A" else "Author Not Found",
            "abstract": abstract,
            "keywords": keywords,
            "subject": subject,
            "creator": creator,
            "producer": producer,
            "creation_date": creation_date,
            "doi": doi
        }

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            "title": "Error",
            "author": "Error",
            "abstract": "Error",
            "keywords": "Error",
            "subject": "Error",
            "creator": "Error",
            "producer": "Error",
            "creation_date": "Error",
            "doi": "Error"
        }

# ----------- XML Creation ------------
def create_xml_output(papers_data, output_filename="research_papers.xml"):
    root = ET.Element("ResearchPapers")

    for paper in papers_data:
        paper_element = ET.SubElement(root, "Paper")
        ET.SubElement(paper_element, "DOI").text = paper.get("doi", "N/A")
        ET.SubElement(paper_element, "FileName").text = paper.get("filename", "N/A")
        ET.SubElement(paper_element, "Title").text = html.escape(paper["title"])
        ET.SubElement(paper_element, "Author").text = html.escape(paper["author"])
        ET.SubElement(paper_element, "Abstract").text = html.escape(paper["abstract"])
        ET.SubElement(paper_element, "Keywords").text = html.escape(paper["keywords"])

        metadata_element = ET.SubElement(paper_element, "Metadata")
        ET.SubElement(metadata_element, "Subject").text = paper["subject"]
        ET.SubElement(metadata_element, "Creator").text = paper["creator"]
        ET.SubElement(metadata_element, "Producer").text = paper["producer"]
        ET.SubElement(metadata_element, "CreationDate").text = paper["creation_date"]

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(output_filename, encoding="utf-8", xml_declaration=True)
    print(f"XML output saved to {output_filename}")
    return os.path.abspath(output_filename)

# ----------- Flet GUI Logic ------------
def main(page: ft.Page):
    selected_pdf_paths = []

    def select_files(e):
        file_picker.pick_files(allow_multiple=True, allowed_extensions=["pdf"])

    def files_selected(e: ft.FilePickerResultEvent):
        nonlocal selected_pdf_paths
        if e.files:
            selected_pdf_paths = [file.path for file in e.files]
            if len(selected_pdf_paths) == 1:
                selected_files_text.value = os.path.basename(selected_pdf_paths[0])
            else:
                selected_files_text.value = f"{len(selected_pdf_paths)} files selected"
            process_button.disabled = False
        else:
            selected_files_text.value = "No files selected."
            selected_pdf_paths = []
            process_button.disabled = True
        page.update()

    def process_pdfs(e):
        if not selected_pdf_paths:
            output_text.value = "Please select PDF files."
            page.update()
            return

        extracted_data = []
        output_text.value = ""

        for paper_path in selected_pdf_paths:
            output_text.value += f"Processing: {os.path.basename(paper_path)}\n"
            page.update()
            info = extract_info_from_pdf(paper_path)
            info["filename"] = os.path.basename(paper_path)
            extracted_data.append(info)

        output_xml_filename = "research_papers.xml"
        if len(selected_pdf_paths) == 1:
            single_pdf_filename = os.path.basename(selected_pdf_paths[0])
            output_xml_filename = os.path.splitext(single_pdf_filename)[0] + ".xml"

        xml_path = create_xml_output(extracted_data, output_xml_filename)
        output_text.value += f"\nAll done! XML file saved to:\n{xml_path}"
        page.update()
        webbrowser.open(xml_path)

    file_picker = ft.FilePicker(on_result=files_selected)
    page.overlay.append(file_picker)

    selected_files_text = ft.TextField(
        label="Selected PDF Files",
        read_only=True,
        expand=True,
        border_radius=ft.border_radius.all(8)
    )

    process_button = ft.ElevatedButton(
        "Process PDFs",
        on_click=process_pdfs,
        disabled=True,
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.all(12),
        )
    )

    output_text = ft.Text(value="", selectable=True, expand=True)

    progress_container = ft.Container(visible=True)

    page.add(
        ft.Column([
            ft.Text(
                "Research Paper Extractor",
                style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton(
                    "Select PDF Files",
                    on_click=select_files,
                    icon=ft.Icons.FOLDER_OPEN,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.all(12)
                    )
                ),
                selected_files_text,
                process_button
            ],
                alignment=ft.MainAxisAlignment.START),
            progress_container,
            ft.Text("Output Log:", style=ft.TextThemeStyle.BODY_LARGE),
            ft.Container(
                content=ft.Column([output_text], scroll=ft.ScrollMode.ADAPTIVE),
                border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
                border_radius=ft.border_radius.all(8),
                padding=10,
                expand=True
            )
        ],
            spacing=15,
            expand=True)
    )
    page.update()

# Entry Point
if __name__ == "__main__":
    ft.app(target=main)
