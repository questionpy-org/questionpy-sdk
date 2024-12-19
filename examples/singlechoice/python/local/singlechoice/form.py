from questionpy.form import FormModel, OptionEnum, checkbox, generated_id, option, repeat, select, text_input


class ChoiceMode(OptionEnum):
    SELECT = option("<select> element")
    RADIO = option('<input type="radio"> element')


class Choice(FormModel):
    id: str = generated_id()
    text: str = text_input("Text", required=True)
    correct: bool = checkbox("Korrekt")


class SinglechoiceFormModel(FormModel):
    description: str = text_input("Beschreibung", required=True)
    mode: ChoiceMode = select("Auswahlelement", ChoiceMode, required=True)
    choices: list[Choice] = repeat(Choice, initial=3, minimum=2)
