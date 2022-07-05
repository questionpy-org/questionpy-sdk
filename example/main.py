from questionpy.sdk.model.form import ButtonElement, CheckboxElement, CheckboxGroupElement, Form, FormSection, \
    HiddenElement, \
    RadioGroupElement, SelectElement, TextElement, TextInputElement
from questionpy.sdk.qtype import QuestionType


class ExampleQuestionType(QuestionType):

    def render_edit_form(self, form: Form) -> None:
        form.general += [
            TextElement(label="A static text element", name="", text="And this is its content."),
            TextInputElement(label="A text input", name="text_input"),
            ButtonElement(label="A button", name="button"),
            CheckboxElement(label="A single checkbox", name="single_checkbox"),
            CheckboxGroupElement(checkboxes=[
                CheckboxElement(label="A checkbox inside a group", name="grouped_checkbox")
            ]),
            RadioGroupElement(label="A radio group", name="radio", buttons=[
                RadioGroupElement.Option(label="Radio Button 1", value="1"),
                RadioGroupElement.Option(label="Radio Button 2", value="2")
            ]),
            SelectElement(label="A select box", name="select", options=[
                SelectElement.Option(label="Option 1", value="1"),
                SelectElement.Option(label="Option 2", value="2", selected=True)
            ]),
            HiddenElement(name="hidden", value="ill be sent along with the form")
        ]

        form.sections += FormSection(header="Custom Section", elements=[
            TextInputElement(label="I'm inside a section!", name="text_input_in_section")
        ])
