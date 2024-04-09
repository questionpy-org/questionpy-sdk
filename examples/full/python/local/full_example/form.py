from questionpy.form import FormModel, static_text


class MyModel(FormModel):
    static = static_text(
        "Some static text",
        """Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
    nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam
    et justo duo dolores et ea rebum.""",
    )
