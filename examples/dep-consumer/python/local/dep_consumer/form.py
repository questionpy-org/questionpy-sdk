from questionpy.form import (
    FormModel,
    static_text,
)


class MyModel(FormModel):
    static = static_text(
        "",
        local.dep.reusable_thing,
    )
