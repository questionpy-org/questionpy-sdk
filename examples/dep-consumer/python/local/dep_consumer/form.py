import local.dep

from questionpy.form import (
    FormModel,
    static_text,
)


class MyModel(FormModel):
    static = static_text(
        "The following is defined in local.dep!",
        local.dep.reusable_thing,
    )
