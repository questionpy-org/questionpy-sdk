from itertools import chain
from typing import Union, Sequence, Optional

from questionpy_common.conditions import IsChecked, IsNotChecked, Equals, DoesNotEqual, In
from questionpy_common.elements import OptionsFormDefinition, FormSection, GroupElement, RepetitionElement, \
    FormElement, CanHaveConditions, CheckboxElement, TextInputElement, RadioGroupElement, SelectElement, HiddenElement
from typing_extensions import TypeAlias

_FormNode: TypeAlias = Union[OptionsFormDefinition, FormSection, FormElement]


class FormError(Exception):
    def __init__(self, node: str, message: str):
        self.node = node
        """Absolute name of the form node which caused the error."""
        super().__init__(f"In '{node}': {message}")


class FormReferenceError(FormError):
    def __init__(self, node: str, reference: str, container_name: Optional[str], local_name: str):
        self.reference = reference
        """Full reference which could not be resolved."""
        self.container_name = container_name
        """Container of which a direct child was not found."""
        self.local_name = local_name
        """Local name of the direct child which was not found."""

        message = f"Unresolved reference '{reference}'"
        if container_name:
            message += f" (Element or section '{container_name}' contains no sub-element named '{local_name}')"
        else:
            message += f" (Form contains no general element or section named '{local_name}')"
        super().__init__(node, message)


def _absolute_name(node: Union[_FormNode, str], *nodes: Union[_FormNode, str]) -> str:
    name_parts = []
    for node in (node, *nodes):
        if isinstance(node, str):
            name_parts.append(node)
        elif not isinstance(node, OptionsFormDefinition):
            name_parts.append(node.name)

    return name_parts[0] + "".join(f"[{part}]" for part in name_parts[1:])


def _resolve_reference(reference: str, referee: str, parents: Sequence[_FormNode]) -> _FormNode:
    parents = list(parents)
    parts = reference.replace("]", "").split("[")
    if not parts:
        raise FormError(referee, f"Empty reference: '{reference}'")

    for i, part in enumerate(parts):
        if part == "..":
            parents.pop()
            continue

        children = _get_children(parents[-1])

        matching_children = [child for child in children if hasattr(child, "name") and child.name == part]
        if not matching_children:
            # Element not found.
            raise FormReferenceError(referee, reference, getattr(parents[-1], "name", None), part)
        if len(matching_children) > 1:
            # Ambiguous reference, i.e. duplicate name.
            raise FormError(_absolute_name(*parents, part), "Duplicate element or section name")
        matching_child = matching_children[0]

        if i < len(parts) - 1 and isinstance(matching_child, RepetitionElement):
            # Since each sub-element of a RepetitionElement may be rendered many times, a reference into it would be
            # ambiguous.
            raise FormError(referee, f"Cannot reference repeated element '{reference}' from the outside")

        parents.append(matching_child)

    # Reference points to parents[-1].
    return parents[-1]


def _get_children(node: _FormNode) -> Sequence[_FormNode]:
    if isinstance(node, OptionsFormDefinition):
        return *node.general, *node.sections

    if isinstance(node, (FormSection, GroupElement, RepetitionElement)):
        return node.elements

    # Node is a leaf, i.e. can't have children.
    return []


_valid_referents: dict[type, tuple[type, ...]] = {
    IsChecked: (CheckboxElement,),
    IsNotChecked: (CheckboxElement,),
    Equals: (TextInputElement, CheckboxElement, RadioGroupElement, SelectElement, HiddenElement),
    DoesNotEqual: (TextInputElement, CheckboxElement, RadioGroupElement, SelectElement, HiddenElement),
    In: (TextInputElement, CheckboxElement, RadioGroupElement, SelectElement, HiddenElement)
}


def _validate_node(node: _FormNode, parents: Sequence[_FormNode]) -> None:
    if isinstance(node, CanHaveConditions) and (node.disable_if or node.hide_if):
        abs_name = _absolute_name(*parents, node)

        for condition in chain(node.disable_if, node.hide_if):
            target = _resolve_reference(condition.name, abs_name, parents)

            valid_targets = _valid_referents[type(condition)]
            if not isinstance(target, valid_targets):
                valid_targets_str = ", ".join(klass.__name__ for klass in valid_targets)
                raise FormError(abs_name, f"{type(condition).__name__} condition referent is {type(target).__name__} "
                                          f"but must be one of {valid_targets_str}")

    children = _get_children(node)
    for child in children:
        _validate_node(child, (*parents, node))


def validate_form(form: OptionsFormDefinition) -> None:
    _validate_node(form, [])
