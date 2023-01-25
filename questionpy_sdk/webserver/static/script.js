import * as conditions from "./conditions.js";


function get_elements_with_conditions() {
    let elements_with_conditions = []
    for (const value in conditions.Types.values) {
        const condition_type = new conditions.Types(value);
        document.querySelectorAll(condition_type.to_selector())
            .forEach(element => {
                add_conditions_to_element(element, condition_type)
                elements_with_conditions.push(element);
            });
    }
    return elements_with_conditions;
}


function add_conditions_to_element(element, condition_type) {
    if (!element.conditions) {
        element.conditions = {};
    }
    element.conditions[condition_type.value] = [];
    JSON.parse(element.attributes.getNamedItem(condition_type.value).nodeValue).forEach(object => {
        let condition = conditions.Condition.from_object(object);
        condition.targets.forEach(target => add_source_element_to_target(target, element, condition_type));
        element.conditions[condition_type.value].push(condition);
    });
}


function add_source_element_to_target(target, source, condition_type) {
    if (!target.source_elements) {
        target.source_elements = []
    }
    target.source_elements.push(source);
    target.addEventListener("change", get_listener(condition_type))
}


function get_listener(condition_type) {
    switch(condition_type.value) {
        case conditions.Types.values.hide_if:
            return hide_if_listener;
        case conditions.Types.values.disable_if:
            return disable_if_listener;
    }
}

function hide_if_listener(event) {
    event.currentTarget.source_elements.forEach(element => toggle_visibility(element));
}


function disable_if_listener(event) {
    event.currentTarget.source_elements.forEach(element => toggle_availability(element));
}

function toggle_visibility(element) {
    if (element.conditions[conditions.Types.values.hide_if].every(condition => condition.is_true())) {
        element.style.display = "none";
    } else {
        element.style.display = "inherit";
    }
}


function toggle_availability(element) {
    if (element.conditions[conditions.Types.values.disable_if].every(condition => condition.is_true())) {
        disable(element);
    } else {
        enable(element);
    }
}

function disable(element) {
    element.disabled = true;
    Array.from(element.children).forEach(child => disable(child))
}


function enable(element) {
    element.disabled = false;
    Array.from(element.children).forEach(child => enable(child))
}


function toggle_condition(element, condition_type_value) {
    switch(condition_type_value) {
        case conditions.Types.values.hide_if:
            toggle_visibility(element); break;
        case conditions.Types.values.disable_if:
            toggle_availability(element); break;
    }
}


function check_all_element_conditions(elements) {
    for (const value in conditions.Types.values) {
        Array.from(elements)
            .filter(element => !(element.conditions[value] === undefined || element.conditions[value].length === 0))
            .forEach(element => toggle_condition(element, value));
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const elements = get_elements_with_conditions();
    // check conditions manually. without the change event
    check_all_element_conditions(elements);
})
