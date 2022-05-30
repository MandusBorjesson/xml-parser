#! /usr/local/bin/python3

import xml.etree.ElementTree as ET
import dash
import dash_bootstrap_components as dbc
from dash import html


# Default parser
class DefaultParser:
    tag = None
    columns = 1
    def parse(self, element):
        print(f"Unknown tag: {element.tag}")
        content = []
        for child in element:
            content.append(parse_element(child))

        if "columns" in element.attrib:
            cols = int(element.attrib["columns"])
        else:
            cols = self.__class__.columns

        # Fill missing columns with empty space (Prevents stretching of last column)
        missing_elements = cols - (len(content) % cols)
        for _ in range(missing_elements):
            content.append(html.P())

        # Create columns
        rows = []

        if "heading" in element.attrib:
            rows.append(html.H1(element.attrib["heading"]))

        for i in range(0, len(content), cols):
            rows.append(dbc.Row([dbc.Col(j) for j in content[i:i+cols]]))
            rows.append(html.P())

        return html.Div(rows)

# Low-level parsers
class ContentParser:
    def get_content(self, element):
        return element.text.strip()

class TextParser(ContentParser):
    tag = "text"
    def parse(self, element):
        return html.P(self.get_content(element))

class TimeParser(TextParser):
    tag = "time"

class DateParser(TimeParser):
    tag = "date"

class HeadingParser(ContentParser):
    tag = "head"
    def parse(self, element):
        return html.H1(self.get_content(element))

class SubHeadingParser(ContentParser):
    tag = "subhead"
    def parse(self, element):
        return html.H3(self.get_content(element))

class TagParser(ContentParser):
    tag = "tag"
    def parse(self, element):
        return dbc.Badge(self.get_content(element), className="ms-1")

class LinkParser(ContentParser):
    tag = "link"
    def parse(self, element):
        content = self.get_content(element).split(";")
        heading = content[0].strip()
        link = content[1].strip()
        return dbc.Badge(
            heading,
            external_link=True,
            href=link,
            color="primary",
            className="ms-1"
            )

class CurrentParser(ContentParser):
    tag = "current"
    def parse(self, element):
        return dbc.Badge("Current Position", color="success")

class ProgressParser(ContentParser):
    tag = "progress"
    def parse(self, element):
        return dbc.Progress(value=int(self.get_content(element)))

class ImageParser(ContentParser):
    tag = "image"
    def parse(self, element):
        return dbc.Card(dbc.CardImg(
                src=self.get_content(element),
                className="img-fluid rounded-start",
            ))

class ContactParser(ContentParser):
    tag = "contact"
    def parse(self, element):
        button = {}

        for field in element:
            button[field.tag] = self.get_content(field)

        for tag in ["type", "text"]:
            assert tag in button, f"Contacts must contain a '{tag}' field!"

        extraargs = {}
        if "link" in button:
            extraargs = {
                'href': button["link"],
                'external_link': True
            }

        return html.P(dbc.ButtonGroup(
                [
                    dbc.Button(button["type"], outline=False, color="primary"),
                    dbc.Button(
                        button["text"],
                        outline=True,
                        color="primary",
                        **extraargs,
                        ),
                ]
            ))

# High-level parsers
class NiceCard:
    tag = "card"
    def parse(self, element):

        card_head = parse_elements_with_tag(element, ["head", "subhead"])
        card_date = parse_elements_with_tag(element, ["date", "time", "current"])
        card_body = parse_elements_with_tag(element, ["head", "subhead", "date", "time", "current"], invert=True)

        card = [dbc.CardHeader(card_head)]
        if card_date:
            card_date.append(html.Hr(className="my-2"))

        card.append(
            dbc.CardBody(
                card_date
                + card_body)
            )

        return dbc.Card(card)

class AuthorParser:
    tag = "author"
    def parse(self, element):
        card_head = parse_elements_with_tag(element, ["head", "subhead"])
        card_image = parse_elements_with_tag(element, "image")
        card_contact = parse_elements_with_tag(element, "contact")
        card_body = parse_elements_with_tag(element, "text")

        card = [dbc.Col(card_image, width=4)]
        card.append(
            dbc.Col(
                card_head
                + [
                html.Hr(className="my-2"),
                dbc.Row(
                    [
                    dbc.Col(card_body),
                    dbc.Col(card_contact)
                    ]
                )
                ]
            )
        )

        return dbc.Card(dbc.Row(card))


PARSERS = [
    # Low-level
    TextParser,
    TimeParser,
    DateParser,
    HeadingParser,
    SubHeadingParser,
    TagParser,
    CurrentParser,
    LinkParser,
    ImageParser,
    ContactParser,
    ProgressParser,
    # High-level
    NiceCard,
    AuthorParser,
    # Default
    DefaultParser,
]

def get_element_parser(element):
    for parser in PARSERS:
        if parser.tag == element.tag:
            return parser()
    return DefaultParser()

def parse_element(element):
    parser = get_element_parser(element)
    return parser.parse(element)

def get_elements_with_tag(elements, tags, invert=False):
    if type(tags) not in [str, list]:
        raise RuntimeError(f"Cant get elements '{tags}' with type '{type(tags)}'")

    if isinstance(tags, str):
        tags = [tags]

    if invert:
        return [e for e in elements if e.tag not in tags]
    else:
        return [e for e in elements if e.tag in tags]

def parse_elements_with_tag(element, tag, invert=False):
    return [parse_element(e) for e in get_elements_with_tag(element, tag, invert)]

if __name__ == "__main__":

    mytree = ET.parse('input.xml')
    myroot = mytree.getroot()

    content = []
    content.append(parse_element(myroot))

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    CONTENT_STYLE = {
        "margin-left": "3rem",
        "margin-right": "3rem",
        "padding": "2rem 1rem",
    }
    app.layout = html.Div(content, style=CONTENT_STYLE)

    app.run_server(port=8888)