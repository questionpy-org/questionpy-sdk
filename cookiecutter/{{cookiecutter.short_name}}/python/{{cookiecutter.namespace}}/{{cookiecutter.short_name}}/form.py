from questionpy.form import FormModel, static_text


class MyFormModel(FormModel):
    static = static_text("Explanation", "You can add question options here.")
