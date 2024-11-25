from questionpy.form import (
    FormModel,
    repeat,
    text_input, checkbox, OptionEnum, option, select
)


class ChoiceMode(OptionEnum):
    SELECT = option("<select> element")
    RADIO = option('<input type="radio"> element')


class Choice(FormModel):
    text: str = text_input("Text", required=True)
    value: str = text_input("Wert", required=True)
    correct: bool = checkbox("Korrekt", required=True)


class MultichoiceFormModel(FormModel):
    mode: ChoiceMode = select("Auswahlelement", ChoiceMode, required=True)
    choices: list[Choice] = repeat(Choice, initial=3, minimum=2)
