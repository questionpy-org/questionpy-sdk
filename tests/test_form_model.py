from questionpy.form_model import FormModel, text_input


class MyModel(FormModel):
    abcdefg: str = text_input("Mein Label", True)
